"""Step 5 (Optional): Mute filler words in video slices using transcript word-level timestamps.

Identifies meaningless interjections/fillers and mutes their audio portions
using ffmpeg volume filter, while preserving the original video track untouched.

Usage:
  python mute_fillers.py -t transcript.json --topics topics.json -s slices_dir -o slices_muted
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


# Filler words to mute: pure interjections with no semantic content
FILLER_WORDS = {
    # 单字语气词
    "嗯", "啊", "哦", "呃", "诶", "唉", "哎", "唔", "噢", "嗷",
    # 叠词语气词
    "嗯嗯", "嗯哼", "啊啊",
    # Whisper 幻觉词
    "我我", "中文字幕提供",
}

# Segments that are pure filler: very short text that is just an interjection
FILLER_SEGMENT_TEXTS = {
    "嗯", "啊", "哦", "呃", "诶", "唉", "哎", "唔",
    "OK", "ok", "Ok",
    "我",  # Whisper often hallucinates repeated "我"
    "喝奶",
}

# Segments where the text is just a connective with no content
FILLER_CONNECTIVES = {"然后", "然後", "那么", "那麼", "就是", "就是說", "所以"}


def is_filler_segment(seg: dict) -> bool:
    """Check if a segment is a filler that should be muted."""
    text = seg["text"].strip()
    duration = seg["end"] - seg["start"]

    # Pure filler words
    if text in FILLER_SEGMENT_TEXTS:
        return True

    # Short connectives (< 0.8s) that are just vocal pauses
    if text in FILLER_CONNECTIVES and duration < 0.8:
        return True

    # Word-level check: if all words in the segment are fillers
    words = seg.get("words", [])
    if words and all(w.get("word", "").strip() in FILLER_WORDS for w in words):
        return True

    # Single-char "我" repeated (Whisper hallucination pattern)
    if text == "我" and duration < 2.0:
        return True

    return False


def find_filler_times(transcript: dict, start_time: float, end_time: float) -> list[tuple[float, float]]:
    """Find all filler time ranges within [start_time, end_time]."""
    fillers = []

    for seg in transcript.get("segments", []):
        if seg["start"] >= end_time:
            break
        if seg["end"] <= start_time:
            continue

        if is_filler_segment(seg):
            seg_start = max(seg["start"], start_time)
            seg_end = min(seg["end"], end_time)

            rel_start = round(seg_start - start_time, 3)
            rel_end = round(seg_end - start_time, 3)

            if rel_end - rel_start > 0.05:  # At least 50ms
                fillers.append((rel_start, rel_end))

    if not fillers:
        return []

    # Merge overlapping/adjacent intervals (within 100ms)
    merged = [fillers[0]]
    for start, end in fillers[1:]:
        if start <= merged[-1][1] + 0.1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged


def build_silence_filter(filler_times: list[tuple[float, float]]) -> str:
    """Build a ffmpeg filter using volume expression."""
    if not filler_times:
        return ""

    conditions = []
    for start, end in filler_times:
        conditions.append(f"between(t,{start:.3f},{end:.3f})")

    enable_expr = "+".join(conditions)
    return f"volume=0:enable='gte({enable_expr},1)'"


def mute_fillers_in_slice(
    slice_path: Path,
    output_path: Path,
    filler_times: list[tuple[float, float]],
) -> bool:
    """Mute filler words in a video slice using ffmpeg."""
    if not filler_times:
        if slice_path != output_path:
            import shutil
            shutil.copy2(slice_path, output_path)
        return True

    audio_filter = build_silence_filter(filler_times)

    cmd = [
        "ffmpeg",
        "-i", str(slice_path),
        "-af", audio_filter,
        "-c:v", "copy",       # Copy video stream unchanged
        "-c:a", "aac",        # Re-encode audio stream with filter
        "-b:a", "192k",
        "-y",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        stderr_text = result.stderr.decode("utf-8", errors="replace")[:300] if result.stderr else "unknown error"
        print(f"    ffmpeg error: {stderr_text}", file=sys.stderr)
        return False

    return True


def mute_fillers(
    transcript_path: str | Path,
    topics_path: str | Path,
    slices_dir: str | Path,
    output_dir: str | Path,
) -> None:
    t_path = Path(transcript_path)
    tp_path = Path(topics_path)
    s_dir = Path(slices_dir)
    o_dir = Path(output_dir)

    if not t_path.exists():
        print(f"Error: transcript not found: {t_path}", file=sys.stderr)
        sys.exit(1)

    if not tp_path.exists():
        print(f"Error: topics not found: {tp_path}", file=sys.stderr)
        sys.exit(1)

    if not s_dir.exists():
        print(f"Error: slices directory not found: {s_dir}", file=sys.stderr)
        sys.exit(1)

    o_dir.mkdir(parents=True, exist_ok=True)

    transcript = json.loads(t_path.read_text(encoding="utf-8"))
    topics_data = json.loads(tp_path.read_text(encoding="utf-8"))
    topics = topics_data.get("topics", [])

    print("=" * 60)
    print("Muting Fillers in Video Slices")
    print("=" * 60)
    print(f"Transcript: {len(transcript.get('segments', []))} segments")
    print(f"Topics:     {len(topics)} items")
    print(f"Slices dir: {s_dir}")
    print(f"Output dir: {o_dir}")
    print()

    total_fillers = 0
    total_muted_time = 0.0

    for topic in topics:
        index = topic["index"]
        title = topic.get("title", f"slice_{index:02d}")
        start = topic["start_time"]
        end = topic["end_time"]

        safe_title = re.sub(r'[\\/:*?"<>|]', "", title).strip(". ") or "untitled"
        slice_name = f"{index:02d}_{safe_title}.mp4"
        slice_path = s_dir / slice_name

        if not slice_path.exists():
            matches = list(s_dir.glob(f"{index:02d}_*.mp4"))
            if matches:
                slice_path = matches[0]
                slice_name = slice_path.name
            else:
                print(f"  Skip [{index:02d}] {title}: video slice file not found")
                continue

        filler_times = find_filler_times(transcript, start, end)

        if not filler_times:
            print(f"  [{index:02d}] {title}: no fillers found")
            if slice_path != o_dir / slice_name:
                import shutil
                shutil.copy2(slice_path, o_dir / slice_name)
            continue

        filler_count = len(filler_times)
        filler_duration = sum(e - s for s, e in filler_times)
        total_fillers += filler_count
        total_muted_time += filler_duration

        print(f"  [{index:02d}] {title}: {filler_count} fillers ({filler_duration:.1f}s muted)")

        output_path = o_dir / slice_name
        success = mute_fillers_in_slice(slice_path, output_path, filler_times)

        if success:
            size_mb = output_path.stat().st_size / 1024 / 1024
            print(f"       -> {slice_name} ({size_mb:.1f} MB)")
        else:
            print(f"       -> FAILED")

    print("=" * 60)
    print(f"Done. Total: {total_fillers} fillers muted, {total_muted_time:.1f}s audio silenced.")
    print(f"Processed slices saved to: {o_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mute filler words in video slices")
    parser.add_argument("-t", "--transcript", default=None, help="Path to transcript.json")
    parser.add_argument("-p", "--topics", default=None, help="Path to topics.json")
    parser.add_argument("-s", "--slices-dir", default=None, help="Input slices directory")
    parser.add_argument("-o", "--output-dir", default=None, help="Output directory (default: overwrite slices)")

    args = parser.parse_args()

    if not args.transcript or not args.topics or not args.slices_dir:
        parser.print_help()
        print("\nError: --transcript, --topics, and --slices-dir are required.", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else Path(args.slices_dir)

    mute_fillers(
        transcript_path=args.transcript,
        topics_path=args.topics,
        slices_dir=args.slices_dir,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    main()
