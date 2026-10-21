"""In-process WebSocket hub for live admin/patient updates (notifications, AI conversations).
For multiple server workers, replace the in-memory sets with Redis pub/sub — the API stays the same."""
import json
from typing import Dict, Set, Tuple

from fastapi import WebSocket


class Hub:
    def __init__(self):
        self.rooms: Dict[Tuple, Set[WebSocket]] = {}

    async def join(self, room: Tuple, ws: WebSocket):
        self.rooms.setdefault(room, set()).add(ws)

    def leave(self, room: Tuple, ws: WebSocket):
        self.rooms.get(room, set()).discard(ws)

    async def send(self, room: Tuple, event: dict):
        dead = []
        for ws in list(self.rooms.get(room, ())):
            try:
                await ws.send_text(json.dumps(event, default=str))
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self.leave(room, ws)


hub = Hub()


def admin_room(hospital_id: str):
    return ("admin", hospital_id)


def patient_room(patient_id: str):
    return ("patient", patient_id)
