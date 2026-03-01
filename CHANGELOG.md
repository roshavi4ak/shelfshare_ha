# Changelog

All notable changes to the ShelfShare Home Assistant integration are documented in this file.

## [0.3.1] - 2026-03-01

### Fixed
- Summary endpoint now counts libraries and upcoming events using the same membership rules as the app (`owner/creator OR members`).
- `libraries_count` and `owned_libraries_count` now match app data for users who own libraries but are not explicitly in `members`.

### Changed
- Added richer sensor attributes:
	- `sensor.shelfshare_libraries` includes `libraries`
	- `sensor.shelfshare_owned_libraries` includes owned `libraries`
	- `sensor.shelfshare_collection_games` includes `collection_preview`
	- lend/borrow sensors now expose direction-specific active lend lists.

## [0.3.0] - 2026-03-01

### Added
- New `shelfshare.get_diagnostics` service with response payload support.
- New `sensor.shelfshare_api_health` diagnostic sensor.
- New backend endpoint `home-assistant-diagnostics` for key health and rate-limit visibility.
- Server-side idempotency guard for duplicate `notification_action` calls.

### Changed
- Integration manifest version bumped to `0.3.0`.
- Release docs/checklist expanded for diagnostics endpoint/service validation.

## [0.2.0] - 2026-02-28

### Added
- New `shelfshare.refresh_now` service for immediate coordinator refresh.
- Backend request telemetry table and endpoint logging for Home Assistant API traffic.
- Endpoint-side API key rate limiting controls for summary/action calls.

### Changed
- Integration manifest version bumped to `0.2.0`.
- Release checklist now requires changelog + release notes template usage.

## [0.1.0] - 2026-02-28

### Added
- Initial ShelfShare Home Assistant custom integration.
- Sensors for upcoming events, lending/borrowing counts, collection/library counts, unread/actionable notifications.
- Services for `mark_notification_read`, `complete_notification`, and `run_notification_action`.
- Packaging workflow, release script, and smoke-test script.
