from __future__ import annotations
import argparse
import json
import os
import threading
import time
import tomllib

from .chat import watch_chat
from .detector import SpikeDetector, message_weight
from .recorder import SEG, Recorder
from .render import concat, to_vertical


def make_caption(streamer: str, cfg: dict) -> str:
    tags = " ".join(cfg.get("hashtags", ["#gta6", "#gta", "#rockstar", "#fyp"]))
    return f"GTA 6 Moment 🔥 Credit: twitch.tv/{streamer} {tags}"


def process_clip(rec: Recorder, streamer: str, trigger_ts: float, cfg: dict) -> None:
    pre, post = cfg["clip"]["pre_seconds"], cfg["clip"]["post_seconds"]
    time.sleep(post + SEG + 2)  # wait until post-roll is recorded
    segs = rec.segments_between(trigger_ts - pre, trigger_ts + post)
    if len(segs) < 2:
        print(f"[{streamer}] not enough buffered video, skipped", flush=True)
        return
    out_dir = cfg["output"]["dir"]
    os.makedirs(out_dir, exist_ok=True)
    name = f"{streamer}_{int(trigger_ts)}"
    raw = os.path.join(out_dir, name + ".raw.ts")
    final = os.path.join(out_dir, name + ".mp4")
    concat(segs, raw)
    to_vertical(raw, final, credit=f"twitch.tv/{streamer}", max_seconds=cfg["clip"].get("max_seconds", 45))
    os.remove(raw)
    with open(os.path.join(out_dir, name + ".json"), "w") as f:
        json.dump({"video": final, "streamer": streamer, "caption": make_caption(streamer, cfg["output"]),
                   "source": f"https://twitch.tv/{streamer}", "approved": False}, f, ensure_ascii=False, indent=2)
    print(f"[{streamer}] clip ready: {final}", flush=True)


def run(cfg_path: str) -> None:
    with open(cfg_path, "rb") as f:
        cfg = tomllib.load(f)
    stop = threading.Event()
    keywords = tuple(cfg["detect"]["keywords"])
    keep = cfg["clip"]["pre_seconds"] + cfg["clip"]["post_seconds"] + 60
    for s in cfg["streamers"]["channels"]:
        s = s.lower()
        rec = Recorder(s, cfg["output"]["buffer_dir"], keep)
        d = cfg["detect"]
        det = SpikeDetector(d["window_seconds"], d["factor"], d["min_score"], d["cooldown_seconds"])

        def on_msg(text, s=s, rec=rec, det=det):
            if det.add(message_weight(text, keywords)):
                print(f"[{s}] hype spike!", flush=True)
                threading.Thread(target=process_clip, args=(rec, s, time.time(), cfg), daemon=True).start()

        threading.Thread(target=rec.run, args=(stop,), daemon=True).start()
        threading.Thread(target=watch_chat, args=(s, on_msg, stop), daemon=True).start()
    print(f"Watching {len(cfg['streamers']['channels'])} streams. Ctrl+C to stop.", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop.set()


def main() -> None:
    ap = argparse.ArgumentParser(prog="clipbot")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("--config", default="config.toml")
    v = sub.add_parser("render", help="convert a local video to 9:16"); v.add_argument("src"); v.add_argument("dst")
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.config)
    else:
        to_vertical(a.src, a.dst, credit="twitch.tv/test")
