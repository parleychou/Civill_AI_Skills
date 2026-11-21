"""Normalize and structurally validate an Abaqus analysis_spec JSON document."""

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
_COMMON_FORBIDDEN_NAME_CHARACTERS = {".", '"', "\\"}
_MODEL_FORBIDDEN_NAME_CHARACTERS = set("$&*~!()[]{}|;'`\u201c\u201d,.?/\\><")
_JOB_FORBIDDEN_NAME_CHARACTERS = _MODEL_FORBIDDEN_NAME_CHARACTERS | {" ", ":"}


def _issue(code: str, path: str, message: str) -> dict[str, str]:
    """构造带错误码、JSON 路径和说明的统一问题记录。"""
    return {"code": code, "path": path, "message": message}


def _schema() -> dict[str, Any]:
    """读取并解析技能内置的 ``analysis_spec`` JSON Schema。"""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _validate_string(
    value: Any,
    path: str,
    errors: list[dict[str, str]],
) -> str | Any:
    """校验必填字符串并返回去除首尾空白后的值。"""
    if not isinstance(value, str) or not value.strip():
        errors.append(_issue("INVALID_STRING", path, "must be a non-empty string"))
        return value
    return value.strip()


def _validate_abaqus_name(
    value: Any,
    path: str,
    errors: list[dict[str, str]],
    *,
    kind: str = "object",
) -> str | Any:
    """按 Abaqus/CAE 2024 规则校验用户可见对象名。"""
    if not isinstance(value, str) or not value.strip():
        return value
    name = value.strip()
    reasons: list[str] = []
    maximum = (
        80 if kind in {"model", "part", "instance", "set", "surface", "feature", "job"} else 38
    )
    if value != name:
        reasons.append("must not begin or end with a space")
    if name.startswith("_") or name.endswith("_"):
        reasons.append("must not begin or end with an underscore")
    if name[0].isdigit() and kind not in {"model", "job"}:
        reasons.append("must not begin with a number")
    if name.casefold() == "assembly":
        reasons.append("'Assembly' is reserved by Abaqus/CAE")
    forbidden = set(_COMMON_FORBIDDEN_NAME_CHARACTERS)
    if kind == "model":
        forbidden |= _MODEL_FORBIDDEN_NAME_CHARACTERS
    elif kind == "job":
        forbidden |= _JOB_FORBIDDEN_NAME_CHARACTERS
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
        errors.append(
            _issue(
                "INVALID_ABAQUS_NAME",
                path,
                "; ".join(reasons),
            )
        )
    return name


def _validate_object_shape(
    value: Any,
    *,
    path: str,
    definition: dict[str, Any],
    errors: list[dict[str, str]],
) -> Any:
    """依据 schema 定义递归校验对象字段、必填项和附加属性。"""
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

    normalized = copy.deepcopy(value)
    for key in (
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
    ):
        if key in normalized:
            normalized[key] = _validate_string(normalized[key], f"{path}.{key}", errors)
    return normalized


def normalize_analysis_spec(raw: Any) -> dict[str, Any]:
    """规范化分析规格并返回确定性报告，不补造缺失工程数据。"""
    schema = _schema()
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not isinstance(raw, dict):
        return {
            "status": "FAIL",
            "errors": [_issue("INVALID_TYPE", "$", "analysis_spec must be a JSON object")],
            "warnings": [],
            "analysis_spec": raw,
        }

    normalized = copy.deepcopy(raw)
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
                "UNSUPPORTED_SCHEMA_VERSION", "$.schema_version", "expected schema_version '1.0'"
            )
        )

    if "analysis_type" in raw:
        analysis_type = _validate_string(raw["analysis_type"], "$.analysis_type", errors)
        if isinstance(analysis_type, str) and analysis_type:
            analysis_schema = schema["properties"]["analysis_type"]
            canonical = {item.casefold(): item for item in analysis_schema["enum"]}
            aliases = {
                alias.strip().casefold(): target
                for alias, target in analysis_schema.get("x-aliases", {}).items()
            }
            key = analysis_type.casefold()
            if key in canonical:
                normalized["analysis_type"] = canonical[key]
            elif key in aliases:
                normalized["analysis_type"] = aliases[key]
                warnings.append(
                    _issue(
                        "ANALYSIS_TYPE_ALIAS_NORMALIZED",
                        "$.analysis_type",
                        f"normalized '{analysis_type}' to '{aliases[key]}'",
                    )
                )

            elif key == "contact" or analysis_type in {"接触", "接触分析"}:
                errors.append(
                    _issue(
                        "CONTACT_IS_NOT_A_PROCEDURE",
                        "$.analysis_type",
                        "choose the solver procedure and declare contact in $.connections",
                    )
                )
            else:
                supported = ", ".join(analysis_schema["enum"])
                errors.append(
                    _issue(
                        "UNSUPPORTED_ANALYSIS_TYPE",
                        "$.analysis_type",
                        f"unsupported value; choose one of: {supported}",
                    )
                )

    for field, kind in (("model_name", "model"), ("job_name", "job")):
        if field in raw:
            normalized[field] = _validate_abaqus_name(
                raw[field],
                f"$.{field}",
                errors,
                kind=kind,
            )

    if "units" in raw:
        units_schema = schema["$defs"]["units"]
        normalized["units"] = _validate_object_shape(
            raw["units"], path="$.units", definition=units_schema, errors=errors
        )
        if isinstance(normalized["units"], dict):
            for key in units_schema["required"]:
                if key in normalized["units"]:
                    normalized["units"][key] = _validate_string(
                        normalized["units"][key], f"$.units.{key}", errors
                    )

    for list_name, definition_name in LIST_DEFINITIONS.items():
        if list_name not in raw:
            continue
        items = raw[list_name]
        if not isinstance(items, list):
            errors.append(_issue("INVALID_TYPE", f"$.{list_name}", "must be an array"))
            continue
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
        normalized_items = []
        seen_ids: set[str] = set()
        for index, item in enumerate(items):
            path = f"$.{list_name}[{index}]"
            normalized_item = _validate_object_shape(
                item, path=path, definition=definition, errors=errors
            )
            normalized_items.append(normalized_item)
            if not isinstance(normalized_item, dict):
                continue
            if list_name in ABAQUS_ID_KINDS and "id" in item:
                normalized_item["id"] = _validate_abaqus_name(
                    item["id"],
                    f"{path}.id",
                    errors,
                    kind=ABAQUS_ID_KINDS[list_name],
                )
            item_id = normalized_item.get("id")
            if isinstance(item_id, str) and item_id:
                duplicate_key = item_id.casefold() if list_name in ABAQUS_ID_KINDS else item_id
                if duplicate_key in seen_ids:
                    errors.append(
                        _issue(
                            "DUPLICATE_ID",
                            f"{path}.id",
                            f"duplicate id '{item_id}' within {list_name}",
                        )
                    )
                seen_ids.add(duplicate_key)
            if list_name == "geometry" and isinstance(normalized_item.get("regions"), list):
                normalized_item["regions"] = [
                    _validate_abaqus_name(
                        region,
                        f"{path}.regions[{region_index}]",
                        errors,
                        kind="set",
                    )
                    for region_index, region in enumerate(normalized_item["regions"])
                ]
            if list_name == "outputs" and "variables" in normalized_item:
                variables = normalized_item["variables"]
                if not isinstance(variables, list) or not variables:
                    errors.append(
                        _issue(
                            "INVALID_VARIABLES", f"{path}.variables", "must be a non-empty array"
                        )
                    )
                elif any(not isinstance(item, str) or not item.strip() for item in variables):
                    errors.append(
                        _issue(
                            "INVALID_VARIABLES",
                            f"{path}.variables",
                            "every output variable must be a non-empty string",
                        )
                    )
                else:
                    normalized_item["variables"] = [item.strip().upper() for item in variables]
            if list_name == "connections" and "regions" in normalized_item:
                regions = normalized_item["regions"]
                if not isinstance(regions, list):
                    errors.append(_issue("INVALID_TYPE", f"{path}.regions", "must be an array"))
                else:
                    region_definition = schema["$defs"]["connectionRegion"]
                    normalized_item["regions"] = [
                        _validate_object_shape(
                            region,
                            path=f"{path}.regions[{region_index}]",
                            definition=region_definition,
                            errors=errors,
                        )
                        for region_index, region in enumerate(regions)
                    ]
                    for region_index, region in enumerate(normalized_item["regions"]):
                        if isinstance(region, dict) and "name" in region:
                            region["name"] = _validate_abaqus_name(
                                region["name"],
                                f"{path}.regions[{region_index}].name",
                                errors,
                                kind="surface",
                            )
            if list_name == "mesh":
                if "element_library" in normalized_item:
                    library = _validate_string(
                        normalized_item["element_library"],
                        f"{path}.element_library",
                        errors,
                    )
                    if isinstance(library, str) and library:
                        library = library.upper()
                        normalized_item["element_library"] = library
                        libraries = definition["properties"]["element_library"]["enum"]
                        if library not in libraries:
                            errors.append(
                                _issue(
                                    "INVALID_ELEMENT_LIBRARY",
                                    f"{path}.element_library",
                                    "must be one of: " + ", ".join(libraries),
                                )
                            )
                if "element_types" in normalized_item:
                    element_types = normalized_item["element_types"]
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
                    else:
                        normalized_item["element_types"] = [
                            item.strip().upper() for item in element_types
                        ]
            if list_name == "acceptance_criteria" and "operator" in normalized_item:
                operators = definition["properties"]["operator"]["enum"]
                if normalized_item["operator"] not in operators:
                    errors.append(
                        _issue(
                            "INVALID_OPERATOR",
                            f"{path}.operator",
                            "must be one of: " + ", ".join(operators),
                        )
                    )
        normalized[list_name] = normalized_items

    status = "FAIL" if errors else ("WARN" if warnings else "PASS")
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "analysis_spec": normalized,
    }
