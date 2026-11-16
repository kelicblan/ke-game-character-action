#!/usr/bin/env python3
"""Validate a millisecond-based game character action card (stdlib only)."""
from __future__ import annotations

import argparse
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive_int(value: Any) -> bool:
    return type(value) is int and value > 0


def validate_data(data: Any, base_dir: Path, check_assets: bool = False) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["Action card must be a JSON object"]

    def err(message: str) -> None:
        errors.append(message)

    for name in ("schema_version", "character_id", "action_id", "type"):
        if not isinstance(data.get(name), str) or not data[name].strip():
            err(f"{name} must be a non-empty string")
    if data.get("schema_version") != "1.0":
        err("schema_version must be 1.0")
    if type(data.get("loop")) is not bool:
        err("loop must be boolean")
    total = data.get("total_ms")
    if not _positive_int(total):
        err("total_ms must be a positive integer")
        total = 0

    phases = data.get("phases")
    if not isinstance(phases, list) or not phases:
        err("phases must be a non-empty list")
    else:
        cursor = 0
        for i, phase in enumerate(phases):
            if not isinstance(phase, dict):
                err(f"phases[{i}] must be an object")
                continue
            a, b = phase.get("start_ms"), phase.get("end_ms")
            if not isinstance(phase.get("name"), str) or not phase["name"].strip():
                err(f"phases[{i}].name is required")
            if not (_number(a) and _number(b) and a == cursor and a < b and b <= total):
                err(f"phases[{i}] must start at {cursor}, have positive duration and stay within total_ms")
            if _number(b):
                cursor = b
        if cursor != total:
            err("phases must cover exactly 0..total_ms without gaps or overlaps")

    poses = data.get("key_poses")
    if not isinstance(poses, list) or not poses:
        err("key_poses must be a non-empty list")
    else:
        prev = -1
        for i, pose in enumerate(poses):
            t = pose.get("at_ms") if isinstance(pose, dict) else None
            if not (_number(t) and prev < t < total):
                err(f"key_poses[{i}].at_ms must be strictly increasing within [0, total_ms)")
            if not isinstance(pose, dict) or not isinstance(pose.get("pose"), str) or not pose["pose"]:
                err(f"key_poses[{i}].pose is required")
            if _number(t):
                prev = t
        if isinstance(poses[0], dict) and poses[0].get("at_ms") != 0:
            err("first key pose must start at 0 ms")

    events = data.get("events", [])
    if not isinstance(events, list):
        err("events must be a list")
    else:
        for i, event in enumerate(events):
            if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                err(f"events[{i}] requires a type")
                continue
            if "at_ms" in event:
                t = event["at_ms"]
                if not (_number(t) and 0 <= t <= total):
                    err(f"events[{i}].at_ms outside action duration")
            elif "start_ms" in event and "end_ms" in event:
                a, b = event["start_ms"], event["end_ms"]
                if not (_number(a) and _number(b) and 0 <= a < b <= total):
                    err(f"events[{i}] invalid start_ms/end_ms window")
            else:
                err(f"events[{i}] requires at_ms or a start_ms/end_ms pair")

    feedback = data.get("feedback", {})
    if not isinstance(feedback, dict):
        err("feedback must be an object")
    else:
        for key in ("hitstop_ms", "hitstun_ms"):
            value = feedback.get(key, 0)
            if not (_number(value) and value >= 0):
                err(f"feedback.{key} must be nonnegative")

    root_motion = data.get("root_motion")
    if not isinstance(root_motion, dict) or root_motion.get("owner") not in ("gameplay", "animation", "hybrid", "none"):
        err("root_motion.owner must be gameplay, animation, hybrid, or none")

    visual = data.get("visual")
    if not isinstance(visual, dict):
        err("visual must be an object")
        return errors
    if visual.get("kind") != "sprite_sheet":
        err("visual.kind currently must be sprite_sheet (validator supports sprite sheets only)")
        return errors
    dims = [visual.get(k) for k in ("columns", "rows", "frame_width", "frame_height")]
    if not all(_positive_int(v) for v in dims):
        err("visual.columns/rows/frame_width/frame_height must be positive integers")
    durations = visual.get("frame_durations_ms")
    if not isinstance(durations, list) or not durations or not all(_number(v) and v > 0 for v in durations):
        err("visual.frame_durations_ms must be non-empty positive numbers")
    else:
        if all(_positive_int(v) for v in dims) and len(durations) != dims[0] * dims[1]:
            err("sprite-sheet cell count must equal frame_durations_ms length")
        if abs(sum(durations) - total) > 0.001:
            err("sum of frame_durations_ms must equal total_ms")
    pivot = visual.get("pivot_normalized")
    if not isinstance(pivot, list) or len(pivot) != 2 or not all(_number(x) and 0 <= x <= 1 for x in pivot):
        err("visual.pivot_normalized must be two numbers in [0, 1]")

    image_path = visual.get("path")
    if not isinstance(image_path, str) or not image_path.strip():
        err("visual.path must be a non-empty file path")
    elif check_assets:
        full_path = Path(image_path)
        if not full_path.is_absolute():
            full_path = base_dir / full_path
        if not full_path.is_file():
            err(f"asset missing: {full_path}")
        elif all(_positive_int(v) for v in dims):
            try:
                with full_path.open("rb") as handle:
                    header = handle.read(24)
                if len(header) < 24 or header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
                    raise ValueError("not a valid PNG header")
                width, height = struct.unpack(">II", header[16:24])
                if (width, height) != (dims[0] * dims[2], dims[1] * dims[3]):
                    err(f"sprite-sheet dimensions {width}x{height} do not match {dims[0] * dims[2]}x{dims[1] * dims[3]}")
            except (OSError, ValueError, struct.error) as exc:
                err(f"cannot inspect asset: {exc}")
    return errors


def validate_file(path: Path, check_assets: bool = False) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [f"cannot read action card: {exc}"]
    return data, validate_data(data, path.parent, check_assets)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate motion action card JSON (Python standard library only)")
    parser.add_argument("card", type=Path, help="Path to an action card JSON file")
    parser.add_argument("--check-assets", action="store_true", help="Require PNG sheet and exact expected dimensions")
    args = parser.parse_args()
    data, errors = validate_file(args.card, args.check_assets)
    print(json.dumps({"ok": not errors, "action_id": data.get("action_id") if isinstance(data, dict) else None,
                      "assets_checked": args.check_assets, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
