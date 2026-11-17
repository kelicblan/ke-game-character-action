"""Only for tests: rejects an action frame's first attempt to verify retry logic."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--state',required=True)
p.add_argument('--frame',required=True,type=int)
p.add_argument('--attempt',required=True,type=int)
p.add_argument('--review-output',required=True)
a=p.parse_args()
refuse=a.state.startswith('hurt') and a.frame==1 and a.attempt==1
Path(a.review_output).write_text(json.dumps({'ok':not refuse,'issues':['测试：重新生成第2帧'] if refuse else []}),encoding='utf-8')
