"""Video normalization for 2026 Gyeongbokgung event.

Accepted uploads: up to 100 MiB, <=45 seconds.
Output: browser-compatible MP4 H.264 + AAC, <=35 MiB.
Encoded files live only in TemporaryDirectory; final bytes live in PostgreSQL.
Never trim or silently fall back to an unplayable source file.
"""
from __future__ import annotations

import re
import subprocess
import tempfile
import threading
from pathlib import Path

MAX_SOURCE = 100 * 1024 * 1024
MAX_FINAL = 35 * 1024 * 1024
TRANSCODE_THRESHOLD = 20 * 1024 * 1024
MAX_SECONDS = 45
_FFMPEG_GATE = threading.BoundedSemaphore(1)


class VideoProcessingError(Exception):
    pass


class VideoProcessingBusy(VideoProcessingError):
    pass


def _ffmpeg_path() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise VideoProcessingError("영상 자동 압축 엔진을 불러오지 못했습니다. 관리자에게 알려주세요.") from exc


def _probe(ffmpeg: str, path: Path):
    try:
        r = subprocess.run(
            [ffmpeg, "-hide_banner", "-nostdin", "-i", str(path)],
            capture_output=True, text=True, timeout=15, check=False
        )
    except subprocess.TimeoutExpired as exc:
        raise VideoProcessingError("영상 정보를 읽는 데 시간이 너무 오래 걸립니다.") from exc

    info = r.stderr or ""
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", info)
    if not match or "Video:" not in info:
        raise VideoProcessingError("영상 파일을 해석할 수 없습니다. MP4 형식으로 다시 저장해 주세요.")
    duration = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))
    if duration <= 0 or duration > MAX_SECONDS:
        raise VideoProcessingError("영상 길이는 45초 이하여야 합니다. 15~30초로 편집해 올려주세요.")
    has_h264 = bool(re.search(r"Video:\s*(h264|avc1)\b", info, re.I))
    has_aac = not ("Audio:" in info) or bool(re.search(r"Audio:\s*aac\b", info, re.I))
    return duration, has_h264, has_aac


def normalize_video(data: bytes, mime: str, filename: str):
    """Return (output_bytes, video/mp4 MIME, safe_filename, compressed, source_bytes).

    35 MB-or-less H.264 MP4 with AAC (or no audio) is left as-is for speed.
    Other videos are transcoded to 720p / <=30fps MP4 with an explicit
    error on failure, and with a global semaphore to limit peak memory use.
    """
    if len(data) > MAX_SOURCE:
        raise VideoProcessingError("영상은 원본 파일 기준 최대 100MB까지 업로드할 수 있습니다.")
    if not _FFMPEG_GATE.acquire(blocking=False):
        raise VideoProcessingBusy("다른 영상이 변환 중입니다. 잠시 후 다시 업로드해주세요.")
    try:
        ffmpeg = _ffmpeg_path()
        with tempfile.TemporaryDirectory(prefix="palace-video-") as td:
            source = Path(td) / ("source.webm" if mime == "video/webm" else "source.mov" if mime == "video/quicktime" else "source.mp4")
            source.write_bytes(data)
            duration, h264, aac = _probe(ffmpeg, source)
            passthrough = mime == "video/mp4" and h264 and aac and len(data) <= MAX_FINAL and len(data) <= TRANSCODE_THRESHOLD
            if passthrough:
                return data, "video/mp4", filename, False, len(data)

            output = Path(td) / "optimized.mp4"
            cmd = [
                ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                "-i", str(source),
                "-map", "0:v:0", "-map", "0:a:0?",
                "-vf", "scale=w='min(1280,iw)':h='min(720,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2,fps=30",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "29",
                "-maxrate", "1800k", "-bufsize", "3600k",
                "-pix_fmt", "yuv420p", "-threads", "2",
                "-c:a", "aac", "-b:a", "96k", "-ar", "44100",
                "-movflags", "+faststart",
                "-f", "mp4", str(output)
            ]
            try:
                run = subprocess.run(cmd, capture_output=True, text=True, timeout=85, check=False)
            except subprocess.TimeoutExpired as exc:
                raise VideoProcessingError("영상 압축 시간이 초과됐습니다. 휴대폰에서 720p·30fps로 낮춰 다시 시도해주세요.") from exc
            if run.returncode != 0 or not output.is_file() or output.stat().st_size < 200:
                raise VideoProcessingError("영상을 자동 압축하지 못했습니다. MP4(H.264)로 저장해 다시 시도해주세요.")
            size = output.stat().st_size
            if size > MAX_FINAL:
                raise VideoProcessingError("압축 후에도 영상이 35MB를 초과했습니다. 720p로 낮추거나 길이를 줄여주세요.")
            normalized_name = re.sub(r"\.[^.]+$", "", filename)[:130] + "_compressed.mp4"
            return output.read_bytes(), "video/mp4", normalized_name, True, len(data)
    finally:
        _FFMPEG_GATE.release()
