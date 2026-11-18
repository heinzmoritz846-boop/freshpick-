"""Turn raw segments into a TikTok-ready 1080x1920 mp4 (blurred background, centered gameplay)."""
from __future__ import annotations
import os
import subprocess
import tempfile


def _run(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr[-800:])


def concat(files: list[str], out: str) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for p in files:
            f.write(f"file '{os.path.abspath(p)}'\n")
        lst = f.name
    try:
        _run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    finally:
        os.remove(lst)


def to_vertical(src: str, dst: str, credit: str | None = None, max_seconds: int = 60) -> None:
    base = (
        "[0:v]split[a][b];"
        "[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:5[bg];"
        "[b]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"
    )

    def build(with_text: bool) -> list[str]:
        vf = base
        if with_text and credit:
            safe = credit.replace("\\", "").replace("'", "").replace(":", "")
            vf += f",drawtext=text='{safe}':fontcolor=white:fontsize=48:borderw=3:bordercolor=black:x=(w-text_w)/2:y=140"
        return [
            "ffmpeg", "-y", "-loglevel", "error", "-i", src, "-t", str(max_seconds),
            "-filter_complex", vf + "[v]", "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", "-r", "30",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", dst,
        ]

    try:
        _run(build(True))
    except RuntimeError:  # drawtext/font missing -> render without overlay
        _run(build(False))
