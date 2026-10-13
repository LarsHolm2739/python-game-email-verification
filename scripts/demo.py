import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.signup_service import InfraiClient, SignupRequest, signup_player


def main() -> None:
    recipient = os.environ.get("DEMO_EMAIL_TO")
    if not recipient:
        raise SystemExit("Set DEMO_EMAIL_TO before running the demo")
    result = signup_player(
        InfraiClient(),
        SignupRequest("player-42", recipient, "https://game.example/verify/player-42"),
    )
    print(result)


if __name__ == "__main__":
    main()
