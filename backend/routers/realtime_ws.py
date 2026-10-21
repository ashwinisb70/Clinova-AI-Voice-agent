from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from auth import decode_access_token, STAFF_ROLES, DEFAULT_HOSPITAL_ID
from services.realtime import hub, admin_room, patient_room

router = APIRouter()


@router.websocket("/ws")
async def ws(websocket: WebSocket, token: str):
    """Live events. Connect with ws://host/ws?token=<JWT>. Admins get hospital-wide events,
    patients only their own."""
    try:
        payload = decode_access_token(token)
    except HTTPException:
        await websocket.close(code=4401)
        return
    role, hid = payload.get("role"), payload.get("hid") or DEFAULT_HOSPITAL_ID
    room = admin_room(hid) if role in STAFF_ROLES else patient_room(payload.get("sub")) if role == "patient" else None
    if room is None:
        await websocket.close(code=4403)
        return
    await websocket.accept()
    await hub.join(room, websocket)
    try:
        while True:
            await websocket.receive_text()  # keep-alive pings from the client
    except WebSocketDisconnect:
        hub.leave(room, websocket)
