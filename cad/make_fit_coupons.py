"""FreeCAD Python: create low-material fit coupons before printing the full case."""
from pathlib import Path
import json
import FreeCAD as App
import Part,MeshPart
HERE=Path(__file__).resolve().parent;out=HERE/'fit-checks';out.mkdir(exist_ok=True)
p=json.loads((HERE/'parameters.json').read_text());r=p['body_radius']-p['wall'];v=App.Vector
doc=App.newDocument('LAUNCHPAD_FitChecks');report={}
shapes={
 'NoseFemaleCoupon':Part.makeCylinder(r+p['wall'],5).cut(Part.makeCylinder(r,5)),
 'NoseMaleCoupon':Part.makeCylinder(r-.3,5).cut(Part.makeCylinder(r-.3-p['wall'],5)),
 'ScreenApertureCoupon':Part.makeBox(p['screen_window_width']+10,p['screen_window_height']+10,2.4).cut(Part.makeBox(p['screen_window_width'],p['screen_window_height'],3,v(5,5,-.2)))
}
for name,shape in shapes.items():
 assert shape.isValid() and len(shape.Solids)==1
 obj=doc.addObject('PartDesign::Feature',name);obj.Shape=shape
 MeshPart.meshFromShape(Shape=shape,LinearDeflection=.12,AngularDeflection=.12,Relative=False).write(str(out/(name+'.stl')))
 Part.export([obj],str(out/(name+'.step')))
 report[name]={'valid':True,'volume_mm3':round(shape.Volume,2),'pla_g':round(shape.Volume*.00124,2)}
doc.recompute();doc.saveAs(str(out/'FitChecks.FCStd'))
(out/'fit-checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
