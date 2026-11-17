"""Chinese offline Web preview and Cocos Creator 3.8 runtime bundle."""
from __future__ import annotations

import base64
import json
import shutil
from pathlib import Path

from .core import save


HTML = r'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>角色动作在线预览</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;color:#e9edf4;background:#101722;font:14px/1.5 "Microsoft Yahei",system-ui,sans-serif}
main{max-width:1200px;margin:auto;padding:24px 16px 50px}h1{font-size:23px;margin:0 0 8px}h2{font-size:16px;margin:0 0 8px}p{color:#a5b4c5;margin:0 0 12px}
.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:10px;border:1px solid #33465b;background:#1a2735;border-radius:12px;padding:12px;margin:14px 0 20px}
select,button{background:#27394d;border:1px solid #50657b;border-radius:8px;color:#f3f8fc;padding:7px 11px;cursor:pointer}
button:hover{background:#354e65} .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.card{border:1px solid #35465b;border-radius:14px;overflow:hidden;background:#1b2633;padding:14px}
.meta{font-size:12px;color:#9eb0c2}.stage{background:repeating-conic-gradient(#263645 0 25%,#2b3b4a 0 50%) 50%/28px 28px;border-radius:10px;min-height:270px;display:flex;align-items:center;justify-content:center;margin:12px 0;overflow:hidden}
canvas{width:auto;height:auto;max-width:100%;max-height:270px;image-rendering:auto}.controls{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.controls input{flex:1;min-width:80px;accent-color:#73b6ee}.status{font-size:12px;color:#bfd5e9;margin-top:7px}
.warn{color:#ffd29b}.ok{color:#98e4c5}label{display:flex;align-items:center;gap:6px}
</style></head><body><main><h1>角色动作动态预览</h1><p>角色：<span id="character"></span>　｜　输出阶段：<span id="quality"></span></p>
<div class="toolbar"><button id="allPlay">全部播放</button><button id="allPause">全部暂停</button><button id="allReplay">全部重播</button>
<label>全局播放速度 <select id="speed"><option value="0.25">0.25倍</option><option value="0.5">0.5倍</option><option value="1" selected>正常</option><option value="1.5">1.5倍</option><option value="2">2倍</option></select></label>
<span class="meta">支持逐帧查看、暂停、拖动进度。所有图片均已内嵌，无需服务器。</span></div>
<div id="cards" class="cards"></div><p style="margin-top:20px">说明：这是视觉动画预览，游戏中的真实击退、碰撞、命中和角色根节点移动仍需在 Cocos 内单独验证。</p></main>
<script>
const M=__MANIFEST__;const IMAGE="__IMAGE__";
const NAMES={idle:'待机',move:'移动',walk:'行走',hop:'跳跃移动',fly:'飞行',attack:'攻击',attack_heavy:'重击',hurt:'受击',hurt_head:'头部受击',hurt_body:'腹部受击',hurt_top:'头顶受击',death:'死亡'};
document.getElementById('character').textContent=M.character_id;
document.getElementById('quality').textContent=M.quality==='draft'?'草稿（部分帧未经视觉审核）':'通过视觉审核（尚未完成引擎验证）';
const img=new Image();img.src=IMAGE;let globalSpeed=1;const animations=[];
function create(state,cfg){const frames=M.frame_layout.rows[state],dur=cfg.durations_ms,total=dur.reduce((a,b)=>a+b,0);
 const node=document.createElement('section');node.className='card';
 const title=document.createElement('h2');title.textContent=NAMES[state]||state;node.appendChild(title);
 const meta=document.createElement('div');meta.className='meta';meta.textContent=frames.length+' 帧 · '+total+' 毫秒 · '+(cfg.loop?'循环播放':'单次播放');node.appendChild(meta);
 const stage=document.createElement('div');stage.className='stage';const canvas=document.createElement('canvas');canvas.width=M.sheet.cell_width;canvas.height=M.sheet.cell_height;stage.appendChild(canvas);node.appendChild(stage);
 const controls=document.createElement('div');controls.className='controls';const play=document.createElement('button');play.textContent='暂停';const prev=document.createElement('button');prev.textContent='上一帧';const next=document.createElement('button');next.textContent='下一帧';const seek=document.createElement('input');seek.type='range';seek.min=0;seek.max=total;seek.step=1;seek.value=0;controls.append(play,prev,next,seek);node.appendChild(controls);
 const status=document.createElement('div');status.className='status';node.appendChild(status);document.getElementById('cards').appendChild(node);
 const ctx=canvas.getContext('2d');let t=0,playing=true,index=0;
 function frameAt(time){let a=0;for(let i=0;i<dur.length;i++){a+=dur[i];if(time<a)return i}return dur.length-1}
 function draw(){index=frameAt(t);const f=frames[index];ctx.clearRect(0,0,canvas.width,canvas.height);if(img.complete&&img.naturalWidth)ctx.drawImage(img,f.x,f.y,f.w,f.h,0,0,canvas.width,canvas.height);
   seek.value=Math.round(t);status.textContent='第 '+(index+1)+'/'+frames.length+' 帧｜'+Math.round(t)+'/'+total+' 毫秒';
   play.textContent=playing?'暂停':'播放';}
 function advance(ms){if(!playing)return;t+=ms*globalSpeed;if(t>=total){if(cfg.loop)t%=total;else{t=total;playing=false}}draw()}
 function jump(i){t=dur.slice(0,Math.max(0,Math.min(i,dur.length-1))).reduce((a,b)=>a+b,0);playing=false;draw()}
 play.onclick=()=>{if(t>=total)t=0;playing=!playing;draw()};prev.onclick=()=>jump(index-1);next.onclick=()=>jump(index+1);
 seek.oninput=()=>{t=Number(seek.value);playing=false;draw()};draw();animations.push({advance,play:()=>{if(t>=total)t=0;playing=true;draw()},pause:()=>{playing=false;draw()},restart:()=>{t=0;playing=true;draw()}})
}
for(const [name,cfg] of Object.entries(M.animation.rows))create(name,cfg);
let last=null;function tick(now){if(last!==null){let dt=Math.min(100,now-last);for(const a of animations)a.advance(dt)}last=now;requestAnimationFrame(tick)}requestAnimationFrame(tick);
document.getElementById('allPlay').onclick=()=>animations.forEach(a=>a.play());document.getElementById('allPause').onclick=()=>animations.forEach(a=>a.pause());document.getElementById('allReplay').onclick=()=>animations.forEach(a=>a.restart());
document.getElementById('speed').onchange=e=>{globalSpeed=Number(e.target.value)};
</script></body></html>'''


def build_preview(root, manifest):
    root = Path(root)
    png = root / "assets" / manifest["game_input"]
    binary = base64.b64encode(png.read_bytes()).decode("ascii")
    payload = json.dumps(manifest,ensure_ascii=False).replace("<","\\u003c").replace("\u2028","\\u2028")
    html = HTML.replace("__MANIFEST__",payload).replace("__IMAGE__","data:image/png;base64," + binary)
    target = root / "previews" / "动作预览.html"
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(html,encoding="utf-8")
    return target


RUNTIME_TS = r'''import { _decorator, Component, Sprite, SpriteFrame, Texture2D, JsonAsset, Rect, Size, Vec2 } from 'cc';
const { ccclass, property } = _decorator;

type ActionFrame = {x:number;y:number;w:number;h:number};
type ActionState = {loop:boolean;durations_ms:number[];events?:{name:string;at_ms:number}[]};
interface MotionManifest { sheet:{cell_width:number;cell_height:number};
  animation:{rows:Record<string,ActionState>};frame_layout:{rows:Record<string,ActionFrame[]>} }

/** Cocos Creator 3.8.x: attach to a node with Sprite and assign atlas/manifest in Inspector.
 * Visual playback only. Logical knockback and hit verification are owned by your combat controller.
 * Emits 'character-action-event' (state, eventName) and 'character-action-end' (state).
 */
@ccclass('CharacterActionPlayer')
export class CharacterActionPlayer extends Component {
  @property({ type: Sprite }) public target: Sprite | null = null;
  @property({ type: Texture2D }) public atlas: Texture2D | null = null;
  @property({ type: JsonAsset }) public manifest: JsonAsset | null = null;
  @property public initialState = 'idle';
  @property public speed = 1;
  private spec: MotionManifest | null = null;
  private frames: Record<string,SpriteFrame[]> = {};
  private state = '';
  private elapsed = 0;
  private completed = false;
  private emitted = new Set<number>();

  onLoad() {
    if (!this.target) this.target = this.getComponent(Sprite);
    if (!this.target || !this.atlas || !this.manifest?.json) {
      console.warn('[CharacterActionPlayer] 请在属性面板配置 Sprite、Texture2D 和 JsonAsset'); return;
    }
    this.spec = this.manifest.json as MotionManifest;
    for (const [name, rects] of Object.entries(this.spec.frame_layout.rows)) {
      this.frames[name] = rects.map(r => {
        const sf = new SpriteFrame();sf.texture = this.atlas!;
        sf.rect = new Rect(r.x,r.y,r.w,r.h);
        sf.originalSize = new Size(this.spec!.sheet.cell_width,this.spec!.sheet.cell_height);
        sf.offset = new Vec2(0,0);return sf;
      });
    }
    this.play(this.initialState);
  }

  public play(name:string, restart=true) {
    if (!this.spec?.animation.rows[name] || !this.frames[name]) return false;
    if (!restart && this.state===name) return true;
    this.state = name;this.elapsed=0;this.completed=false;this.emitted.clear();this.showFrame(0);return true;
  }

  private showFrame(index:number) {
    if (!this.target)return;
    const frames=this.frames[this.state];if(frames?.[index])this.target.spriteFrame=frames[index];
  }

  update(dt:number) {
    if (!this.spec || this.completed || this.speed<=0 || !this.state)return;
    const action=this.spec.animation.rows[this.state];if (!action)return;
    const durations=action.durations_ms;const total=durations.reduce((s,v)=>s+v,0);
    if (total<=0)return;
    let next=this.elapsed+Math.max(0,dt*1000*this.speed);
    // Emit events on every crossed interval; cap large delta to avoid unbounded loops.
    let ticks=0;
    while(next>=total && action.loop && ticks++<8){this.emitEvents(action,this.elapsed,total);next-=total;this.elapsed=0;this.emitted.clear();}
    if(next>=total && !action.loop){this.emitEvents(action,this.elapsed,total);this.elapsed=total;this.showFrame(durations.length-1);
      this.completed=true;this.node.emit('character-action-end',this.state);return;}
    if(ticks>=8){next%=total;this.elapsed=0;this.emitted.clear();}
    this.emitEvents(action,this.elapsed,next);this.elapsed=next;
    let t=next,index=0;while(index<durations.length-1 && t>=durations[index]){t-=durations[index];index++}this.showFrame(index);
  }

  private emitEvents(action:ActionState, a:number,b:number){
    const ev=action.events||[];for(let i=0;i<ev.length;i++){if(this.emitted.has(i))continue;
      if(ev[i].at_ms>=a && ev[i].at_ms<=b){this.emitted.add(i);this.node.emit('character-action-event',this.state,ev[i].name);}}
  }
}
'''


def export_cocos(root, manifest):
    root=Path(root)
    out=root/"cocos"
    (out/"scripts").mkdir(parents=True,exist_ok=True)
    shutil.copy2(root/"assets"/"sprite-sheet.png",out/"sprite-sheet.png")
    # Static manifest is a native Cocos JsonAsset once imported into resources.
    save(out/"actions.json",manifest)
    (out/"scripts"/"CharacterActionPlayer.ts").write_text(RUNTIME_TS,encoding="utf-8")
    (out/"使用说明.md").write_text("""# Cocos Creator 3.8.x 导入说明

1. 将 sprite-sheet.png 和 actions.json 放入项目 assets/resources/角色名/ 下（不需要原始动图）。
2. 将 scripts/CharacterActionPlayer.ts 放入项目 assets/scripts/。
3. 在场景创建一个带 Sprite 的节点，挂载 CharacterActionPlayer。
4. 在组件属性面板，把图集生成的 Texture2D 子资源赋值给 atlas，把 actions.json 赋值给 manifest，把 Sprite 组件赋值给 target。
5. 设置 initialState，例如 idle。使用 player.play('attack') 或 player.play('hurt_head') 切换动作。
6. 监听节点 character-action-event 触发实际命中判定；不要仅凭视觉帧造成伤害。
7. **重要：** 本包提供可加载素材与运行时播放器，不伪称已在你的游戏工程中测试，也不会自动生成原生 .anim / Prefab。
8. 真实受击击退、碰撞、落地与 hitstop 由游戏战斗系统处理；本组件只负责图像播放与动作事件。
""",encoding="utf-8")
    return out
