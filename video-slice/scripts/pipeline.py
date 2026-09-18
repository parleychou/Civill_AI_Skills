"""All-in-one Video Slicing Pipeline Orchestrator.

Orchestrates the entire end-to-end workflow:
  1. Extract 16kHz mono WAV audio
  2. Transcribe speech using Whisper
  3. Analyze topics with LLM
  4. Slice video into short clips
  5. (Optional) Mute filler words

Usage:
  python pipeline.py --video input.mp4 --work-dir ./output
  python pipeline.py --video input.mp4 --step 1
  python pipeline.py --video input.mp4 --step 4 --topics ./output/topics.json
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add scripts directory to sys.path so we can import modules directly
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from extract_audio import extract_audio
from slice_video import slice_video


def run_pipeline(
    video_path: Path,
    work_dir: Path,
    steps: list[int],
    *,
    model: str = "medium",
    language: str = "zh",
    chunk_seconds: int = 300,
    api_key: str | None = None,
    base_url: str | None = None,
    llm_model: str | None = None,
    copy_mode: bool = False,
    mute_fillers_flag: bool = False,
    force: bool = False,
) -> None:
    work_dir.mkdir(parents=True, exist_ok=True)
    audio_path = work_dir / "audio.wav"
    transcript_path = work_dir / "transcript.json"
    topics_path = work_dir / "topics.json"
    slices_dir = work_dir / "slices"
    slices_muted_dir = work_dir / "slices_muted"

    print("=" * 60)
    print("Video Slice Pipeline")
    print(f"Video:    {video_path}")
    print(f"Work Dir: {work_dir}")
    print(f"Steps:    {steps}")
    print("=" * 60)

    # Step 1: Extract Audio
    if 1 in steps:
        print("\n>>> Step 1: Extracting Audio...")
        extract_audio(video_path, audio_path, force=force)

    # Step 2: Transcribe
    if 2 in steps:
        print("\n>>> Step 2: Transcribing Audio with Whisper...")
        if not audio_path.exists():
            print(f"Error: {audio_path} not found. Run step 1 first.", file=sys.stderr)
            sys.exit(1)

        # Check if CUDA is available, use chunked GPU transcription if available or requested
        has_cuda = False
        try:
            import torch
            has_cuda = torch.cuda.is_available()
        except ImportError:
            pass

        if has_cuda:
            print("CUDA detected, using chunked GPU transcription...")
            from transcribe_gpu import transcribe_gpu_chunked
            transcribe_gpu_chunked(
                audio_path=audio_path,
                output_path=transcript_path,
                model_name=model,
                chunk_seconds=chunk_seconds,
                language=language,
                prompt_confirm_cpu=False,
            )
        else:
            print("Running local Whisper transcription...")
            from transcribe import transcribe
            transcribe(
                audio_path=audio_path,
                output_path=transcript_path,
                model_name=model,
                language=language,
                force=force,
            )

    # Step 3: Analyze Topics
    if 3 in steps:
        print("\n>>> Step 3: Analyzing Topics...")
        if not transcript_path.exists():
            print(f"Error: {transcript_path} not found. Run step 2 first.", file=sys.stderr)
            sys.exit(1)

        from analyze_topics import analyze_topics
        analyze_topics(
            transcript_path=transcript_path,
            output_path=topics_path,
            api_key=api_key,
            base_url=base_url,
            model=llm_model,
        )

    # Step 4: Slice Video
    if 4 in steps:
        print("\n>>> Step 4: Slicing Video...")
        if not topics_path.exists():
            print(f"Error: {topics_path} not found. Run step 3 first or provide topics.json.", file=sys.stderr)
            sys.exit(1)

        slice_video(
            video_path=video_path,
            topics_path=topics_path,
            output_dir=slices_dir,
            copy_mode=copy_mode,
            force=force,
        )

    # Step 5: Mute Fillers (Optional)
    if 5 in steps or mute_fillers_flag:
        print("\n>>> Step 5: Muting Fillers in Video Slices...")
        if not slices_dir.exists():
            print(f"Error: {slices_dir} not found. Run step 4 first.", file=sys.stderr)
            sys.exit(1)

        from mute_fillers import mute_fillers
        mute_fillers(
            transcript_path=transcript_path,
            topics_path=topics_path,
            slices_dir=slices_dir,
            output_dir=slices_muted_dir,
        )

    print("\n" + "=" * 60)
    print("Pipeline finished successfully!")
    print(f"Output files in: {work_dir}")
    print("=" * 60)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Unified Video Slicing Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--video", required=True, help="Input long video path")
    parser.add_argument("-w", "--work-dir", default=None, help="Working directory for audio/transcripts/slices")
    parser.add_argument(
        "--step",
        default="all",
        help="Step to execute: 'all', '1' (audio), '2' (transcribe), '3' (topics), '4' (slice), '5' (mute), or comma-separated e.g. '1,2'",
    )
    parser.add_argument("-m", "--model", default="medium", help="Whisper model (default: medium)")
    parser.add_argument("-l", "--language", default="zh", help="Language code (default: zh)")
    parser.add_argument("-c", "--chunk", type=int, default=300, help="Chunk duration in seconds for GPU transcribe")
    parser.add_argument("--api-key", default=None, help="LLM API key for topic analysis")
    parser.add_argument("--base-url", default=None, help="LLM API base URL")
    parser.add_argument("--llm-model", default=None, help="LLM model name")
    parser.add_argument("--copy", action="store_true", help="Use ffmpeg stream copy for fast cutting")
    parser.add_argument("--mute-fillers", action="store_true", help="Execute Step 5 to mute filler words")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite existing outputs")

    args = parser.parse_args()

    video_path = Path(args.video).resolve()
    if not video_path.exists():
        print(f"Error: Video file not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    work_dir = Path(args.work_dir).resolve() if args.work_dir else video_path.parent / f"{video_path.stem}_work"

    if args.step == "all":
        steps = [1, 2, 3, 4]
        if args.mute_fillers:
            steps.append(5)
    else:
        steps = [int(s.strip()) for s in args.step.split(",") if s.strip().isdigit()]

    run_pipeline(
        video_path=video_path,
        work_dir=work_dir,
        steps=steps,
        model=args.model,
        language=args.language,
        chunk_seconds=args.chunk,
        api_key=args.api_key,
        base_url=args.base_url,
        llm_model=args.llm_model,
        copy_mode=args.copy,
        mute_fillers_flag=args.mute_fillers,
        force=args.force,
    )


if __name__ == "__main__":
    main()
