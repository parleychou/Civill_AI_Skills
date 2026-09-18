"""Step 4: Slice video into clips based on topics.json using ffmpeg."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]', "", name)
    cleaned = cleaned.strip(". ")
    return cleaned or "untitled"


def slice_video(
    video_path: str | Path,
    topics_path: str | Path,
    output_dir: str | Path,
    *,
    copy_mode: bool = False,
    force: bool = False,
) -> Path:
    video = Path(video_path)
    topics_file = Path(topics_path)
    out_dir = Path(output_dir)

    if not video.exists():
        print(f"Error: video not found: {video}", file=sys.stderr)
        sys.exit(1)

    if not topics_file.exists():
        print(f"Error: topics not found: {topics_file}", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    topics_data = json.loads(topics_file.read_text(encoding="utf-8"))
    topics = topics_data.get("topics", [])

    print(f"Video: {video}")
    print(f"Topics file: {topics_file}")
    print(f"Total topics: {len(topics)}")
    print(f"Mode: {'Stream Copy (fast, keyframe-aligned)' if copy_mode else 'Re-encode (precise cut, H.264/AAC)'}")
    print(f"Output directory: {out_dir}")
    print("=" * 60)

    success_count = 0
    for topic in topics:
        index = topic["index"]
        title = topic.get("title", f"slice_{index:02d}")
        start = topic["start_time"]
        end = topic["end_time"]
        duration = end - start

        filename = f"{index:02d}_{sanitize_filename(title)}.mp4"
        output_path = out_dir / filename

        if output_path.exists() and not force:
            print(f"  [{index:02d}] Skip (already exists): {filename}")
            success_count += 1
            continue

        if copy_mode:
            cmd = [
                "ffmpeg",
                "-i", str(video),
                "-ss", str(start),
                "-t", str(duration),
                "-c", "copy",
                "-avoid_negative_ts", "1",
                "-y",
                str(output_path),
            ]
        else:
            cmd = [
                "ffmpeg",
                "-i", str(video),
                "-ss", str(start),
                "-t", str(duration),
                "-c:v", "libx264",
                "-c:a", "aac",
                "-avoid_negative_ts", "1",
                "-y",
                str(output_path),
            ]

        print(f"  [{index:02d}] Slicing: {title} ({start:.1f}s - {end:.1f}s, duration {duration:.1f}s)")
        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            err = result.stderr.decode("utf-8", errors="replace")[:300]
            print(f"    ERROR: {err}", file=sys.stderr)
        else:
            size_mb = output_path.stat().st_size / 1024 / 1024
            print(f"    OK: {filename} ({size_mb:.1f} MB)")
            success_count += 1

    print("=" * 60)
    print(f"Slicing complete: {success_count}/{len(topics)} clips generated.")
    print(f"Directory: {out_dir}")
    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Slice long video into short topic clips using ffmpeg",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("video_pos", nargs="?", default=None, help="Input video path (positional)")
    parser.add_argument("topics_pos", nargs="?", default=None, help="Input topics.json path (positional)")
    parser.add_argument("output_pos", nargs="?", default=None, help="Output directory for slices (positional)")
    parser.add_argument("-i", "--video", dest="video_flag", default=None, help="Input video path")
    parser.add_argument("-t", "--topics", dest="topics_flag", default=None, help="Input topics.json path")
    parser.add_argument("-o", "--output-dir", dest="output_flag", default=None, help="Output directory")
    parser.add_argument("--copy", action="store_true", help="Use ffmpeg stream copy mode (faster, keyframe-aligned)")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite existing slice clips")

    args = parser.parse_args()

    video_input = args.video_flag or args.video_pos
    topics_input = args.topics_flag or args.topics_pos
    output_input = args.output_flag or args.output_pos

    if not video_input or not topics_input:
        parser.print_help()
        print("\nError: Both video path and topics.json path are required.", file=sys.stderr)
        sys.exit(1)

    video_path = Path(video_input)
    topics_path = Path(topics_input)
    output_dir = Path(output_input) if output_input else video_path.parent / "slices"

    slice_video(
        video_path=video_path,
        topics_path=topics_path,
        output_dir=output_dir,
        copy_mode=args.copy,
        force=args.force,
    )


if __name__ == "__main__":
    main()
