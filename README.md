# Notion for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=wan0net&repository=homeassistant-notion&category=integration)

A Home Assistant custom integration that connects your Notion databases to HA, exposing:

- **Todo list entity** — create, update, and check off tasks. Changes write back to Notion instantly.
- **Kanban sensor** — outputs a Todoist-compatible JSON structure for use with kanban Lovelace cards such as [todoist-kanban-card](https://github.com/corte/todoist-kanban-card) or [power-todoist-card](https://github.com/pgorod/power-todoist-card).

## Features

- Works with any Notion database that has a `select` or `status` property for task state
- Configurable active and completed status values — no hard-coded column names
- Full write-back: create, rename, complete, and delete tasks from HA
- Configurable poll interval (default 5 min)
- Supports multiple databases as separate config entries

## Requirements

- Home Assistant 2024.1+
- A Notion internal integration with access to your database

## Installation

### Via HACS (recommended)

1. In HACS, go to **Integrations** → three-dot menu → **Custom repositories**
2. Add `https://github.com/wan0net/homeassistant-notion` as an **Integration**
3. Search for "Notion" in HACS and install
4. Restart Home Assistant

### Manual

Copy `custom_components/notion_ha/` into your HA `custom_components/` directory and restart.

## Setup

### 1. Create a Notion integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **New integration**, give it a name (e.g. "Home Assistant"), select your workspace
3. Copy the **Internal Integration Token** (starts with `secret_`)

### 2. Share your database with the integration

1. Open the database in Notion
2. Click **...** → **Connections** → find your integration and connect it

### 3. Add the integration to Home Assistant

1. Go to **Settings** → **Devices & Services** → **Add Integration**
2. Search for **Notion**
3. Enter your API key
4. Paste the database URL or ID
5. Select the property used for task status and configure which values are active vs completed

## Usage

### Todo card

Add a **Todo** card to any dashboard and select the Notion todo entity. You can create, complete, and delete tasks directly from HA — all changes sync back to Notion.

### Kanban card

Install [todoist-kanban-card](https://github.com/corte/todoist-kanban-card) or [power-todoist-card](https://github.com/pgorod/power-todoist-card) via HACS.

Configure a REST sensor pointing at the Notion kanban sensor entity:

```yaml
# In your Lovelace card config
type: custom:todoist-kanban-card
entity: sensor.personal_to_do_kanban
```

The sensor's state attributes expose `sections` (kanban columns) and `items` (tasks) in the format these cards expect.

## Limitations

- Kanban card drag-and-drop write-back is not supported (cards are hardcoded to Todoist's API). Use the HA Todo card for write-back, or update status directly in Notion.
- Image attachments on pages are not fetched.
- Notion API rate limit: 3 requests/second. With large databases and short poll intervals you may hit this; increase the poll interval in Options if needed.

## License

MIT License — see [LICENSE](LICENSE).

## Attribution

This integration was developed with the assistance of [Claude](https://claude.ai) (Anthropic). Contributions and improvements welcome.

## Development

```bash
pip install -r requirements-dev.txt
pytest
```
