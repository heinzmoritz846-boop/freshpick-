import os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from clipbot.detector import SpikeDetector, message_weight
from clipbot.render import to_vertical


def test_spike_triggers_once_and_cooldown():
    d = SpikeDetector(window=10, factor=3, min_score=25, cooldown=60)
    t = 0.0
    for _ in range(300):               # quiet chat: 1 msg / 2s
        assert not d.add(1.0, t); t += 2
    hits = [d.add(2.0, t + i * 0.1) for i in range(100)]  # burst
    assert sum(hits) == 1
    assert not any(d.add(2.0, t + 11 + i * 0.1) for i in range(100))  # cooldown


def test_quiet_chat_never_triggers():
    d = SpikeDetector()
    assert not any(d.add(1.0, i * 1.0) for i in range(1000))


def test_weight():
    assert message_weight("hello", ("gta 6",)) == 1
    assert message_weight("OMG GTA 6", ("gta 6",)) == 3


def test_render_vertical(tmp_path):
    src, dst = tmp_path / "in.mp4", tmp_path / "out.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=s=1280x720:d=3",
                    "-f", "lavfi", "-i", "sine=d=3", "-shortest", str(src)], check=True)
    to_vertical(str(src), str(dst), credit="twitch.tv/test")
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(dst)],
                         capture_output=True, text=True).stdout
    assert "1080,1920" in out
