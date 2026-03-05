"""Tests for the Notion API client."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.notion_ha.notion_client import NotionClient, parse_database_id


# --- parse_database_id ---

@pytest.mark.parametrize(
    "input_value, expected",
    [
        # Raw UUID
        (
            "b5c3f873-ce91-428d-8c69-69bdebc9bb25",
            "b5c3f873-ce91-428d-8c69-69bdebc9bb25",
        ),
        # Notion URL with title prefix
        (
            "https://www.notion.so/Personal-To-Do-b5c3f873ce91428d8c6969bdebc9bb25",
            "b5c3f873-ce91-428d-8c69-69bdebc9bb25",
        ),
        # Bare 32-char hex
        (
            "b5c3f873ce91428d8c6969bdebc9bb25",
            "b5c3f873-ce91-428d-8c69-69bdebc9bb25",
        ),
    ],
)
def test_parse_database_id(input_value, expected):
    assert parse_database_id(input_value) == expected


# --- NotionClient ---

def _make_response(status: int, json_data: dict):
    resp = MagicMock()
    resp.status = status
    resp.raise_for_status = MagicMock()
    resp.json = AsyncMock(return_value=json_data)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    return resp


@pytest.fixture
def session():
    s = MagicMock()
    return s


@pytest.fixture
def client(session):
    return NotionClient(session, "secret_test_key")


@pytest.mark.asyncio
async def test_validate_api_key_success(client, session):
    resp = MagicMock()
    resp.status = 200
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    session.get = MagicMock(return_value=resp)

    result = await client.validate_api_key()
    assert result is True


@pytest.mark.asyncio
async def test_validate_api_key_failure(client, session):
    resp = MagicMock()
    resp.status = 401
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=False)
    session.get = MagicMock(return_value=resp)

    result = await client.validate_api_key()
    assert result is False


@pytest.mark.asyncio
async def test_query_database_single_page(client, session):
    """Single page of results (no pagination)."""
    resp = _make_response(
        200,
        {
            "results": [{"id": "page-1"}, {"id": "page-2"}],
            "has_more": False,
        },
    )
    session.post = MagicMock(return_value=resp)

    pages = await client.query_database("db-id")
    assert len(pages) == 2
    assert pages[0]["id"] == "page-1"


@pytest.mark.asyncio
async def test_query_database_pagination(client, session):
    """Results spread across two pages."""
    first = _make_response(
        200,
        {
            "results": [{"id": "page-1"}],
            "has_more": True,
            "next_cursor": "cursor-abc",
        },
    )
    second = _make_response(
        200,
        {
            "results": [{"id": "page-2"}],
            "has_more": False,
        },
    )
    session.post = MagicMock(side_effect=[first, second])

    pages = await client.query_database("db-id")
    assert len(pages) == 2
    assert pages[1]["id"] == "page-2"


@pytest.mark.asyncio
async def test_update_page(client, session):
    resp = _make_response(200, {"id": "page-1"})
    session.patch = MagicMock(return_value=resp)

    result = await client.update_page("page-1", {"Status": {"select": {"name": "Done"}}})
    assert result["id"] == "page-1"


@pytest.mark.asyncio
async def test_archive_page(client, session):
    resp = _make_response(200, {"id": "page-1", "archived": True})
    session.patch = MagicMock(return_value=resp)

    result = await client.archive_page("page-1")
    assert result["archived"] is True
