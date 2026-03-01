# ShelfShare Home Assistant Integration

Custom Home Assistant integration for ShelfShare.

This integration reads from:

- `home-assistant-summary` Edge Function
- `home-assistant-action` Edge Function
- `home-assistant-diagnostics` Edge Function

## Features

- Sensors:
  - Upcoming events
  - Lent out (active)
  - Borrowed (active)
  - Collection games count
  - Libraries count
  - Owned libraries count
  - Unread notifications count
  - Actionable notifications count
  - API health status
- Services:
  - Refresh now (manual pull)
  - Get diagnostics (service response)
  - Mark notification as read
  - Complete notification
  - Run notification action (accept/decline/snooze/view)

## Installation (private custom repository)

1. Put this folder in a dedicated GitHub repo (recommended).
2. In Home Assistant, open HACS → Integrations → three dots → Custom repositories.
3. Add your repo URL and select category **Integration**.
4. Install **ShelfShare** from HACS.
5. Restart Home Assistant.

## Configuration

In Home Assistant:

1. Settings → Devices & Services → Add Integration.
2. Search for **ShelfShare**.
3. Enter:
   - ShelfShare Supabase project URL (`https://<project-ref>.supabase.co`)
   - ShelfShare Home Assistant API key (from ShelfShare My Account page)
   - Optional name

## Services

- `shelfshare.refresh_now`
  - `entry_id` (str, optional)
- `shelfshare.get_diagnostics`
  - `entry_id` (str, optional)
  - Returns local coordinator status + backend diagnostics, including rate-limit usage.
- `shelfshare.mark_notification_read`
  - `notification_id` (int, required)
- `shelfshare.complete_notification`
  - `notification_id` (int, required)
- `shelfshare.run_notification_action`
  - `notification_id` (int, required)
  - `notification_type` (str, required: `library_invite|event_invite|lend_request|game_table_request|game_event_request`)
  - `related_id` (str, required)
  - `decision` (accept|decline|snooze|view, optional, default `view`)

## Examples

- Lovelace dashboard example:
  - `examples/lovelace-dashboard.yaml`
- Service-call examples for Developer Tools:
  - `examples/service-calls.yaml`

## Notes

- Keep the API key secret.
- Revoke compromised keys from ShelfShare My Account.
- Polling interval is configurable in integration options.
- Duplicate `run_notification_action` calls are idempotency-guarded server-side.

## CI Validation

- GitHub Actions workflow: `.github/workflows/home-assistant-integration-check.yml`
- It validates required integration files, JSON/YAML syntax, and Python syntax for `custom_components/shelfshare`.

## Release Packaging

- Local packaging script:
  - `python home_assistant/shelfshare/scripts/package_release.py --version 0.3.0`
  - Output zip goes to `home_assistant/shelfshare/dist/`
- GitHub workflow (manual):
  - `.github/workflows/home-assistant-package.yml`
  - Run via **Actions → Package Home Assistant Integration** and provide a version label.
- Release process checklist:
  - `RELEASE_CHECKLIST.md`
  - `CHANGELOG.md`
  - `RELEASE_NOTES_TEMPLATE.md`
  - Includes a **Quick-Start Test Matrix (10 minutes)** for release smoke tests.

## API Smoke Test

- Summary only:
  - `python home_assistant/shelfshare/scripts/smoke_test_endpoints.py --base-url https://<project-ref>.supabase.co --api-key <ha_api_key>`
- Summary + action test:
  - `python home_assistant/shelfshare/scripts/smoke_test_endpoints.py --base-url https://<project-ref>.supabase.co --api-key <ha_api_key> --test-action mark_notification_read --notification-id 123`
- Summary + notification_action test:
  - `python home_assistant/shelfshare/scripts/smoke_test_endpoints.py --base-url https://<project-ref>.supabase.co --api-key <ha_api_key> --test-action notification_action --notification-id 123 --notification-type lend_request --related-id 456 --decision accept`