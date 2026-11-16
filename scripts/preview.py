#!/usr/bin/env python3
"""Build a self-contained visual-only sprite-sheet preview from an action card."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from validate_motion import validate_file


HTML = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Character Action Preview</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#10141b;color:#e9edf1;font:15px/1.5 system-ui,sans-serif}
main{max-width:980px;padding:28px 20px;margin:auto}.muted{color:#9ba9b8}.stage{border:1px solid #344253;border-radius:16px;background:#1a2330;display:grid;place-items:center;min-height:440px;overflow:hidden}canvas{display:block;max-width:100%;height:auto}button,select,input{accent-color:#9ac8e5}button,select{border:1px solid #556778;border-radius:9px;background:#243444;color:#f5f8fc;padding:9px 13px;cursor:pointer}
.controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:16px}input[type=range]{flex:1;min-width:180px}small{color:#b2becb}code{color:#b9dce9}
</style></head><body><main>
<h1 id="heading">角色动作预览</h1><p class="muted">视觉预览 · 不包含真实受击碰撞、根节点位移或引擎性能测试</p>
<div class="stage"><canvas id="stage" width="600" height="480"></canvas></div>
<div class="controls"><button id="play">暂停</button><button id="back">◀ 上一帧</button><button id="next">下一帧 ▶</button><button id="reset">重播</button><label>速度 <select id="speed"><option value="0.25">0.25×</option><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label></div>
<div class="controls"><input id="seek" type="range" min="0" value="0"><code id="status"></code></div>
<small>动作时间来自 JSON 的 frame_durations_ms；帧图来自外部素材，已嵌入此 HTML。跳跃、击退等真实世界位移必须在游戏引擎里另行验证。</small>
</main><script>
const card=__CARD__;
const dataUrl="__IMAGE__";
const durations=card.visual.frame_durations_ms;
const cumulative=[0];for(const d of durations)cumulative.push(cumulative[cumulative.length-1]+d);
const total=card.total_ms;
const canvas=document.getElementById('stage'),ctx=canvas.getContext('2d');
const seek=document.getElementById('seek'),status=document.getElementById('status'),play=document.getElementById('play');
seek.max=total;seek.step=1;
document.getElementById('heading').textContent=card.character_id+' · '+card.action_id;
let current=0,playing=true,last=null,speed=1;
const image=new Image();image.src=dataUrl;
function frameAt(t){for(let i=0;i<durations.length;i++)if(t<cumulative[i+1])return i;return durations.length-1}
function draw(){
 ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#202b37';ctx.fillRect(0,0,canvas.width,canvas.height);
 const index=frameAt(current),v=card.visual,scale=Math.min((canvas.width-36)/v.frame_width,(canvas.height-36)/v.frame_height);
 const w=v.frame_width*scale,h=v.frame_height*scale;
 if(image.complete&&image.naturalWidth)ctx.drawImage(image,(index%v.columns)*v.frame_width,Math.floor(index/v.columns)*v.frame_height,v.frame_width,v.frame_height,(canvas.width-w)/2,(canvas.height-h)/2,w,h);
 seek.value=Math.min(total,current);status.textContent=Math.floor(current)+' / '+total+' ms · '+(index+1)+' / '+durations.length+' 帧';play.textContent=playing?'暂停':'播放';
}
function tick(ts){if(last!==null&&playing){current+=(ts-last)*speed;if(current>=total){if(card.loop)current%=total;else{current=total;playing=false}}}last=ts;draw();requestAnimationFrame(tick)}
function setFrame(i){current=cumulative[Math.max(0,Math.min(durations.length-1,i))];playing=false;draw()}
play.onclick=()=>{if(current>=total)current=0;playing=!playing;last=null;draw()};
document.getElementById('back').onclick=()=>setFrame(frameAt(Math.max(0,current-0.01))-1);
document.getElementById('next').onclick=()=>setFrame(frameAt(current)+1);
document.getElementById('reset').onclick=()=>{current=0;playing=true;last=null;draw()};
document.getElementById('speed').onchange=e=>{speed=Number(e.target.value)};
seek.oninput=e=>{current=Math.min(total,Number(e.target.value));playing=false;draw()};
image.onload=draw;draw();requestAnimationFrame(tick);
</script></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a self-contained HTML preview for an actual PNG spritesheet")
    parser.add_argument("card", type=Path, help="Action card JSON")
    parser.add_argument("-o", "--output", type=Path, default=Path("preview.html"))
    args = parser.parse_args()
    card, errors = validate_file(args.card, check_assets=True)
    if errors:
        parser.exit(1, "Cannot build preview:\n- " + "\n- ".join(errors) + "\n")
    image = Path(card["visual"]["path"])
    if not image.is_absolute():
        image = args.card.parent / image
    data_url = "data:image/png;base64," + base64.b64encode(image.read_bytes()).decode("ascii")
    escaped_card = json.dumps(card, ensure_ascii=False).replace("<", "\\u003c")
    html = HTML.replace("__CARD__", escaped_card).replace("__IMAGE__", data_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
