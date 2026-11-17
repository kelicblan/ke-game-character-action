"""CLI for host-tool-driven image animation production."""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from PIL import Image

from .core import ActionError, initialize, ingest, load, next_task, prompt_for, review, save, summary
from .image_ops import diagnostics, make_atlas
from .outputs import build_preview, export_cocos


def output(obj):
    print(json.dumps(obj,ensure_ascii=False,indent=2))


def command_items(raw):
    if not raw:
        return None
    if raw.startswith("["):
        out=json.loads(raw)
    else:
        out=shlex.split(raw)
    if not isinstance(out,list) or not out or any(not isinstance(x,str) or not x for x in out):
        raise ActionError("生成器命令应为非空 argv 数组或非空命令行字符串")
    return out


def call_command(argv, values, timeout=180):
    # No shell; user configured tools run using the already permitted host environment.
    cmd=[x.format_map(values) for x in argv]
    res=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout)
    if res.returncode:
        raise ActionError("命令失败："+" ".join(cmd[:2])+"\n"+(res.stderr or res.stdout)[-800:])
    return res.stdout


def prepare_request(root, task):
    d=root/"prompts"/task["state"]
    d.mkdir(parents=True,exist_ok=True)
    name=f"frame_{task['frame']:03d}_attempt_{task['attempt']}"
    path=d/(name+".txt")
    path.write_text(task["prompt"],encoding="utf-8")
    jpath=d/(name+".json")
    save(jpath,task)
    return path,jpath


def execute(root, args):
    generator=command_items(args.generator)
    if not generator:
        raise ActionError("run 必须指定实际可运行的图片生成器命令；没有命令时由宿主 AI 按 next→图片工具→ingest→review 执行")
    reviewer=command_items(args.reviewer) if args.reviewer else None
    job=load(root/"job.json")
    job["max_attempts"]=args.attempts
    save(root/"job.json",job)
    while True:
        task=next_task(root)
        if task["status"]=="complete":
            break
        if task["status"]=="blocked":
            output(task)
            raise ActionError("存在已达重试上限的不合格动作帧")
        prompt_file,request_file=prepare_request(root,task)
        out=Path(task["output"])
        out.parent.mkdir(parents=True,exist_ok=True)
        vals={"source":task["references"][0],"reference":task["references"][-1],
              "prompt":task["prompt"],"prompt_file":str(prompt_file),"request_file":str(request_file),
              "state":task["state"],"frame":str(task["frame"]),"attempt":str(task["attempt"]),"output":str(out)}
        try:
            call_command(generator,vals,timeout=args.timeout)
            result=ingest(root,task["state"],task["frame"],out,chroma=args.chroma)
            if result["status"]=="rejected":
                continue
            if reviewer:
                verdict_path=out.with_suffix(".review.json")
                vals["image"]=str((root/"frames"/task["state"]/f"frame_{task['frame']:03d}.png").resolve())
                vals["review_output"]=str(verdict_path)
                call_command(reviewer,vals,timeout=args.timeout)
                verdict=load(verdict_path)
                if type(verdict.get("ok")) is not bool:
                    raise ActionError("审核器必须产生 {ok:boolean, issues:string[]} 格式")
                review(root,task["state"],task["frame"],passed=verdict["ok"],issues=verdict.get("issues"))
        except (OSError,ValueError,subprocess.TimeoutExpired) as e:
            job=load(root/"job.json")
            frame=job["states"][task["state"]][task["frame"]]
            # Avoid double counting if ingest already rejected the attempt.
            if frame["attempts"]<task["attempt"]:
                frame["attempts"]+=1
            frame["status"]="rejected"
            frame["issues"]=[str(e)[:300]]
            save(root/"job.json",job)
    return produce(root,draft=reviewer is None)


def produce(root, *, draft):
    job, plan=load(root/"job.json"),load(root/"plan.json")
    manifest=make_atlas(root,job,plan,draft=draft)
    html=build_preview(root,manifest)
    cocos=export_cocos(root,manifest)
    return {"status":"success","quality":manifest["quality"],
            "preview":str(html),"atlas":str(root/"assets"/"sprite-sheet.png"),
            "manifest":str(root/"assets"/"manifest.json"),"cocos":str(cocos),"summary":summary(job)}


def ingest_grid(root,args):
    root=Path(root)
    with Image.open(args.image) as im:
        if im.width%args.columns or im.height%args.rows:
            raise ActionError("生成的网格宽高不能被列数/行数整除")
        w,h=im.width//args.columns,im.height//args.rows
        size=args.columns*args.rows
        job=load(root/"job.json")
        if args.state not in job["states"]:
            raise ActionError("状态不存在")
        if args.start+size>len(job["states"][args.state]):
            raise ActionError("精灵网格帧数超出动作方案")
        for i in range(size):
            frame=args.start+i
            crop=im.crop(((i%args.columns)*w,(i//args.columns)*h,(i%args.columns+1)*w,(i//args.columns+1)*h))
            path=root/"incoming"/f"{args.state}_{frame:03d}_grid.png"
            path.parent.mkdir(parents=True,exist_ok=True)
            crop.save(path)
            ingest(root,args.state,frame,path,chroma=args.chroma)
    return {"status":"imported","state":args.state,"frames":size}


def main(argv=None):
    p=argparse.ArgumentParser(description="独立角色动画自动化：宿主 AI 调用图片工具并回填帧，或者通过生成器命令一键运行")
    sp=p.add_subparsers(dest="cmd",required=True)
    init=sp.add_parser("init",help="从角色原图与动作方案初始化任务")
    init.add_argument("--source",required=True);init.add_argument("--plan",required=True);init.add_argument("--job",required=True);init.add_argument("--force",action="store_true")
    nxt=sp.add_parser("next",help="领取下一帧生成请求（JSON）");nxt.add_argument("--job",required=True)
    imp=sp.add_parser("ingest",help="导入当前宿主图像工具实际生成的帧")
    imp.add_argument("--job",required=True);imp.add_argument("--state",required=True);imp.add_argument("--frame",required=True,type=int);imp.add_argument("--image",required=True);imp.add_argument("--chroma")
    grid=sp.add_parser("ingest-grid",help="把等格子网格图切为独立帧并回填")
    grid.add_argument("--job",required=True);grid.add_argument("--state",required=True);grid.add_argument("--image",required=True);grid.add_argument("--columns",type=int,required=True);grid.add_argument("--rows",type=int,required=True);grid.add_argument("--start",type=int,default=0);grid.add_argument("--chroma")
    rv=sp.add_parser("review",help="记录视觉/角色一致性审核结论")
    rv.add_argument("--job",required=True);rv.add_argument("--state",required=True);rv.add_argument("--frame",type=int,required=True)
    choice=rv.add_mutually_exclusive_group(required=True);choice.add_argument("--pass",action="store_true",dest="passed");choice.add_argument("--reject",action="store_true");rv.add_argument("--issue",action="append")
    run=sp.add_parser("run",help="使用当前环境已配置的生成器命令自动生成和打包")
    run.add_argument("--job",required=True);run.add_argument("--generator",required=True,help="argv JSON 数组或非 shell 命令，支持 {source}/{reference}/{prompt_file}/{output}/{state}/{frame}")
    run.add_argument("--reviewer",help="可选视觉审核命令，支持 {image}/{review_output}")
    run.add_argument("--attempts",type=int,default=3);run.add_argument("--timeout",type=int,default=180);run.add_argument("--chroma")
    build=sp.add_parser("build",help="打包图集、中国网页预览与 Cocos 运行时资源")
    build.add_argument("--job",required=True);build.add_argument("--draft",action="store_true")
    st=sp.add_parser("status",help="查看任务和 QA 状态");st.add_argument("--job",required=True)
    args=p.parse_args(argv)
    try:
        root=Path(args.job).resolve()
        if args.cmd=="init":
            output({"status":"initialized","summary":summary(initialize(root,args.source,args.plan,force=args.force))})
        elif args.cmd=="next":
            task=next_task(root)
            if task["status"]=="ready":
                prompt_file,req=prepare_request(root,task)
                task["prompt_file"]=str(prompt_file)
            output(task)
        elif args.cmd=="ingest":output(ingest(root,args.state,args.frame,args.image,chroma=args.chroma))
        elif args.cmd=="ingest-grid":output(ingest_grid(root,args))
        elif args.cmd=="review":output(review(root,args.state,args.frame,passed=args.passed,issues=args.issue))
        elif args.cmd=="run":
            if not 1<=args.attempts<=10:raise ActionError("attempts须为1到10")
            output(execute(root,args))
        elif args.cmd=="build":output(produce(root,draft=args.draft))
        elif args.cmd=="status":
            job=load(root/"job.json");output({"summary":summary(job),"qa":diagnostics(root,job,load(root/"plan.json"))})
        return 0
    except (ActionError,ValueError,OSError,subprocess.TimeoutExpired) as e:
        print("错误："+str(e),file=sys.stderr)
        return 1


if __name__=="__main__":
    raise SystemExit(main())
