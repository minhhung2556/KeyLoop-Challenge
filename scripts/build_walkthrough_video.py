"""VieNeu TTS + screenshot slides + FFmpeg mux."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CheckResult, REPO_ROOT, print_banner, print_result, print_section

SCRIPT = REPO_ROOT / "video/walkthrough_script.json"
OUT_DIR = REPO_ROOT / "video/output"
WORK = REPO_ROOT / "video/work"
SHOTS = REPO_ROOT / "video/assets/screenshots"
FONTS = REPO_ROOT / "video/assets/fonts"
ACCENT = (0, 181, 216)
BG = (15, 23, 42)
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
CARD = (30, 41, 59)
PYENV_PY = Path.home() / ".pyenv/pyenv-win/versions/3.10.11/python.exe"
VOICE_PCM = ("pcm_s16le", "44100", "1")
_vieneu_model = None
_torchaudio_patched = False


def ffmpeg_bin() -> str:
    return shutil.which("ffmpeg") or shutil.which("ffmpeg.exe") or "ffmpeg"


def ffprobe_bin() -> str:
    return shutil.which("ffprobe") or shutil.which("ffprobe.exe") or "ffprobe"


def ensure_vieneu_python() -> None:
    try:
        import vieneu  # noqa: F401

        return
    except ImportError:
        pass
    py = PYENV_PY if PYENV_PY.is_file() else None
    exe = Path(sys.executable).resolve()
    if py and py.resolve() != exe:
        os.execv(str(py), [str(py), *sys.argv])
    hint = str(py) if py else "pyenv install 3.10.11"
    sys.exit(
        "Walkthrough TTS requires Python 3.10 with vieneu installed.\n"
        f"Use: {hint} {Path(__file__).name}"
    )


def _patch_torchaudio() -> None:
    global _torchaudio_patched
    if _torchaudio_patched:
        return
    try:
        import torch
        import torchaudio
        import soundfile as sf
    except ImportError:
        return

    def _sf_load(path, *a, **k):
        data, sr = sf.read(str(path), dtype="float32", always_2d=True)
        return torch.from_numpy(data.T), sr

    torchaudio.load = _sf_load
    _torchaudio_patched = True


def resolve_device(preferred: str = "auto") -> str:
    pref = str(preferred or "auto").lower()
    if pref == "cpu":
        return "cpu"
    try:
        import torch
    except ImportError:
        return "cpu"
    if pref == "cuda":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def parse_rate_multiplier(rate: str) -> float:
    s = str(rate or "+0%").strip()
    m = re.match(r"^([+-]?\d+(?:\.\d+)?)%$", s)
    if not m:
        return 1.0
    return 1.0 + float(m.group(1)) / 100.0


def parse_pitch_hz(pitch: str) -> float:
    s = str(pitch or "+0Hz").strip()
    m = re.match(r"^([+-]?\d+(?:\.\d+)?)Hz$", s, re.IGNORECASE)
    if not m:
        return 0.0
    return float(m.group(1))


def _atempo_chain(tempo: float) -> str:
    parts: list[str] = []
    remaining = tempo
    while remaining > 2.0 + 1e-9:
        parts.append("atempo=2.0")
        remaining /= 2.0
    while remaining < 0.5 - 1e-9:
        parts.append("atempo=0.5")
        remaining /= 0.5
    remaining = max(0.5, min(2.0, remaining))
    parts.append(f"atempo={remaining:.6f}".rstrip("0").rstrip("."))
    return ",".join(parts)


def _ffmpeg_af_replace(wav_path: Path, filt: str, suffix: str) -> None:
    fd, tmp_name = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        subprocess.run(
            [ffmpeg_bin(), "-y", "-i", str(wav_path), "-af", filt, str(tmp)],
            check=True,
            capture_output=True,
        )
        if tmp.is_file() and tmp.stat().st_size > 1000:
            tmp.replace(wav_path)
        elif tmp.is_file():
            tmp.unlink(missing_ok=True)
    except Exception:
        if tmp.is_file():
            tmp.unlink(missing_ok=True)
        raise


def apply_pitch_asetrate(wav_path: Path, pitch: str) -> None:
    delta = parse_pitch_hz(pitch)
    if abs(delta) < 0.5:
        return
    ratio = max(0.5, min(2.0, (200.0 + delta) / 200.0))
    if abs(ratio - 1.0) < 0.001:
        return
    sr = probe_sample_rate(wav_path)
    new_sr = sr * ratio
    tempo = 1.0 / ratio
    filt = (
        f"asetrate={new_sr:.6f}".rstrip("0").rstrip(".")
        + f",aresample={sr},"
        + _atempo_chain(tempo)
    )
    _ffmpeg_af_replace(wav_path, filt, ".pitch.wav")


def apply_rate_atempo(wav_path: Path, rate: str) -> None:
    tempo = parse_rate_multiplier(rate)
    if abs(tempo - 1.0) < 0.001:
        return
    _ffmpeg_af_replace(wav_path, _atempo_chain(tempo), ".rate.wav")


def probe_sample_rate(path: Path) -> int:
    out = subprocess.run(
        [
            ffprobe_bin(),
            "-v",
            "quiet",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return int(float(out.stdout.strip()))


def probe_duration(path: Path) -> float:
    out = subprocess.run(
        [
            ffprobe_bin(),
            "-v",
            "quiet",
            "-show_entries",
            "format=duration",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(out.stdout.strip())


def normalize_pcm_wav(wav: Path) -> None:
    fd, name = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    tmp = Path(name)
    codec, rate, channels = VOICE_PCM
    try:
        subprocess.run(
            [
                ffmpeg_bin(),
                "-y",
                "-i",
                str(wav),
                "-c:a",
                codec,
                "-ar",
                rate,
                "-ac",
                channels,
                str(tmp),
            ],
            check=True,
            capture_output=True,
        )
        if tmp.is_file() and tmp.stat().st_size > 1000:
            tmp.replace(wav)
        elif tmp.is_file():
            tmp.unlink(missing_ok=True)
    except Exception:
        if tmp.is_file():
            tmp.unlink(missing_ok=True)
        raise


def trim_trailing_silence(wav: Path, pad_s: float = 0.25) -> None:
    try:
        dur = probe_duration(wav)
    except Exception:
        return
    try:
        r = subprocess.run(
            [
                ffmpeg_bin(),
                "-i",
                str(wav),
                "-af",
                "silencedetect=n=-40dB:d=0.08",
                "-f",
                "null",
                "-",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return
    starts = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", r.stderr)]
    ends = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", r.stderr)]
    segs: list[list[float]] = []
    prev = 0.0
    for s, e in zip(starts, ends):
        if s - prev > 0.05:
            segs.append([prev, s])
        prev = e
    if dur - prev > 0.05:
        segs.append([prev, dur])
    if not segs:
        return
    end = min(dur, segs[-1][1] + pad_s)
    if end >= dur - 0.05:
        return
    fd, name = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    tmp = Path(name)
    try:
        subprocess.run(
            [ffmpeg_bin(), "-y", "-i", str(wav), "-t", f"{end:.3f}", "-c:a", "pcm_s16le", str(tmp)],
            check=True,
            capture_output=True,
        )
        if tmp.is_file() and tmp.stat().st_size > 1000:
            tmp.replace(wav)
        elif tmp.is_file():
            tmp.unlink(missing_ok=True)
    except subprocess.CalledProcessError:
        if tmp.is_file():
            tmp.unlink(missing_ok=True)


def synth_vieneu(text: str, dest: Path, tts: dict) -> None:
    global _vieneu_model
    _patch_torchaudio()
    from vieneu import Vieneu

    dest.parent.mkdir(parents=True, exist_ok=True)
    if _vieneu_model is None:
        device = resolve_device(str(tts.get("device", "auto")))
        kw = {
            "mode": tts.get("mode", "v3turbo"),
            "device": device,
        }
        model = tts.get("model") or tts.get("model_name")
        if model:
            kw["model_name"] = model
        _vieneu_model = Vieneu(**kw)
        print(f"[tts] vieneu mode={kw.get('mode')} model={kw.get('model_name', 'default')} device={device}")
    voice = tts.get("voice", "Adam")
    audio = _vieneu_model.infer(text, voice=voice)
    _vieneu_model.save(audio, str(dest))
    apply_pitch_asetrate(dest, str(tts.get("pitch", "+0Hz")))
    apply_rate_atempo(dest, str(tts.get("rate", "+0%")))
    trim_trailing_silence(dest)
    normalize_pcm_wav(dest)


def font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = FONTS / name
    if path.is_file():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def draw_badge(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fonts) -> None:
    x, y = xy
    pad_x, pad_y = 16, 8
    bbox = draw.textbbox((0, 0), text, font=fonts["badge"])
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.rounded_rectangle([x, y, x + w + pad_x * 2, y + h + pad_y * 2], radius=16, fill=ACCENT)
    draw.text((x + pad_x, y + pad_y - 2), text, fill=WHITE, font=fonts["badge"])


def destile_shot(shot: Image.Image) -> Image.Image:
    """CDP 1920x1080 captures were 2x2 repeats of the unique viewport. Keep one pane."""
    width, height = shot.size
    if (width, height) == (1920, 1080):
        return shot.crop((0, 0, 960, 540))
    return shot


def load_shot(name: str) -> Image.Image | None:
    path = SHOTS / name
    if not path.is_file():
        return None
    return destile_shot(Image.open(path).convert("RGB"))


def fit_shot(shot: Image.Image, box: tuple[int, int, int, int]) -> Image.Image:
    x0, y0, x1, y1 = box
    tw, th = max(1, x1 - x0), max(1, y1 - y0)
    sw, sh = shot.size
    scale = max(tw / sw, th / sh)
    nw = max(tw, int(round(sw * scale)))
    nh = max(th, int(round(sh * scale)))
    resized = shot.resize((nw, nh), Image.Resampling.LANCZOS)
    left = max(0, (nw - tw) // 2)
    top = max(0, (nh - th) // 2)
    return resized.crop((left, top, left + tw, top + th))


def chrome_frame(canvas: Image.Image, box: tuple[int, int, int, int], shot_name: str, fonts) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle([x0 - 8, y0 - 40, x1 + 8, y1 + 8], radius=12, fill=(8, 15, 30), outline=ACCENT, width=2)
    draw.ellipse([x0, y0 - 28, x0 + 12, y0 - 16], fill=(248, 113, 113))
    draw.ellipse([x0 + 20, y0 - 28, x0 + 32, y0 - 16], fill=(250, 204, 21))
    draw.ellipse([x0 + 40, y0 - 28, x0 + 52, y0 - 16], fill=(74, 222, 128))
    draw.text((x0 + 70, y0 - 32), "127.0.0.1:3000" if "swagger" not in shot_name else "127.0.0.1:8000/docs", fill=MUTED, font=fonts["small"])


def new_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw, dict]:
    image = Image.new("RGB", (1920, 1080), BG)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, 1920, 16], fill=ACCENT)
    draw.rectangle([0, 1064, 1920, 1080], fill=ACCENT)
    fonts = {
        "kicker": font("BeVietnamPro-Bold.ttf", 22),
        "title": font("BeVietnamPro-Black.ttf", 48),
        "card": font("SpaceGrotesk-Variable.ttf", 28),
        "badge": font("BeVietnamPro-Bold.ttf", 20),
        "small": font("SpaceGrotesk-Variable.ttf", 18),
    }
    return image, draw, fonts


def draw_cards(draw: ImageDraw.ImageDraw, cards: list[str], fonts, origin: tuple[int, int]) -> None:
    x, y = origin
    for i, card in enumerate(cards, start=1):
        draw.rounded_rectangle([x, y, x + 760, y + 88], radius=12, fill=CARD)
        draw.rectangle([x, y, x + 8, y + 88], fill=ACCENT)
        draw.text((x + 28, y + 26), f"{i}. {card}", fill=WHITE, font=fonts["card"])
        y += 108


def compose_split(chapter: dict) -> Image.Image:
    image, draw, fonts = new_canvas()
    draw.text((80, 48), "Keyloop · Scenario C", fill=ACCENT, font=fonts["kicker"])
    draw.text((80, 90), chapter["title"], fill=WHITE, font=fonts["title"])
    draw_cards(draw, chapter.get("cards") or [], fonts, (80, 180))
    bx = 80
    for badge in chapter.get("badges") or []:
        draw_badge(draw, (bx, 980), badge, fonts)
        bbox = draw.textbbox((0, 0), badge, font=fonts["badge"])
        bx += (bbox[2] - bbox[0]) + 48
    shot = load_shot(chapter.get("preview") or "demo_01_inbox.png")
    box = (900, 140, 1840, 960)
    chrome_frame(image, box, chapter.get("preview") or "", fonts)
    if shot:
        framed = fit_shot(shot, box)
        image.paste(framed, (box[0], box[1]))
    return image


def compose_architecture(chapter: dict) -> Image.Image:
    image, draw, fonts = new_canvas()
    draw.text((80, 48), "Keyloop · Architecture", fill=ACCENT, font=fonts["kicker"])
    draw.text((80, 90), chapter["title"], fill=WHITE, font=fonts["title"])
    nodes = [
        (80, 220, "Next.js :3000"),
        (500, 220, "FastAPI :8000"),
        (920, 220, "LeadService"),
        (1340, 220, "SQLite WAL"),
    ]
    for i, (x, y, label) in enumerate(nodes):
        draw.rounded_rectangle([x, y, x + 340, y + 120], radius=16, fill=CARD, outline=ACCENT, width=2)
        draw.text((x + 24, y + 42), label, fill=WHITE, font=fonts["card"])
        if i < len(nodes) - 1:
            draw.polygon([(x + 350, y + 50), (x + 380, y + 60), (x + 350, y + 70)], fill=ACCENT)
    draw_cards(draw, chapter.get("cards") or [], fonts, (80, 400))
    bx = 80
    for badge in chapter.get("badges") or []:
        draw_badge(draw, (bx, 980), badge, fonts)
        bbox = draw.textbbox((0, 0), badge, font=fonts["badge"])
        bx += (bbox[2] - bbox[0]) + 48
    shot = load_shot(chapter.get("preview") or "")
    if shot:
        box = (980, 400, 1840, 940)
        chrome_frame(image, box, chapter.get("preview") or "", fonts)
        image.paste(fit_shot(shot, box), (box[0], box[1]))
    return image


def compose_demo_frame(step: dict, title: str) -> Image.Image:
    image, draw, fonts = new_canvas()
    draw.text((80, 48), "Keyloop · Live demo", fill=ACCENT, font=fonts["kicker"])
    draw.text((80, 90), title, fill=WHITE, font=fonts["title"])
    badge = step.get("badge") or ""
    if badge:
        draw_badge(draw, (80, 160), badge, fonts)
    shot = load_shot(step.get("screenshot") or "")
    box = (80, 230, 1840, 1000)
    chrome_frame(image, box, step.get("screenshot") or "", fonts)
    if shot:
        image.paste(fit_shot(shot, box), (box[0], box[1]))
    return image


def compose_chapter(chapter: dict) -> Image.Image:
    visual = chapter.get("visual")
    if visual == "architecture":
        return compose_architecture(chapter)
    return compose_split(chapter)


def mux_slide(image: Path, audio: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg_bin(),
            "-y",
            "-loop",
            "1",
            "-i",
            str(image),
            "-i",
            str(audio),
            "-c:v",
            "libx264",
            "-tune",
            "stillimage",
            "-c:a",
            "aac",
            "-shortest",
            "-pix_fmt",
            "yuv420p",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )


def mux_demo_sequence(chapter: dict, audio: Path, dest: Path, work: Path) -> None:
    steps = chapter.get("steps") or []
    if not steps:
        raise ValueError("demo chapter missing steps")
    dur = probe_duration(audio)
    each = max(2.0, dur / len(steps))
    clips: list[Path] = []
    for i, step in enumerate(steps, start=1):
        png = work / f"04_demo_step_{i:02d}.png"
        compose_demo_frame(step, chapter["title"]).save(png)
        clip = work / f"04_demo_step_{i:02d}.mp4"
        subprocess.run(
            [
                ffmpeg_bin(),
                "-y",
                "-loop",
                "1",
                "-t",
                f"{each:.3f}",
                "-i",
                str(png),
                "-c:v",
                "libx264",
                "-tune",
                "stillimage",
                "-pix_fmt",
                "yuv420p",
                str(clip),
            ],
            check=True,
            capture_output=True,
        )
        clips.append(clip)
    list_file = work / "demo_concat.txt"
    list_file.write_text("\n".join(f"file '{c.as_posix()}'" for c in clips), encoding="utf-8")
    silent = work / "04_demo_silent.mp4"
    subprocess.run(
        [
            ffmpeg_bin(),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(silent),
        ],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            ffmpeg_bin(),
            "-y",
            "-i",
            str(silent),
            "-i",
            str(audio),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )


def concat_clips(clips: list[Path], dest: Path) -> None:
    list_file = dest.parent / "concat.txt"
    list_file.write_text(
        "\n".join(f"file '{clip.as_posix()}'" for clip in clips),
        encoding="utf-8",
    )
    subprocess.run(
        [
            ffmpeg_bin(),
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-c",
            "copy",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )


def main() -> int:
    ensure_vieneu_python()
    print_banner("walkthrough video")
    result = CheckResult()
    print_section("bootstrap assets")
    bootstrap = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/bootstrap_from_hei.py"), "--target", "video"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if bootstrap.returncode == 0:
        result.ok("video assets")
    else:
        result.fail("video asset bootstrap")
        print(bootstrap.stdout[-1000:] if bootstrap.stdout else bootstrap.stderr[-1000:])
        return print_result(result)

    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    tts = script.get("tts") or {
        "backend": "vieneu",
        "mode": "v3turbo",
        "model": "pnnbao-ump/VieNeu-TTS-v3-Turbo",
        "voice": "Adam",
    }
    WORK.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clips: list[Path] = []

    print_section("vieneu tts + visuals")
    for index, chapter in enumerate(script["chapters"], start=1):
        body = " ".join(chapter["lines"])
        audio = WORK / f"{index:02d}_{chapter['id']}.wav"
        clip = WORK / f"{index:02d}_{chapter['id']}.mp4"
        try:
            if audio.is_file() and audio.stat().st_size > 1000:
                result.ok(f"tts {chapter['id']} reuse")
            else:
                synth_vieneu(body, audio, tts)
                result.ok(f"tts {chapter['id']}")
        except Exception as exc:
            result.fail(f"audio {chapter['id']}: {exc}")
            return print_result(result)
        try:
            if chapter.get("visual") == "demo_sequence":
                mux_demo_sequence(chapter, audio, clip, WORK)
            else:
                slide = WORK / f"{index:02d}_{chapter['id']}.png"
                compose_chapter(chapter).save(slide)
                mux_slide(slide, audio, clip)
            clips.append(clip)
            result.ok(f"mux {chapter['id']}")
        except subprocess.CalledProcessError as exc:
            result.fail(f"ffmpeg mux {chapter['id']}")
            err = (exc.stderr or b"").decode("utf-8", errors="ignore")[-800:]
            print(err)
            return print_result(result)

    dest = OUT_DIR / "keyloop_walkthrough.mp4"
    print_section("concat")
    try:
        concat_clips(clips, dest)
        result.ok(str(dest.relative_to(REPO_ROOT)))
    except subprocess.CalledProcessError as exc:
        result.fail("concat")
        print((exc.stderr or b"").decode("utf-8", errors="ignore")[-800:])
    return print_result(result, pass_message="walkthrough rendered")


if __name__ == "__main__":
    raise SystemExit(main())
