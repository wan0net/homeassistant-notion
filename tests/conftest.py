"""Shared fixtures for Notion integration tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


MOCK_API_KEY = "secret_test_api_key_123"
MOCK_DATABASE_ID = "b5c3f873-ce91-428d-8c69-69bdebc9bb25"


def make_page(
    page_id: str,
    title: str,
    status: str,
    due: str | None = None,
    archived: bool = False,
) -> dict:
    """Build a minimal Notion page dict."""
    return {
        "id": page_id,
        "archived": archived,
        "url": f"https://www.notion.so/{page_id.replace('-', '')}",
        "properties": {
            "Name": {
                "type": "title",
                "title": [{"plain_text": title}],
            },
            "Status": {
                "type": "select",
                "select": {"name": status} if status else None,
            },
            "Due": {
                "type": "date",
                "date": {"start": due} if due else None,
            },
        },
    }


def make_database(options: list[str]) -> dict:
    """Build a minimal Notion database dict with a select Status property."""
    return {
        "title": [{"plain_text": "Personal To-Do"}],
        "properties": {
            "Name": {"type": "title"},
            "Status": {
                "type": "select",
                "select": {
                    "options": [{"name": o, "color": "default"} for o in options]
                },
            },
            "Due": {"type": "date"},
        },
    }


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.validate_api_key = AsyncMock(return_value=True)
    client.get_database = AsyncMock(
        return_value=make_database(
            ["Do Next", "Doing", "To Do Soon", "On Hold", "Long Term", "Done", "Archive"]
        )
    )
    client.query_database = AsyncMock(
        return_value=[
            make_page("page-1", "Buy groceries", "Do Next", due="2026-03-06"),
            make_page("page-2", "Fix homelab", "Doing"),
            make_page("page-3", "Read book", "Long Term"),
            make_page("page-4", "Old task", "Done"),
            make_page("page-5", "Archived task", "Done", archived=True),
        ]
    )
    client.update_page = AsyncMock(return_value={})
    client.create_page = AsyncMock(return_value=make_page("page-new", "New task", "Do Next"))
    client.archive_page = AsyncMock(return_value={})
    return client
