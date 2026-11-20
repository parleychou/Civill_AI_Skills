# -*- coding: utf-8 -*-
"""OpenSTAAD codes cited by this skill.

These are the codes the workflow actually passes. Other country, load-type,
and group-type values belong on the Bentley page for the matching method.
"""

from __future__ import annotations

import json


LENGTH_METER = 4
FORCE_KN = 5
LOAD_TYPES = {
    0: "Dead",
    1: "Live",
    2: "Roof live",
    3: "Wind",
    4: "Seismic horizontal",
    5: "Seismic vertical",
}
# 1-3 local, 4-6 global, 7-9 projected, each in X, Y, Z order.
FORCE_DIRECTIONS = {
    1: "local X",
    2: "local Y",
    3: "local Z",
    4: "global X",
    5: "global Y",
    6: "global Z",
    7: "projected X",
    8: "projected Y",
    9: "projected Z",
}
MEMBER_GROUP_TYPE = 2
COUNTRY_CODES = {1: "American", 5: "Chinese"}
ANALYSIS_STATUS = {
    "failure_or_zero": "negative or 0",
    1: "still running",
    2: "finished clean",
    3: "finished with warnings",
    4: "finished with errors",
    5: "not analyzed",
}


def self_check() -> dict:
    if LENGTH_METER != 4 or FORCE_KN != 5:
        raise RuntimeError("sample frame units must stay metre and kilonewton")
    if LOAD_TYPES[0] != "Dead" or FORCE_DIRECTIONS[2] != "local Y":
        raise RuntimeError("dead-load local-Y codes drifted")
    if MEMBER_GROUP_TYPE != 2 or COUNTRY_CODES[5] != "Chinese":
        raise RuntimeError("group or country code drifted")
    return {
        "status": "ok",
        "self_check": True,
        "length_code": LENGTH_METER,
        "force_code": FORCE_KN,
        "load_types": LOAD_TYPES,
        "force_directions": FORCE_DIRECTIONS,
        "member_group_type": MEMBER_GROUP_TYPE,
        "country_codes": COUNTRY_CODES,
        "analysis_status": {str(key): value for key, value in ANALYSIS_STATUS.items()},
    }


if __name__ == "__main__":
    print(json.dumps(self_check(), ensure_ascii=False))
