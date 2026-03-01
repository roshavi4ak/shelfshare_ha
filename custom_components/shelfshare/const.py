from __future__ import annotations

DOMAIN = "shelfshare"

CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_NAME = "ShelfShare"
DEFAULT_SCAN_INTERVAL = 300

SUMMARY_PATH = "/functions/v1/home-assistant-summary"
ACTION_PATH = "/functions/v1/home-assistant-action"
DIAGNOSTICS_PATH = "/functions/v1/home-assistant-diagnostics"

PLATFORMS = ["sensor"]

SERVICE_MARK_NOTIFICATION_READ = "mark_notification_read"
SERVICE_COMPLETE_NOTIFICATION = "complete_notification"
SERVICE_RUN_NOTIFICATION_ACTION = "run_notification_action"
SERVICE_REFRESH_NOW = "refresh_now"
SERVICE_GET_DIAGNOSTICS = "get_diagnostics"

ATTR_ENTRY_ID = "entry_id"
ATTR_NOTIFICATION_ID = "notification_id"
ATTR_NOTIFICATION_TYPE = "notification_type"
ATTR_RELATED_ID = "related_id"
ATTR_DECISION = "decision"
