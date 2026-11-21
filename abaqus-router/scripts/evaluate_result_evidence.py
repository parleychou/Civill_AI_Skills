"""Evaluate Abaqus result evidence against sourced analysis_spec criteria."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

from preflight_analysis_spec import semantic_preflight


def _token(value: Any) -> str:
    """将任意值规范为仅含数字、英文和中文的比较词元。"""
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(value or "").casefold())


def _norm(vector: list[float]) -> float:
    """计算三维或任意长度数值向量的欧氏范数。"""
    return math.sqrt(sum(float(value) ** 2 for value in vector))


def _relative_change(current: float, previous: float) -> float:
    """计算两个数值相对于较大绝对值的稳定相对变化。"""
    scale = max(abs(float(current)), abs(float(previous)), 1.0e-30)
    return abs(float(current) - float(previous)) / scale


def _numeric_vector(value: Any) -> bool:
    """判断值是否为恰含三个非布尔数值的向量。"""
    return (
        isinstance(value, list)
        and len(value) == 3
        and all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)
    )


def _compare(value: Any, operator: str, limit: Any) -> tuple[bool, str]:
    """按验收操作符比较计算值与阈值，并返回结果及错误说明。"""
    if operator == "review":
        return False, "operator 'review' requires human judgment and cannot pass automatically"
    if operator == "between":
        if not (
            isinstance(value, (int, float))
            and isinstance(limit, list)
            and len(limit) == 2
            and all(isinstance(item, (int, float)) for item in limit)
        ):
            return False, "between requires a numeric value and [lower, upper] limit"
        return limit[0] <= value <= limit[1], ""
    if operator == "approximately":
        if not (isinstance(value, (int, float)) and isinstance(limit, dict)):
            return False, "approximately requires numeric value and {target, tolerance} limit"
        target = limit.get("target")
        tolerance = limit.get("tolerance")
        if not isinstance(target, (int, float)) or not isinstance(tolerance, (int, float)):
            return False, "approximately limit needs numeric target and tolerance"
        return abs(value - target) <= tolerance, ""
    operations = {
        "<": lambda left, right: left < right,
        "<=": lambda left, right: left <= right,
        "==": lambda left, right: left == right,
        ">=": lambda left, right: left >= right,
        ">": lambda left, right: left > right,
    }
    if operator not in operations:
        return False, f"unsupported operator: {operator}"
    try:
        return bool(operations[operator](value, limit)), ""
    except (TypeError, ValueError) as error:
        return False, str(error)


class EvidenceEvaluator:
    def __init__(self, analysis_spec: dict[str, Any], evidence: dict[str, Any]):
        """保存分析规格和结果证据，并建立验收准则索引。"""
        self.spec = analysis_spec
        self.evidence = evidence
        self.gates: list[dict[str, Any]] = []
        self.criteria = {item["id"]: item for item in analysis_spec.get("acceptance_criteria", [])}

    def environment_limitation(self, gate_id: str) -> tuple[dict[str, Any] | None, list[str]]:
        """查找并校验某门禁对应的、具有充分证据的环境限制记录。"""
        limitations = self.evidence.get("environment_limitations", [])
        if not isinstance(limitations, list):
            return None, ["environment_limitations must be an array"]
        for limitation in limitations:
            if not isinstance(limitation, dict) or gate_id not in limitation.get("gate_ids", []):
                continue
            errors: list[str] = []
            for name in ("capability", "reason"):
                if not str(limitation.get(name) or "").strip():
                    errors.append(f"{name} must be non-empty")
            environment = limitation.get("environment")
            if not isinstance(environment, dict):
                errors.append("environment must be an object")
            else:
                for name in ("abaqus_version", "runtime_mode"):
                    if not str(environment.get(name) or "").strip():
                        errors.append(f"environment.{name} must be non-empty")
            attempts = limitation.get("attempts")
            if not isinstance(attempts, list) or len(attempts) < 2:
                errors.append("at least two controlled attempts are required")
            else:
                for index, attempt in enumerate(attempts):
                    if not isinstance(attempt, dict):
                        errors.append(f"attempts[{index}] must be an object")
                        continue
                    for name in ("configuration", "result", "diagnostic"):
                        if not str(attempt.get(name) or "").strip():
                            errors.append(f"attempts[{index}].{name} must be non-empty")
            alternatives = limitation.get("alternative_evidence")
            if not isinstance(alternatives, list) or not alternatives:
                errors.append("alternative_evidence must be a non-empty array")
            return (limitation if not errors else None), errors
        return None, []

    def add_missing_or_environment_blocked(self, gate_id: str, message: str) -> bool:
        """将缺失证据记录为失败，或在证据充分时记录为环境阻塞。"""
        limitation, errors = self.environment_limitation(gate_id)
        if limitation is not None:
            self.add(
                gate_id,
                "BLOCKED_BY_ENVIRONMENT",
                "required evidence is unavailable in the recorded Abaqus environment; this is not a pass",
                evidence=[limitation],
            )
            return True
        self.add(
            gate_id,
            "FAIL",
            message,
            evidence=errors,
        )
        return False

    def add(
        self,
        gate_id: str,
        status: str,
        message: str,
        *,
        metrics: dict[str, Any] | None = None,
        evidence: list[Any] | None = None,
        criterion_id: str | None = None,
    ) -> None:
        """向结果门禁列表追加状态、指标、证据和关联准则。"""
        self.gates.append(
            {
                "id": gate_id,
                "status": status,
                "message": message,
                "metrics": metrics or {},
                "evidence": [str(item) for item in (evidence or [])],
                "criterion_id": criterion_id,
            }
        )

    def evaluate_metric(
        self,
        gate_id: str,
        value: float,
        criterion_id: Any,
        expected_metric: str,
        *,
        unit: str = "1",
        evidence: list[Any] | None = None,
    ) -> bool:
        """用指定验收准则评价计算指标，并记录门禁结果。"""
        if not isinstance(criterion_id, str) or criterion_id not in self.criteria:
            self.add(
                gate_id,
                "FAIL",
                "a matching acceptance criterion id is required",
                metrics={expected_metric: value, "unit": unit},
                evidence=evidence,
                criterion_id=str(criterion_id) if criterion_id is not None else None,
            )
            return False
        criterion = self.criteria[criterion_id]
        if _token(criterion.get("metric")) != _token(expected_metric):
            self.add(
                gate_id,
                "FAIL",
                "criterion metric does not match the computed metric",
                metrics={expected_metric: value, "unit": unit},
                evidence=[criterion.get("metric"), *(evidence or [])],
                criterion_id=criterion_id,
            )
            return False
        if not str(criterion.get("source") or "").strip():
            self.add(
                gate_id,
                "FAIL",
                "acceptance threshold has no source; defaults cannot become design allowables",
                metrics={expected_metric: value, "unit": unit},
                evidence=evidence,
                criterion_id=criterion_id,
            )
            return False
        passed, error = _compare(value, criterion.get("operator"), criterion.get("limit"))
        self.add(
            gate_id,
            "PASS" if passed else "FAIL",
            error
            or (
                "computed metric satisfies criterion"
                if passed
                else "computed metric violates criterion"
            ),
            metrics={
                expected_metric: value,
                "unit": unit,
                "operator": criterion.get("operator"),
                "limit": criterion.get("limit"),
            },
            evidence=evidence,
            criterion_id=criterion_id,
        )
        return passed

    def check_provenance(self) -> None:
        """检查 ODB、Step、Frame、区域、坐标系和提取器等证据来源。"""
        provenance = self.evidence.get("provenance")
        required = (
            "odb_paths",
            "step",
            "frames",
            "regions",
            "coordinate_system",
            "position",
            "averaging",
            "extractor",
        )
        if not isinstance(provenance, dict):
            self.add("evidence.provenance", "FAIL", "result evidence provenance is missing")
            return
        missing = [name for name in required if name not in provenance]
        if not provenance.get("odb_paths"):
            missing.append("odb_paths(non-empty)")
        if not provenance.get("frames"):
            missing.append("frames(non-empty)")
        self.add(
            "evidence.provenance",
            "FAIL" if missing else "PASS",
            "record ODB, step/frame, region, coordinate system, position, averaging, and extractor",
            evidence=missing or [provenance],
        )

    def check_solver(self) -> None:
        """检查求解器是否正常完成，以及错误和警告数量。"""
        solver = self.evidence.get("solver")
        if not isinstance(solver, dict):
            self.add("solver.terminal_state", "FAIL", "solver evidence is missing")
            return
        state = str(solver.get("terminal_state") or "").upper()
        errors = solver.get("analysis_errors")
        warnings = solver.get("analysis_warnings")
        if state != "COMPLETED" or not isinstance(errors, int) or errors != 0:
            self.add(
                "solver.terminal_state",
                "FAIL",
                "solver must be COMPLETED with zero analysis errors",
                metrics={"terminal_state": state, "analysis_errors": errors},
                evidence=solver.get("diagnostic_lines", []),
            )
        elif isinstance(warnings, int) and warnings > 0:
            self.add(
                "solver.terminal_state",
                "WARN",
                "solver completed but analysis warnings require review",
                metrics={"terminal_state": state, "analysis_warnings": warnings},
                evidence=solver.get("diagnostic_lines", []),
            )
        else:
            self.add(
                "solver.terminal_state",
                "PASS",
                "solver completed with zero reported analysis errors and warnings",
                metrics={
                    "terminal_state": state,
                    "analysis_errors": errors,
                    "analysis_warnings": warnings,
                },
            )

    def check_equilibrium(self) -> None:
        """重新计算力与力矩平衡误差，并按对应准则评价。"""
        equilibrium = self.evidence.get("equilibrium")
        if not isinstance(equilibrium, dict):
            self.add(
                "equilibrium.force",
                "FAIL",
                "force-balance evidence is required for this analysis profile",
            )
            self.add(
                "equilibrium.moment",
                "FAIL",
                "moment-balance evidence about a declared reference point is required",
            )
            return
        vector_names = ("applied_force", "reaction_force", "applied_moment", "reaction_moment")
        invalid = [name for name in vector_names if not _numeric_vector(equilibrium.get(name))]
        if not _numeric_vector(equilibrium.get("reference_point")):
            invalid.append("reference_point")
        if invalid:
            self.add(
                "equilibrium.force",
                "FAIL",
                "equilibrium vectors must have three numeric components",
                evidence=invalid,
            )
            self.add(
                "equilibrium.moment",
                "FAIL",
                "equilibrium vectors must have three numeric components",
                evidence=invalid,
            )
            return

        force_residual = [
            float(left) + float(right)
            for left, right in zip(equilibrium["applied_force"], equilibrium["reaction_force"])
        ]
        force_scale = max(
            _norm(equilibrium["applied_force"]),
            _norm(equilibrium["reaction_force"]),
            float(equilibrium.get("characteristic_force") or 0.0),
        )
        force_error = _norm(force_residual) / force_scale if force_scale > 0 else math.inf
        self.evaluate_metric(
            "equilibrium.force",
            force_error,
            equilibrium.get("force_criterion_id"),
            "force_balance_relative_error",
            evidence=[force_residual, f"scale={force_scale}"],
        )

        moment_residual = [
            float(left) + float(right)
            for left, right in zip(equilibrium["applied_moment"], equilibrium["reaction_moment"])
        ]
        moment_scale = max(
            _norm(equilibrium["applied_moment"]),
            _norm(equilibrium["reaction_moment"]),
            float(equilibrium.get("characteristic_moment") or 0.0),
        )
        moment_error = _norm(moment_residual) / moment_scale if moment_scale > 0 else math.inf
        self.evaluate_metric(
            "equilibrium.moment",
            moment_error,
            equilibrium.get("moment_criterion_id"),
            "moment_balance_relative_error",
            evidence=[moment_residual, f"scale={moment_scale}", equilibrium["reference_point"]],
        )

    def check_energy(self) -> None:
        """用显式分析能量历程计算能量漂移和能量比例门禁。"""
        energy = self.evidence.get("energy")
        if not isinstance(energy, dict):
            self.add("energy.balance", "FAIL", "explicit analysis requires energy-history evidence")
            return
        series = energy.get("series", {})
        criteria = energy.get("criteria", {})
        required = ("ALLKE", "ALLIE", "ETOTAL")
        missing = [
            name for name in required if not isinstance(series.get(name), list) or not series[name]
        ]
        if missing:
            self.add(
                "energy.balance",
                "FAIL",
                "required explicit energy histories are missing",
                evidence=missing,
            )
            return
        numeric_series = {
            name: [float(value) for value in values]
            for name, values in series.items()
            if isinstance(values, list)
            and values
            and all(
                isinstance(value, (int, float)) and not isinstance(value, bool) for value in values
            )
        }
        if any(name not in numeric_series for name in required):
            self.add(
                "energy.balance", "FAIL", "energy histories must be numeric", evidence=required
            )
            return
        scale = max(
            (
                abs(internal) + abs(kinetic)
                for internal, kinetic in zip(numeric_series["ALLIE"], numeric_series["ALLKE"])
            ),
            default=0.0,
        )
        total = numeric_series["ETOTAL"]
        drift = max(abs(value - total[0]) for value in total) / scale if scale > 0 else math.inf
        self.evaluate_metric(
            "energy.balance",
            drift,
            criteria.get("energy_balance_relative_error"),
            "energy_balance_relative_error",
            evidence=[f"energy_scale={scale}"],
        )
        if "ALLAE" in numeric_series:
            internal_scale = max((abs(value) for value in numeric_series["ALLIE"]), default=0.0)
            ratio = (
                max(abs(value) for value in numeric_series["ALLAE"]) / internal_scale
                if internal_scale > 0
                else math.inf
            )
            self.evaluate_metric(
                "energy.artificial",
                ratio,
                criteria.get("artificial_energy_ratio"),
                "artificial_energy_ratio",
            )
        else:
            self.add(
                "energy.artificial",
                "WARN",
                "ALLAE is absent; artificial-energy ratio was not evaluated",
            )
        final_internal = abs(numeric_series["ALLIE"][-1])
        kinetic_ratio = (
            abs(numeric_series["ALLKE"][-1]) / final_internal if final_internal > 0 else math.inf
        )
        criterion_id = criteria.get("kinetic_internal_ratio_final")
        if criterion_id:
            self.evaluate_metric(
                "energy.kinetic_internal",
                kinetic_ratio,
                criterion_id,
                "kinetic_internal_ratio_final",
            )

    def check_contact(self) -> None:
        """检查接触输出可用性、活动状态以及穿透和滑移指标。"""
        contact = self.evidence.get("contact")
        if not isinstance(contact, dict):
            self.add_missing_or_environment_blocked(
                "contact.state",
                "contact evidence is required because contact is declared",
            )
            return
        outputs = {str(item).upper() for item in contact.get("available_outputs", [])}
        if not outputs.intersection({"CSTRESS", "CPRESS", "COPEN", "CDISP", "CSLIP"}):
            blocked = self.add_missing_or_environment_blocked(
                "contact.outputs",
                "no contact status/traction/opening/slip output is available",
            )
            if blocked:
                self.gates[-1]["evidence"].append(str(sorted(outputs)))
        else:
            self.add(
                "contact.outputs",
                "PASS",
                "contact diagnostic output is available",
                evidence=sorted(outputs),
            )
        total = contact.get("total_count")
        active = contact.get("active_count")
        if total is None and active is None:
            self.add_missing_or_environment_blocked(
                "contact.state",
                "contact counts are missing",
            )
            return
        if (
            not isinstance(total, int)
            or not isinstance(active, int)
            or total <= 0
            or not 0 <= active <= total
        ):
            self.add(
                "contact.state", "FAIL", "contact counts are invalid", evidence=[total, active]
            )
            return
        expected = contact.get("expected_state")
        state_ok = {
            "engaged": active > 0,
            "separated": active == 0,
            "mixed": 0 < active < total,
        }.get(expected, False)
        self.add(
            "contact.state",
            "PASS" if state_ok else "FAIL",
            "observed contact activity must match the declared expected state",
            metrics={
                "active_count": active,
                "total_count": total,
                "active_fraction": active / total,
            },
            evidence=[expected],
        )
        criteria = contact.get("criteria", {})
        metric_values = {
            "max_contact_penetration": contact.get("max_penetration"),
            "max_contact_slip": contact.get("max_slip"),
            "min_contact_active_fraction": active / total,
        }
        for metric, criterion_id in criteria.items():
            value = metric_values.get(metric)
            if not isinstance(value, (int, float)):
                self.add(
                    f"contact.{metric}",
                    "FAIL",
                    "contact metric value is missing",
                    criterion_id=criterion_id,
                )
            else:
                self.evaluate_metric(
                    f"contact.{metric}", value, criterion_id, metric, evidence=[expected]
                )

    def check_mesh_convergence(self) -> None:
        """检查粗到细网格序列，并评价最后两级结果的相对变化。"""
        studies = self.evidence.get("mesh_convergence")
        if not isinstance(studies, list) or not studies:
            self.add("mesh.convergence", "FAIL", "at least one mesh-convergence metric is required")
            return
        for index, study in enumerate(studies):
            metric = str(study.get("metric") or f"metric_{index}")
            gate_id = f"mesh.convergence.{metric}"
            samples = study.get("samples")
            if not isinstance(samples, list) or len(samples) < 2:
                self.add(gate_id, "FAIL", "mesh convergence needs at least two levels")
                continue
            valid = all(
                isinstance(item, dict)
                and isinstance(item.get("mesh_size"), (int, float))
                and item["mesh_size"] > 0
                and isinstance(item.get("value"), (int, float))
                for item in samples
            )
            sizes = [item.get("mesh_size") for item in samples]
            if not valid or any(sizes[pos] <= sizes[pos + 1] for pos in range(len(sizes) - 1)):
                self.add(
                    gate_id,
                    "FAIL",
                    "samples must be ordered coarse-to-fine with strictly decreasing mesh_size",
                    evidence=[sizes],
                )
                continue
            change = _relative_change(samples[-1]["value"], samples[-2]["value"])
            self.evaluate_metric(
                gate_id,
                change,
                study.get("criterion_id"),
                f"mesh_convergence.{metric}",
                evidence=[samples[-2:], study.get("region")],
            )

    def check_stress_singularity(self) -> None:
        """比较原始峰值与稳健应力的网格趋势，识别疑似奇异点。"""
        studies = self.evidence.get("stress_singularity")
        if not isinstance(studies, list) or not studies:
            self.add(
                "stress.singularity",
                "FAIL",
                "stress output is claimed but no singularity/robust-stress mesh study is provided",
            )
            return
        for index, study in enumerate(studies):
            region = str(study.get("region") or f"region_{index}")
            gate_id = f"stress.singularity.{region}"
            samples = study.get("samples")
            if not isinstance(samples, list) or len(samples) < 3:
                self.add(gate_id, "FAIL", "singularity assessment needs at least three mesh levels")
                continue
            valid = all(
                isinstance(item.get("mesh_size"), (int, float))
                and item["mesh_size"] > 0
                and isinstance(item.get("raw_max"), (int, float))
                and isinstance(item.get("robust_value"), (int, float))
                for item in samples
            )
            sizes = [item.get("mesh_size") for item in samples]
            if not valid or any(sizes[pos] <= sizes[pos + 1] for pos in range(len(sizes) - 1)):
                self.add(
                    gate_id,
                    "FAIL",
                    "stress samples must be ordered coarse-to-fine",
                    evidence=[sizes],
                )
                continue
            raw_values = [float(item["raw_max"]) for item in samples]
            robust_values = [float(item["robust_value"]) for item in samples]
            raw_change = _relative_change(raw_values[-1], raw_values[-2])
            robust_change = _relative_change(robust_values[-1], robust_values[-2])
            raw_monotonic = all(
                raw_values[pos + 1] >= raw_values[pos] for pos in range(len(raw_values) - 1)
            )
            passed = self.evaluate_metric(
                gate_id,
                robust_change,
                study.get("criterion_id"),
                f"stress_robust_mesh_change.{region}",
                evidence=[samples[-2:]],
            )
            suspected = raw_monotonic and raw_change > robust_change and raw_change > 0.05
            if suspected:
                self.add(
                    f"{gate_id}.raw_max",
                    "WARN" if passed else "FAIL",
                    "raw maximum grows under refinement; do not use it as a design acceptance value",
                    metrics={
                        "raw_last_change": raw_change,
                        "robust_last_change": robust_change,
                        "raw_max_usable": False,
                    },
                    evidence=[study.get("raw_metric"), study.get("robust_metric")],
                )
            else:
                self.add(
                    f"{gate_id}.raw_max",
                    "PASS",
                    "raw and robust stress trends do not show the configured singular pattern",
                    metrics={
                        "raw_last_change": raw_change,
                        "robust_last_change": robust_change,
                        "raw_max_usable": True,
                    },
                )

    def report(self) -> dict[str, Any]:
        """汇总全部门禁状态并生成最终结果证据报告。"""
        counts = {
            status: sum(item["status"] == status for item in self.gates)
            for status in ("PASS", "WARN", "FAIL", "UNSUPPORTED", "BLOCKED_BY_ENVIRONMENT")
        }
        if counts["FAIL"]:
            status = "FAIL"
        elif counts["BLOCKED_BY_ENVIRONMENT"]:
            status = "BLOCKED_BY_ENVIRONMENT"
        else:
            status = "WARN" if counts["WARN"] else "PASS"
        return {"status": status, "summary": counts, "gates": self.gates}


def evaluate_result_evidence(analysis_spec: Any, evidence: Any) -> dict[str, Any]:
    """完成语义预检后，按分析类型执行适用的结果证据门禁。"""
    semantic = semantic_preflight(analysis_spec)
    if semantic["status"] in {"FAIL", "UNSUPPORTED"}:
        return {
            "status": "FAIL",
            "summary": {"PASS": 0, "WARN": 0, "FAIL": 1, "UNSUPPORTED": 0},
            "gates": [
                {
                    "id": "input.semantic_preflight",
                    "status": "FAIL",
                    "message": "analysis_spec must pass semantic preflight before result validation",
                    "metrics": {},
                    "evidence": [
                        f"{item['id']}: {item['message']}"
                        for item in semantic["checks"]
                        if item["status"] in {"FAIL", "UNSUPPORTED"}
                    ],
                    "criterion_id": None,
                }
            ],
        }
    if not isinstance(evidence, dict) or evidence.get("schema_version") != "1.0":
        return {
            "status": "FAIL",
            "summary": {"PASS": 0, "WARN": 0, "FAIL": 1, "UNSUPPORTED": 0},
            "gates": [
                {
                    "id": "evidence.structure",
                    "status": "FAIL",
                    "message": "result evidence must be an object with schema_version '1.0'",
                    "metrics": {},
                    "evidence": [],
                    "criterion_id": None,
                }
            ],
        }

    evaluator = EvidenceEvaluator(semantic["analysis_spec"], evidence)
    evaluator.check_provenance()
    evaluator.check_solver()
    analysis_type = semantic["analysis_spec"]["analysis_type"]
    if analysis_type in {"static", "coupled_temp_displacement"}:
        evaluator.check_equilibrium()
    if analysis_type == "dynamic_explicit":
        evaluator.check_energy()
    has_contact = "contact" in semantic["profiles"]
    if has_contact:
        evaluator.check_contact()
    evaluator.check_mesh_convergence()
    output_variables = {
        str(variable).upper()
        for output in semantic["analysis_spec"].get("outputs", [])
        for variable in output.get("variables", [])
    }
    if "S" in output_variables and analysis_type in {"static", "coupled_temp_displacement"}:
        evaluator.check_stress_singularity()
    for warning in semantic["checks"]:
        if warning["status"] == "WARN":
            evaluator.add(
                f"semantic.{warning['id']}",
                "WARN",
                warning["message"],
                evidence=warning.get("evidence", []),
            )
    return evaluator.report()


def main() -> None:
    """读取分析规格和证据 JSON，输出门禁报告并设置退出码。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis_spec", type=Path)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    try:
        analysis_spec = json.loads(args.analysis_spec.read_text(encoding="utf-8"))
        evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, ensure_ascii=False))
        raise SystemExit(2) from error
    report = evaluate_result_evidence(analysis_spec, evidence)
    print(json.dumps(report, ensure_ascii=False, indent=None if args.compact else 2))
    if report["status"] == "FAIL":
        raise SystemExit(2)
    if report["status"] == "BLOCKED_BY_ENVIRONMENT":
        raise SystemExit(3)


if __name__ == "__main__":
    main()
