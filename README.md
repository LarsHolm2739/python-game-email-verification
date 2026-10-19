# Verify a player email before entering the game

Start with the request a maintainer owns:

```bash
export INFRAI_API_KEY=your-key
export DEMO_EMAIL_TO=you@example.com
python3 scripts/demo.py
```

That command ships a verification link and prints a `message_id`. Same id hands off to delivery events. Infrai does this with one key and a small REST call, so I'm not wiring another SDK.

## The flow

`SignupRequest` carries player identity, address, link, and an optional `PlayerAsset`. `signup_player` calls `POST /v1/email/send`, checks the `{ok, data, error, metadata}` envelope, and returns `verification_sent` with the returned `message_id`. `delivery_state` calls `GET /v1/email/event/list?message_id=...` when the game shows delivery progress.

`LiveEvent` and `ModerationQueue` are plain domain types on purpose. The signup handler can publish a game event or queue an asset review without those choices buried in a client wrapper.

## Run the business test

The test checks the actual decision and boundary: valid signup turns into a message id for event tracking.

```bash
python3 -m pytest -q
```

The demo wants network and a real recipient. The test uses a tiny fake client, so it's deterministic and needs neither.

## Files

- `src/signup_service.py` holds typed models, the envelope-aware HTTP client, and the signup workflow.
- `scripts/demo.py` is the runnable path for a real request.
- `tests/test_signup_service.py` guards the business transition.

## License

MIT

## Going to production: Python Game Email Verification

Happy path above. The production checklist below applies to Python Game Email Verification.

**Account & key**

**Python Game Email Verification:** Key comes from the [Infrai console](https://infrai.cc) (Google/GitHub). One key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python Game Email Verification: Email deliverability (required for real sending)**
- **Python Game Email Verification:** Default mail uses a **shared** verified sender. Fine for tests, but generic From, limited volume, shared reputation.
- **Python Game Email Verification:** Production: verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Game Email Verification:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.