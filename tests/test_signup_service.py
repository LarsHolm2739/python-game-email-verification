from src.signup_service import SignupRequest, signup_player


class FakeClient:
    def send_verification(self, to, link, request_id):
        assert to == "player@example.com"
        assert link.endswith("/p1")
        return {"ok": True, "data": {"message_id": "msg-1"}}


def test_signup_returns_message_for_event_handoff():
    result = signup_player(FakeClient(), SignupRequest("p1", "player@example.com", "https://game/verify/p1"))
    assert result == {"player_id": "p1", "message_id": "msg-1", "status": "verification_sent"}
