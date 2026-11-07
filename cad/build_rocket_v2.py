"""Revision 0.4 assembly. Run with FreeCAD's Python; see production/BUILD.md.
The original builder is retained as the base geometry source, not the final exporter.
Optional --lcd-reference accepts Waveshare's STEP for local collision checking.
"""
from pathlib import Path
import argparse,runpy,json
import FreeCAD as App
import Part,MeshPart
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--lcd-reference',type=Path);args=parser.parse_args()
B=runpy.run_path(str(HERE/'build_rocket.py'))
doc=B['doc'];P=B['P'];V=App.Vector;r=P['body_radius'];h=P['body_height'];wall=P['wall']
def box(x,y,z,at):return Part.makeBox(x,y,z,V(*at))
def cyl(r,h,at,axis=(0,0,1)):return Part.makeCylinder(r,h,V(*at),V(*axis))
body=doc.getObject('RocketBody').Shape.copy()
body=body.cut(box(200,200,100,(-100,-100,h)))
# Remove protruding provisional clips; replace them with screwed retainer bridges.
pw=51.4;ph=80.5;pz=P['screen_bottom']+(P['screen_window_height']-ph)/2
for sx in (-1,1):
    for zz in (pz+4,pz+ph-10):body=body.cut(box(7,12,6,(sx*(pw/2+2)-3.5,-r+7,zz)))
# Official STEP bounds: PCB 50.7648x79.8595x1.6, glass front z=-5.4.
# Active area centred nominally at (25.424,38.8); portrait assembly transform below.
lcd_y=-34;lcd_z=54.5
bezel_width=P['screen_window_width']+14
body=body.fuse(box(bezel_width,24,85.6,(-bezel_width/2,-43,lcd_z-.4-wall)))
body=body.cut(box(P['screen_window_width'],30,P['screen_window_height'],(-P['screen_window_width']/2,-46,P['screen_bottom'])))
body=body.cut(box(51.6,21,80.8,(-25.8,-40,lcd_z-.4)))

# Flat seating flange resolves the gap left by a planar cover on a curved barrel.
rear_face=43
body=body.fuse(box(56,15,114,(-28,28,14))).cut(box(44,35,102,(-22,20,20)))
lid=box(56,3,114,(-28,rear_face+.2,14))
tongue=box(42.8,2.2,100.8,(-21.4,rear_face-2,20.6)).cut(box(38.8,3,96.8,(-19.4,rear_face-2.2,22.6)))
lid=lid.fuse(tongue)
for x in (-24,24):
    for z in (18,124):
        body=body.fuse(cyl(4,12,(x,rear_face-12,z),(0,1,0)))
        body=body.cut(cyl(1.25,18,(x,rear_face-14,z),(0,1,0)))
        lid=lid.cut(cyl(1.7,8,(x,rear_face-3,z),(0,1,0)))
for z in (48,56,64,72,80,88):lid=lid.cut(box(16,10,2.5,(-8,rear_face-4,z)))
for xx in (-11.5,11.5):
    for zz in (42,100):lid=lid.cut(cyl(1.4,10,(xx,rear_face-4,zz),(0,1,0)))
for z in (9,25):body=body.cut(box(18,2.5,3,(r-12,-1.25,z)))
for x in (-13,13):body=body.cut(box(3,30,8,(x-1.5,24,134)))
for x in (-6,0,6):body=body.cut(cyl(1.6,30,(x,24,137),(0,1,0)))

retainers=[]
for name,z in [('LCDRetainerLower',lcd_z+8),('LCDRetainerUpper',lcd_z+75)]:
    retainer=box(70,3,5,(-35,-25,z-2.5))
    for x in (-23.8,23.8):retainer=retainer.fuse(box(3.2,8,5,(x-1.6,-33,z-2.5)))
    for x in (-31,31):
        body=body.fuse(cyl(4,10,(x,-35,z),(0,1,0))).cut(cyl(1.25,15,(x,-37,z),(0,1,0)))
        retainer=retainer.cut(cyl(1.7,6,(x,-27,z),(0,1,0)))
    body=body.cut(box(70.4,3.4,5.4,(-35.2,-25.2,z-2.7)))
    for x in (-23.8,23.8):body=body.cut(box(3.6,8.4,5.4,(x-1.8,-33.2,z-2.7)))
    retainers.append((name,retainer))

# Nose separates from the barrel; a 0.3mm radial slip-fit plug enables assembly.
cone=Part.makeCone(r,2,P['nose_height'],V(0,0,h))
cone=cone.cut(Part.makeCone(r-wall,0,P['nose_height']-wall,V(0,0,h)))
plug_r=r-wall-.3
plug=cyl(plug_r,9,(0,0,h-8)).cut(cyl(plug_r-wall,10,(0,0,h-8)))
cone=cone.fuse(plug)
for a in (0,180):
    notch=box(7,10,3,(-3.5,plug_r-5,h-7));notch.rotate(V(),V(0,0,1),a);cone=cone.cut(notch)

printed=doc.addObject('App::DocumentObjectGroup','PrintedParts')
hardware=doc.addObject('App::DocumentObjectGroup','HardwareReferences')
colors={'RocketBody':(.84,.88,.91),'NoseCone':(.99,.43,.19),'RearCover':(.17,.23,.3),'PiCarrier':(.19,.57,.48),'LCDRetainerLower':(.99,.65,.25),'LCDRetainerUpper':(.99,.65,.25)}
lid=lid.cut(body)
objects=[]
for name,shape in [('RocketBody',body),('NoseCone',cone),('RearCover',lid),('PiCarrier',B['carrier'])]+retainers:
    obj=doc.getObject(name) or doc.addObject('PartDesign::Feature',name)
    obj.Placement=App.Placement();obj.Shape=shape.removeSplitter();printed.addObject(obj)
    if not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:raise RuntimeError(name+' not a valid single solid')
    if 'ColorRGB' not in obj.PropertiesList:obj.addProperty('App::PropertyString','ColorRGB')
    obj.ColorRGB=','.join(str(c) for c in colors[name])
    if obj.ViewObject:obj.ViewObject.ShapeColor=colors[name]
    export_shape=obj.Shape.copy();export_shape.translate(V(0,0,-export_shape.BoundBox.ZMin))
    MeshPart.meshFromShape(Shape=export_shape,LinearDeflection=.12,AngularDeflection=.12,Relative=False).write(str(HERE/(name+'.stl')))
    Part.export([obj],str(HERE/(name+'.step')))
    objects.append(obj)
m=App.Matrix();m.A11=0;m.A12=-1;m.A13=0;m.A14=18.5
m.A21=0;m.A22=0;m.A23=-1;m.A24=rear_face-3.8
m.A31=1;m.A32=0;m.A33=0;m.A34=35
doc.getObject('PiCarrier').Placement=App.Placement(m)

def reference(name,shape,color,note):
    obj=doc.addObject('PartDesign::Feature',name);obj.Shape=shape
    obj.addProperty('App::PropertyString','DesignNote');obj.DesignNote=note
    obj.addProperty('App::PropertyString','ColorRGB');obj.ColorRGB=','.join(str(c) for c in color)
    if obj.ViewObject:obj.ViewObject.ShapeColor=color
    hardware.addObject(obj);return obj
reference('LCD_PCB_Reference',box(50.8,1.6,79.9,(-25.424,lcd_y-1.6,lcd_z)),(.14,.35,.64),'Reference envelope, not a fabrication model')
reference('LCD_Glass_Reference',box(50,3.61,71.5,(-25,lcd_y-5.4,lcd_z+3.05)),(.07,.11,.14),'Nominal front glass envelope')
reference('LCD_ActiveArea',box(43.2,.15,57.6,(-21.6,lcd_y-5.55,lcd_z+10)),(.15,.74,.84),'43.2x57.6 display active area')
pi=box(65,30,1.6,(3.5,3.5,8))
for x in (7,65):
    for y in (7,30):pi=pi.cut(cyl(1.35,3,(x,y,7.5)))
reference('PiZero2W_Reference',pi,(.08,.46,.27),'PCB envelope; components and cables require physical verification').Placement=App.Placement(m)
report={'revision':'0.4','parts':{},'printed_part_intersections_mm3':{},'lcd_reference_check':None}
for obj in objects:
    s=obj.Shape;b=s.BoundBox
    report['parts'][obj.Name]={'valid':s.isValid(),'solids':len(s.Solids),'volume_mm3':round(s.Volume,3),'pla_mass_g_estimate':round(s.Volume*.00124,1),'bounds_mm':[round(b.XLength,3),round(b.YLength,3),round(b.ZLength,3)]}
for i,a in enumerate(objects):
    for b in objects[i+1:]:
        volume=a.Shape.common(b.Shape).Volume
        if volume>.01:report['printed_part_intersections_mm3'][a.Name+' / '+b.Name]=round(volume,4)
if args.lcd_reference:
    vendor=Part.Shape();vendor.read(str(args.lcd_reference))
    lm=App.Matrix();lm.A11=1;lm.A12=0;lm.A13=0;lm.A14=-25.424
    lm.A21=0;lm.A22=0;lm.A23=1;lm.A24=lcd_y
    lm.A31=0;lm.A32=1;lm.A33=0;lm.A34=lcd_z
    vendor=vendor.transformGeometry(lm)
    report['lcd_reference_check']={'source':'Waveshare SKU16446 official STEP (not redistributed)','transform':'x=vendor_x-25.424; y=vendor_z-34; z=vendor_y+54.5','intersections_mm3':{o.Name:round(o.Shape.common(vendor).Volume,4) for o in objects}}
if report['printed_part_intersections_mm3']:raise RuntimeError('Printed part collision: '+str(report['printed_part_intersections_mm3']))
if report['lcd_reference_check'] and any(v>.01 for v in report['lcd_reference_check']['intersections_mm3'].values()):raise RuntimeError('LCD reference collision')
doc.recompute();doc.saveAs(str(HERE/'LAUNCHPAD.FCStd'))
Part.export(objects+list(hardware.Group),str(HERE/'LAUNCHPAD-assembly.step'))
(HERE/'geometry-check.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
