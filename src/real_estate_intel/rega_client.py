from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import requests

from .catalog import ODP_API_URL, ODP_BASE_URL, ODP_DATA_API_URL, REGA_PUBLISHER_ID


class OpenDataError(RuntimeError):
    """Raised when the open-data portal returns an unusable response."""


@dataclass(frozen=True)
class ResourceDownload:
    dataset_id: str
    resource_id: str
    name: str
    format: str
    content: bytes


class OpenDataClient:
    def __init__(self, timeout: int = 60) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
                ),
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.8",
                "Origin": ODP_BASE_URL,
                "Referer": f"{ODP_BASE_URL}/ar/datasets",
            }
        )

    def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        url = f"{ODP_API_URL}/datasets/{dataset_id}"
        return self._json(
            "GET",
            url,
            headers={"Referer": f"{ODP_BASE_URL}/ar/datasets/view/{dataset_id}"},
        )

    def list_datasets(self, page: int = 0, size: int = 100) -> dict[str, Any]:
        url = f"{ODP_API_URL}/datasets/list"
        params = {"page": page, "size": size}
        return self._json("POST", url, params=params, json={})

    def iter_publisher_datasets(
        self,
        publisher_id: str = REGA_PUBLISHER_ID,
        max_pages: int = 10,
        page_size: int = 100,
    ) -> Iterable[dict[str, Any]]:
        for page in range(max_pages):
            payload = self.list_datasets(page=page, size=page_size)
            for item in payload.get("content", []):
                if item.get("publisherId") == publisher_id:
                    yield item
            if payload.get("last"):
                break

    def download_resource(self, dataset_id: str, resource: dict[str, Any]) -> ResourceDownload:
        resource_id = resource["resourceID"]
        url = f"{ODP_DATA_API_URL}/v1/datasets/{dataset_id}/resources/{resource_id}/download"
        response = self.session.get(
            url,
            timeout=self.timeout,
            headers={"Accept": "text/csv,application/octet-stream,*/*"},
        )
        self._raise_for_bad_response(response)
        return ResourceDownload(
            dataset_id=dataset_id,
            resource_id=resource_id,
            name=resource.get("name") or resource_id,
            format=(resource.get("format") or "bin").lower(),
            content=response.content,
        )

    def preferred_tabular_resources(self, dataset: dict[str, Any]) -> list[dict[str, Any]]:
        resources = dataset.get("resources") or []
        csv_resources = [r for r in resources if str(r.get("format", "")).lower() == "csv"]
        return csv_resources or [
            r for r in resources if str(r.get("format", "")).lower() in {"xlsx", "xls"}
        ]

    def _json(self, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
        response = self.session.request(method, url, timeout=self.timeout, **kwargs)
        self._raise_for_bad_response(response)
        try:
            return response.json()
        except ValueError as exc:
            snippet = response.text[:200].replace("\n", " ")
            raise OpenDataError(f"Expected JSON from {url}, got: {snippet}") from exc

    def _raise_for_bad_response(self, response: requests.Response) -> None:
        response.raise_for_status()
        text = response.text[:120].lower() if response.content else ""
        if "<html" in text and "request rejected" in text:
            raise OpenDataError("Open-data platform rejected the request.")
