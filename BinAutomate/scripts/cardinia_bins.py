#!/usr/bin/env python3
"""Fetch Cardinia bin collection dates for Home Assistant."""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


SEARCH_EXTENT = "145.36,-37.86,145.78,-38.34"
GEOCODER_BASE = (
    "https://corp-geo.mapshare.vic.gov.au/arcgis/rest/services/Geocoder/"
    "VMAddressEZIAdd/GeocodeServer"
)
WASTE_URL = (
    "https://services3.arcgis.com/TJxZpUnYIJOvcYwE/arcgis/rest/services/"
    "Waste_Collection_Zones/FeatureServer/0/query"
)
BIN_DISPLAY = {
    "rubbish": "Red Bin - Rubbish",
    "recycling": "Yellow Bin - Recycling",
    "green_waste": "Green Bin - Organic Waste",
}
try:
    TIMEZONE = ZoneInfo("Australia/Melbourne")
except ZoneInfoNotFoundError:
    TIMEZONE = None


class LookupErrorWithPayload(RuntimeError):
    def __init__(self, message: str, **payload: Any) -> None:
        super().__init__(message)
        self.payload = payload


def fetch_json(url: str, params: dict[str, Any], timeout: int) -> dict[str, Any]:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(
        f"{url}?{query}",
        headers={"User-Agent": "GateAutomate-HomeAssistant/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def normalize_address(value: str) -> str:
    return " ".join(value.upper().replace(",", " ").split())


def resolve_address(address: str, timeout: int) -> dict[str, Any]:
    suggestions = fetch_json(
        f"{GEOCODER_BASE}/suggest",
        {
            "searchExtent": SEARCH_EXTENT,
            "text": address,
            "f": "json",
            "maxSuggestions": 15,
        },
        timeout,
    ).get("suggestions", [])

    if not suggestions:
        raise LookupErrorWithPayload("No Cardinia address suggestions found.")

    requested = normalize_address(address)
    exact_matches = [
        item
        for item in suggestions
        if normalize_address(item.get("text", "")) == requested
        or normalize_address(item.get("text", "")).startswith(requested)
    ]

    if len(suggestions) == 1:
        match = suggestions[0]
    elif len(exact_matches) == 1:
        match = exact_matches[0]
    else:
        raise LookupErrorWithPayload(
            "Address lookup is ambiguous.",
            suggestions=[item.get("text", "") for item in suggestions],
        )

    candidates = fetch_json(
        f"{GEOCODER_BASE}/findAddressCandidates",
        {
            "SingleLine": match["text"],
            "magicKey": match["magicKey"],
            "f": "json",
            "outFields": "*",
            "maxLocations": 5,
        },
        timeout,
    ).get("candidates", [])

    if not candidates:
        raise LookupErrorWithPayload(
            "Address suggestion could not be resolved.",
            matched_address=match.get("text", ""),
        )

    candidates.sort(key=lambda item: item.get("score", 0), reverse=True)
    best = candidates[0]
    if best.get("score", 0) < 90:
        raise LookupErrorWithPayload(
            "Address match score was too low.",
            matched_address=best.get("address", match.get("text", "")),
            score=best.get("score"),
        )

    location = best.get("location") or {}
    if "x" not in location or "y" not in location:
        raise LookupErrorWithPayload("Address candidate did not include coordinates.")

    return {
        "matched_address": best.get("address", match.get("text", "")),
        "longitude": location["x"],
        "latitude": location["y"],
        "score": best.get("score"),
    }


def fetch_waste_zone(longitude: float, latitude: float, timeout: int) -> dict[str, Any]:
    data = fetch_json(
        WASTE_URL,
        {
            "f": "json",
            "outFields": "*",
            "returnGeometry": "false",
            "inSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "geometryType": "esriGeometryPoint",
            "geometry": f"{longitude},{latitude}",
        },
        timeout,
    )
    features = data.get("features", [])
    if len(features) != 1:
        raise LookupErrorWithPayload(
            "Waste zone lookup did not return exactly one zone.",
            zone_count=len(features),
        )
    return features[0].get("attributes") or {}


def next_collection(start: str, interval_weeks: int, today: date) -> date | None:
    if not start or not interval_weeks:
        return None

    start_date = date.fromisoformat(start[:10])
    interval_days = int(interval_weeks) * 7
    if today <= start_date:
        return start_date

    elapsed = (today - start_date).days
    intervals = math.ceil(elapsed / interval_days)
    return start_date + timedelta(days=intervals * interval_days)


def collection_prefix(collection_date: date, today: date) -> str:
    if collection_date == today:
        return f"Today ({collection_date.strftime('%A')})"
    if collection_date == today + timedelta(days=1):
        return f"Tomorrow ({collection_date.strftime('%A')})"
    return f"Next {collection_date.strftime('%A')}"


def build_payload(address: str, today: date, timeout: int) -> dict[str, Any]:
    resolved = resolve_address(address, timeout)
    zone = fetch_waste_zone(resolved["longitude"], resolved["latitude"], timeout)

    bins = {
        "rubbish": {
            "label": "Rubbish",
            "display": BIN_DISPLAY["rubbish"],
            "day": zone.get("rub_day"),
            "weeks": zone.get("rub_weeks"),
            "start": zone.get("rub_start"),
        },
        "recycling": {
            "label": "Recycling",
            "display": BIN_DISPLAY["recycling"],
            "day": zone.get("rec_day"),
            "weeks": zone.get("rec_weeks"),
            "start": zone.get("rec_start"),
            "week_name": zone.get("rec_name"),
        },
        "green_waste": {
            "label": "Green waste",
            "display": BIN_DISPLAY["green_waste"],
            "day": zone.get("grn_day"),
            "weeks": zone.get("grn_weeks"),
            "start": zone.get("grn_start"),
            "week_name": zone.get("grn_name"),
        },
    }

    tomorrow = today + timedelta(days=1)
    tomorrow_collections: list[str] = []
    next_dates: dict[str, str | None] = {}
    dated_collections: list[tuple[date, str]] = []

    for key, item in bins.items():
        next_date = next_collection(str(item.get("start") or ""), int(item.get("weeks") or 0), today)
        next_dates[key] = next_date.isoformat() if next_date else None
        item["next_date"] = next_dates[key]
        if next_date:
            dated_collections.append((next_date, key))
        if next_date == tomorrow:
            tomorrow_collections.append(key)

    tomorrow_labels = [bins[key]["label"] for key in tomorrow_collections]
    tomorrow_display_lines = [bins[key]["display"] for key in tomorrow_collections]
    next_collection_date = min((item[0] for item in dated_collections), default=None)
    next_collection_keys = [
        key for collection_date, key in dated_collections if collection_date == next_collection_date
    ]
    next_collection_lines = [bins[key]["display"] for key in next_collection_keys]
    next_collection_prefix = (
        collection_prefix(next_collection_date, today) if next_collection_date else "No collection found"
    )
    next_collection_message = (
        f"{next_collection_prefix} : {next_collection_date.isoformat()}:\n"
        + "\n".join(f" {line}" for line in next_collection_lines)
        if next_collection_date
        else "No Cardinia bin collection date found."
    )

    return {
        "status": "ok",
        "address": address,
        **resolved,
        "zone_id": zone.get("FID"),
        "zone_note": (zone.get("Note") or "").strip(),
        "today": today.isoformat(),
        "tomorrow": tomorrow.isoformat(),
        "next_rubbish_date": next_dates["rubbish"],
        "next_recycling_date": next_dates["recycling"],
        "next_green_waste_date": next_dates["green_waste"],
        "next_collection_date": next_collection_date.isoformat() if next_collection_date else None,
        "next_collection_prefix": next_collection_prefix,
        "next_collection_lines": next_collection_lines,
        "next_collection_message": next_collection_message,
        "tomorrow_collections": tomorrow_collections,
        "tomorrow_collection_labels": tomorrow_labels,
        "tomorrow_collection_lines": tomorrow_display_lines,
        "message": next_collection_message,
        "bins": bins,
        "source": WASTE_URL,
        "updated_at": now_local().isoformat(timespec="seconds"),
    }


def now_local() -> datetime:
    if TIMEZONE is not None:
        return datetime.now(TIMEZONE)
    return datetime.now().astimezone()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", required=True)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--date", help="Override today's date, YYYY-MM-DD.")
    parser.add_argument("--format", choices=["json", "home-assistant"], default="json")
    args = parser.parse_args()

    today = date.fromisoformat(args.date) if args.date else now_local().date()

    try:
        payload = build_payload(args.address, today, args.timeout)
        print(json.dumps(payload, separators=(",", ":")))
        return 0
    except Exception as exc:
        payload = {
            "status": "error",
            "address": args.address,
            "message": str(exc),
            "updated_at": now_local().isoformat(timespec="seconds"),
        }
        if isinstance(exc, LookupErrorWithPayload):
            payload.update(exc.payload)
        print(json.dumps(payload, separators=(",", ":")))
        return 0 if args.format == "home-assistant" else 1


if __name__ == "__main__":
    sys.exit(main())
