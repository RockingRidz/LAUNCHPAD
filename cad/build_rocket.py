"""Base geometry helper for build_rocket_v2.py. Run the v2 builder for final exports."""
from pathlib import Path
import json, math
import FreeCAD as App
import Part, MeshPart

HERE = Path(__file__).resolve().parent
P = json.loads((HERE/'parameters.json').read_text())
V=App.Vector
doc=App.newDocument('LAUNCHPAD')
sheet=doc.addObject('Spreadsheet::Sheet','Dimensions')
for row,(key,value) in enumerate(P.items(),1):
    sheet.set('A'+str(row),key); sheet.set('B'+str(row),str(value))
    if isinstance(value,(int,float)): sheet.setAlias('B'+str(row),key)
r=P['body_radius']; h=P['body_height']; wall=P['wall']; nose=P['nose_height']
outer=Part.makeCylinder(r,h).fuse(Part.makeCone(r,2,nose,V(0,0,h)))
inner=Part.makeCylinder(r-wall,h-wall,V(0,0,wall)).fuse(Part.makeCone(r-wall,0,nose-wall,V(0,0,h)))
shell=outer.cut(inner)
# Front faces -Y. Window and flat bezel support touch presses without bending glass.
w=P['screen_window_width']; sh=P['screen_window_height']; z=P['screen_bottom']
bezel=Part.makeBox(w+14,12,sh+14,V(-(w+14)/2,-r-3,z-7))
shell=shell.fuse(bezel).cut(Part.makeBox(w,25,sh,V(-w/2,-r-6,z)))
# Rear-open display pocket for portrait 50.8 x 79.9 PCB, with 0.6mm clearance.
# Four printed clips hold its PCB edges; foam tape supports the bezel, not the glass.
pw=51.4; ph=80.5; pz=z+(sh-ph)/2
shell=shell.cut(Part.makeBox(pw,9,ph,V(-pw/2,-r+3,pz)))
for sx in (-1,1):
    for zz in (pz+4,pz+ph-10):
        clip=Part.makeBox(7,12,6,V(sx*(pw/2+2)-3.5,-r+7,zz))
        # Clip geometry bridges the curved wall and rear edge of PCB.
        shell=shell.fuse(clip)
# Three fins, each fused to the shell, provide a broad base.
for deg in (30,150,270):
    points=[V(r-5,0,0),V(r+24,0,0),V(r+21,0,8),V(r-5,0,52),V(r-5,0,0)]
    fin=Part.Face(Part.makePolygon(points)).extrude(V(0,4,0))
    fin.rotate(V(0,0,0),V(0,0,1),deg)
    shell=shell.fuse(fin)
# Rear service cover cut-out, screw bosses and a removable lid.
cw=44; ch=102; cz=20
shell=shell.cut(Part.makeBox(cw,25,ch,V(-cw/2,r-14,cz)))
lid=Part.makeBox(cw+12,3,ch+12,V(-(cw+12)/2,r-1,cz-6))
for x in (-cw/2-2,cw/2+2):
    for zz in (cz-2,cz+ch+2):
        boss=Part.makeCylinder(4,12,V(x,r-12,zz),V(0,1,0))
        bore=Part.makeCylinder(1.25,18,V(x,r-14,zz),V(0,1,0))
        shell=shell.fuse(boss).cut(bore)
        lid=lid.cut(Part.makeCylinder(1.7,8,V(x,r-3,zz),V(0,1,0)))
# Side USB cable slot and rear cover ventilation slots.
shell=shell.cut(Part.makeBox(18,16,10,V(r-12,-8,12)))
for zz in range(40,106,8):
    lid=lid.cut(Part.makeBox(25,8,2.5,V(-12.5,r-3,zz)))
for xx in (-11.5,11.5):
    for zz in (42,100):
        lid=lid.cut(Part.makeCylinder(1.4,8,V(xx,r-3,zz),V(0,1,0)))
# Pi mounts on a removable carrier; four true Pi Zero mounting centres: 58 x 23.
carrier=Part.makeBox(72,37,2)
for x in (7,65):
    for y in (7,30):
        carrier=carrier.fuse(Part.makeCylinder(3.5,6,V(x,y,2)))
        carrier=carrier.cut(Part.makeCylinder(1.4,10,V(x,y,0)))
objects=[]
for name,shape in [('RocketBody',shell),('RearCover',lid),('PiCarrier',carrier)]:
    shape=shape.removeSplitter()
    if not shape.isValid(): raise RuntimeError(name+' failed solid validation')
    if len(shape.Solids)!=1: raise RuntimeError(name+' must be one solid, got '+str(len(shape.Solids)))
    obj=doc.addObject('PartDesign::Feature',name); obj.Shape=shape; objects.append(obj)
    mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=0.15,AngularDeflection=0.15,Relative=False)
    mesh.write(str(HERE/(name+'.stl')))
    Part.export([obj],str(HERE/(name+'.step')))
# Place carrier vertically behind the LCD in the assembly, keeping individual exports flat.
transform=App.Matrix()
transform.A11=0; transform.A12=1; transform.A13=0; transform.A14=-18.5
transform.A21=0; transform.A22=0; transform.A23=-1; transform.A24=r-5
transform.A31=1; transform.A32=0; transform.A33=0; transform.A34=35
objects[2].Placement=App.Placement(transform)
doc.recompute()
doc.saveAs(str(HERE/'LAUNCHPAD.FCStd'))
Part.export(objects,str(HERE/'LAUNCHPAD-assembly.step'))
report={o.Name:{'valid':o.Shape.isValid(),'solids':len(o.Shape.Solids),'volume_mm3':o.Shape.Volume,'pla_mass_g_estimate':round(o.Shape.Volume*0.00124,1),'bounds_mm':[o.Shape.BoundBox.XLength,o.Shape.BoundBox.YLength,o.Shape.BoundBox.ZLength]} for o in objects}
(HERE/'geometry-check.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
