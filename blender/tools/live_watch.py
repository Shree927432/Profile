"""Watch a component being built, live, in one Blender window (2026-10-26, the owner asked to see it).

Builders run Blender headless; this opens ONE window that rebuilds the component every time its
script is saved, so each edit the builder makes shows up a second or two later. It never renders,
never writes files, and the window keeps the owner's camera angle between rebuilds.

    LIVE_MODULE=arms ARMS_PART=all /Applications/Blender.app/Contents/MacOS/Blender --factory-startup \\
        --python blender/tools/live_watch.py

LIVE_MODULE is a module in blender/components/ with a build() function; LIVE_BUILD picks another.
"""
import importlib
import os
import sys
import time
import traceback

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
COMP = os.path.abspath(os.path.join(HERE, "..", "components"))
sys.path.insert(0, COMP)
MOD = os.environ.get("LIVE_MODULE", "arms")
FN = os.environ.get("LIVE_BUILD", "build")
PATH = os.path.join(COMP, MOD + ".py")
state = {"mtime": 0.0, "first": True, "mod": None}


def view3d():
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type == "VIEW_3D":
                return win, area
    return None, None


def status(text):
    win, area = view3d()
    if area:
        area.header_text_set(text)


def rebuild():
    t = time.time()
    try:
        mod = importlib.import_module(MOD) if state["mod"] is None else importlib.reload(state["mod"])
        state["mod"] = mod
        if hasattr(mod, "clear"):
            mod.clear()
        else:
            for o in list(bpy.data.objects):
                bpy.data.objects.remove(o)
        getattr(mod, FN)()
        n = sum(1 for o in bpy.data.objects if o.type == "MESH")
        status(f"LIVE  {MOD}.py  rebuilt {time.strftime('%H:%M:%S')} in {time.time() - t:.1f} s, "
               f"{n} meshes  (orbit freely; it rebuilds on every save)")
        if state["first"]:
            win, area = view3d()
            if area:
                for sp in area.spaces:
                    if sp.type == "VIEW_3D":
                        sp.shading.type = "MATERIAL"
                        sp.overlay.show_floor = True
                region = next(r for r in area.regions if r.type == "WINDOW")
                with bpy.context.temp_override(window=win, area=area, region=region):
                    bpy.ops.view3d.view_all()
            state["first"] = False
    except Exception as e:
        traceback.print_exc()
        status(f"LIVE  {MOD}.py  mid-edit, last save did not build ({type(e).__name__}: {e})"[:200])


def tick():
    try:
        m = os.path.getmtime(PATH)
    except OSError:
        return 2.0
    if m != state["mtime"]:
        state["mtime"] = m
        time.sleep(0.3)          # let the writer finish
        rebuild()
    return 2.0


bpy.app.timers.register(tick, first_interval=1.0, persistent=True)
