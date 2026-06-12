import pytest
from unittest.mock import patch, MagicMock
from loopforge.services.ffmpeg_service import render_loop

@patch("loopforge.services.ffmpeg_service._get_ffmpeg_path")
@patch("loopforge.services.ffmpeg_service.get_video_info")
@patch("loopforge.services.ffmpeg_service.check_disk_space")
@patch("loopforge.services.ffmpeg_service._run_ffmpeg_with_progress")
def test_render_loop_routes_av1_to_concat(mock_run, mock_check, mock_info, mock_ffmpeg):
    mock_ffmpeg.return_value = "ffmpeg"
    mock_info.return_value = {
        "file_path": "input.mp4",
        "file_name": "input.mp4",
        "resolution": "1920x1080",
        "width": 1920,
        "height": 1080,
        "fps": 30.0,
        "codec": "av1",
        "duration": 10.0,
        "bitrate": "1000 kbps",
        "file_size": "10 MB",
        "file_size_bytes": 10 * 1024 * 1024,
        "has_audio": True,
    }

    render_loop("input.mp4", "output.mp4", 60.0, [])
    
    # Verify that the command uses concat demuxer
    called_args = mock_run.call_args[0]
    cmd = called_args[0]
    assert "-f" in cmd
    assert "concat" in cmd

@patch("loopforge.services.ffmpeg_service._get_ffmpeg_path")
@patch("loopforge.services.ffmpeg_service.get_video_info")
@patch("loopforge.services.ffmpeg_service.check_disk_space")
@patch("loopforge.services.ffmpeg_service._run_ffmpeg_with_progress")
def test_render_loop_routes_h264_to_stream_loop(mock_run, mock_check, mock_info, mock_ffmpeg):
    mock_ffmpeg.return_value = "ffmpeg"
    mock_info.return_value = {
        "file_path": "input.mp4",
        "file_name": "input.mp4",
        "resolution": "1920x1080",
        "width": 1920,
        "height": 1080,
        "fps": 30.0,
        "codec": "h264",
        "duration": 10.0,
        "bitrate": "1000 kbps",
        "file_size": "10 MB",
        "file_size_bytes": 10 * 1024 * 1024,
        "has_audio": True,
    }

    render_loop("input.mp4", "output.mp4", 60.0, [])
    
    # Verify that the command uses stream_loop
    called_args = mock_run.call_args[0]
    cmd = called_args[0]
    assert "-stream_loop" in cmd
