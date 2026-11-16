"""Regression tests for action-card validation and self-contained preview."""
import copy
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_motion import validate_data, validate_file  # noqa: E402


def sample_card():
    return {
        "schema_version": "1.0", "character_id": "test-actor", "action_id": "hop", "type": "locomotion",
        "loop": True, "total_ms": 600,
        "phases": [{"name": "takeoff", "start_ms": 0, "end_ms": 200},
                   {"name": "flight", "start_ms": 200, "end_ms": 400},
                   {"name": "landing", "start_ms": 400, "end_ms": 600}],
        "key_poses": [{"at_ms": 0, "pose": "ready"}, {"at_ms": 200, "pose": "airborne"},
                      {"at_ms": 400, "pose": "landing"}],
        "events": [{"type": "takeoff", "at_ms": 200}, {"type": "landing", "at_ms": 400}],
        "feedback": {"hitstop_ms": 0, "hitstun_ms": 0},
        "root_motion": {"owner": "gameplay"},
        "visual": {"kind": "sprite_sheet", "path": "sheet.png", "columns": 2, "rows": 2,
                   "frame_width": 2, "frame_height": 2, "frame_durations_ms": [120, 180, 180, 120],
                   "pivot_normalized": [0.5, 1]},
    }


def png_chunk(name, data):
    body = name + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def write_png(path, width=4, height=4):
    scan = b"".join(b"\x00" + b"\xff\x66\x22\xff" * width for _ in range(height))
    with path.open("wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)))
        f.write(png_chunk(b"IDAT", zlib.compress(scan)))
        f.write(png_chunk(b"IEND", b""))


class TestActionCard(unittest.TestCase):
    def test_valid_metadata(self):
        self.assertEqual(validate_data(sample_card(), ROOT), [])

    def test_phase_gap_fails(self):
        card = sample_card()
        card["phases"][1]["start_ms"] = 210
        self.assertTrue(any("phases" in e for e in validate_data(card, ROOT)))

    def test_incorrect_frame_duration_fails(self):
        card = sample_card()
        card["visual"]["frame_durations_ms"][0] = 140
        self.assertTrue(any("sum of frame_durations" in e for e in validate_data(card, ROOT)))

    def test_invalid_event_window_fails(self):
        card = sample_card()
        card["events"].append({"type": "hit_window", "start_ms": 500, "end_ms": 700})
        self.assertTrue(any("invalid" in e for e in validate_data(card, ROOT)))

    def test_asset_missing_and_size(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            card = sample_card()
            self.assertTrue(any("asset missing" in e for e in validate_data(card, root, True)))
            write_png(root / "sheet.png", 6, 4)
            self.assertTrue(any("dimensions" in e for e in validate_data(card, root, True)))
            write_png(root / "sheet.png", 4, 4)
            self.assertEqual(validate_data(card, root, True), [])

    def test_preview_embeds_asset(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            card = sample_card()
            (root / "hop.json").write_text(json.dumps(card), encoding="utf-8")
            write_png(root / "sheet.png")
            out = root / "hop.html"
            result = subprocess.run([sys.executable, str(ROOT / "scripts" / "preview.py"), str(root / "hop.json"),
                                     "-o", str(out)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            page = out.read_text(encoding="utf-8")
            self.assertIn("data:image/png;base64", page)
            self.assertIn("frame_durations_ms", page)
            self.assertIn("test-actor", page)


if __name__ == "__main__":
    unittest.main()
