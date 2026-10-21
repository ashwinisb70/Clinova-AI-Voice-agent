from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user, STAFF_ROLES
from database import notifications_collection, require_db
from services.common import serialize

router = APIRouter(prefix="/notifications", tags=["notifications"])


def scope_for(user: dict) -> dict:
    if user["role"] == "patient":
        return {"hospital_id": user["hospital_id"], "audience": "patient", "patient_id": user["username"]}
    if user["role"] in STAFF_ROLES:
        return {"hospital_id": user["hospital_id"], "audience": "admin"}
    raise HTTPException(status_code=403, detail="Not allowed")


@router.get("")
async def list_notifications(user: dict = Depends(get_current_user), unread_only: bool = False, limit: int = 50):
    require_db()
    q = scope_for(user)
    if unread_only:
        q["read"] = False
    items = await notifications_collection.find(q).sort("created_at", -1).to_list(min(limit, 200))
    unread = await notifications_collection.count_documents({**scope_for(user), "read": False})
    return {"notifications": serialize(items), "unread": unread}


@router.get("/unread-count")
async def unread_count(user: dict = Depends(get_current_user)):
    require_db()
    return {"unread": await notifications_collection.count_documents({**scope_for(user), "read": False})}


@router.post("/read-all")
async def read_all(user: dict = Depends(get_current_user)):
    await notifications_collection.update_many({**scope_for(user), "read": False}, {"$set": {"read": True}})
    return {"success": True}


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, user: dict = Depends(get_current_user)):
    res = await notifications_collection.update_one({**scope_for(user), "notification_id": notification_id}, {"$set": {"read": True}})
    if not res.matched_count:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}
