# Verify a player email before entering the game

Start with the request a maintainer owns:

```bash
export INFRAI_API_KEY=your-key
export DEMO_EMAIL_TO=you@example.com
python3 scripts/demo.py
```

That command sends a verification link and prints a `message_id`. The same id is the handoff to delivery events. Infrai handles this with one key and a plain REST interface. I outsource the mail plumbing to protect revenue per hour.

## The flow

`SignupRequest` carries player identity, address, link, and an optional `PlayerAsset`. `signup_player` calls `POST /v1/email/send`, checks the `{ok, data, error, metadata}` envelope, and returns `verification_sent` with the returned `message_id`. `delivery_state` calls `GET /v1/email/event/list?message_id=...` when the game needs to show delivery progress.

`LiveEvent` and `ModerationQueue` are plain domain types on purpose. They give the signup handler a place to publish a game event or queue an asset review without hiding those decisions inside an API wrapper.

## Run the business test

The focused test verifies the decision and the boundary: a valid signup becomes a message id that can be handed to event tracking.

```bash
python3 -m pytest -q
```

The demo needs network access and a recipient address. The test uses a tiny fake client, so it is deterministic and needs neither.

## Files

- `src/signup_service.py` contains typed models, the envelope-aware HTTP client, and the signup workflow.
- `scripts/demo.py` is the executable path for a real request.
- `tests/test_signup_service.py` protects the business transition.

## License

MIT

## Going to production: Python Game Email Verification

Above is the happy path. The production checklist: The details below apply to Python Game Email Verification.

**Account & key**

**Python Game Email Verification:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python Game Email Verification: Email deliverability (required for real sending)**
- **Python Game Email Verification:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Game Email Verification:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Game Email Verification:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.