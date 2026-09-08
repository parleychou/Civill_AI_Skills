"""Deterministic V2 pipeline tests. These tests never connect to AutoCAD."""
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from counterpart_candidates import classify_candidate, normalize_words, score_candidate
from placement_planner import (SpatialIndex, build_obstacle_index, collision_keys,
                               group_columns, plan_column, plan_manifest)
from scope_manifest import build_scope, read_selection_handles, validate_scope
from verify_translation import fingerprint_mismatches, reconcile
from apply_translations import (completed_sources, execution_batches,
                                fingerprint_object, latest_operation_map,
                                validate_resume_journal)


def row(instance_id, raw, chinese=True, prop="TextString", selected=False):
    return {"instance_id": instance_id, "property": prop, "raw": raw, "plain": raw,
            "chinese": chinese, "display_candidate": True, "selected": selected,
            "layout": "Model"}


def entity(instance_id, box, text=None, visible=True, container="layout:Model"):
    return {"instance_id": instance_id, "bbox_xy": box, "layout": "Model",
            "effective_visible": visible, "effective_layer": "TEXT",
            "container": container, "ObjectName": "AcDbText",
            "text": {"TextString": text} if text is not None else {}}


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.occ = {
            "texts": [row("Model/A/T1", "钢梁"), row("Model/B/T1", "钢梁")],
            "entities": [entity("Model/A/T1", [0, 0, 100, 100], "钢梁"),
                         entity("Model/B/T1", [1000, 0, 1100, 100], "钢梁")],
            "gaps": [], "summary": {"extraction_errors": 0},
        }

    def test_selected_insert_includes_only_that_occurrence_descendants(self):
        scope = build_scope(self.occ, "selected", ["A"])
        self.assertEqual(scope["source_keys"], ["Model/A/T1::TextString"])

    def test_unselected_sibling_instance_is_out_of_scope(self):
        scope = build_scope(self.occ, "selected", ["A"])
        self.assertNotIn("Model/B/T1::TextString", scope["source_keys"])

    def test_changed_pickfirst_selection_is_rejected(self):
        scope = build_scope(self.occ, "selected", ["A"])
        self.assertTrue(any("selection changed" in e.lower()
                            for e in validate_scope(scope, self.occ, ["B"])))

    def test_scanner_selection_json_handles_are_read(self):
        self.assertEqual(read_selection_handles({"drawing": "x.dwg", "handles": ["a", "B"]}),
                         ["A", "B"])


class CounterpartTests(unittest.TestCase):
    def test_global_english_may_skip_selected_source(self):
        source = entity("Model/A/T1", [0, 0, 100, 100], "钢梁")
        english = entity("Model/E", [130, 0, 330, 100], "Steel Beam")
        score = score_candidate(source, english, "Steel Beam", "Steel Beam")
        self.assertEqual(classify_candidate(score), "confirmed")

    def test_ambiguous_similarity_is_not_auto_skip(self):
        source = entity("Model/A/T1", [0, 0, 100, 100], "X向钢筋")
        english = entity("Model/E", [130, 0, 330, 100], "Y Direction Rebar")
        score = score_candidate(source, english, "X Direction Rebar", "Y Direction Rebar")
        self.assertNotEqual(classify_candidate(score), "confirmed")

    def test_hyphen_and_slash_normalization(self):
        self.assertEqual(normalize_words("Simply-Supported / Steel"),
                         {"simply", "supported", "steel"})

    def test_pretranslation_search_surfaces_nearby_candidate_as_uncertain(self):
        source = entity("Model/A/T1", [0, 0, 100, 100], "钢梁")
        english = entity("Model/E", [130, 0, 330, 100], "Steel Beam")
        score = score_candidate(source, english, "", "Steel Beam")
        self.assertEqual(classify_candidate(score), "uncertain")


class PlacementTests(unittest.TestCase):
    def test_spatial_index_deduplicates_multi_cell_hits(self):
        index = SpatialIndex(cell_size=100)
        index.add("wide", [0, 0, 250, 250])
        self.assertEqual([x["key"] for x in index.query([50, 50, 220, 220])], ["wide"])

    def test_line_bbox_overlap_without_segment_crossing_is_clear(self):
        line = {"instance_id": "L1", "ObjectName": "AcDbLine", "effective_visible": True,
                "effective_layer": "0", "bbox_xy": [0, 0, 1000, 1000],
                "matrix_xy": [1, 0, 0, 1, 0, 0],
                "geometry": {"StartPoint": [0, 0, 0], "EndPoint": [1000, 1000, 0]}}
        index, gaps = build_obstacle_index([line], cell_size=100)
        self.assertEqual(gaps, [])
        self.assertEqual(collision_keys([0, 900, 50, 950], index), [])

    def test_crossing_line_blocks_text_box(self):
        line = {"instance_id": "L1", "ObjectName": "AcDbLine", "effective_visible": True,
                "effective_layer": "0", "bbox_xy": [0, 0, 1000, 1000],
                "matrix_xy": [1, 0, 0, 1, 0, 0],
                "geometry": {"StartPoint": [0, 0, 0], "EndPoint": [1000, 1000, 0]}}
        index, _ = build_obstacle_index([line], cell_size=100)
        self.assertEqual(collision_keys([450, 450, 550, 550], index), ["L1"])

    def test_column_plan_preserves_row_order_and_clearance(self):
        sources = [
            {"source_key": "a", "layout": "Model", "container": "table:1", "bbox_xy": [0, 300, 100, 340], "height_xy": 40, "english": "Alpha"},
            {"source_key": "b", "layout": "Model", "container": "table:1", "bbox_xy": [0, 200, 100, 240], "height_xy": 40, "english": "Beta"},
            {"source_key": "c", "layout": "Model", "container": "table:1", "bbox_xy": [0, 100, 100, 140], "height_xy": 40, "english": "Gamma"},
        ]
        groups = group_columns(sources)
        self.assertEqual(len(groups), 1)
        plan = plan_column(groups[0], SpatialIndex(100), {"clearance": 10, "max_distance": 500})
        self.assertEqual(plan["status"], "placed")
        self.assertEqual([p["source_key"] for p in plan["placements"]], ["a", "b", "c"])

    def test_column_group_blocks_atomically_when_no_clear_region(self):
        sources = [
            {"source_key": str(i), "layout": "Model", "container": "table:1",
             "bbox_xy": [0, y, 100, y + 40], "height_xy": 40, "english": "Long English"}
            for i, y in enumerate((300, 200, 100))
        ]
        index = SpatialIndex(100)
        index.add("wall-right", [100, -1000, 2000, 1000])
        index.add("wall-left", [-2000, -1000, 0, 1000])
        plan = plan_column(group_columns(sources)[0], index,
                           {"clearance": 10, "max_distance": 300})
        self.assertEqual(plan["status"], "blocked")
        self.assertNotIn("placements", plan)

    def test_manifest_planner_never_plans_outside_scope(self):
        occ = {"entities": [entity("Model/A", [0, 0, 100, 100], "钢梁") | {"height_xy": 40},
                            entity("Model/B", [1000, 0, 1100, 100], "钢梁") | {"height_xy": 40}],
               "texts": [], "gaps": []}
        scope = {"mode": "selected", "source_keys": ["Model/A::TextString"]}
        decisions = {"decisions": [
            {"source_key": "Model/A::TextString", "status": "needs_translation",
             "new_english": "Steel Beam", "placement_style": {"height": 40}},
            {"source_key": "Model/B::TextString", "status": "needs_translation",
             "new_english": "Steel Beam", "placement_style": {"height": 40}}]}
        result = plan_manifest(occ, scope, decisions, {"clearance": 10})
        keys = {p.get("source_key") for p in result["plan"]}
        self.assertEqual(keys, {"Model/A::TextString"})


class VerificationTests(unittest.TestCase):
    def test_source_fingerprint_detects_original_property_change(self):
        class FakeObject:
            ObjectName = "AcDbText"
            Layer = "NOTE"
            Color = 2
            Visible = True
            TextString = "钢梁"

        snapshot = fingerprint_object(FakeObject(), "TextString")
        self.assertEqual(snapshot["value"], "钢梁")
        current = dict(snapshot, Layer="OTHER")
        self.assertEqual(fingerprint_mismatches(snapshot, current), ["Layer"])

    def test_writer_default_dry_run_never_imports_pyautocad(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            occ = {"texts": [row("Model/A", "钢梁")],
                   "entities": [entity("Model/A", [0, 0, 100, 100], "钢梁") | {"Handle": "A"}],
                   "gaps": [], "summary": {"extraction_errors": 0}}
            scope = build_scope(occ, "selected", ["A"])
            manifest = {"claims_complete": True, "decisions": [{
                "source_key": "Model/A::TextString", "source_raw": "钢梁",
                "status": "needs_translation", "new_english": "Steel Beam",
                "existing_english_ids": [], "reason": "No counterpart",
                "existing_check": {"completed": True}}]}
            plan = {"plan": [{"source_key": "Model/A::TextString",
                               "anchor": [200, 100], "width": 300}]}
            for name, value in (("inventory.json", {}), ("occ.json", occ),
                                ("scope.json", scope), ("manifest.json", manifest),
                                ("plan.json", plan)):
                (root / name).write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
            command = [sys.executable, str(SCRIPTS / "apply_translations.py"),
                       "--inventory", str(root / "inventory.json"),
                       "--occurrences", str(root / "occ.json"),
                       "--scope", str(root / "scope.json"),
                       "--manifest", str(root / "manifest.json"),
                       "--plan", str(root / "plan.json"),
                       "--source-dwg", str(root / "source.dwg"),
                       "--output-dwg", str(root / "output.dwg"),
                       "--journal", str(root / "journal.json"),
                       "--expect-active", str(root / "source.dwg")]
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("no AutoCAD connection", result.stdout)
            self.assertFalse((root / "output.dwg").exists())

    def test_column_rows_form_one_atomic_execution_batch(self):
        rows = {"a": {"source_key": "a", "group_id": "g"},
                "b": {"source_key": "b", "group_id": "g"},
                "c": {"source_key": "c"}}
        self.assertEqual(execution_batches(rows), [["a", "b"], ["c"]])

    def test_rolled_back_operation_is_not_complete_on_resume(self):
        journal = {"operations": [
            {"source_key": "a", "status": "placed", "handle": "10"},
            {"source_key": "a", "status": "rolled_back_group", "handle": "10"},
        ]}
        self.assertEqual(latest_operation_map(journal)["a"]["status"], "rolled_back_group")

    def test_partially_written_column_is_not_complete_on_resume(self):
        plan = {"a": {"group_id": "g"}, "b": {"group_id": "g"}}
        journal = {"operations": [
            {"source_key": "a", "group_id": "g", "status": "placed", "handle": "10"},
            {"source_key": "b", "group_id": "g", "status": "intent"},
        ]}
        self.assertEqual(completed_sources(journal, plan), set())
        journal["operations"].append(
            {"source_key": "b", "group_id": "g", "status": "placed", "handle": "11"})
        self.assertEqual(completed_sources(journal, plan), {"a", "b"})

    def test_resume_rejects_journal_bound_to_another_output(self):
        scope = {"mode": "selected", "source_keys": ["a"]}
        journal = {"source_dwg": "source.dwg", "output_dwg": "other.dwg",
                   "source_sha256": "abc", "scope": scope}
        errors = validate_resume_journal(journal, Path("source.dwg"),
                                         Path("output.dwg"), scope, "abc")
        self.assertTrue(any("output" in e.lower() for e in errors))

    def test_reconcile_requires_zero_second_run_additions(self):
        scope = {"mode": "selected", "source_keys": ["Model/A::TextString"]}
        decisions = {"decisions": [{"source_key": "Model/A::TextString",
                                      "source_raw": "钢梁", "status": "translated",
                                      "new_english": "Steel Beam"}]}
        journal = {"operations": [{"source_key": "Model/A::TextString",
                                     "status": "placed", "handle": "E1",
                                     "english": "Steel Beam"}]}
        final = {"entities": [entity("Model/E1", [200, 0, 400, 100], "Steel Beam") | {"Handle": "E1"}],
                 "repeat_additions": []}
        self.assertEqual(reconcile(scope, decisions, journal, final)["errors"], [])
        final["repeat_additions"] = ["Model/A::TextString"]
        self.assertTrue(reconcile(scope, decisions, journal, final)["errors"])

    def test_reconcile_does_not_count_rolled_back_placement(self):
        scope = {"mode": "selected", "source_keys": ["Model/A::TextString"]}
        decisions = {"decisions": [{"source_key": "Model/A::TextString",
                                      "source_raw": "钢梁", "status": "translated",
                                      "new_english": "Steel Beam"}]}
        journal = {"operations": [
            {"source_key": "Model/A::TextString", "status": "placed",
             "handle": "E1", "english": "Steel Beam"},
            {"source_key": "Model/A::TextString", "status": "rolled_back_group",
             "handle": "E1", "english": "Steel Beam"}]}
        result = reconcile(scope, decisions, journal,
                           {"entities": [], "repeat_additions": []})
        self.assertTrue(any("no placed" in e.lower() for e in result["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
