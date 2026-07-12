from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_ROOT / "data" / "catalog" / "rega_catalog.json"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
SNAPSHOT_PATH = PROJECT_ROOT / "data" / "processed" / "rental_market.csv.gz"

COLUMN_ALIASES = {
    "year": "year",
    "السنة": "year",
    "quarter": "quarter",
    "الربع": "quarter",
    "region_ar": "region_ar",
    "المنطقة": "region_ar",
    "city_ar": "city_ar",
    "المدينة": "city_ar",
    "district_ar": "district_ar",
    "الحي": "district_ar",
    "category": "property_type",
    "نوع العقار": "property_type",
    "property_type": "property_type",
    "تصنيف العقار": "property_class",
    "total_deals": "total_deals",
    "مجموع الصفقات": "total_deals",
    "عدد الصفقات": "total_deals",
    "average": "average_rent",
    "المتوسط": "average_rent",
    "متوسط الايجار": "average_rent",
    "متوسط الإيجار": "average_rent",
    "متوسط الايجار ر.س": "average_rent",
    "متوسط الإيجار ر.س": "average_rent",
    "avg": "average_rent",
}

RENTAL_COLUMNS = {
    "year",
    "quarter",
    "region_ar",
    "city_ar",
    "property_type",
    "total_deals",
    "average_rent",
}

OPTIONAL_COLUMNS = ["district_ar", "property_class"]
OUTPUT_COLUMNS = [
    "year",
    "quarter",
    "region_ar",
    "city_ar",
    "district_ar",
    "location_ar",
    "property_type",
    "property_class",
    "total_deals",
    "average_rent",
]


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"datasets": []}
    return json.loads(path.read_text(encoding="utf-8"))


def dataset_metadata_by_id(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item.get("datasetID"): item for item in catalog.get("datasets", []) if item.get("datasetID")}


def load_rental_data(
    raw_dir: Path = RAW_DIR,
    catalog_path: Path = CATALOG_PATH,
    snapshot_path: Path = SNAPSHOT_PATH,
) -> pd.DataFrame:
    if not any(raw_dir.glob("*.csv")) and snapshot_path.exists():
        return load_snapshot(snapshot_path)

    catalog = load_catalog(catalog_path)
    metadata = dataset_metadata_by_id(catalog)
    frames: list[pd.DataFrame] = []
    for path in sorted(raw_dir.glob("*.csv")):
        frame = _read_csv(path)
        frame = normalize_rental_frame(frame)
        if frame.empty:
            continue

        dataset_id, resource_id = parse_raw_file_ids(path)
        dataset_meta = metadata.get(dataset_id, {})
        frame["dataset_id"] = dataset_id
        frame["resource_id"] = resource_id
        frame["dataset_title_ar"] = dataset_meta.get("titleAr", dataset_id)
        frame["dataset_title_en"] = dataset_meta.get("titleEn", dataset_id)
        frame["source_updated_at"] = dataset_meta.get("updatedAt")
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    data = pd.concat(frames, ignore_index=True)
    data = data.dropna(subset=["year", "quarter", "region_ar", "city_ar", "average_rent"])
    data["year"] = data["year"].astype("int64")
    data["quarter"] = data["quarter"].astype("int64")
    data["total_deals"] = data["total_deals"].fillna(0).astype("float64")
    data["average_rent"] = data["average_rent"].astype("float64")
    data["district_ar"] = data["district_ar"].fillna("").astype(str).str.strip()
    data["property_class"] = data["property_class"].fillna("").astype(str).str.strip()
    data["location_ar"] = data.apply(location_label, axis=1)
    data["period_index"] = data["year"] * 4 + data["quarter"]
    data["period"] = data["year"].astype(str) + " Q" + data["quarter"].astype(str)
    return data


def load_snapshot(path: Path = SNAPSHOT_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    data = pd.read_csv(path, compression="infer")
    for column in ["year", "quarter", "period_index"]:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce").astype("Int64")
    for column in ["total_deals", "average_rent"]:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    for column in ["district_ar", "property_class", "source_updated_at"]:
        if column in data:
            data[column] = data[column].fillna("").astype(str)
    if "location_ar" not in data.columns:
        data["location_ar"] = data.apply(location_label, axis=1)
    if "period_index" not in data.columns and {"year", "quarter"}.issubset(data.columns):
        data["period_index"] = data["year"].astype("int64") * 4 + data["quarter"].astype("int64")
    if "period" not in data.columns and {"year", "quarter"}.issubset(data.columns):
        data["period"] = data["year"].astype(str) + " Q" + data["quarter"].astype(str)
    return data


def normalize_rental_frame(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for column in frame.columns:
        key = normalize_column_name(column)
        if key in COLUMN_ALIASES:
            renamed[column] = COLUMN_ALIASES[key]
    frame = frame.rename(columns=renamed)
    if not RENTAL_COLUMNS.issubset(set(frame.columns)):
        return pd.DataFrame()

    for column in OPTIONAL_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""

    selected = frame[[*RENTAL_COLUMNS, *OPTIONAL_COLUMNS]].copy()
    for column in ["region_ar", "city_ar", "district_ar", "property_type", "property_class"]:
        selected[column] = selected[column].astype(str).str.strip()
    for column in ["year", "quarter", "total_deals", "average_rent"]:
        selected[column] = pd.to_numeric(selected[column], errors="coerce")
    selected = selected[selected["average_rent"] > 0]
    return selected


def normalize_column_name(value: object) -> str:
    cleaned = str(value).strip().replace("\ufeff", "").lower()
    return re.sub(r"\s+", " ", cleaned)


def location_label(row: pd.Series) -> str:
    city = str(row.get("city_ar", "")).strip()
    district = str(row.get("district_ar", "")).strip()
    if not district or district.lower() == "nan" or district == city:
        return city
    return f"{city} - {district}"


def parse_raw_file_ids(path: Path) -> tuple[str, str]:
    parts = path.stem.split("_", 2)
    if len(parts) >= 2:
        return parts[0], parts[1]
    return path.stem, ""


def _read_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "utf-8", "cp1256"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, low_memory=False)
