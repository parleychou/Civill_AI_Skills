"""GPU machine runner: run Whisper transcription on a GPU machine.

Usage on GPU machine:
  1. pip install openai-whisper torch
  2. python run_on_gpu.py [--audio audio.wav] [--model medium]

This will:
  - Check CUDA availability and GPU VRAM
  - Transcribe audio with chunked/direct Whisper model
  - Output transcript.json
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Quick GPU runner for Whisper transcription")
    parser.add_argument("-a", "--audio", default="audio.wav", help="Path to audio file (default: audio.wav)")
    parser.add_argument("-o", "--output", default="transcript.json", help="Path to output transcript (default: transcript.json)")
    parser.add_argument("-m", "--model", default="medium", help="Whisper model name (default: medium)")
    parser.add_argument("-c", "--chunk", type=int, default=300, help="Chunk duration in seconds (default: 300)")
    parser.add_argument("--yes", action="store_true", help="Skip CPU confirmation if no GPU found")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    audio = Path(args.audio)
    transcript = Path(args.output)

    if not audio.exists():
        # Check current working dir as fallback
        if (Path.cwd() / args.audio).exists():
            audio = Path.cwd() / args.audio
        else:
            print(f"Error: {audio} not found. Please ensure audio file is present.", file=sys.stderr)
            sys.exit(1)

    if transcript.exists():
        print(f"Transcript already exists: {transcript}")
        choice = input("Overwrite? (y/N): ").strip().lower()
        if choice != "y":
            return

    print("=" * 60)
    print("GPU Machine Whisper Transcription Runner")
    print("=" * 60)

    # Detect GPU
    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"VRAM: {vram_gb:.1f} GB")
        else:
            print("WARNING: No CUDA detected! Will run on CPU (very slow).")
            if not args.yes:
                confirm = input("Continue anyway with CPU? (y/N): ").strip().lower()
                if confirm != "y":
                    sys.exit(0)
    except ImportError:
        print("torch not installed, cannot verify CUDA status.")

    # Check if transcribe_gpu.py exists in same directory
    transcribe_gpu_script = script_dir / "transcribe_gpu.py"
    if transcribe_gpu_script.exists():
        cmd = [
            sys.executable,
            str(transcribe_gpu_script),
            "--audio", str(audio),
            "--output", str(transcript),
            "--model", args.model,
            "--chunk", str(args.chunk),
        ]
        if args.yes:
            cmd.append("--yes")
    else:
        # Fallback to direct transcribe.py
        transcribe_script = script_dir / "transcribe.py"
        cmd = [
            sys.executable,
            str(transcribe_script),
            "-a", str(audio),
            "-o", str(transcript),
            "-m", args.model,
        ]

    print(f"\nRunning command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("Transcription process failed!", file=sys.stderr)
        sys.exit(1)

    print(f"\nTranscription complete: {transcript}")
    print(f"File size: {transcript.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
