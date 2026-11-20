"""Shape an analysis_spec document against the skill schema.

The schema lives at references/analysis-spec.schema.json. This module checks
structure and Abaqus/CAE object names. It does not fill in missing materials,
units, boundary conditions, contact, nlgeom, or acceptance limits.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).parents[1] / "references" / "analysis-spec.schema.json"

LIST_DEFINITIONS = {
    "materials": "material",
    "geometry": "geometry",
    "steps": "step",
    "boundary_conditions": "boundaryCondition",
    "connections": "connection",
    "loads": "load",
    "mesh": "mesh",
    "outputs": "output",
    "acceptance_criteria": "acceptanceCriterion",
}
ABAQUS_ID_KINDS = {
    "materials": "object",
    "geometry": "part",
    "steps": "object",
    "boundary_conditions": "object",
    "connections": "object",
    "loads": "object",
    "outputs": "object",
}
STRING_FIELDS = (
    "id",
    "kind",
    "source",
    "step",
    "region",
    "metric",
    "operator",
    "previous",
    "geometry",
    "name",
    "role",
)
_COMMON_FORBIDDEN = {".", '"', "\\"}
_MODEL_FORBIDDEN = set("$&*~!()[]{}|;'`\u201c\u201d,.?/\\><")
_JOB_FORBIDDEN = _MODEL_FORBIDDEN | {" ", ":"}
_LONG_NAME_KINDS = {"model", "part", "instance", "set", "surface", "feature", "job"}


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    return {"code": code, "path": path, "message": message}


def _load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _require_text(value: Any, path: str, errors: list[dict[str, str]]) -> str | Any:
    if not isinstance(value, str) or not value.strip():
        errors.append(_issue("INVALID_STRING", path, "must be a non-empty string"))
        return value
    return value.strip()


def _check_cae_name(
    value: Any,
    path: str,
    errors: list[dict[str, str]],
    *,
    kind: str = "object",
) -> str | Any:
    """Apply Abaqus/CAE naming limits. A repository that accepts a name is not enough."""
    if not isinstance(value, str) or not value.strip():
        return value
    name = value.strip()
    reasons: list[str] = []
    maximum = 80 if kind in _LONG_NAME_KINDS else 38
    if value != name:
        reasons.append("must not begin or end with a space")
    if name.startswith("_") or name.endswith("_"):
        reasons.append("must not begin or end with an underscore")
    if name[0].isdigit() and kind not in {"model", "job"}:
        reasons.append("must not begin with a number")
    if name.casefold() == "assembly":
        reasons.append("'Assembly' is reserved by Abaqus/CAE")
    forbidden = set(_COMMON_FORBIDDEN)
    if kind == "model":
        forbidden |= _MODEL_FORBIDDEN
    elif kind == "job":
        forbidden |= _JOB_FORBIDDEN
        if name.startswith("-"):
            reasons.append("job names must not begin with a dash")
    present = sorted(character for character in forbidden if character in name)
    if present:
        reasons.append(
            "contains forbidden character(s): " + " ".join(repr(item) for item in present)
        )
    if len(name) > maximum:
        reasons.append(f"exceeds the {maximum}-character limit for {kind} names")
    if reasons:
        errors.append(_issue("INVALID_ABAQUS_NAME", path, "; ".join(reasons)))
    return name


def _shape_object(
    value: Any,
    *,
    path: str,
    definition: dict[str, Any],
    errors: list[dict[str, str]],
) -> Any:
    if not isinstance(value, dict):
        errors.append(_issue("INVALID_TYPE", path, "must be an object"))
        return value
    allowed = set(definition.get("properties", {}))
    for key in sorted(set(value) - allowed):
        errors.append(
            _issue("UNKNOWN_FIELD", f"{path}.{key}", "field is not defined by analysis_spec 1.0")
        )
    for key in definition.get("required", []):
        if key not in value:
            errors.append(_issue("MISSING_FIELD", f"{path}.{key}", "required field is missing"))
    shaped = copy.deepcopy(value)
    for key in STRING_FIELDS:
        if key in shaped:
            shaped[key] = _require_text(shaped[key], f"{path}.{key}", errors)
    return shaped


def _shape_analysis_type(
    raw: dict[str, Any],
    shaped: dict[str, Any],
    schema: dict[str, Any],
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
) -> None:
    if "analysis_type" not in raw:
        return
    analysis_type = _require_text(raw["analysis_type"], "$.analysis_type", errors)
    if not isinstance(analysis_type, str) or not analysis_type:
        return
    analysis_schema = schema["properties"]["analysis_type"]
    canonical = {item.casefold(): item for item in analysis_schema["enum"]}
    aliases = {
        alias.strip().casefold(): target
        for alias, target in analysis_schema.get("x-aliases", {}).items()
    }
    key = analysis_type.casefold()
    if key in canonical:
        shaped["analysis_type"] = canonical[key]
        return
    if key in aliases:
        shaped["analysis_type"] = aliases[key]
        warnings.append(
            _issue(
                "ANALYSIS_TYPE_ALIAS_NORMALIZED",
                "$.analysis_type",
                f"normalized '{analysis_type}' to '{aliases[key]}'",
            )
        )
        return
    if key == "contact" or analysis_type in {"接触", "接触分析"}:
        errors.append(
            _issue(
                "CONTACT_IS_NOT_A_PROCEDURE",
                "$.analysis_type",
                "choose the solver procedure and declare contact in $.connections",
            )
        )
        return
    supported = ", ".join(analysis_schema["enum"])
    errors.append(
        _issue(
            "UNSUPPORTED_ANALYSIS_TYPE",
            "$.analysis_type",
            f"unsupported value; choose one of: {supported}",
        )
    )


def _remember_id(
    list_name: str,
    item: Any,
    shaped_item: dict[str, Any],
    path: str,
    seen_ids: set[str],
    errors: list[dict[str, str]],
) -> None:
    if list_name in ABAQUS_ID_KINDS and isinstance(item, dict) and "id" in item:
        shaped_item["id"] = _check_cae_name(
            item["id"], f"{path}.id", errors, kind=ABAQUS_ID_KINDS[list_name]
        )
    item_id = shaped_item.get("id")
    if not isinstance(item_id, str) or not item_id:
        return
    duplicate_key = item_id.casefold() if list_name in ABAQUS_ID_KINDS else item_id
    if duplicate_key in seen_ids:
        errors.append(
            _issue("DUPLICATE_ID", f"{path}.id", f"duplicate id '{item_id}' within {list_name}")
        )
    seen_ids.add(duplicate_key)


def _shape_geometry_regions(
    shaped_item: dict[str, Any], path: str, errors: list[dict[str, str]]
) -> None:
    if not isinstance(shaped_item.get("regions"), list):
        return
    shaped_item["regions"] = [
        _check_cae_name(region, f"{path}.regions[{index}]", errors, kind="set")
        for index, region in enumerate(shaped_item["regions"])
    ]


def _shape_output_variables(
    shaped_item: dict[str, Any], path: str, errors: list[dict[str, str]]
) -> None:
    if "variables" not in shaped_item:
        return
    variables = shaped_item["variables"]
    if not isinstance(variables, list) or not variables:
        errors.append(_issue("INVALID_VARIABLES", f"{path}.variables", "must be a non-empty array"))
        return
    if any(not isinstance(item, str) or not item.strip() for item in variables):
        errors.append(
            _issue(
                "INVALID_VARIABLES",
                f"{path}.variables",
                "every output variable must be a non-empty string",
            )
        )
        return
    shaped_item["variables"] = [item.strip().upper() for item in variables]


def _shape_connection_regions(
    shaped_item: dict[str, Any],
    path: str,
    schema: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    if "regions" not in shaped_item:
        return
    regions = shaped_item["regions"]
    if not isinstance(regions, list):
        errors.append(_issue("INVALID_TYPE", f"{path}.regions", "must be an array"))
        return
    definition = schema["$defs"]["connectionRegion"]
    shaped_item["regions"] = [
        _shape_object(
            region,
            path=f"{path}.regions[{index}]",
            definition=definition,
            errors=errors,
        )
        for index, region in enumerate(regions)
    ]
    for index, region in enumerate(shaped_item["regions"]):
        if isinstance(region, dict) and "name" in region:
            region["name"] = _check_cae_name(
                region["name"],
                f"{path}.regions[{index}].name",
                errors,
                kind="surface",
            )


def _shape_mesh_item(
    shaped_item: dict[str, Any],
    path: str,
    definition: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    if "element_library" in shaped_item:
        library = _require_text(
            shaped_item["element_library"], f"{path}.element_library", errors
        )
        if isinstance(library, str) and library:
            library = library.upper()
            shaped_item["element_library"] = library
            libraries = definition["properties"]["element_library"]["enum"]
            if library not in libraries:
                errors.append(
                    _issue(
                        "INVALID_ELEMENT_LIBRARY",
                        f"{path}.element_library",
                        "must be one of: " + ", ".join(libraries),
                    )
                )
    if "element_types" not in shaped_item:
        return
    element_types = shaped_item["element_types"]
    if not isinstance(element_types, list) or any(
        not isinstance(item, str) or not item.strip() for item in element_types
    ):
        errors.append(
            _issue(
                "INVALID_ELEMENT_TYPES",
                f"{path}.element_types",
                "must be an array of non-empty strings",
            )
        )
        return
    shaped_item["element_types"] = [item.strip().upper() for item in element_types]


def _shape_operator(
    shaped_item: dict[str, Any],
    path: str,
    definition: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    if "operator" not in shaped_item:
        return
    operators = definition["properties"]["operator"]["enum"]
    if shaped_item["operator"] not in operators:
        errors.append(
            _issue(
                "INVALID_OPERATOR",
                f"{path}.operator",
                "must be one of: " + ", ".join(operators),
            )
        )


def _shape_list(
    list_name: str,
    definition_name: str,
    raw: dict[str, Any],
    shaped: dict[str, Any],
    schema: dict[str, Any],
    errors: list[dict[str, str]],
) -> None:
    if list_name not in raw:
        return
    items = raw[list_name]
    if not isinstance(items, list):
        errors.append(_issue("INVALID_TYPE", f"$.{list_name}", "must be an array"))
        return
    minimum = schema["properties"][list_name].get("minItems", 0)
    if len(items) < minimum:
        errors.append(
            _issue(
                "TOO_FEW_ITEMS",
                f"$.{list_name}",
                f"must contain at least {minimum} item(s)",
            )
        )
    definition = schema["$defs"][definition_name]
    shaped_items = []
    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        path = f"$.{list_name}[{index}]"
        shaped_item = _shape_object(item, path=path, definition=definition, errors=errors)
        shaped_items.append(shaped_item)
        if not isinstance(shaped_item, dict):
            continue
        _remember_id(list_name, item, shaped_item, path, seen_ids, errors)
        if list_name == "geometry":
            _shape_geometry_regions(shaped_item, path, errors)
        elif list_name == "outputs":
            _shape_output_variables(shaped_item, path, errors)
        elif list_name == "connections":
            _shape_connection_regions(shaped_item, path, schema, errors)
        elif list_name == "mesh":
            _shape_mesh_item(shaped_item, path, definition, errors)
        elif list_name == "acceptance_criteria":
            _shape_operator(shaped_item, path, definition, errors)
    shaped[list_name] = shaped_items


def shape_document(raw: Any) -> dict[str, Any]:
    """Return status, errors, warnings, and the shaped analysis_spec."""
    schema = _load_schema()
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not isinstance(raw, dict):
        return {
            "status": "FAIL",
            "errors": [_issue("INVALID_TYPE", "$", "analysis_spec must be a JSON object")],
            "warnings": [],
            "analysis_spec": raw,
        }

    shaped = copy.deepcopy(raw)
    allowed_top = set(schema["properties"])
    for key in sorted(set(raw) - allowed_top):
        errors.append(
            _issue("UNKNOWN_FIELD", f"$.{key}", "field is not defined by analysis_spec 1.0")
        )
    for key in schema["required"]:
        if key not in raw:
            errors.append(_issue("MISSING_FIELD", f"$.{key}", "required field is missing"))
    if "schema_version" in raw and raw["schema_version"] != "1.0":
        errors.append(
            _issue(
                "UNSUPPORTED_SCHEMA_VERSION",
                "$.schema_version",
                "expected schema_version '1.0'",
            )
        )
    _shape_analysis_type(raw, shaped, schema, errors, warnings)
    for field, kind in (("model_name", "model"), ("job_name", "job")):
        if field in raw:
            shaped[field] = _check_cae_name(raw[field], f"$.{field}", errors, kind=kind)
    if "units" in raw:
        units_schema = schema["$defs"]["units"]
        shaped["units"] = _shape_object(
            raw["units"], path="$.units", definition=units_schema, errors=errors
        )
        if isinstance(shaped["units"], dict):
            for key in units_schema["required"]:
                if key in shaped["units"]:
                    shaped["units"][key] = _require_text(
                        shaped["units"][key], f"$.units.{key}", errors
                    )
    for list_name, definition_name in LIST_DEFINITIONS.items():
        _shape_list(list_name, definition_name, raw, shaped, schema, errors)
    if errors:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "analysis_spec": shaped,
    }
