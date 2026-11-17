import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from action_factory.core import ActionError,initialize,load,next_task,ingest,review,validate_plan
from action_factory.image_ops import prepare_frame


class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.src=self.root/'source.png'
        Image.new('RGBA',(128,128),(0,0,0,0)).save(self.src)
        self.plan=self.root/'plan.json'
        self.plan.write_text((ROOT/'templates'/'action_plan_v2.example.json').read_text(encoding='utf-8'),encoding='utf-8')
        self.job=self.root/'job'

    def invoke(self,*args):
        return subprocess.run([sys.executable,'-m','action_factory',*args],cwd=ROOT,capture_output=True,text=True,timeout=30)

    def test_plan_validation(self):
        p=json.loads(self.plan.read_text(encoding='utf-8'))
        validate_plan(p)
        p['states']['idle']['poses'].pop()
        with self.assertRaises(ActionError):validate_plan(p)

    def test_run_with_image_generator_and_reviewer(self):
        # Keep the live-provider/reviewer integration test small; full schedules are validated separately.
        plan=json.loads(self.plan.read_text(encoding='utf-8'))
        plan['states']={k:plan['states'][k] for k in ('idle','hurt_head')}
        for state in plan['states'].values():
            state['frames']=2
            state['durations_ms']=state['durations_ms'][:2]
            state['poses']=state['poses'][:2]
            state.pop('events',None)
        self.plan.write_text(json.dumps(plan,ensure_ascii=False),encoding='utf-8')
        init=self.invoke('init','--source',str(self.src),'--plan',str(self.plan),'--job',str(self.job))
        self.assertEqual(init.returncode,0,init.stderr)
        generator=json.dumps([sys.executable,str(ROOT/'tests'/'stub_generator.py'),
              '--state','{state}','--frame','{frame}','--attempt','{attempt}','--output','{output}'])
        reviewer=json.dumps([sys.executable,str(ROOT/'tests'/'stub_reviewer.py'),
              '--state','{state}','--frame','{frame}','--attempt','{attempt}','--review-output','{review_output}'])
        run=self.invoke('run','--job',str(self.job),'--generator',generator,'--reviewer',reviewer)
        self.assertEqual(run.returncode,0,run.stderr)
        result=json.loads(run.stdout)
        self.assertEqual(result['quality'],'visually_reviewed')
        j=load(self.job/'job.json')
        self.assertEqual(j['states']['hurt_head'][1]['attempts'],2)
        manifest=load(self.job/'assets'/'manifest.json')
        self.assertEqual(set(manifest['animation']['rows']),{'idle','hurt_head'})
        self.assertEqual(sum(manifest['animation']['rows']['hurt_head']['durations_ms']),150)
        with Image.open(self.job/'assets'/'sprite-sheet.png') as im:
            self.assertEqual(im.mode,'RGBA')
            self.assertEqual(im.width,256)
        html=(self.job/'previews'/'动作预览.html').read_text(encoding='utf-8')
        for text in ['全部播放','全部暂停','上一帧','播放速度','data:image/png;base64']:
            self.assertIn(text,html)
        ts=(self.job/'cocos'/'scripts'/'CharacterActionPlayer.ts').read_text(encoding='utf-8')
        self.assertIn('SpriteFrame',ts)
        self.assertIn('character-action-event',ts)
        self.assertIn('hit_context',json.dumps(manifest,ensure_ascii=False))

    def test_host_tool_manual_ingest_and_draft(self):
        initialize(self.job,self.src,self.plan)
        task=next_task(self.job)
        self.assertEqual(task['status'],'ready')
        self.assertIn('固定视角',task['prompt'])
        frame=self.root/'frame.png'
        gen=self.invoke('status','--job',str(self.job))
        self.assertEqual(gen.returncode,0)
        Image.new('RGBA',(64,64),(0,0,0,0)).save(frame)
        r=ingest(self.job,'idle',0,frame)
        self.assertEqual(r['status'],'rejected')
        self.assertIn('全透明',r['issues'][0])
        with Image.open(self.src) as im:
            pass
        Image.new('RGBA',(64,64),(255,0,255,255)).save(frame)
        with self.assertRaises(ValueError):prepare_frame(frame,self.root/'out.png')
        r=ingest(self.job,'idle',0,frame,chroma='FF00FF')
        self.assertEqual(r['status'],'rejected')
        with Image.new('RGBA',(64,64),(0,0,0,0)) as im:
            for x in range(20,45):
                for y in range(12,48):im.putpixel((x,y),(200,80,50,255))
            im.save(frame)
        r=ingest(self.job,'idle',0,frame)
        self.assertEqual(r['status'],'generated')
        review(self.job,'idle',0,passed=True)
        self.assertEqual(next_task(self.job)['frame'],1)

    def test_cannot_build_missing_frames(self):
        initialize(self.job,self.src,self.plan)
        proc=self.invoke('build','--job',str(self.job),'--draft')
        self.assertNotEqual(proc.returncode,0)
        self.assertIn('缺失',proc.stderr)


if __name__=='__main__':unittest.main()
