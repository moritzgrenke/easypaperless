"""HTTP session with auth, error mapping, and pagination."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from easypaperless.exceptions import (
    AuthError,
    NotFoundError,
    PaperlessError,
    ServerError,
    ValidationError,
)

logger = logging.getLogger(__name__)


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
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _raise_for_status(self, response: httpx.Response, method: str, path: str) -> None:
        if response.is_success:
            return
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text

        status = response.status_code
        logger.warning("HTTP %s on %s %s — %s", status, method.upper(), path, detail)
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
        logger.debug("%s %s", method.upper(), path)
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
        logger.debug("%s %s %s", response.status_code, method.upper(), path)
        self._raise_for_status(response, method, path)
        return response

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        return await self.request("GET", path, params=params)

    async def get_download(self, path: str) -> httpx.Response:
        """GET for binary downloads with auth-preserving redirect handling.

        httpx strips the Authorization header when following redirects to a
        different host (a security default).  Download endpoints commonly
        redirect to a media URL served by nginx, which still needs the token.
        This method follows each redirect hop as a *fresh* request so the
        client's default Authorization header is always re-attached.
        """
        client = self._get_client()
        logger.debug("GET (download) %s", path)
        try:
            resp = await client.request("GET", path, follow_redirects=False)
        except httpx.HTTPError as exc:
            raise ServerError(str(exc)) from exc

        hops = 0
        while resp.is_redirect and hops < 5:
            location = resp.headers["location"]
            logger.debug("Redirect %d -> %s", resp.status_code, location)
            try:
                resp = await client.request("GET", location, follow_redirects=False)
            except httpx.HTTPError as exc:
                raise ServerError(str(exc)) from exc
            hops += 1

        logger.debug("%d GET %s", resp.status_code, path)
        self._raise_for_status(resp, "GET", path)
        return resp

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

    async def get_all_pages(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        *,
        max_results: int | None = None,
    ) -> list[dict]:
        results: list[dict] = []
        # First page — use path relative to base_url
        if params:
            logger.debug("Fetching %s (params=%s)", path, params)
        else:
            logger.debug("Fetching %s", path)
        response = await self.get(path, params=params)
        page = response.json()
        results.extend(page.get("results", []))

        if max_results is not None and len(results) >= max_results:
            logger.debug("max_results=%d reached after first page", max_results)
            return results[:max_results]

        next_url: str | None = page.get("next")
        while next_url:
            logger.debug("Fetching next page: %s", next_url)
            # next is absolute; pass it directly to the client
            client = self._get_client()
            try:
                response = await client.get(next_url)
            except httpx.HTTPError as exc:
                raise ServerError(str(exc)) from exc
            self._raise_for_status(response, "GET", next_url)
            page = response.json()
            results.extend(page.get("results", []))
            next_url = page.get("next")

            if max_results is not None and len(results) >= max_results:
                logger.debug("max_results=%d reached", max_results)
                break

        if max_results is not None:
            results = results[:max_results]

        logger.debug("Pagination complete: %d items from %s", len(results), path)
        return results
