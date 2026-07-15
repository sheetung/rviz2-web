from types import SimpleNamespace

import pytest

from app.api.v1 import video


def _settings(**overrides):
    values = {
        "rtsp_transport": "tcp",
        "rtsp_frame_rate": 12,
        "rtsp_width": 640,
        "rtsp_jpeg_quality": 5,
        "rtsp_startup_timeout": 10.0,
        "rtsp_session_ttl": 300,
        "ffmpeg_path": "ffmpeg",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_ffmpeg_command_uses_configured_rtsp_source(monkeypatch):
    monkeypatch.setattr(video.shutil, "which", lambda _: "/usr/bin/ffmpeg")

    command = video._build_ffmpeg_command(
        _settings(),
        "rtsp://192.168.1.66:8554/1",
    )

    assert command[0] == "/usr/bin/ffmpeg"
    assert command[command.index("-i") + 1] == "rtsp://192.168.1.66:8554/1"
    assert command[command.index("-rtsp_transport") + 1] == "tcp"
    assert "fps=12,scale=640:-2:force_original_aspect_ratio=decrease" in command
    assert command[-2:] == ["image2pipe", "pipe:1"]
    assert "-rw_timeout" not in command

    probe_command = video._build_ffmpeg_command(
        _settings(),
        "rtsp://192.168.1.66:8554/1",
        frame_limit=1,
    )
    assert probe_command[probe_command.index("-frames:v") + 1] == "1"
    assert "-rw_timeout" not in probe_command


def test_jpeg_frames_are_extracted_without_losing_remainder():
    first = b"\xff\xd8first\xff\xd9"
    second = b"\xff\xd8second\xff\xd9"
    buffer = bytearray(b"noise" + first + second)

    assert video._pop_jpeg_frame(buffer) == first
    assert video._pop_jpeg_frame(buffer) == second
    assert video._pop_jpeg_frame(buffer) is None


def test_non_rtsp_source_is_rejected():
    with pytest.raises(ValueError):
        video._validated_rtsp_url("http://192.168.1.66/video")


@pytest.mark.asyncio
async def test_video_status_does_not_expose_rtsp_url(monkeypatch):
    monkeypatch.setattr(video, "get_settings", lambda: _settings())
    monkeypatch.setattr(video.shutil, "which", lambda _: "/usr/bin/ffmpeg")

    status = await video.get_video_status()

    assert status.ready is True
    assert "192.168.1.66" not in status.model_dump_json()


@pytest.mark.asyncio
async def test_video_session_uses_an_opaque_stream_path(monkeypatch):
    monkeypatch.setattr(video, "get_settings", lambda: _settings())
    monkeypatch.setattr(video.shutil, "which", lambda _: "/usr/bin/ffmpeg")

    async def successful_probe(_settings, _source_url):
        return None

    monkeypatch.setattr(video, "_probe_rtsp_source", successful_probe)

    session = await video.create_video_session(
        video.VideoSessionRequest(source_url="rtsp://192.168.1.66:8554/1")
    )

    assert "192.168.1.66" not in session.stream_path
    assert session.session_id in session.stream_path


@pytest.mark.asyncio
async def test_video_session_is_not_created_when_probe_fails(monkeypatch):
    monkeypatch.setattr(video, "get_settings", lambda: _settings())
    monkeypatch.setattr(video.shutil, "which", lambda _: "/usr/bin/ffmpeg")

    async def failed_probe(_settings, _source_url):
        raise RuntimeError("no video stream")

    monkeypatch.setattr(video, "_probe_rtsp_source", failed_probe)

    with pytest.raises(video.HTTPException) as error:
        await video.create_video_session(
            video.VideoSessionRequest(
                source_url="rtsp://192.168.1.66:8554/1"
            )
        )

    assert error.value.status_code == 504
    assert "未检测到可用视频流" in error.value.detail
