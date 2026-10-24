"""One Cycles (GPU) render at a time on this Mac, across every Blender process that opts in.

Two builders rendering Cycles on the one Metal GPU at once slow each other down and, on 2026-10-24,
stalled the GPU outright (screens NOTE.md, "What went wrong"). This is a plain file lock
(fcntl.flock on blender/out/render-queue.lock): the OS frees it when the holder exits or crashes, so a
killed Blender never leaves the queue stuck.

    from lib import renderqueue

    with renderqueue.slot("speakers hero"):              # blocks until the GPU is free
        bpy.ops.render.render(write_still=True)

    dt = yield from renderqueue.render_to(path, "screens front")   # the windowed run.drive() pattern:
                                                                    # waits by yielding, the window stays live

While waiting it logs one MILESTONE line, then one a minute, naming who holds the GPU. A timeout
(default 2 h) raises TimeoutError. EEVEE and Workbench renders do not need the queue; Cycles renders
and Cycles bakes do. Nothing existing uses it until a builder opts in.

    python3 blender/lib/renderqueue.py        prints who holds the queue now, if anyone
"""
import contextlib
import fcntl
import json
import os
import sys
import time

LOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "render-queue.lock")
HOLDER = LOCK + ".holder.json"


def _log(msg):
    print(f"MILESTONE {time.strftime('%H:%M:%S')} renderqueue: {msg}", flush=True)


def holder():
    """Who holds the GPU now (pid, label, script, since), or None."""
    try:
        with open(HOLDER) as f:
            h = json.load(f)
    except (OSError, ValueError):
        return None
    try:
        os.kill(int(h.get("pid", -1)), 0)
    except (OSError, ValueError):
        return None
    return h if is_held() else None


def is_held():
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    fd = os.open(LOCK, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return True
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)
    return False


def _try(label):
    os.makedirs(os.path.dirname(LOCK), exist_ok=True)
    fd = os.open(LOCK, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        return None
    with open(HOLDER, "w") as f:
        json.dump({"pid": os.getpid(), "label": label, "script": " ".join(sys.argv[-4:]),
                   "since": time.strftime("%Y-%m-%d %H:%M:%S")}, f)
    return fd


def _release(fd, label, t0):
    try:
        os.remove(HOLDER)
    except OSError:
        pass
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)
    _log(f"released by {label!r} after {time.time() - t0:.0f} s")


def _waiting(label, waited, last):
    if waited == 0 or time.time() - last >= 60:
        h = holder() or {}
        _log(f"{label!r} waiting for the GPU: held by {h.get('label', '?')!r} (pid {h.get('pid', '?')}, "
             f"since {h.get('since', '?')}); waited {waited:.0f} s")
        return time.time()
    return last


@contextlib.contextmanager
def slot(label="render", timeout=7200, poll=2.0):
    """Hold the GPU for the body of the with-block. Blocks (sleeping) while another process holds it."""
    t0 = time.time()
    last = 0
    while True:
        fd = _try(label)
        if fd is not None:
            break
        last = _waiting(label, time.time() - t0 if last else 0, last)
        if time.time() - t0 > timeout:
            raise TimeoutError(f"renderqueue: {label!r} gave up after {timeout} s")
        time.sleep(poll)
    t1 = time.time()
    if t1 - t0 > 1:
        _log(f"{label!r} got the GPU after {t1 - t0:.0f} s")
    try:
        yield
    finally:
        _release(fd, label, t1)


def acquire(label="render", timeout=7200):
    """Generator form for run.drive() jobs: `fd = yield from renderqueue.acquire(label)`, waits by
    yielding "wait" (the window keeps redrawing); release with renderqueue.release(fd, label)."""
    t0 = time.time()
    last = 0
    while True:
        fd = _try(label)
        if fd is not None:
            return fd
        last = _waiting(label, time.time() - t0 if last else 0, last)
        if time.time() - t0 > timeout:
            raise TimeoutError(f"renderqueue: {label!r} gave up after {timeout} s")
        yield "wait"


def release(fd, label="render"):
    _release(fd, label, time.time())


def render_to(path, label=None, animation=False, timeout=7200):
    """run.render_to() inside the queue: `dt = yield from renderqueue.render_to(path, "label")`."""
    from . import run
    label = label or os.path.basename(path)
    fd = yield from acquire(label, timeout)
    try:
        dt = yield from run.render_to(path, animation=animation)
    finally:
        release(fd, label)
    return dt


if __name__ == "__main__":
    h = holder()
    print("GPU free" if h is None else f"held by {h['label']!r} (pid {h['pid']}, since {h['since']}): {h['script']}")
