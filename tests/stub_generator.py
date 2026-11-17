"""Only for tests: synthetic PNG image output, not a real generative model."""
import argparse
from PIL import Image, ImageDraw
p=argparse.ArgumentParser()
p.add_argument('--output',required=True)
p.add_argument('--state',required=True)
p.add_argument('--frame',required=True,type=int)
p.add_argument('--attempt',required=True,type=int)
a=p.parse_args()
im=Image.new('RGBA',(128,128),(0,0,0,0))
d=ImageDraw.Draw(im)
o=a.frame*3
# Strict alpha + a visible body, with different shapes for test states.
d.ellipse((37+o,17,87+o,66),fill=(91,165,180,255))
d.rectangle((40+o,60,82+o,112),fill=(72,85,132,255))
if a.state.startswith('hurt'):
    d.rectangle((36+o,58,85+o,79),fill=(116,94,190,255))
im.save(a.output)
