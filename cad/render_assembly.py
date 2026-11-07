"""Rasterize the actual STL exports for documentation; references are simplified boxes."""
from pathlib import Path
import struct
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent

def mesh(name):
    b=(ROOT/(name+'.stl')).read_bytes();n=struct.unpack_from('<I',b,80)[0]
    dt=np.dtype([('normal','<f4',(3,)),('v','<f4',(3,3)),('attr','<u2')]);return np.frombuffer(b,dt,n,84)['v'].astype(float)
def box(size,origin):
    x,y,z=size;a,b,c=origin
    v=np.array([[a,b,c],[a+x,b,c],[a+x,b+y,c],[a,b+y,c],[a,b,c+z],[a+x,b,c+z],[a+x,b+y,c+z],[a,b+y,c+z]])
    return v[np.array([[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]])]
def geometry(exploded=False):
    parts=[]
    def add(name,vertices,color,delta=(0,0,0)):parts.append((name,vertices+np.array(delta),np.array(color)))
    add('Body',mesh('RocketBody'),[219,229,234])
    add('Nose',mesh('NoseCone'),[245,112,53],(0,0,182 if exploded else 142))
    add('Cover',mesh('RearCover'),[48,66,83],(95,20,14) if exploded else (0,0,14))
    tray=mesh('PiCarrier');tray=np.stack([18.5-tray[:,:,1],39.2-tray[:,:,2],35+tray[:,:,0]],axis=-1)
    add('Carrier',tray,[56,153,124],(80,20,0) if exploded else (0,0,0))
    for name,z in [('LCDRetainerLower',60),('LCDRetainerUpper',127)]:add(name,mesh(name),[250,172,74],(-72,0,z) if exploded else (0,0,z))
    add('LCD',box((50,3.61,71.5),(-25,-39.4,57.55)),[27,40,48])
    add('Screen',box((43.2,.15,57.6),(-21.6,-39.55,64.5)),[66,192,207])
    return parts

def render(exploded=False):
    width,height=1600,1200;parts=geometry(exploded)
    camera=np.array([.55,-1,.45]);camera/=np.linalg.norm(camera)
    right=np.cross([0,0,1],camera);right/=np.linalg.norm(right);up=np.cross(camera,right)
    allv=np.concatenate([p[1].reshape(-1,3) for p in parts]);bounds=np.stack([allv@right,allv@up],axis=-1)
    low=bounds.min(axis=0);high=bounds.max(axis=0);scale=min((width-240)/(high[0]-low[0]),(height-330)/(high[1]-low[1]));center=(low+high)/2
    rgb=np.full((height,width,3),[245,247,249],dtype=np.uint8);depth=np.full((height,width),-np.inf)
    light=np.array([-.2,-1,1]);light/=np.linalg.norm(light)
    for name,triangles,color in parts:
        for world in triangles:
            normal=np.cross(world[1]-world[0],world[2]-world[0]);length=np.linalg.norm(normal)
            if length<1e-9:continue
            normal/=length
            if normal@camera<=0:continue
            xy=np.stack([(world@right-center[0])*scale+width/2,-(world@up-center[1])*scale+height/2+40],axis=-1)
            z=world@camera
            minx=max(0,int(np.floor(xy[:,0].min())));maxx=min(width-1,int(np.ceil(xy[:,0].max())))
            miny=max(0,int(np.floor(xy[:,1].min())));maxy=min(height-1,int(np.ceil(xy[:,1].max())))
            if maxx<minx or maxy<miny:continue
            xx,yy=np.meshgrid(np.arange(minx,maxx+1)+.5,np.arange(miny,maxy+1)+.5)
            a,b,c=xy;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-9:continue
            u=((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/den
            v=((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/den;w=1-u-v
            zz=u*z[0]+v*z[1]+w*z[2];region=depth[miny:maxy+1,minx:maxx+1]
            mask=(u>=-1e-6)&(v>=-1e-6)&(w>=-1e-6)&(zz>region)
            shade=.52+.48*max(0,normal@light);rgb[miny:maxy+1,minx:maxx+1][mask]=np.clip(color*shade,0,255).astype(np.uint8);region[mask]=zz[mask]
    im=Image.fromarray(rgb);d=ImageDraw.Draw(im)
    try:title=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',40);small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
    except OSError:title=small=ImageFont.load_default()
    d.text((70,45),'LAUNCHPAD / '+('EXPLODED ASSEMBLY' if exploded else 'ROCKET COMPUTER'),font=title,fill='#152b3a')
    d.text((70,105),'Removable nose  /  LCD retainers  /  Pi carrier  /  Service cover',font=small,fill='#526d7e')
    d.text((70,height-80),'CAD design preview. Electronics shown as reference envelopes. Physical fit requires testing.',font=small,fill='#526d7e')
    out=ROOT.parent/'images'/('cad-exploded.png' if exploded else 'cad-assembled.png');im.save(out)
    if not exploded:im.save(ROOT.parent/'images'/'rocket-preview.png')
    print(out)
render();render(True)
