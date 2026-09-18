"""Step 3: Analyze transcript with LLM to identify topic breakpoints.

Uses Anthropic-compatible API (e.g. Claude, DeepSeek, or Qianfan endpoints).
Requires: pip install anthropic
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


SYSTEM_PROMPT = """你是一个专业的视频内容分析师。你的任务是根据转录文本，将一段长视频按话题/知识点划分为多个切片。

规则：
1. 每个切片必须是一个完整的话题或知识点，不要在话题中间切断
2. 切片时长不设硬性限制，以知识点完整性为准
3. 为每个切片生成一个简短标题（10字以内），概括该切片的核心内容
4. 返回 JSON 格式，严格如下：

```json
{
  "topics": [
    {
      "index": 1,
      "title": "标题",
      "start_time": 0.0,
      "end_time": 123.5,
      "summary": "一句话概述这段内容"
    }
  ]
}
```

注意：
- start_time 和 end_time 必须对应转录文本中的时间戳（秒）
- 相邻切片的 end_time 和 start_time 可以衔接
- 不要遗漏任何时间段，所有切片必须覆盖完整视频
- 只返回 JSON，不要返回其他内容"""

MERGE_PROMPT = """你是一个视频内容分析师。以下是分段分析得出的话题列表，请完成以下任务：
1. 合并相邻的重复或过于碎片化的话题
2. 调整时间边界使其无缝衔接（前一个的 end_time = 后一个的 start_time）
3. 重新编号 index 从 1 开始
4. 保持相同 JSON 格式返回

话题列表：

{topics_json}"""

CHUNK_DURATION_SECONDS = 1200
RETRY_DELAYS = [30, 60, 120, 300]


def build_transcript_text(segments: list[dict]) -> str:
    lines = []
    for seg in segments:
        start_min = int(seg["start"] // 60)
        start_sec = seg["start"] % 60
        lines.append(f"[{start_min:02d}:{start_sec:05.2f}] {seg['text']}")
    return "\n".join(lines)


def split_segments_by_duration(segments: list[dict], chunk_seconds: int) -> list[list[dict]]:
    """Split segments into chunks of roughly chunk_seconds duration."""
    chunks: list[list[dict]] = []
    current: list[dict] = []
    chunk_start = segments[0]["start"] if segments else 0.0

    for seg in segments:
        current.append(seg)
        if seg["end"] - chunk_start >= chunk_seconds:
            chunks.append(current)
            current = []
            chunk_start = seg["end"]

    if current:
        chunks.append(current)

    return chunks


def call_llm_with_retry(
    client, model: str, user_content: str, max_retries: int = 4,
) -> str:
    """Call LLM with retry logic for rate limits."""
    for attempt in range(max_retries + 1):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=8192,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            if not text_blocks:
                raise RuntimeError(f"No text in response: {[type(b).__name__ for b in response.content]}")
            return text_blocks[-1].strip()

        except Exception as e:
            error_str = str(e)
            is_rate_limit = "429" in error_str or "rate_limit" in error_str.lower()

            if is_rate_limit and attempt < max_retries:
                delay = RETRY_DELAYS[attempt]
                print(f"    Rate limited, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise

    raise RuntimeError("Max retries exceeded")


def extract_topics_from_response(text: str) -> list[dict]:
    """Parse topics from LLM response, handling markdown code blocks."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)
    return data["topics"]


def analyze_topics(
    transcript_path: str | Path,
    output_path: str | Path,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> Path:
    try:
        import anthropic
    except ImportError:
        print("Error: anthropic package is required. Run: pip install anthropic", file=sys.stderr)
        sys.exit(1)

    transcript_file = Path(transcript_path)
    output = Path(output_path)

    if not transcript_file.exists():
        print(f"Error: transcript not found: {transcript_file}", file=sys.stderr)
        sys.exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)

    transcript = json.loads(transcript_file.read_text(encoding="utf-8"))
    segments = transcript["segments"]
    total_duration = segments[-1]["end"] if segments else 0
    total_chars = sum(len(s["text"]) for s in segments)

    print(f"Transcript: {len(segments)} segments, {total_chars} chars, {total_duration:.0f}s")

    key = api_key or os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")
    url = base_url or os.environ.get("ANTHROPIC_BASE_URL", "https://qianfan.baidubce.com/anthropic/coding")
    mdl = model or os.environ.get("TOPIC_ANALYSIS_MODEL", "deepseek-v4-pro")

    if not key:
        print("Error: no API key provided. Set ANTHROPIC_AUTH_TOKEN env var or pass --api-key", file=sys.stderr)
        print("Tip: If you are using Claude Code or an agent directly, you can also let the agent read transcript.json and write topics.json directly.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=key, base_url=url)
    print(f"LLM Config: model={mdl}, base_url={url}")

    chunks = split_segments_by_duration(segments, CHUNK_DURATION_SECONDS)
    print(f"Split into {len(chunks)} chunks (~{CHUNK_DURATION_SECONDS // 60} min each)")

    all_topics: list[dict] = []

    # Resume from partial results if they exist
    resume_from = 0
    if output.exists():
        try:
            partial = json.loads(output.read_text(encoding="utf-8"))
            saved = partial.get("topics", [])
            if saved:
                last_end_time = max(t.get("end_time", 0) for t in saved)
                for ci, cs in enumerate(chunks):
                    if cs[-1]["end"] <= last_end_time + 1:
                        resume_from = ci + 1
                if resume_from > 0:
                    all_topics = saved
                    print(f"Resuming from chunk {resume_from + 1} ({len(saved)} topics already saved)")
        except (json.JSONDecodeError, KeyError):
            pass

    for i, chunk_segments in enumerate(chunks):
        if i < resume_from:
            continue

        chunk_text = build_transcript_text(chunk_segments)
        chunk_start = chunk_segments[0]["start"]
        chunk_end = chunk_segments[-1]["end"]

        prompt = (
            f"以下是一段 {chunk_start:.0f}s - {chunk_end:.0f}s 的视频转录文本（带时间戳）：\n\n"
            f"{chunk_text}"
        )

        print(f"  Chunk {i + 1}/{len(chunks)}: {chunk_start:.0f}s - {chunk_end:.0f}s ({len(chunk_segments)} segments)...")

        try:
            response_text = call_llm_with_retry(client, mdl, prompt)
            topics = extract_topics_from_response(response_text)
            all_topics.extend(topics)
            print(f"    -> {len(topics)} topics found")
        except Exception as e:
            print(f"    ERROR: {e}", file=sys.stderr)
            print(f"    Partial results saved to {output}. Re-run to resume from chunk {i + 2}.", file=sys.stderr)
            sys.exit(1)

        if i < len(chunks) - 1:
            time.sleep(15)

        partial = {"topics": all_topics}
        output.write_text(json.dumps(partial, ensure_ascii=False, indent=2), encoding="utf-8")

    if len(chunks) > 1:
        print(f"\nMerging {len(all_topics)} topics from {len(chunks)} chunks...")
        merge_content = MERGE_PROMPT.format(
            topics_json=json.dumps(all_topics, ensure_ascii=False, indent=2)
        )

        try:
            response_text = call_llm_with_retry(client, mdl, merge_content)
            all_topics = extract_topics_from_response(response_text)
        except Exception as e:
            print(f"  Merge warning ({e}), using unmerged topics")

    for idx, topic in enumerate(all_topics, 1):
        topic["index"] = idx

    result = {"topics": all_topics}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTopics saved successfully: {output} ({len(all_topics)} topics)")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze transcript topics with LLM")
    parser.add_argument("transcript_pos", nargs="?", default=None, help="Path to transcript.json (positional)")
    parser.add_argument("output_pos", nargs="?", default=None, help="Path to output topics.json (positional)")
    parser.add_argument("-t", "--transcript", dest="transcript_flag", default=None, help="Path to transcript.json")
    parser.add_argument("-o", "--output", dest="output_flag", default=None, help="Path to output topics.json")
    parser.add_argument("-k", "--api-key", default=None, help="API key (or set ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY env)")
    parser.add_argument("-u", "--base-url", default=None, help="API base URL (default: Qianfan Anthropic endpoint or env ANTHROPIC_BASE_URL)")
    parser.add_argument("-m", "--model", default=None, help="Model name (default: deepseek-v4-pro or env TOPIC_ANALYSIS_MODEL)")

    args = parser.parse_args()

    transcript_input = args.transcript_flag or args.transcript_pos
    output_input = args.output_flag or args.output_pos

    if not transcript_input:
        parser.print_help()
        print("\nError: Please specify the transcript.json path.", file=sys.stderr)
        sys.exit(1)

    transcript_path = Path(transcript_input)
    output_path = Path(output_input) if output_input else transcript_path.parent / "topics.json"

    analyze_topics(
        transcript_path=transcript_path,
        output_path=output_path,
        api_key=args.api_key,
        base_url=args.base_url,
        model=args.model,
    )


if __name__ == "__main__":
    main()
