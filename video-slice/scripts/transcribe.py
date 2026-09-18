"""Step 2: Transcribe audio using OpenAI Whisper with timestamps.

Requires: pip install openai-whisper
Run on a machine with GPU for best performance.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def transcribe(
    audio_path: str | Path,
    output_path: str | Path,
    model_name: str = "medium",
    language: str = "zh",
    device: str | None = None,
    force: bool = False,
) -> Path:
    try:
        import whisper
    except ImportError:
        print("Error: openai-whisper not installed. Please run: pip install openai-whisper", file=sys.stderr)
        sys.exit(1)

    audio = Path(audio_path)
    output = Path(output_path)

    if not audio.exists():
        print(f"Error: audio not found: {audio}", file=sys.stderr)
        sys.exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists() and not force:
        print(f"Transcript already exists: {output} (use --force to overwrite)")
        return output

    print(f"Loading Whisper model: {model_name}")
    load_kwargs = {}
    if device:
        load_kwargs["device"] = device
    model = whisper.load_model(model_name, **load_kwargs)

    print(f"Transcribing: {audio}")
    print("This may take some time depending on audio duration and hardware...")

    result = model.transcribe(
        str(audio),
        language=language,
        verbose=True,
        word_timestamps=True,
    )

    segments = []
    for seg in result["segments"]:
        segments.append({
            "id": seg["id"],
            "start": round(seg["start"], 3),
            "end": round(seg["end"], 3),
            "text": seg["text"].strip(),
            "words": [
                {
                    "word": w["word"].strip(),
                    "start": round(w["start"], 3),
                    "end": round(w["end"], 3),
                    "probability": round(w.get("probability", 1.0), 4),
                }
                for w in seg.get("words", [])
                if w.get("word")
            ] if seg.get("words") else [],
        })

    transcript = {
        "text": result["text"].strip(),
        "language": result.get("language", language),
        "segments": segments,
    }

    output.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Transcript saved: {output} ({len(segments)} segments)")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe audio using OpenAI Whisper with word-level timestamps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("audio_pos", nargs="?", default=None, help="Input audio path (positional)")
    parser.add_argument("output_pos", nargs="?", default=None, help="Output transcript path (positional)")
    parser.add_argument("model_pos", nargs="?", default=None, help="Model name (positional, default: medium)")
    parser.add_argument("-a", "--audio", dest="audio_flag", default=None, help="Input audio WAV path")
    parser.add_argument("-o", "--output", dest="output_flag", default=None, help="Output transcript JSON path")
    parser.add_argument("-m", "--model", dest="model_flag", default="medium", help="Whisper model (tiny/base/small/medium/large-v3/large-v3-turbo, default: medium)")
    parser.add_argument("-l", "--language", default="zh", help="Language code (default: zh)")
    parser.add_argument("-d", "--device", default=None, help="Device to use ('cuda', 'cpu', or None for auto)")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite existing output")

    args = parser.parse_args()

    audio_input = args.audio_flag or args.audio_pos
    output_input = args.output_flag or args.output_pos
    model_name = args.model_flag if args.model_flag != "medium" else (args.model_pos or "medium")

    if not audio_input:
        parser.print_help()
        print("\nError: Please specify the input audio path via positional argument or -a/--audio.", file=sys.stderr)
        sys.exit(1)

    audio_path = Path(audio_input)
    output_path = Path(output_input) if output_input else audio_path.parent / "transcript.json"

    transcribe(
        audio_path=audio_path,
        output_path=output_path,
        model_name=model_name,
        language=args.language,
        device=args.device,
        force=args.force,
    )


if __name__ == "__main__":
    main()
