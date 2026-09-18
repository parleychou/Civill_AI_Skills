"""Step 2 (GPU Chunked): Whisper transcription with chunking for long audio.

Splits long audio into chunks using ffmpeg, transcribes each chunk separately,
and merges timestamps to prevent Whisper hallucinations and memory issues.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def check_gpu() -> None:
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"GPU detected: {name} ({vram:.1f} GB VRAM)")
        else:
            print("WARNING: No CUDA GPU detected! Will use CPU (slow).")
            confirm = input("Continue with CPU? (y/N): ").strip().lower()
            if confirm != "y":
                sys.exit(0)
    except ImportError:
        print("WARNING: torch not installed, cannot verify GPU status.")


def split_audio(audio_path: str, chunk_dir: str, chunk_seconds: int) -> list[Path]:
    """Split audio into chunks using ffmpeg to avoid Whisper hallucination on long audio."""
    chunk_dir_path = Path(chunk_dir)
    chunk_dir_path.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-i", audio_path,
        "-f", "segment",
        "-segment_time", str(chunk_seconds),
        "-c", "copy",
        "-y",
        str(chunk_dir_path / "chunk_%04d.wav"),
    ]

    print(f"Splitting audio into {chunk_seconds}s chunks...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ffmpeg error:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    chunks = sorted(chunk_dir_path.glob("chunk_*.wav"))
    print(f"Split into {len(chunks)} chunks")
    return chunks


def transcribe_chunk(model, chunk_path: Path, chunk_index: int, total: int, language: str = "zh") -> list[dict]:
    """Transcribe a single chunk and return segments with corrected timestamps."""
    print(f"  Transcribing chunk {chunk_index + 1}/{total}: {chunk_path.name} ...")

    result = model.transcribe(
        str(chunk_path),
        language=language,
        verbose=False,
        word_timestamps=True,
    )

    segments = []
    for seg in result["segments"]:
        text = seg["text"].strip()
        if not text:
            continue
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "text": text,
            "words": [
                {
                    "word": w["word"].strip(),
                    "start": w["start"],
                    "end": w["end"],
                    "probability": round(w.get("probability", 1.0), 4),
                }
                for w in seg.get("words", [])
                if w.get("word", "").strip()
            ] if seg.get("words") else [],
        })

    print(f"    -> {len(segments)} segments")
    return segments


def get_chunk_durations(chunk_dir: str) -> list[float]:
    """Get actual duration of each chunk using ffprobe."""
    chunks = sorted(Path(chunk_dir).glob("chunk_*.wav"))
    durations = []
    for chunk in chunks:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(chunk),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        try:
            dur = float(result.stdout.strip())
        except ValueError:
            dur = 0.0
        durations.append(dur)
    return durations


def transcribe_gpu_chunked(
    audio_path: str | Path,
    output_path: str | Path,
    model_name: str = "medium",
    chunk_seconds: int = 300,
    language: str = "zh",
    prompt_confirm_cpu: bool = True,
) -> Path:
    audio = Path(audio_path)
    output = Path(output_path)

    if not audio.exists():
        print(f"Error: audio file not found: {audio}", file=sys.stderr)
        sys.exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Whisper GPU Transcription (Chunked)")
    print("=" * 60)
    print(f"Audio:   {audio}")
    print(f"Model:   {model_name}")
    print(f"Chunk:   {chunk_seconds}s")
    print(f"Output:  {output}")
    print()

    if prompt_confirm_cpu:
        check_gpu()

    with tempfile.TemporaryDirectory(prefix="whisper_chunks_") as chunk_dir:
        chunks = split_audio(str(audio), chunk_dir, chunk_seconds)
        if not chunks:
            print("Error: no audio chunks produced", file=sys.stderr)
            sys.exit(1)

        chunk_durations = get_chunk_durations(chunk_dir)

        try:
            import whisper
        except ImportError:
            print("Error: openai-whisper not installed. Please run: pip install openai-whisper", file=sys.stderr)
            sys.exit(1)

        print(f"\nLoading Whisper model: {model_name}")
        model = whisper.load_model(model_name)

        all_segments = []
        time_offset = 0.0

        print(f"\nTranscribing {len(chunks)} chunks...")
        for i, chunk_path in enumerate(chunks):
            segments = transcribe_chunk(model, chunk_path, i, len(chunks), language=language)

            for seg in segments:
                seg["start"] = round(seg["start"] + time_offset, 3)
                seg["end"] = round(seg["end"] + time_offset, 3)
                for w in seg.get("words", []):
                    w["start"] = round(w["start"] + time_offset, 3)
                    w["end"] = round(w["end"] + time_offset, 3)

            all_segments.extend(segments)
            time_offset += chunk_durations[i]

            progress = (i + 1) / len(chunks) * 100
            total_time = sum(chunk_durations[:i + 1])
            total_all = sum(chunk_durations)
            print(f"  Progress: {progress:.0f}% | Time processed: {total_time:.0f}s / {total_all:.0f}s")

    final_segments = []
    for idx, seg in enumerate(all_segments):
        final_segments.append({
            "id": idx,
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"],
            "words": seg.get("words", []),
        })

    full_text = " ".join(s["text"] for s in final_segments)

    transcript = {
        "text": full_text,
        "language": language,
        "segments": final_segments,
    }

    output.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'=' * 60}")
    print("Transcription complete!")
    print(f"Segments: {len(final_segments)}")
    print(f"Text length: {len(full_text)} chars")
    if final_segments:
        print(f"Duration: {final_segments[-1]['end']:.1f}s ({final_segments[-1]['end']/60:.1f}min)")
    print(f"Output: {output} ({output.stat().st_size / 1024:.1f} KB)")
    print(f"{'=' * 60}")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Whisper GPU transcription with chunking")
    parser.add_argument("audio_pos", nargs="?", default=None, help="Input audio WAV path (positional)")
    parser.add_argument("output_pos", nargs="?", default=None, help="Output transcript JSON path (positional)")
    parser.add_argument("-a", "--audio", dest="audio_flag", default=None, help="Input audio file")
    parser.add_argument("-o", "--output", dest="output_flag", default=None, help="Output transcript file")
    parser.add_argument("-m", "--model", default="medium", help="Whisper model name (default: medium)")
    parser.add_argument("-c", "--chunk", type=int, default=300, help="Chunk duration in seconds (default: 300)")
    parser.add_argument("-l", "--language", default="zh", help="Language code (default: zh)")
    parser.add_argument("--yes", action="store_true", help="Do not prompt for CPU confirmation")

    args = parser.parse_args()

    audio_input = args.audio_flag or args.audio_pos
    output_input = args.output_flag or args.output_pos

    if not audio_input:
        parser.print_help()
        print("\nError: Please specify the audio file path.", file=sys.stderr)
        sys.exit(1)

    audio_path = Path(audio_input)
    output_path = Path(output_input) if output_input else audio_path.parent / "transcript.json"

    transcribe_gpu_chunked(
        audio_path=audio_path,
        output_path=output_path,
        model_name=args.model,
        chunk_seconds=args.chunk,
        language=args.language,
        prompt_confirm_cpu=not args.yes,
    )


if __name__ == "__main__":
    main()
