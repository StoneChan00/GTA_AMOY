"""GTA_AMOY: generate two placeholder landmark GLBs so the landmark manifests
resolve to real assets (a single invisible triangle far below ground) without
crashing load(). Uses the same Blender glTF export path as the rest of the city,
so the output is guaranteed loadable by the Babylon runtime.
"""
import bpy
from pathlib import Path
OUT=Path(r'D:\2_Projects\github\GTA_AMOY\public\city')
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for name in ['landmark-detail','landmark-candidates']:
 mesh=bpy.data.meshes.new(name);mesh.from_pydata([(0,-100,0),(1,-100,0),(0,-100,1)],[],[(0,1,2)]);mesh.update()
 ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
bpy.ops.export_scene.gltf(filepath=str(OUT/'landmark-detail.glb'),export_format='GLB',use_selection=False,export_cameras=False,export_lights=False,export_apply=False)
# Delete the first mesh so the second file only contains its own placeholder.
bpy.data.objects.remove(bpy.data.objects['landmark-detail'],do_unlink=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'landmark-candidates.glb'),export_format='GLB',use_selection=False,export_cameras=False,export_lights=False,export_apply=False)
print('placeholder landmark GLBs written')