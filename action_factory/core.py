"""Persistent state machine for host-native image generation jobs."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from .image_ops import prepare_frame, inspect_frame

ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class ActionError(ValueError):
    pass


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix="." + path.name + ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_plan(p):
    if not isinstance(p, dict) or p.get("version") != "2.0":
        raise ActionError("动作方案 version 必须为 2.0")
    character = p.get("character", {})
    if not ID.fullmatch(str(character.get("id", ""))):
        raise ActionError("character.id 必须为安全的字母、数字或下划线标识")
    for key in ("identity", "body_type", "locomotion", "view"):
        if not str(character.get(key, "")).strip():
            raise ActionError(f"character.{key} 必填")
    states = p.get("states")
    if not isinstance(states, dict) or not states:
        raise ActionError("states 至少需要一个动作")
    for name, action in states.items():
        if not ID.fullmatch(str(name)):
            raise ActionError(f"无效动作名称: {name}")
        if not isinstance(action, dict):
            raise ActionError(f"{name} 必须为对象")
        n = action.get("frames")
        durations = action.get("durations_ms")
        poses = action.get("poses")
        if type(n) is not int or not 1 <= n <= 48:
            raise ActionError(f"{name}.frames 必须在1~48范围内")
        if type(action.get("loop")) is not bool:
            raise ActionError(f"{name}.loop 必须是布尔值")
        if not isinstance(durations, list) or len(durations) != n or any(type(v) is not int or v < 16 or v > 10000 for v in durations):
            raise ActionError(f"{name}.durations_ms 必须包含{n}个合理的毫秒时长")
        if not isinstance(poses, list) or len(poses) != n or any(not isinstance(v, str) or not v.strip() for v in poses):
            raise ActionError(f"{name}.poses 必须包含{n}个不同时间的姿势描述")
        events = action.get("events", [])
        if not isinstance(events, list) or any(not isinstance(ev, dict) or not isinstance(ev.get("name"), str) or type(ev.get("at_ms")) is not int or not 0 <= ev["at_ms"] < sum(durations) for ev in events):
            raise ActionError(f"{name}.events 必须包含合法的name和at_ms")
        if name.startswith("hurt") and not isinstance(action.get("hit_context"), dict):
            raise ActionError(f"{name} 必须指定 hit_context (部位/方向/运动状态)")
    return p


def initialize(root, source, plan, *, force=False):
    root = Path(root).resolve()
    source, plan = Path(source).resolve(), Path(plan).resolve()
    if not source.is_file() or not plan.is_file():
        raise ActionError("角色设计图和动作方案 JSON 必须实际存在")
    p = validate_plan(load(plan))
    if (root / "job.json").exists() and not force:
        raise ActionError("任务已存在，使用现有任务续做，不要覆盖。强制重建请指定 --force")
    root.mkdir(parents=True, exist_ok=True)
    dest = root / "source" / ("character" + source.suffix.lower())
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source != dest:
        shutil.copyfile(source, dest)
    save(root / "plan.json", p)
    job = {"version": "2.0", "character_id": p["character"]["id"], "source": str(dest.relative_to(root)),
           "source_sha256": sha(dest), "max_attempts": 3, "states": {}}
    for state, action in p["states"].items():
        job["states"][state] = [{"status": "pending", "attempts": 0, "issues": [], "visual_reviewed": False} for _ in range(action["frames"])]
        (root / "frames" / state).mkdir(parents=True, exist_ok=True)
        (root / "prompts" / state).mkdir(parents=True, exist_ok=True)
    save(root / "job.json", job)
    return job


def _refs(root, job, state, index):
    refs = [str((root / job["source"]).resolve())]
    entries = job["states"][state]
    if index > 0 and entries[index - 1].get("file"):
        refs.append(str((root / entries[index - 1]["file"]).resolve()))
    names = list(job["states"])
    loc = names.index(state)
    if loc > 0:
        previous = job["states"][names[loc-1]]
        first = next((v for v in previous if v.get("file")), None)
        if first:
            refs.append(str((root / first["file"]).resolve()))
    return list(dict.fromkeys(refs))


def prompt_for(root, job, plan, state, index):
    a = plan["states"][state]
    c = plan["character"]
    f = job["states"][state][index]
    text = f"""请以附带的角色原图作为最高优先级身份锚点，生成【单独一张】完整角色的动画关键帧。
角色：{c['identity']}；身体：{c['body_type']}；移动方式：{c['locomotion']}；固定视角：{c['view']}。
动作：{state}，第 {index + 1}/{a['frames']} 帧。本帧角色姿势：{a['poses'][index]}
动作整体要求：{a.get('motion_notes', '保持角色与物理受力合理')}
本帧时长：{a['durations_ms'][index]} ms；循环：{'是' if a['loop'] else '否'}。
必须保持头脸、眼睛、发型、服装、道具数量、身体比例、线条和配色一致，不允许突然长胡须、多手或更换衣服。
角色完整入画，固定逻辑画布，脚下接触或腾空基准一致。真实透明背景或便于抠图的纯色背景；禁止文字、格线、帧序号或多角色。
受击场景必须考虑部位、受力方向、当前接地/腾空状态；实际移动位置由游戏运行时根节点处理，不把图像回位当作真实击退。"""
    if a.get("hit_context"):
        text += "\n受击上下文：" + json.dumps(a["hit_context"], ensure_ascii=False)
    if f.get("issues"):
        text += "\n上轮失败项，必须定向修复：" + "；".join(f["issues"])
    return {"character_id": c["id"], "state": state, "frame": index,
            "attempt": f["attempts"] + 1, "references": _refs(root, job, state, index),
            "prompt": text, "output": str((root / "incoming" / f"{state}_{index:03d}.png").resolve())}


def next_task(root):
    root = Path(root).resolve()
    job, plan = load(root / "job.json"), validate_plan(load(root / "plan.json"))
    for state, frames in job["states"].items():
        for index, f in enumerate(frames):
            if f["status"] in ("pending", "rejected"):
                if f["attempts"] >= job["max_attempts"]:
                    return {"status": "blocked", "reason": "超过该帧最大生成次数", "state": state, "frame": index, "issues": f["issues"]}
                return {"status": "ready", **prompt_for(root, job, plan, state, index)}
    return {"status": "complete", "summary": summary(job)}


def ingest(root, state, index, file, *, chroma=None):
    root = Path(root).resolve()
    job = load(root / "job.json")
    if state not in job["states"] or not 0 <= index < len(job["states"][state]):
        raise ActionError("不存在的动作或帧索引")
    f = job["states"][state][index]
    if f["status"] == "accepted":
        raise ActionError("已审核通过的帧不可被普通导入覆盖")
    if f["attempts"] >= job["max_attempts"]:
        raise ActionError("此帧已超过最大生成次数")
    dest = root / "frames" / state / f"frame_{index:03d}.png"
    try:
        meta = prepare_frame(Path(file), dest, chroma=chroma)
    except (ValueError, OSError) as e:
        f["attempts"] += 1
        f["status"] = "rejected"
        f["issues"] = [str(e)]
        save(root / "job.json", job)
        return {"status": "rejected", "state": state, "frame": index, "issues": f["issues"]}
    f.update({"status": "generated", "attempts": f["attempts"]+1,
              "issues": [], "file": str(dest.relative_to(root)), "sha256": sha(dest),
              "visual_reviewed": False, "metrics": meta})
    save(root / "job.json", job)
    return {"status": "generated", "state": state, "frame": index, "metrics": meta}


def review(root, state, index, *, passed, issues=None):
    root = Path(root).resolve()
    job = load(root / "job.json")
    f = job["states"][state][index]
    if f["status"] not in ("generated", "accepted", "rejected") or not f.get("file"):
        raise ActionError("只能审核已有有效图片的帧")
    f["status"] = "accepted" if passed else "rejected"
    f["issues"] = [] if passed else (issues or ["视觉或动作连续性未通过"])
    f["visual_reviewed"] = bool(passed)
    save(root / "job.json", job)
    return {"state": state, "frame": index, "status": f["status"], "issues": f["issues"]}


def summary(job):
    statuses = [f["status"] for fs in job["states"].values() for f in fs]
    counts = {status: statuses.count(status) for status in ("pending", "generated", "accepted", "rejected")}
    return {"counts": counts, "total": len(statuses), "visual_pass": counts["accepted"] == len(statuses)}
