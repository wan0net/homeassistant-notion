"""Async Notion API client."""
from __future__ import annotations

import re
from typing import Any

import aiohttp

from .const import NOTION_API_BASE, NOTION_VERSION


def parse_database_id(value: str) -> str:
    """Accept a raw UUID or a Notion URL and return a clean UUID."""
    # Strip URL cruft: https://www.notion.so/Title-<id> or notion.so/<id>
    match = re.search(r"([0-9a-f]{32})", value.replace("-", ""))
    if match:
        raw = match.group(1)
        return f"{raw[:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:]}"
    return value


class NotionClient:
    """Thin async wrapper around the Notion REST API."""

    def __init__(self, session: aiohttp.ClientSession, api_key: str) -> None:
        self._session = session
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def get_database(self, database_id: str) -> dict[str, Any]:
        """Retrieve database metadata including schema."""
        url = f"{NOTION_API_BASE}/databases/{database_id}"
        async with self._session.get(url, headers=self._headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def query_database(
        self,
        database_id: str,
        filter_payload: dict | None = None,
    ) -> list[dict[str, Any]]:
        """Query all pages from a database, handling pagination."""
        url = f"{NOTION_API_BASE}/databases/{database_id}/query"
        pages: list[dict] = []
        payload: dict[str, Any] = {"page_size": 100}
        if filter_payload:
            payload["filter"] = filter_payload

        while True:
            async with self._session.post(
                url, headers=self._headers, json=payload
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()

            pages.extend(data.get("results", []))

            if not data.get("has_more"):
                break
            payload["start_cursor"] = data["next_cursor"]

        return pages

    async def update_page(
        self, page_id: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """Update properties on a Notion page."""
        url = f"{NOTION_API_BASE}/pages/{page_id}"
        async with self._session.patch(
            url, headers=self._headers, json={"properties": properties}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def create_page(
        self, database_id: str, properties: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new page in a database."""
        url = f"{NOTION_API_BASE}/pages"
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties,
        }
        async with self._session.post(
            url, headers=self._headers, json=payload
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def archive_page(self, page_id: str) -> dict[str, Any]:
        """Archive (soft-delete) a Notion page."""
        url = f"{NOTION_API_BASE}/pages/{page_id}"
        async with self._session.patch(
            url, headers=self._headers, json={"archived": True}
        ) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def validate_api_key(self) -> bool:
        """Check that the API key is valid."""
        url = f"{NOTION_API_BASE}/users/me"
        async with self._session.get(url, headers=self._headers) as resp:
            return resp.status == 200
