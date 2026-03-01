# ShelfShare Home Assistant Release Checklist

Use this checklist for each integration release.

## 1) Prep

- [ ] Update version in `custom_components/shelfshare/manifest.json`
- [ ] Add/update release entry in `CHANGELOG.md`
- [ ] Confirm `README.md` and examples are current
- [ ] Confirm backend endpoints are deployed:
  - `home-assistant-summary`
  - `home-assistant-action`
  - `home-assistant-diagnostics`

## 2) Validate

- [ ] Run integration CI check workflow:
  - `.github/workflows/home-assistant-integration-check.yml`
- [ ] Run endpoint smoke test script (summary at minimum):
  - `python home_assistant/shelfshare/scripts/smoke_test_endpoints.py --base-url https://<project-ref>.supabase.co --api-key <ha_api_key>`
  - Optional action smoke test:
    - `python home_assistant/shelfshare/scripts/smoke_test_endpoints.py --base-url https://<project-ref>.supabase.co --api-key <ha_api_key> --test-action notification_action --notification-id <id> --notification-type lend_request --related-id <related_id> --decision view`
- [ ] Validate local package build:
  - `python home_assistant/shelfshare/scripts/package_release.py --version <version>`
- [ ] Confirm zip appears in `home_assistant/shelfshare/dist/`

## 3) Publish

- [ ] Trigger workflow:
  - `.github/workflows/home-assistant-package.yml`
- [ ] Download generated artifact
- [ ] Prepare release notes from `RELEASE_NOTES_TEMPLATE.md`
- [ ] Publish/update release in integration repository (if split repo is used)
- [ ] Ensure HACS custom repository points to the latest release

## 4) Verify in Home Assistant

- [ ] Update/install integration from HACS
- [ ] Configure integration with base URL and ShelfShare API key
- [ ] Confirm sensors populate values
- [ ] Run service tests:
  - `shelfshare.refresh_now`
  - `shelfshare.get_diagnostics`
  - `shelfshare.mark_notification_read`
  - `shelfshare.complete_notification`
  - `shelfshare.run_notification_action`
- [ ] Confirm ShelfShare UI reflects notification action changes

## 5) Post-release

- [ ] Revoke any temporary test API keys
- [ ] Record release notes and known limitations
- [ ] Open follow-up tasks for enhancements or bug fixes

---

## Quick-Start Test Matrix (10 minutes)

Use this matrix for fast smoke testing before/after release.

| Area | Check | Pass Criteria |
|---|---|---|
| Local package | Run `python home_assistant/shelfshare/scripts/package_release.py --version smoke` | Zip is created in `home_assistant/shelfshare/dist/` |
| HACS install | Install/update from custom repository | Integration installs without errors |
| Config flow | Add integration with valid base URL + API key | Entry created successfully |
| Sensor sync | Wait one polling cycle or reload entry | All ShelfShare sensors show non-`unknown` values |
| API health sensor | Open `sensor.shelfshare_api_health` | State is `ok`, `degraded`, `rate_limited`, or `auth_error` |
| Events data | Open `sensor.shelfshare_upcoming_events` attributes | `events` list present (can be empty) |
| Notifications data | Open `sensor.shelfshare_unread_notifications` attributes | `notifications` list present |
| Refresh service | Call `shelfshare.refresh_now` | Coordinator refresh executes successfully |
| Diagnostics service | Call `shelfshare.get_diagnostics` | Response includes `local` and `server` blocks |
| Mark read service | Call `shelfshare.mark_notification_read` | Target notification is marked read in ShelfShare |
| Complete service | Call `shelfshare.complete_notification` | Target notification is completed in ShelfShare |
| Action service | Call `shelfshare.run_notification_action` with valid type/decision | Notification action applies successfully |
| Error path | Configure with revoked key | Integration reports auth failure cleanly |
