"""Running Blender scripts with the window open (or headless), shared by build.py and the
video scripts. The pattern from tests/piano_quality.py:

    drive(job())      job() is a generator; with a window it runs from a timer and yields
                      between steps so the window redraws; with -b it runs straight through
    render_to(path)   `dt = yield from render_to(...)`: a render that shows in the render window
    log(msg)          one line starting with MILESTONE, for whoever watches the output
"""
import json
import os
import struct
import time

import bpy


def log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} {msg}", flush=True)


def args():
    import sys
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def _window():
    wm = bpy.data.window_managers[0]
    return wm.windows[0] if wm.windows else None


def windowed():
    return not bpy.app.background and _window() is not None


def show_in_viewport(shading="MATERIAL", camera=True):
    """Look through the scene camera in material preview, so the owner can watch."""
    win = _window()
    if win is None:
        return
    for area in win.screen.areas:
        if area.type == "VIEW_3D":
            for sp in area.spaces:
                if sp.type == "VIEW_3D":
                    sp.shading.type = shading
                    sp.overlay.show_overlays = False
                    if camera and bpy.context.scene.camera is not None:
                        sp.region_3d.view_perspective = "CAMERA"
            area.tag_redraw()


def render_to(path, animation=False):
    """Yield-driven render; returns seconds. Caller: `dt = yield from render_to(...)`."""
    scene = bpy.context.scene
    scene.render.filepath = path
    t = time.time()
    win = _window()
    if not windowed():
        bpy.ops.render.render(write_still=not animation, animation=animation)
    else:
        with bpy.context.temp_override(window=win, screen=win.screen):
            bpy.ops.render.render("INVOKE_DEFAULT", write_still=not animation, animation=animation)
        yield "wait"
        yield "wait"
        while bpy.app.is_job_running("RENDER"):
            yield "wait"
    return time.time() - t


def drive(gen):
    """Run the job generator: straight through when headless, from a timer when windowed."""
    if not windowed():
        for _ in gen:
            pass
        return

    def tick():
        try:
            r = next(gen)
        except StopIteration:
            return None
        except Exception:
            import traceback
            traceback.print_exc()
            log("FAILED, see the traceback above; Blender stays open")
            return None
        return 0.4 if r == "wait" else 0.02
    bpy.app.timers.register(tick, first_interval=0.5, persistent=True)


def setup_render(engine="CYCLES", samples=320, quick=False, fps=30):
    scene = bpy.context.scene
    scene.render.engine = engine
    scene.render.resolution_x, scene.render.resolution_y = 1920, 1080
    scene.render.resolution_percentage = 50 if quick else 100
    scene.render.fps = fps
    scene.render.film_transparent = False
    scene.render.use_stamp = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    if engine == "CYCLES":
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "METAL"
        scene.cycles.device = "GPU"
        scene.cycles.samples = 32 if quick else samples
        scene.cycles.use_denoising = True
        scene.cycles.denoiser = "OPENIMAGEDENOISE"
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.max_bounces = 8
        scene.cycles.caustics_reflective = False
        scene.cycles.caustics_refractive = False
    else:
        ev = scene.eevee
        ev.taa_render_samples = 8 if quick else samples
        for k, v in (("use_raytracing", True), ("use_shadows", True)):
            try:
                setattr(ev, k, v)
            except AttributeError:
                pass


def glb_stats(path):
    """Size, nodes, meshes, triangles and images of a GLB, read from its JSON chunk."""
    with open(path, "rb") as f:
        f.read(12)
        clen, _ = struct.unpack("<II", f.read(8))
        doc = json.loads(f.read(clen))
    acc = doc["accessors"]
    per = {m["name"]: sum(acc[p["indices"]]["count"] // 3 for p in m["primitives"] if "indices" in p)
           for m in doc["meshes"]}
    top = sorted(((v, k) for k, v in per.items()), reverse=True)[:8]
    imgs = [f"{i.get('name', '?')} {round(doc['bufferViews'][i['bufferView']]['byteLength'] / 1024)} KB"
            for i in doc.get("images", []) if "bufferView" in i]
    return {"kb": round(os.path.getsize(path) / 1024), "nodes": len(doc["nodes"]),
            "node_names": [n.get("name") for n in doc["nodes"]], "meshes": len(doc["meshes"]),
            "triangles": sum(per.values()), "materials": len(doc.get("materials", [])),
            "images": imgs, "biggest": [f"{k} {v}" for v, k in top]}
