#!/usr/bin/env python3
"""Вклеить перерисованный участок (правка увеличенной вырезки) обратно в кадр базы.

  python tools/assets/patch_region.py БАЗА.png СЫРОЙ_КАДР.png X0,Y0,X1,Y1 ВЫХОД.png [ШИРЕ]

Участок X0,Y0–X1,Y1 базы вырезался, увеличивался (×3–×4) и правился генератором. Генератор отдаёт
кадр своей пропорции (обрезка по центру или растяжение) и чуть другого масштаба — подбираются
способ подгонки, масштаб 0,97–1,03 и сдвиг ±8 px по медиане разницы с базой; с ШИРЕ=1 — масштаб
0,93–1,07 и сдвиг ±16 px (участок правился дважды и «уплыл»). ВЫХОД — кадр-вариант
1920×1080 (база с вклеенным участком) для tools/assets/cutout.py.
"""
import sys, numpy as np
from PIL import Image
base=Image.open(sys.argv[1]).convert('RGB'); raw=Image.open(sys.argv[2]).convert('RGB')
x0,y0,x1,y1=map(int,sys.argv[3].split(','))
WIDE=len(sys.argv)>5 and sys.argv[5]=='1'
SCALES=[round(0.93+0.01*i,2) for i in range(15)] if WIDE else [0.97,0.98,0.99,1.0,1.01,1.02,1.03]
SH=16 if WIDE else 8
w,h=x1-x0,y1-y0
B=np.asarray(base,float)
best=None
# варианты: сырой кадр растянут целиком в участок, либо обрезан по центру по большей стороне
cands=[]
rw,rh=raw.size
cands.append(('stretch',raw))
t=w/h
if rw/rh>t:
  nw=round(rh*t); cands.append(('cropx',raw.crop(((rw-nw)//2,0,(rw-nw)//2+nw,rh))))
else:
  nh=round(rw/t); cands.append(('cropy',raw.crop((0,(rh-nh)//2,rw,(rh-nh)//2+nh))))
for name,im in cands:
  for s in SCALES:
    pw,ph=round(w*s),round(h*s)
    p=np.asarray(im.resize((pw,ph),Image.LANCZOS),float)
    cx,cy=x0+(w-pw)//2,y0+(h-ph)//2
    for dx in range(-SH,SH+1,2):
      for dy in range(-SH,SH+1,2):
        X,Y=cx+dx,cy+dy
        a=B[Y+10:Y+ph-10, X+10:X+pw-10]; b=p[10:-10,10:-10]
        if a.shape!=b.shape: continue
        d=np.median(np.abs(a-b))
        if best is None or d<best[0]: best=(d,name,s,dx,dy)
d,name,s,dx,dy=best
# доуточнить сдвиг по 1 px
im=dict(cands)[name]; pw,ph=round(w*s),round(h*s)
p=np.asarray(im.resize((pw,ph),Image.LANCZOS),float); cx,cy=x0+(w-pw)//2,y0+(h-ph)//2
for ddx in (-1,0,1):
  for ddy in (-1,0,1):
    X,Y=cx+dx+ddx,cy+dy+ddy
    a=B[Y+10:Y+ph-10, X+10:X+pw-10]; b=p[10:-10,10:-10]
    if a.shape!=b.shape: continue
    dd=np.median(np.abs(a-b))
    if dd<d: d,best=dd,(dd,name,s,dx+ddx,dy+ddy)
d,name,s,dx,dy=best
out=base.copy(); out.paste(Image.fromarray(p.astype('uint8')),(cx+dx,cy+dy)); out.save(sys.argv[4])
print(name,'scale',s,'shift',dx,dy,'median',d,'at',cx+dx,cy+dy,pw,ph)
