"""AI receptionist conversations.

Bolna → FastAPI (authenticated with AGENT_API_KEY):
  POST /agent/conversations/events   live turn-by-turn updates (optional)
  POST /agent/bolna/webhook?key=...  Bolna's end-of-call execution webhook (transcript)
Admin dashboard:
  GET  /admin/conversations?state=live|history
  GET  /admin/conversations/{id}
  PATCH /admin/conversations/{id}    resolve / escalate
Only real records are stored — nothing is generated here.
"""
import re
from typing import List, Literal, Optional

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

from auth import require_staff, DEFAULT_HOSPITAL_ID
from database import conversations_collection, require_db
from services.common import now, short_id, serialize, require_agent
from services.realtime import hub, admin_room

router = APIRouter(tags=["conversations"])

LIVE = ["active"]


async def broadcast(conv: dict):
    await hub.send(admin_room(conv["hospital_id"]), {"event": "conversation", "conversation": serialize(conv)})


async def upsert(hospital_id: str, external_id: str, **fields) -> dict:
    require_db()
    conv = await conversations_collection.find_one({"hospital_id": hospital_id, "external_id": external_id})
    if not conv:
        conv = {"conversation_id": short_id("CNV-"), "hospital_id": hospital_id, "external_id": external_id,
                "channel": "voice", "status": "active", "messages": [], "started_at": now()}
        await conversations_collection.insert_one(conv)
    changes = {k: v for k, v in fields.items() if v is not None}
    changes["updated_at"] = now()
    await conversations_collection.update_one({"_id": conv["_id"]}, {"$set": changes})
    return await conversations_collection.find_one({"_id": conv["_id"]})


async def record_tool_event(hospital_id: str, external_id: Optional[str], text: str, status: str = None, **fields):
    """Called by the existing tool endpoints when Bolna passes X-Conversation-Id."""
    if not external_id or conversations_collection is None:
        return
    conv = await upsert(hospital_id, external_id, status=status, **fields)
    await conversations_collection.update_one({"_id": conv["_id"]}, {"$push": {"messages": {"role": "system", "text": text, "at": now()}}})
    await broadcast(await conversations_collection.find_one({"_id": conv["_id"]}))


class Message(BaseModel):
    role: Literal["patient", "assistant", "staff", "system"]
    text: str


class ConversationEvent(BaseModel):
    external_id: str
    hospital_id: Optional[str] = None
    patient_name: Optional[str] = None
    phone: Optional[str] = None
    topic: Optional[str] = None
    channel: Optional[str] = None
    status: Optional[Literal["active", "resolved", "escalated"]] = None
    messages: List[Message] = []


@router.post("/agent/conversations/events", dependencies=[Depends(require_agent)])
async def conversation_event(payload: ConversationEvent):
    hid = (payload.hospital_id or DEFAULT_HOSPITAL_ID).upper()
    conv = await upsert(hid, payload.external_id, patient_name=payload.patient_name, phone=payload.phone,
                        topic=payload.topic, channel=payload.channel, status=payload.status)
    if payload.messages:
        await conversations_collection.update_one({"_id": conv["_id"]}, {"$push": {"messages": {"$each": [
            {**m.model_dump(), "at": now()} for m in payload.messages]}}})
    conv = await conversations_collection.find_one({"_id": conv["_id"]})
    await broadcast(conv)
    return {"conversation_id": conv["conversation_id"]}


ROLE_MAP = {"assistant": "assistant", "agent": "assistant", "bot": "assistant", "user": "patient", "human": "patient", "customer": "patient"}


def parse_transcript(transcript: str) -> list:
    out = []
    for line in (transcript or "").splitlines():
        m = re.match(r"^\s*(assistant|agent|bot|user|human|customer)\s*:\s*(.+)$", line, re.I)
        if m:
            out.append({"role": ROLE_MAP[m.group(1).lower()], "text": m.group(2).strip(), "at": now()})
        elif out and line.strip():
            out[-1]["text"] += " " + line.strip()
    return out


@router.post("/agent/bolna/webhook", dependencies=[Depends(require_agent)])
async def bolna_webhook(payload: dict = Body(...), hospital_id: Optional[str] = None):
    """Bolna posts the call execution here. Fields are read defensively; the raw payload is kept."""
    hid = (hospital_id or payload.get("hospital_id") or DEFAULT_HOSPITAL_ID).upper()
    ext = str(payload.get("id") or payload.get("execution_id") or payload.get("call_id") or short_id())
    tel = payload.get("telephony_data") or {}
    extracted = payload.get("extracted_data") or {}
    raw_status = str(payload.get("status") or "").lower()
    status = "active" if raw_status in ("in-progress", "ringing", "initiated", "queued", "in_progress") else "resolved"
    conv = await conversations_collection.find_one({"hospital_id": hid, "external_id": ext})
    if conv and conv.get("status") == "escalated":
        status = "escalated"  # never downgrade an escalation
    conv = await upsert(hid, ext, channel="voice", status=status,
                        phone=tel.get("from_number") or tel.get("to_number") or payload.get("user_number"),
                        patient_name=extracted.get("patient_name") or extracted.get("name"),
                        topic=extracted.get("topic") or payload.get("summary"),
                        duration_seconds=tel.get("duration") or payload.get("conversation_duration"),
                        bolna_status=raw_status, raw=payload)
    msgs = parse_transcript(payload.get("transcript"))
    if msgs:
        await conversations_collection.update_one({"_id": conv["_id"]}, {"$set": {"messages": msgs}})
    conv = await conversations_collection.find_one({"_id": conv["_id"]})
    await broadcast(conv)
    return {"received": True, "conversation_id": conv["conversation_id"]}


def _summary(c: dict) -> dict:
    d = serialize(c)
    d.pop("raw", None)
    msgs = d.pop("messages", [])
    d["message_count"] = len(msgs)
    d["last_message"] = msgs[-1]["text"] if msgs else None
    return d


@router.get("/admin/conversations")
async def list_conversations(user: dict = Depends(require_staff), state: Literal["live", "history", "all"] = "all", limit: int = 100):
    require_db()
    q = {"hospital_id": user["hospital_id"]}
    if state == "live":
        q["status"] = {"$in": LIVE}
    elif state == "history":
        q["status"] = {"$nin": LIVE}
    items = await conversations_collection.find(q).sort("updated_at", -1).to_list(min(limit, 500))
    counts = {"live": await conversations_collection.count_documents({"hospital_id": user["hospital_id"], "status": {"$in": LIVE}}),
              "history": await conversations_collection.count_documents({"hospital_id": user["hospital_id"], "status": {"$nin": LIVE}})}
    return {"conversations": [_summary(c) for c in items], "counts": counts}


@router.get("/admin/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user: dict = Depends(require_staff)):
    require_db()
    c = await conversations_collection.find_one({"hospital_id": user["hospital_id"], "conversation_id": conversation_id})
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found")
    d = serialize(c)
    d.pop("raw", None)
    return {"conversation": d}


class ConversationUpdate(BaseModel):
    status: Literal["active", "resolved", "escalated"]


@router.patch("/admin/conversations/{conversation_id}")
async def update_conversation(conversation_id: str, payload: ConversationUpdate, user: dict = Depends(require_staff)):
    res = await conversations_collection.update_one({"hospital_id": user["hospital_id"], "conversation_id": conversation_id},
                                                    {"$set": {"status": payload.status, "updated_at": now()},
                                                     "$push": {"messages": {"role": "system", "text": f"Marked {payload.status} by {user['username']}", "at": now()}}})
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="Conversation not found")
    c = await conversations_collection.find_one({"hospital_id": user["hospital_id"], "conversation_id": conversation_id})
    await broadcast(c)
    return await get_conversation(conversation_id, user)
