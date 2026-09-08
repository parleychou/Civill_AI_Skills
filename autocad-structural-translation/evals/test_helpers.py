"""Meaningful offline regression checks; run with Python standard-library unittest."""
import copy
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from analyze_inventory import bounds, compose, flatten, insert_matrix, normalize, point, text_rows
from translation_rules import candidate_anchors, protected_tokens, rectangle_overlap, segment_hits_box, validate_decisions


class GeometryTests(unittest.TestCase):
    def test_block_origin_rotation_and_scale(self):
        m=insert_matrix({"Rotation":math.pi/2,"XScaleFactor":2,"YScaleFactor":3,"InsertionPoint":[100,200,0]},[10,20,0])
        self.assertEqual(point(m,[10,20,0])[:2],[100,200])
        result=point(m,[11,20,0])
        self.assertAlmostEqual(result[0],100)
        self.assertAlmostEqual(result[1],202)

    def test_nested_transform_and_mirror(self):
        m=compose((1,0,0,1,100,0),(-1,0,0,1,20,30))
        self.assertEqual(point(m,[5,6,0]),[115,36,0])
        self.assertEqual(bounds(m,[[0,0,0],[10,10,0]]),[110,30,120,40])

    def test_crossing_line_with_both_endpoints_outside(self):
        self.assertTrue(segment_hits_box([-10,5],[20,5],[0,0,10,10]))

    def test_parallel_line_outside(self):
        self.assertFalse(segment_hits_box([-10,11],[20,11],[0,0,10,10]))

    def test_zero_length_point(self):
        self.assertTrue(segment_hits_box([5,5],[5,5],[0,0,10,10]))
        self.assertFalse(segment_hits_box([15,5],[15,5],[0,0,10,10]))

    def test_clearance_and_touching(self):
        self.assertTrue(rectangle_overlap([0,0,10,10],[10,5,20,15]))
        self.assertTrue(rectangle_overlap([0,0,10,10],[11,5,20,15],1))
        self.assertFalse(rectangle_overlap([0,0,10,10],[12,5,20,15],1))

    def test_rotated_candidate(self):
        candidate=next(candidate_anchors([100,200],math.pi/2,10,(0,-1)))
        self.assertAlmostEqual(candidate[0],110)
        self.assertAlmostEqual(candidate[1],200)


class OccurrenceTests(unittest.TestCase):
    def fixture(self,visible=True):
        return {"selected_handles":["I1"],"layers":[{"Name":"EN","Color":6}],
                "layouts":[{"layout_name":"Model","entities":[
                    {"Handle":"I1","ObjectName":"AcDbBlockReference","Name":"B","Layer":"EN","InsertionPoint":[100,200,0],"Visible":visible,
                     "GetAttributes":[{"Handle":"A1","ObjectName":"AcDbAttribute","text":{"TextString":"注释"},"InsertionPoint":[105,206,0]}]},
                    {"Handle":"I2","ObjectName":"AcDbBlockReference","Name":"B","Layer":"EN","InsertionPoint":[300,400,0]}]}],
                "blocks":[{"Name":"B","Origin":[0,0,0],"entities":[
                    {"Handle":"C1","ObjectName":"AcDbText","text":{"TextString":"钢梁"},"Layer":"0","Color":256,"InsertionPoint":[1,2,0],"Height":10}]}]}

    def test_distinct_instances_and_selection_inheritance(self):
        records,gaps=flatten(self.fixture())
        self.assertEqual(gaps,[])
        sources=[e for e in records if e["Handle"]=="C1"]
        self.assertEqual([e["instance_id"] for e in sources],["Model/I1/C1","Model/I2/C1"])
        self.assertEqual([e["selected_occurrence"] for e in sources],[True,False])
        self.assertEqual(sources[0]["anchor_xy"],[101,202])
        self.assertEqual(sources[0]["effective_layer"],"EN")
        self.assertEqual(sources[0]["effective_aci"],6)

    def test_attribute_not_double_transformed(self):
        records,_=flatten(self.fixture())
        attr=next(e for e in records if e["Handle"]=="A1")
        self.assertEqual(attr["anchor_xy"],[105,206])

    def test_parent_invisibility_propagates(self):
        records,_=flatten(self.fixture(False))
        self.assertFalse(next(e for e in records if e["instance_id"]=="Model/I1/C1")["effective_visible"])

    def test_nonplanar_not_silently_flattened(self):
        data=self.fixture()
        data["layouts"][0]["entities"][0]["Normal"]=[0,1,0]
        _,gaps=flatten(data)
        self.assertTrue(any("Non-+Z" in g["reason"] for g in gaps))

    def test_chinese_escape_and_raw_preservation(self):
        self.assertEqual(normalize(r"\U+94A2\U+6881\P Steel Beam"),"钢梁 steel beam")

    def test_dimension_tokens_remain_distinct(self):
        tokens=protected_tokens("间距<>，4处 %<FIELD_CODE>% M12(4.6s) %%c13.5")
        self.assertEqual(tokens["<>"],1)
        self.assertEqual(tokens["%<FIELD_CODE>%"],1)
        self.assertEqual(tokens["M12"],1)
        self.assertEqual(tokens["13.5"],1)


class DecisionTests(unittest.TestCase):
    def fixture(self):
        occurrence={"texts":[{"instance_id":"Model/C1","property":"TextString","raw":"钢梁","chinese":True,"display_candidate":True,"layout":"Model"}],
                    "entities":[{"instance_id":"Model/I1/E1","layout":"Model","effective_visible":True,"text":{"TextString":"Steel Beam"}}],"gaps":[]}
        manifest={"claims_complete":True,"decisions":[{"source_key":"Model/C1::TextString","source_raw":"钢梁","status":"already_translated","existing_check":{"completed":True},"existing_english_ids":["Model/I1/E1"],"reason":"Confirmed same callout"}]}
        return occurrence,manifest

    def test_confirmed_skip(self):
        data,plan=self.fixture()
        self.assertEqual(validate_decisions(data,plan),[])

    def test_duplicate_insertion_rejected(self):
        data,plan=self.fixture()
        plan["decisions"][0]["new_english"]="Steel Beam"
        self.assertTrue(any("must not receive" in e for e in validate_decisions(data,plan)))

    def test_missing_occurrence_disposition(self):
        data,plan=self.fixture()
        plan["decisions"]=[]
        self.assertTrue(any("Missing disposition" in e for e in validate_decisions(data,plan)))

    def test_hidden_counterpart_rejected(self):
        data,plan=self.fixture()
        data["entities"][0]["effective_visible"]=False
        self.assertTrue(any("not visible" in e for e in validate_decisions(data,plan)))

    def test_stale_source_and_unperformed_check(self):
        data,plan=self.fixture()
        plan["decisions"][0]["source_raw"]="钢柱"
        plan["decisions"][0]["existing_check"]["completed"]=False
        self.assertEqual(len(validate_decisions(data,plan)),2)

    def test_gap_prevents_complete_claim(self):
        data,plan=self.fixture()
        data["gaps"]=[{"reason":"Unknown proxy"}]
        self.assertTrue(any("Cannot claim" in e for e in validate_decisions(data,plan)))


if __name__=="__main__":
    unittest.main(verbosity=2)
