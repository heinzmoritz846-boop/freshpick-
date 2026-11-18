"""Rolling buffer per stream: streamlink -> ffmpeg segments named by epoch start time."""
from __future__ import annotations
import glob
import os
import shlex
import subprocess
import threading
import time

SEG = 4  # seconds per segment


class Recorder:
    def __init__(self, channel: str, buffer_dir: str, keep_seconds: int, quality: str = "720p60,720p,best"):
        self.channel = channel
        self.dir = os.path.join(buffer_dir, channel)
        os.makedirs(self.dir, exist_ok=True)
        self.keep = keep_seconds
        self.quality = quality

    def run(self, stop: threading.Event) -> None:
        backoff = 15
        while not stop.is_set():
            cmd = (
                f"streamlink --stdout --loglevel error twitch.tv/{shlex.quote(self.channel)} {shlex.quote(self.quality)} | "
                f"ffmpeg -loglevel error -i pipe:0 -c copy -f segment -segment_time {SEG} "
                f"-strftime 1 {shlex.quote(os.path.join(self.dir, '%s.ts'))}"
            )
            p = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
            started = time.time()
            while p.poll() is None and not stop.is_set():
                self.cleanup()
                stop.wait(10)
            if stop.is_set():
                try:
                    os.killpg(p.pid, 15)
                except ProcessLookupError:
                    pass
                return
            # stream offline / ended: wait and retry, backing off while offline
            backoff = 15 if time.time() - started > 60 else min(backoff * 2, 300)
            stop.wait(backoff)

    def cleanup(self) -> None:
        cutoff = time.time() - self.keep
        for f in glob.glob(os.path.join(self.dir, "*.ts")):
            if int(os.path.basename(f)[:-3]) < cutoff:
                os.remove(f)

    def segments_between(self, start: float, end: float) -> list[str]:
        out = []
        for f in sorted(glob.glob(os.path.join(self.dir, "*.ts"))):
            try:
                t = int(os.path.basename(f)[:-3])
            except ValueError:
                continue
            if start - SEG <= t <= end:
                out.append(f)
        return out
