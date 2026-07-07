from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from real_estate_intel.catalog import REGA_PUBLISHER_ID, SEED_DATASET_IDS
from real_estate_intel.rega_client import OpenDataClient

RAW_DIR = ROOT / "data" / "raw"
CATALOG_DIR = ROOT / "data" / "catalog"
CATALOG_PATH = CATALOG_DIR / "rega_catalog.json"


def main() -> None:
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)

    client = OpenDataClient()
    datasets = []

    if args.seed_only or not args.crawl_pages:
        datasets.extend(fetch_seed_datasets(client))

    if args.crawl_pages:
        datasets.extend(fetch_publisher_catalog(client, args.crawl_pages, args.page_size))

    datasets = unique_datasets(datasets)
    saved_files = []
    for dataset in datasets:
        saved_files.extend(download_dataset_resources(client, dataset, force=args.force))

    write_catalog(datasets)
    print(f"datasets={len(datasets)} files={len(saved_files)} catalog={CATALOG_PATH}")
    for path in saved_files:
        print(path.relative_to(ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch REGA open-data datasets.")
    parser.add_argument("--seed-only", action="store_true", help="Fetch the known starter REGA datasets.")
    parser.add_argument("--crawl-pages", type=int, default=0, help="Crawl N public catalog pages and filter REGA.")
    parser.add_argument("--page-size", type=int, default=100, help="Catalog page size.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing raw files.")
    return parser.parse_args()


def fetch_seed_datasets(client: OpenDataClient) -> list[dict[str, Any]]:
    datasets = []
    for dataset_id in SEED_DATASET_IDS:
        try:
            datasets.append(client.get_dataset(dataset_id))
        except Exception as exc:
            print(f"warning: failed dataset {dataset_id}: {exc}")
    return datasets


def fetch_publisher_catalog(
    client: OpenDataClient,
    crawl_pages: int,
    page_size: int,
) -> list[dict[str, Any]]:
    return list(
        client.iter_publisher_datasets(
            publisher_id=REGA_PUBLISHER_ID,
            max_pages=crawl_pages,
            page_size=page_size,
        )
    )


def download_dataset_resources(
    client: OpenDataClient,
    dataset: dict[str, Any],
    force: bool = False,
) -> list[Path]:
    saved = []
    dataset_id = dataset["datasetID"]
    for resource in client.preferred_tabular_resources(dataset):
        if str(resource.get("format", "")).lower() != "csv":
            continue
        download = client.download_resource(dataset_id, resource)
        path = RAW_DIR / f"{download.dataset_id}_{download.resource_id}.{download.format}"
        if path.exists() and not force:
            continue
        path.write_bytes(download.content)
        saved.append(path)
    return saved


def unique_datasets(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for dataset in datasets:
        dataset_id = dataset.get("datasetID")
        if dataset_id:
            unique[dataset_id] = dataset
    return list(unique.values())


def write_catalog(datasets: list[dict[str, Any]]) -> None:
    payload = {
        "publisher_id": REGA_PUBLISHER_ID,
        "datasets": datasets,
    }
    CATALOG_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
