"""Generate auditable existing-English candidates; never mutate a decision manifest."""
import argparse
import json
import math
import re
from pathlib import Path

from translation_rules import protected_tokens


def normalize_words(text):
    text = re.sub(r"[-,/]", " ", str(text or ""))
    return {w.lower() for w in re.findall(r"[A-Za-z][A-Za-z'.-]*", text) if len(w) > 1}


def word_similarity(expected, observed):
    a, b = normalize_words(expected), normalize_words(observed)
    return len(a & b) / max(len(a), len(b)) if a and b else 0.0


def bbox_distance(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0)
    dy = max(b[1] - a[3], a[1] - b[3], 0)
    return math.hypot(dx, dy)


def _row_overlap(a, b):
    return min(a[3], b[3]) - max(a[1], b[1]) > 0


def _common_ancestry(a, b):
    aa, bb = str(a).split("/"), str(b).split("/")
    return sum(x == y for x, y in zip(aa, bb))


def _direction_conflict(expected, observed):
    groups = ({"x", "y"}, {"left", "right"}, {"top", "bottom"}, {"upper", "lower"})
    a, b = normalize_words(expected), normalize_words(observed)
    return any((a & group) and (b & group) and (a & group) != (b & group) for group in groups)


def score_candidate(source, english, proposed_english, observed_english=None):
    observed = observed_english
    if observed is None:
        observed = next((str(v) for v in english.get("text", {}).values()
                         if re.search(r"[A-Za-z]{2,}", str(v))), "")
    source_box, english_box = source.get("bbox_xy"), english.get("bbox_xy")
    distance = bbox_distance(source_box, english_box) if source_box and english_box else None
    source_tokens = protected_tokens(str(source.get("source_raw", "")))
    expected_tokens = protected_tokens(str(proposed_english or ""))
    observed_tokens = protected_tokens(str(observed or ""))
    # The proposed translation establishes which source identifiers must survive.
    token_agreement = all(observed_tokens[k] >= n for k, n in expected_tokens.items())
    return {
        "source_id": source.get("instance_id"),
        "english_id": english.get("instance_id"),
        "observed_english": observed,
        "semantic_query_available": bool(normalize_words(proposed_english)),
        "layout_match": source.get("layout") == english.get("layout"),
        "visible": bool(english.get("effective_visible", False)),
        "distance": distance,
        "row_overlap": bool(source_box and english_box and _row_overlap(source_box, english_box)),
        "common_ancestry": _common_ancestry(source.get("instance_id", ""), english.get("instance_id", "")),
        "same_container": source.get("container") == english.get("container"),
        "word_similarity": word_similarity(proposed_english, observed),
        "token_agreement": token_agreement,
        "direction_conflict": _direction_conflict(proposed_english, observed),
        "source_tokens": dict(source_tokens),
        "expected_tokens": dict(expected_tokens),
        "observed_tokens": dict(observed_tokens),
    }


def classify_candidate(score):
    if (not score.get("visible") or not score.get("layout_match")
            or not score.get("token_agreement") or score.get("direction_conflict")):
        return "rejected"
    similarity = score.get("word_similarity", 0.0)
    distance = score.get("distance")
    spatial = distance is not None and distance <= 1600
    structural = score.get("row_overlap") or score.get("same_container") or score.get("common_ancestry", 0) >= 2
    if not score.get("semantic_query_available"):
        return "uncertain" if spatial and structural else "rejected"
    if similarity >= 0.8 and spatial and structural:
        return "confirmed"
    if similarity >= 0.5 and distance is not None and distance <= 3000:
        return "uncertain"
    return "rejected"


def generate_candidates(source, english_entities, proposed_english):
    rows = []
    for english in english_entities:
        score = score_candidate(source, english, proposed_english)
        score["classification"] = classify_candidate(score)
        if score["classification"] != "rejected":
            rows.append(score)
    return sorted(rows, key=lambda x: ({"confirmed": 0, "uncertain": 1}[x["classification"]],
                                      -x["word_similarity"], x["distance"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("occurrences")
    parser.add_argument("decisions")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    occ = json.loads(Path(args.occurrences).read_text(encoding="utf-8"))
    manifest = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    entities = {e["instance_id"]: e for e in occ["entities"]}
    english = []
    for row in occ["texts"]:
        if row.get("display_candidate") and not row.get("chinese") and re.search(r"[A-Za-z]{2,}", row.get("plain", "")):
            item = dict(entities[row["instance_id"]])
            item["text"] = {row["property"]: row["plain"]}
            english.append(item)
    output = []
    for decision in manifest.get("decisions", []):
        source_id = decision["source_key"].split("::", 1)[0]
        source = dict(entities[source_id])
        source["source_raw"] = decision.get("source_raw", "")
        query = (decision.get("existing_check", {}).get("search_english")
                 or decision.get("english_search_terms")
                 or decision.get("new_english", ""))
        output.append({"source_key": decision["source_key"],
                       "semantic_query": query,
                       "candidates": generate_candidates(source, english, query)})
    Path(args.output).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"sources": len(output), "confirmed": sum(bool(x["candidates"]) and x["candidates"][0]["classification"] == "confirmed" for x in output)}))


if __name__ == "__main__":
    main()
