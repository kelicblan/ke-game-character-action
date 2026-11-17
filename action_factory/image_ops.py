"""Frame normalization, deterministic image diagnostics and runtime atlas packaging."""
from __future__ import annotations

import hashlib
from pathlib import Path
from PIL import Image, ImageChops, ImageStat


def prepare_frame(src, dest, *, chroma=None):
    src, dest = Path(src), Path(dest)
    if not src.is_file():
        raise ValueError("生成模型未提供可读取的图像文件")
    with Image.open(src) as raw:
        image = raw.convert("RGBA")
        original_alpha = raw.mode in ("RGBA", "LA", "PA") or "transparency" in raw.info
    if chroma is not None:
        key = chroma.lstrip("#")
        if len(key) != 6:
            raise ValueError("色键必须为六位 RGB，例如 FF00FF")
        rgb = tuple(bytes.fromhex(key))
        pixel = image.load()
        for y in range(image.height):
            for x in range(image.width):
                r, g, b, a = pixel[x,y]
                distance = max(abs(r-rgb[0]), abs(g-rgb[1]), abs(b-rgb[2]))
                if distance <= 16:
                    pixel[x,y] = (0,0,0,0)
                elif distance < 42:
                    pixel[x,y] = (r,g,b, round(a*(distance-16)/26))
    elif not original_alpha:
        raise ValueError("图片不具备真实透明通道；请启用图片工具透明输出或显式使用 --chroma 色键")
    if image.width < 16 or image.height < 16 or image.width > 4096 or image.height > 4096:
        raise ValueError("帧尺寸无效；要求16~4096像素")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        raise ValueError("图像为全透明，无法提取角色")
    count = sum(alpha.histogram()[1:])
    occupancy = count / (image.width * image.height)
    if occupancy < 0.015:
        raise ValueError("角色像素占比过小，疑似生成空白图")
    if occupancy > .985:
        raise ValueError("几乎整张图均不透明，疑似把背景烘焙进了图片")
    # Sanitize RGB under fully transparent pixels; do not change semi-transparency.
    rgb = image.load()
    for y in range(image.height):
        for x in range(image.width):
            if rgb[x,y][3] == 0:
                rgb[x,y] = (0,0,0,0)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, "PNG")
    return inspect_frame(dest)


def inspect_frame(path):
    with Image.open(path) as image:
        rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        raise ValueError("空白图")
    hist = alpha.histogram()
    return {"size": [rgba.width,rgba.height], "opaque_or_translucent_pct": round((1-hist[0]/(rgba.width*rgba.height))*100,2),
            "bbox": list(bbox), "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}


def diagnostics(root, job, plan):
    """Non-semantic diagnostics. Never claim a numerical score proves identity."""
    root = Path(root)
    records = {}
    for state, frames in job["states"].items():
        warnings = []
        prev = None
        for i, f in enumerate(frames):
            if not f.get("file"):
                warnings.append(f"第{i+1}帧缺少图片")
                continue
            path = root/f["file"]
            if not path.is_file():
                warnings.append(f"第{i+1}帧文件不存在")
                continue
            with Image.open(path) as im:
                im = im.convert("RGBA")
                if prev is not None:
                    a = prev.resize((48,48),Image.Resampling.BILINEAR)
                    b = im.resize((48,48),Image.Resampling.BILINEAR)
                    delta = ImageStat.Stat(ImageChops.difference(a,b)).mean
                    if max(delta)<.5:
                        warnings.append(f"第{i+1}帧与前一帧几乎重复，需确认是否故意停势")
                prev = im.copy()
            if f["status"] != "accepted":
                warnings.append(f"第{i+1}帧尚未通过视觉审核（{f['status']}）")
        records[state] = {"warnings": warnings,"visual_reviewed": all(f["status"] == "accepted" for f in frames)}
    return records


def make_atlas(root, job, plan, *, draft=False):
    root = Path(root)
    from .core import ActionError,save
    states = plan["states"]
    if any(f["status"] not in (("accepted","generated") if draft else ("accepted",)) for fs in job["states"].values() for f in fs):
        raise ActionError("动画有缺失、失败或未审核帧；如仅需要概念预览，使用 --draft")
    frames = []
    max_width = max_height = 0
    for state, entries in job["states"].items():
        for f in entries:
            path = root / f["file"]
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != f["sha256"]:
                raise ActionError(f"图片缺失或已被篡改: {path}")
            with Image.open(path) as im:
                w,h = im.size
            max_width, max_height = max(max_width,w),max(max_height,h)
            frames.append((state,f,path))
    if not frames:
        raise ActionError("没有任何可导出的图片")
    # Logical untrimmed canvas: each character center x, feet baseline at bottom.
    ncols = min(8,max(len(v) for v in job["states"].values()))
    rows = (len(frames)+ncols-1)//ncols
    if max_width*ncols > 8192 or max_height*rows > 8192:
        raise ActionError("图集尺寸超过8192，需先分批或压缩素材")
    sheet = Image.new("RGBA", (max_width*ncols,max_height*rows),(0,0,0,0))
    state_frames = {k: [] for k in states}
    for idx, (state,f,path) in enumerate(frames):
        with Image.open(path) as im:
            im = im.convert("RGBA")
            dx = (max_width-im.width)//2
            dy = max_height-im.height
            x = (idx%ncols)*max_width
            y = (idx//ncols)*max_height
            sheet.alpha_composite(im,(x+dx,y+dy))
            seq = len(state_frames[state])
            state_frames[state].append({"index":seq,"x":x,"y":y,"w":max_width,"h":max_height,
                                        "source":"" + f["file"],"offset_x":dx,"offset_y":dy})
    asset = root/"assets"
    asset.mkdir(parents=True,exist_ok=True)
    sheet.save(asset/"sprite-sheet.png")
    manifest = {"version":"2.0","character_id":plan["character"]["id"],
                "game_input":"sprite-sheet.png","sheet":{"width":sheet.width,"height":sheet.height,
                    "cell_width":max_width,"cell_height":max_height,"columns":ncols,"rows":rows},
                "quality":"draft" if draft else "visually_reviewed",
                "animation":{"rows":{name:{"frames":len(state_frames[name]),"loop":s["loop"],
                   "durations_ms":s["durations_ms"],"events":s.get("events",[]),"hit_context":s.get("hit_context"),
                   "root_motion_owner":"gameplay"} for name,s in states.items()}},
                "frame_layout":{"rows":state_frames}}
    save(asset/"manifest.json",manifest)
    save(asset/"qa-report.json",{"stage":manifest["quality"],"diagnostics":diagnostics(root,job,plan)})
    return manifest
