"""Open a room .blend looking through the desk (hero) camera, in EEVEE's rendered view, overlays off.

    /Applications/Blender.app/Contents/MacOS/Blender blender/out/room_v3_rich.blend --python blender/tools/view_room.py

The full-detail room (room_v3_rich.blend) comes from `RICH=1 Blender -b --factory-startup --python blender/build_v3.py`.
Other cameras in the Outliner: still_about, still_intro, still_desk_corner, still_top, still_hero_v3_portrait.
"""
import bpy


def setup():
    sc = bpy.context.scene
    try:
        sc.render.engine = "BLENDER_EEVEE"
    except TypeError:
        sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.view_settings.view_transform = "AgX"
    cam = bpy.data.objects.get("still_hero_v3") or bpy.data.objects.get("still_hero")
    if cam:
        sc.camera = cam
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                sp = area.spaces.active
                sp.shading.type = "RENDERED"
                sp.overlay.show_overlays = False
                with bpy.context.temp_override(window=win, area=area,
                                               region=next(r for r in area.regions if r.type == "WINDOW")):
                    bpy.ops.view3d.view_camera()
    return None


bpy.app.timers.register(setup, first_interval=1.0)
