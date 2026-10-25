"""Loader gris (128 px) -> couleurs Pony Express, fond transparent, cactus violets."""
Usage : python scripts/animations/recolor_loader.py source_gris.webp static/img/loader.webp
import numpy as np
from PIL import Image
from scipy import ndimage

VIOLET=np.array((0x6C,0x38,0xF5),float); BLEU=np.array((0x1E,0x4F,0xD8),float)
PECHE=np.array((0xFF,0xA7,0x66),float); LAVANDE=np.array((0xDC,0xD8,0xF8),float)

def teinte(c, g, ref):
    r=np.clip(g/ref,0.7,1.25)[...,None]
    return np.where(r<=1, c*r, c+(255-c)*(r-1)*1.5)

src=Image.open(__import__("sys").argv[1]); frames=[]; durees=[]
for i in range(src.n_frames):
    src.seek(i); durees.append(src.info.get("duration",40))
    a=np.array(src.convert("RGBA")).astype(float)
    g=a[...,:3].mean(-1); al=a[...,3]
    vis=al>20
    out=a.copy()
    sol=vis&(al<140)&(g>200)                       # ligne de sol estompée
    fonce=vis&(g<125)&~sol                          # chapeau, ceinture, pistolets, bâton, bride
    clair=vis&(g>=185)&~sol                         # tête du cheval, reflets
    moyen=vis&~fonce&~clair&~sol                    # chemise, bras, jambes, cou
    # cactus : composante séparée du cavalier, haute et étroite, posée au sol
    corps=vis&~sol
    lab,n=ndimage.label(corps)
    tailles=ndimage.sum(corps,lab,range(1,n+1))
    cactus=np.zeros_like(vis)
    if n>1:
        cavalier=1+int(np.argmax([ndimage.sum(fonce,lab,k) for k in range(1,n+1)]))
        for k in range(1,n+1):
            if k==cavalier or tailles[k-1]<15: continue
            ys,xs=np.nonzero(lab==k)
            if (ys.max()-ys.min()+1)>=1.5*(xs.max()-xs.min()+1) and ndimage.sum(fonce,lab,k)==0:
                cactus|=lab==k
    # chemise = partie épaisse du gris moyen (les membres, fins, disparaissent à l'ouverture)
    epais=ndimage.binary_opening(moyen&~cactus, structure=np.ones((5,5)))
    le,ne=ndimage.label(epais)
    if ne>1:  # seule la plus grande zone épaisse est la chemise
        epais=le==1+int(np.argmax(ndimage.sum(epais,le,range(1,ne+1))))
    chemise=ndimage.binary_dilation(epais, np.ones((3,3)))&moyen&~cactus
    peau=(moyen|clair)&~chemise&~cactus
    for masque,coul,ref in ((fonce&~cactus,VIOLET,95),(chemise,BLEU,165),(peau,PECHE,180),(cactus,VIOLET,170),(sol,LAVANDE,222)):
        out[masque,:3]=np.clip(teinte(coul,g,ref)[masque],0,255)
    out[~vis,3]=0
    frames.append(Image.fromarray(out.astype("uint8"),"RGBA"))
boxes=[f.getbbox() for f in frames if f.getbbox()]
x0=min(b[0] for b in boxes)-4;y0=min(b[1] for b in boxes)-4;x1=max(b[2] for b in boxes)+4;y1=max(b[3] for b in boxes)+4
frames=[f.crop((max(0,x0),max(0,y0),min(128,x1),min(128,y1))) for f in frames]
w,h=frames[0].size
frames=[f.resize((w*3,h*3),Image.LANCZOS) for f in frames]
frames[0].save(__import__("sys").argv[2],save_all=True,append_images=frames[1:],duration=durees,loop=0,lossless=True,method=6)
print(frames[0].size, len(frames))
