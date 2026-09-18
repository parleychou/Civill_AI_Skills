"""Step 1: Extract audio from video using ffmpeg for Whisper transcription.

Converts video audio track into 16kHz, mono, 16-bit PCM WAV,
which is the optimal input format for OpenAI Whisper.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def extract_audio(video_path: str | Path, output_path: str | Path, *, force: bool = False) -> Path:
    video = Path(video_path)
    output = Path(output_path)

    if not video.exists():
        print(f"Error: video not found: {video}", file=sys.stderr)
        sys.exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists() and not force:
        print(f"Audio already exists: {output} (use --force to overwrite)")
        return output

    cmd = [
        "ffmpeg",
        "-i", str(video),
        "-vn",                   # Disable video stream
        "-acodec", "pcm_s16le",  # Uncompressed 16-bit PCM WAV
        "-ar", "16000",          # 16kHz sampling rate (Whisper standard)
        "-ac", "1",              # Mono channel
        "-y",                    # Overwrite
        str(output),
    ]

    print(f"Extracting audio from: {video}")
    print(f"Output: {output}")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    size_mb = output.stat().st_size / 1024 / 1024
    print(f"Audio extracted successfully: {output} ({size_mb:.1f} MB)")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract 16kHz mono WAV audio from video using ffmpeg",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("video_pos", nargs="?", default=None, help="Input video path (positional)")
    parser.add_argument("output_pos", nargs="?", default=None, help="Output audio path (positional)")
    parser.add_argument("-i", "--video", dest="video_flag", default=None, help="Input video path")
    parser.add_argument("-o", "--output", dest="output_flag", default=None, help="Output audio WAV path")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite existing output")

    args = parser.parse_args()

    video_input = args.video_flag or args.video_pos
    output_input = args.output_flag or args.output_pos

    if not video_input:
        parser.print_help()
        print("\nError: Please specify the input video path via positional argument or -i/--video.", file=sys.stderr)
        sys.exit(1)

    video_path = Path(video_input)
    if not output_input:
        output_path = video_path.parent / f"{video_path.stem}_audio.wav"
    else:
        output_path = Path(output_input)

    extract_audio(video_path, output_path, force=args.force)


if __name__ == "__main__":
    main()
