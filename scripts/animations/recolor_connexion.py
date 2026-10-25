"""GIF gris du cavalier -> webp transparent aux couleurs Pony Express (teintes reprises du loader).

Usage : python scripts/animations/recolor_connexion.py source.gif sortie.webp
(puis réduire à 820 px de large pour static/img/connexion-cavalier.webp)
"""
import sys
import numpy as np
from scipy import ndimage
from PIL import Image
K=3                                   # agrandissement
src=Image.open(sys.argv[1]); lw=Image.open("static/img/loader.webp")
PAL=np.array([(0x6C,0x38,0xF5),(0x1E,0x4F,0xD8),(0xFF,0xA7,0x66),(0xC9,0xC3,0xF4)],float)
S_,OX,OY=0.8375,-86.5,-57.5                 # position du loader par rapport au GIF
frames=[];dur=[]
for i in range(src.n_frames):
    src.seek(i); lw.seek(i); dur.append(src.info.get("duration",100))
    g0=src.convert("L"); W0,H0=g0.size
    g=np.array(g0.resize((W0*K,H0*K),Image.LANCZOS)).astype(float)
    L=np.array(lw.convert("RGBA")).astype(float)
    H,W=g.shape; ys,xs=np.mgrid[0:H,0:W]
    lx=np.clip(np.round(xs/K*S_+OX).astype(int),0,L.shape[1]-1); ly=np.clip(np.round(ys/K*S_+OY).astype(int),0,L.shape[0]-1)
    ref=L[ly,lx]
    cls=((ref[...,None,:3]-PAL[None,None])**2).sum(-1).argmin(-1)
    cls[ref[...,3]<100]=3
    # vote majoritaire 9x9 : supprime les liserés de mauvaise couleur aux bords
    votes=np.stack([ndimage.uniform_filter((cls==k).astype(float),size=9) for k in range(4)])
    cls=votes.argmax(0)
    # bords clairs collés au personnage : couleur du personnage, pas lavande
    perso=votes[:3].max(0)>0.04
    bord=(g>=215)&perso
    cls[bord]=votes[:3].argmax(0)[bord]
    out=np.zeros((H,W,4))
    for k in range(4):
        m=(cls==k)&(g<248)
        if not m.any(): continue
        med=np.median(g[m&(g<235)]) if (m&(g<235)).any() else np.median(g[m])
        ratio=np.clip(g/med,0.6,1.0)[...,None]          # on garde les ombres, pas les bords clairs
        col=PAL[k]*ratio
        out[m,:3]=np.clip(col[m],0,255)
    # alpha doux : le gris clair du bord devient transparent progressivement
    out[...,3]=np.clip((252-g)/22*255,0,255)
    out[g>=250,3]=0
    frames.append(Image.fromarray(out.astype("uint8"),"RGBA"))
boxes=[f.getbbox() for f in frames]
x0=min(b[0] for b in boxes);y0=min(b[1] for b in boxes);x1=max(b[2] for b in boxes);y1=max(b[3] for b in boxes)
m=12*K; frames=[f.crop((max(0,x0-m),max(0,y0-m),x1+m,y1+m)) for f in frames]
frames[0].save(sys.argv[2],save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True,method=6)
print(frames[0].size)
