"""Normalize Xquik tweet exports for Streamlit sentiment analysis."""

from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Any


TEXT_FIELDS = ("tweet", "text", "full_text", "tweet_text", "content", "body")


def _unwrap_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict):
        for key in ("data", "results", "tweets", "items"):
            rows = value.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]
        return [value]
    return []


def _parse_jsonl(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        rows.extend(_unwrap_rows(json.loads(line)))
    return rows


def _parse_csv(text: str) -> list[dict[str, Any]]:
    return [dict(row) for row in csv.DictReader(StringIO(text))]


def _get_text(row: dict[str, Any]) -> str:
    for field in TEXT_FIELDS:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def load_xquik_rows(payload: bytes | str) -> list[dict[str, str]]:
    text = payload.decode("utf-8-sig") if isinstance(payload, bytes) else payload
    stripped = text.lstrip()
    try:
        rows = _unwrap_rows(json.loads(text)) if stripped.startswith(("{", "[")) else _parse_jsonl(text)
    except json.JSONDecodeError:
        try:
            rows = _parse_jsonl(text)
        except json.JSONDecodeError:
            rows = _parse_csv(text)

    normalized: list[dict[str, str]] = []
    for row in rows:
        tweet = _get_text(row)
        if not tweet:
            continue
        normalized.append({"tweet": tweet})
    return normalized
