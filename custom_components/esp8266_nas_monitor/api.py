from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
from yarl import URL


class EspNasMonitorApi:
    """Small HTTP client for ESP8266 NAS Monitor."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self._session = session
        self._host = host.strip().replace("http://", "").replace("https://", "").strip("/")
        self._port = int(port)
        self._username = username or None
        self._password = password or None

    def _url(self, path: str) -> str:
        return str(URL.build(scheme="http", host=self._host, port=self._port, path=path))

    def _auth(self) -> aiohttp.BasicAuth | None:
        if self._username and self._password:
            return aiohttp.BasicAuth(self._username, self._password)
        return None

    async def _get_json(self, path: str) -> dict[str, Any]:
        try:
            async with self._session.get(
                self._url(path),
                auth=self._auth(),
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status in (401, 403):
                    raise PermissionError("ESP authentication failed")
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except asyncio.TimeoutError as exc:
            raise ConnectionError("ESP request timed out") from exc
        except aiohttp.ClientError as exc:
            raise ConnectionError(f"ESP request failed: {exc}") from exc

    async def _get_text(self, path: str) -> str:
        try:
            async with self._session.get(
                self._url(path),
                auth=self._auth(),
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status in (401, 403):
                    raise PermissionError("ESP authentication failed")
                resp.raise_for_status()
                return await resp.text()
        except asyncio.TimeoutError as exc:
            raise ConnectionError("ESP request timed out") from exc
        except aiohttp.ClientError as exc:
            raise ConnectionError(f"ESP request failed: {exc}") from exc

    async def status(self) -> dict[str, Any]:
        """Return display status."""
        return await self._get_json("/api/display/status")

    async def turn_on(self) -> None:
        """Turn screen on."""
        await self._get_text("/api/display/on")

    async def turn_off(self) -> None:
        """Turn screen off."""
        await self._get_text("/api/display/off")

    async def test_connection(self) -> None:
        """Validate connectivity and credentials."""
        await self.status()
