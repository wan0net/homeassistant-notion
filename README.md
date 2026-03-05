# Notion for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=wan0net&repository=homeassistant-notion&category=integration)

A Home Assistant custom integration that connects your Notion databases to HA. A single HACS install gives you:

- **Todo list entity** — create, update, and check off tasks; changes write back to Notion instantly.
- **Kanban sensor** — structured state attributes for the included kanban card.
- **`notion-kanban-card`** — a built-in custom Lovelace card: columns per status, drag-and-drop, click-to-move popup, label chips, due dates, and an *Archive All* button. No third-party cards needed.

## Features

- Works with any Notion database that has a `select` or `status` property for task state
- Configurable active and completed status values — no hard-coded column names
- Full write-back: create, rename, complete, and delete tasks from HA, or drag tasks between kanban columns
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

The integration automatically registers `notion-kanban-card` as a Lovelace resource on first setup — no manual resource steps needed.

### Manual

1. Copy `custom_components/notion_ha/` into your HA `custom_components/` directory.
2. Restart Home Assistant.

The integration registers the card JS and Lovelace resource automatically on startup.

## Setup

### 1. Create a Notion integration

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **New integration**, give it a name (e.g. "Home Assistant"), select your workspace
3. Copy the **Internal Integration Token**

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

Add a **Manual card** to your Lovelace dashboard:

```yaml
type: custom:notion-kanban-card
entity: sensor.personal_to_do_kanban
```

The entity name is derived from your database name. If your database is called "Personal To-Do", the sensor is `sensor.personal_to_do_kanban`. You can confirm the exact name in **Settings → Devices & Services → Notion**.

#### Card configuration

```yaml
type: custom:notion-kanban-card
entity: sensor.my_notion_kanban   # required
title: My Tasks                   # optional — overrides entity friendly name
hide_sections:                    # optional — columns to hide, default: [Archive]
  - Archive
archive_all_section: Done         # optional — column that shows the Archive All button
```

#### Drag-and-drop write-back

Moving a card between columns calls the `notion_ha.set_item_status` HA service, which updates the page status in Notion immediately. Clicking a task opens a popup to choose the target column without drag-and-drop.

The **Archive All** button on the configured column calls `notion_ha.archive_done`, which moves all completed (non-archive) items to the archive status in Notion.

### HA Services

You can also call these services from automations or scripts:

| Service | Fields | Description |
|---------|--------|-------------|
| `notion_ha.set_item_status` | `item_id`, `status` | Set the status of a Notion page |
| `notion_ha.archive_done` | `archive_status` (optional, default `Archive`) | Move all completed items to the archive status |

## Limitations

- Image attachments on Notion pages are not fetched.
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
