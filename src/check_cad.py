from pathlib import Path
import cadquery as cq
import json, itertools, math, vtk
import numpy as np
from vtk.util.numpy_support import numpy_to_vtk
BASE=Path(__file__).resolve().parent
OUT=BASE.parent/'build'
OUT.mkdir(exist_ok=True)
CACHE=OUT/'.cad_cache'
meta=json.loads((CACHE/'placed.json').read_text())
for o in meta:
    o['shape']=cq.Shape.importBrep(str(CACHE/o['file']))
    o['bb']=o['shape'].BoundingBox()
def bbox_overlap(a,b):
    return all(getattr(a,k+'max')>getattr(b,k+'min')+.01 and getattr(b,k+'max')>getattr(a,k+'min')+.01 for k in 'xyz')
inter=[]
structural=[o for o in meta if o['kind'] not in ('fastener','insert','nut')]
for i,a in enumerate(structural):
    for b in structural[i+1:]:
        if not bbox_overlap(a['bb'],b['bb']):continue
        vol=a['shape'].intersect(b['shape']).Volume()
        if vol>.05:
            inter.append([a['name'],b['name'],round(vol,3)])
            print(inter[-1],flush=True)
report=json.loads((OUT/'cad_validation.json').read_text())
report['intersections']=inter
report['assembly_instances']=len(meta)
report['servo_count']=sum(o['kind']=='servo' for o in meta)
report['assembly_bounds_mm']=[round(max(getattr(o['bb'],k+'max') for o in meta)-min(getattr(o['bb'],k+'min') for o in meta),2) for k in 'xyz']
(OUT/'cad_validation.json').write_text(json.dumps(report,indent=2))
print('Interference count:',len(inter),flush=True)

def actor(shape,color):
    verts,tri=shape.tessellate(.15,.16)
    points=vtk.vtkPoints(); points.SetData(numpy_to_vtk(np.array([v.toTuple() for v in verts]),deep=True))
    cells=vtk.vtkCellArray()
    for t in tri:
        cells.InsertNextCell(3)
        for n in t:cells.InsertCellPoint(n)
    poly=vtk.vtkPolyData();poly.SetPoints(points);poly.SetPolys(cells)
    norm=vtk.vtkPolyDataNormals(); norm.SetInputData(poly); norm.SetFeatureAngle(50);norm.Update()
    mapper=vtk.vtkPolyDataMapper();mapper.SetInputConnection(norm.GetOutputPort())
    a=vtk.vtkActor();a.SetMapper(mapper);a.GetProperty().SetColor(*color)
    a.GetProperty().SetSpecular(.22);a.GetProperty().SetSpecularPower(35)
    return a
def render(filename,hide=(),cam=(430,-590,390),target=(0,0,10),scale=285,title='ARACHNE / 18',subtitle='STS3215 12V  |  6 legs  |  3 axes per leg'):
    ren=vtk.vtkRenderer();ren.SetBackground(.95,.955,.94)
    ren.SetBackground2(.78,.82,.80);ren.GradientBackgroundOn()
    for o in meta:
        if o['name'] in hide:continue
        ren.AddActor(actor(o['shape'],o['color']))
    camera=ren.GetActiveCamera();camera.SetPosition(*cam);camera.SetFocalPoint(*target);camera.SetViewUp(0,0,1)
    camera.ParallelProjectionOn();camera.SetParallelScale(scale)
    for text,pos,size in [(title,(55,960),38),(subtitle,(58,920),18)]:
        txt=vtk.vtkTextActor();txt.SetInput(text);txt.SetPosition(*pos)
        txt.GetTextProperty().SetFontSize(size);txt.GetTextProperty().SetColor(.12,.21,.22)
        ren.AddActor2D(txt)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.AddRenderer(ren);win.SetSize(1600,1050);win.SetMultiSamples(4)
    win.Render()
    grab=vtk.vtkWindowToImageFilter();grab.SetInput(win);grab.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(OUT/filename));writer.SetInputConnection(grab.GetOutputPort());writer.Write()
    win.Finalize()
render('ARACHNE_18_overview.png')
render('ARACHNE_18_internals.png',hide=('05_SHELL',),cam=(330,-480,510),subtitle='Removable 3S battery 115 x 40 x 35 mm  |  Universal controller plate')
render('ARACHNE_18_top_view.png',cam=(0,-.01,650),target=(0,0,0),scale=290,subtitle='Compact chassis and six identical leg modules')
print('Renders complete',flush=True)
