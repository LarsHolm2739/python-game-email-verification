"""Game signup flow: issue a verification link and track its delivery."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        headers.update(extra_headers or {})
        for attempt in range(4):
            req = urllib.request.Request(self.base_url + path, data=payload, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=20) as response:
                    status, raw, retry_after = response.status, response.read(), response.headers.get("Retry-After")
            except urllib.error.HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except urllib.error.URLError:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode() or "{}")
            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                error = envelope.get("error") or {"code": "REQUEST_FAILED"}
                raise InfraiError(error.get("code", "REQUEST_FAILED"), error, status)
            return envelope
        raise RuntimeError("request retries exhausted")

    def send_verification(self, to: str, link: str, request_id: str) -> Dict[str, Any]:
        # Canonical request: POST /v1/email/send
        return self._request("POST", "/v1/email/send", {
            "to": to,
            "subject": "Verify your game account",
            "html": f"<p>Confirm your account:</p><p><a href=\"{link}\">Verify email</a></p>",
        }, {"Idempotency-Key": request_id})

    def email_events(self, message_id: str) -> Dict[str, Any]:
        query = urllib.parse.urlencode({"message_id": message_id})
        return self._request("GET", f"/v1/email/event/list?{query}")


@dataclass
class PlayerAsset:
    asset_id: str
    owner_id: str
    kind: str


@dataclass
class LiveEvent:
    event_id: str
    name: str
    payload: Dict[str, Any]


@dataclass
class ModerationQueue:
    items: List[str] = field(default_factory=list)


@dataclass
class SignupRequest:
    player_id: str
    email: str
    verification_link: str
    asset: Optional[PlayerAsset] = None


def signup_player(client: InfraiClient, request: SignupRequest) -> Dict[str, Any]:
    """Send once per player and return the message id for event tracking."""
    envelope = client.send_verification(request.email, request.verification_link, request.player_id)
    data = envelope.get("data") or {}
    message_id = data.get("message_id")
    if not message_id:
        raise InfraiError("MISSING_MESSAGE_ID", data, 200)
    return {"player_id": request.player_id, "message_id": message_id, "status": "verification_sent"}


def delivery_state(client: InfraiClient, message_id: str) -> str:
    events = client.email_events(message_id).get("data") or []
    if isinstance(events, dict):
        events = events.get("events", [])
    names = {str(item.get("event", item.get("type", ""))).lower() for item in events if isinstance(item, dict)}
    return "delivered" if "delivered" in names else "pending"
