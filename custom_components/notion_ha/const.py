"""Constants for the Notion integration."""

DOMAIN = "notion_ha"

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

DEFAULT_SCAN_INTERVAL = 300  # seconds

CONF_DATABASE_ID = "database_id"
CONF_STATUS_PROPERTY = "status_property"
CONF_ACTIVE_STATUSES = "active_statuses"
CONF_COMPLETED_STATUSES = "completed_statuses"

# Notion property types that can be used as status/section
STATUS_PROPERTY_TYPES = ("select", "status")
