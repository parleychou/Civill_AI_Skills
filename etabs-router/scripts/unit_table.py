# -*- coding: utf-8 -*-
"""ETABS present-unit codes used by SapModel.InitializeNewModel and GetPresentUnits.

The names match the ETABS API enumeration. A new model in this skill uses
N_mm_C (9). An existing model keeps the code GetPresentUnits already reports.
"""

from __future__ import annotations

import json


UNIT_CODES = (
    (1, "lb_in_F"),
    (2, "lb_ft_F"),
    (3, "kip_in_F"),
    (4, "kip_ft_F"),
    (5, "kN_mm_C"),
    (6, "kN_m_C"),
    (7, "kgf_mm_C"),
    (8, "kgf_m_C"),
    (9, "N_mm_C"),
    (10, "N_m_C"),
    (11, "Ton_mm_C"),
    (12, "Ton_m_C"),
    (13, "kN_cm_C"),
    (14, "kgf_cm_C"),
    (15, "N_cm_C"),
    (16, "Ton_cm_C"),
)
NEW_MODEL_UNIT = 9


def table() -> list[dict]:
    return [{"code": code, "name": name} for code, name in UNIT_CODES]


def self_check() -> dict:
    rows = table()
    codes = [row["code"] for row in rows]
    names = [row["name"] for row in rows]
    if codes != list(range(1, 17)):
        raise RuntimeError("unit codes must be 1 through 16")
    if len(set(names)) != 16:
        raise RuntimeError("unit names must be unique")
    if dict(UNIT_CODES)[NEW_MODEL_UNIT] != "N_mm_C":
        raise RuntimeError("new models use N_mm_C")
    return {
        "status": "ok",
        "self_check": True,
        "new_model_unit": {"code": NEW_MODEL_UNIT, "name": "N_mm_C"},
        "count": len(rows),
    }


if __name__ == "__main__":
    print(json.dumps({"units": table(), **self_check()}, ensure_ascii=False))
