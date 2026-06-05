"""
ingestion.py
------------
Takes a video or audio file and extracts the audio track as a WAV file.
If the input is already audio (WAV, MP3), it converts or copies to the output folder.
Returns a dict with the session ID and path to the extracted audio.
"""

import shutil
from pathlib import Path


def ingest_session(file_path: str, session_id: str, output_dir: str) -> dict:
    """
    Takes a video or audio file and prepares it for transcription.

    Parameters:
        file_path  -- path to the input file (MP4, MOV, WAV, MP3)
        session_id -- label for this session e.g. "P1"
        output_dir -- folder where extracted audio will be saved

    Returns a dict with:
        session_id   -- the label passed in
        audio_path   -- path to the extracted WAV file
        source_file  -- original file path
    """

    file_path = Path(file_path)
    output_dir = Path(output_dir)

    session_folder = output_dir / session_id
    session_folder.mkdir(parents=True, exist_ok=True)

    audio_output = session_folder / "audio.wav"
    suffix = file_path.suffix.lower()

    if suffix in (".mp4", ".mov", ".avi", ".mkv", ".webm"):
        try:
            from moviepy.editor import VideoFileClip
        except ImportError:
            raise ImportError(
                "moviepy is required for video files. Run: pip install moviepy"
            )

        print(f"Extracting audio from video: {file_path.name}")
        clip = VideoFileClip(str(file_path))
        clip.audio.write_audiofile(
            str(audio_output),
            fps=16000,
            ffmpeg_params=["-ac", "1"],
            logger=None,
        )
        clip.close()

    elif suffix == ".wav":
        print(f"Using audio file directly: {file_path.name}")
        shutil.copy(str(file_path), str(audio_output))

    elif suffix in (".mp3", ".m4a", ".ogg"):
        try:
            from moviepy.editor import AudioFileClip
        except ImportError:
            raise ImportError(
                "moviepy is required for MP3/M4A/OGG files. Run: pip install moviepy"
            )

        print(f"Converting audio to WAV: {file_path.name}")
        clip = AudioFileClip(str(file_path))
        clip.write_audiofile(
            str(audio_output),
            fps=16000,
            ffmpeg_params=["-ac", "1"],
            logger=None,
        )
        clip.close()

    else:
        raise ValueError(
            f"Unsupported file type: {suffix}. "
            "Supported types: MP4, MOV, AVI, MKV, WEBM, WAV, MP3, M4A, OGG"
        )

    print(f"Audio ready at: {audio_output}")

    return {
        "session_id": session_id,
        "audio_path": str(audio_output),
        "source_file": str(file_path),
    }
