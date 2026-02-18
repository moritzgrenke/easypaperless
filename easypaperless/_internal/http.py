"""HTTP session with auth, error mapping, and pagination."""

from __future__ import annotations

from typing import Any

import httpx

from easypaperless.exceptions import (
    AuthError,
    NotFoundError,
    PaperlessError,
    ServerError,
    ValidationError,
)


class HttpSession:
    def __init__(self, base_url: str, api_key: str) -> None:
        # Normalize: strip trailing slash, then append /api
        self._base_url = base_url.rstrip("/") + "/api"
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers={"Authorization": f"Token {self._api_key}"},
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text

        status = response.status_code
        if status in (401, 403):
            raise AuthError(detail, status_code=status)
        elif status == 404:
            raise NotFoundError(detail, status_code=status)
        elif status == 422:
            raise ValidationError(detail, status_code=status)
        elif status >= 500:
            raise ServerError(detail, status_code=status)
        else:
            raise PaperlessError(detail, status_code=status)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: dict[str, Any] | None = None,
        files: Any = None,
    ) -> httpx.Response:
        client = self._get_client()
        try:
            response = await client.request(
                method,
                path,
                params=params,
                json=json,
                data=data,
                files=files,
            )
        except httpx.HTTPError as exc:
            raise ServerError(str(exc)) from exc
        self._raise_for_status(response)
        return response

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        return await self.request("GET", path, params=params)

    async def post(
        self,
        path: str,
        *,
        json: Any = None,
        data: dict[str, Any] | None = None,
        files: Any = None,
    ) -> httpx.Response:
        return await self.request("POST", path, json=json, data=data, files=files)

    async def patch(self, path: str, *, json: Any = None) -> httpx.Response:
        return await self.request("PATCH", path, json=json)

    async def delete(self, path: str) -> httpx.Response:
        return await self.request("DELETE", path)

    async def get_all_pages(self, path: str, params: dict[str, Any] | None = None) -> list[dict]:
        results: list[dict] = []
        # First page — use path relative to base_url
        response = await self.get(path, params=params)
        page = response.json()
        results.extend(page.get("results", []))

        next_url: str | None = page.get("next")
        while next_url:
            # next is absolute; pass it directly to the client
            client = self._get_client()
            try:
                response = await client.get(next_url)
            except httpx.HTTPError as exc:
                raise ServerError(str(exc)) from exc
            self._raise_for_status(response)
            page = response.json()
            results.extend(page.get("results", []))
            next_url = page.get("next")

        return results
