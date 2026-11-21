"""Run profile-aware semantic checks on a normalized Abaqus analysis_spec."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from normalize_analysis_spec import normalize_analysis_spec

_RIGID_KINDS = {"analyticalrigid", "discreterigid", "rigid", "rigidbody"}
_THERMAL_KIND_WORDS = ("temperature", "heat", "film", "radiation", "thermal")
_PROPERTY_ALIASES = {
    "density": {"density", "rho", "密度"},
    "elasticity": {"elastic", "elasticity", "youngsmodulus", "弹性", "弹性模量"},
    "conductivity": {"conductivity", "thermalconductivity", "导热系数"},
    "specific_heat": {"specificheat", "heatcapacity", "比热", "比热容"},
    "expansion": {"expansion", "thermalexpansion", "cte", "热膨胀", "热膨胀系数"},
    "plasticity": {"plastic", "plasticity", "plastictable", "塑性"},
}


def _token(value: Any) -> str:
    """将任意值规范为仅含数字、英文和中文的比较词元。"""
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(value or "").casefold())


def _matches_token_alias(value: Any, aliases: set[str]) -> bool:
    """使用规范化别名匹配值，同时兼容带限定词的名称。"""
    token = _token(value)
    return bool(token) and any(alias == token or alias in token for alias in aliases)


def _walk_keys(value: Any) -> Iterable[str]:
    """递归遍历字典或列表中的所有键，并产出规范化词元。"""
    if isinstance(value, dict):
        for key, child in value.items():
            yield _token(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def _find_value(value: Any, aliases: set[str]) -> Any:
    """递归查找第一个键名命中别名集合的值。"""
    if isinstance(value, dict):
        for key, child in value.items():
            if _token(key) in aliases:
                return child
            found = _find_value(child, aliases)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_value(child, aliases)
            if found is not None:
                return found
    return None


def _has_material_property(materials: list[dict[str, Any]], property_name: str) -> bool:
    """判断材料列表是否显式声明指定工程属性。"""
    aliases = _PROPERTY_ALIASES[property_name]
    for material in materials:
        if _token(material.get("kind")) in aliases:
            return True
        if aliases.intersection(_walk_keys(material.get("properties", {}))):
            return True
    return False


def _parameter(step: dict[str, Any], name: str) -> Any:
    """从分析步的嵌套参数中查找指定参数值。"""
    aliases = {_token(name)}
    return _find_value(step.get("parameters", {}), aliases)


def _region_names(values: Any) -> set[str]:
    """从字符串或区域对象列表中提取规范区域名称集合。"""
    names: set[str] = set()
    if not isinstance(values, list):
        return names
    for value in values:
        if isinstance(value, str) and value.strip():
            names.add(value.strip())
        elif isinstance(value, dict):
            name = value.get("name") or value.get("id") or value.get("region")
            if isinstance(name, str) and name.strip():
                names.add(name.strip())
    return names


def _is_true(value: Any) -> bool:
    """判断值是否表示显式启用状态。"""
    if value is True:
        return True
    return _token(value) in {"true", "on", "yes", "1", "enabled"}


def _is_false(value: Any) -> bool:
    """判断值是否表示显式禁用状态。"""
    if value is False:
        return True
    return _token(value) in {"false", "off", "no", "0", "disabled"}


class SemanticChecker:
    def __init__(self, analysis_spec: dict[str, Any]):
        """保存规范化分析规格，并初始化语义检查结果列表。"""
        self.spec = analysis_spec
        self.checks: list[dict[str, Any]] = []

    def add(
        self,
        check_id: str,
        status: str,
        message: str,
        *evidence: Any,
    ) -> None:
        """向报告追加一条检查状态、说明和非空证据。"""
        self.checks.append(
            {
                "id": check_id,
                "status": status,
                "message": message,
                "evidence": [str(item) for item in evidence if item is not None],
            }
        )

    @property
    def materials(self) -> list[dict[str, Any]]:
        """返回规格中声明的材料列表。"""
        return self.spec.get("materials", [])

    @property
    def deformable_ids(self) -> set[str]:
        """返回全部非刚体几何对象的标识集合。"""
        return {
            item["id"]
            for item in self.spec.get("geometry", [])
            if _token(item.get("kind")) not in _RIGID_KINDS
        }

    @property
    def output_variables(self) -> set[str]:
        """返回统一转为大写的 Field/History 输出变量集合。"""
        return {
            str(variable).upper()
            for output in self.spec.get("outputs", [])
            for variable in output.get("variables", [])
        }

    def find_step(self, accepted_kinds: set[str]) -> dict[str, Any] | None:
        """查找第一个类型属于允许集合的分析步。"""
        return next(
            (
                step
                for step in self.spec.get("steps", [])
                if _token(step.get("kind")) in accepted_kinds
            ),
            None,
        )

    def check_step(
        self, check_id: str, accepted_kinds: set[str], expected: str
    ) -> dict[str, Any] | None:
        """校验分析步类型，记录结果并返回命中的分析步。"""
        step = self.find_step(accepted_kinds)
        if step:
            self.add(
                check_id,
                "PASS",
                f"analysis step matches {expected}",
                step.get("id"),
                step.get("kind"),
            )
        else:
            actual = [item.get("kind") for item in self.spec.get("steps", [])]
            self.add(check_id, "FAIL", f"expected {expected} analysis step", actual)
        return step

    def check_cross_references(self) -> None:
        """校验网格、分析步和区域名称之间的交叉引用。"""
        geometry_ids = {item["id"] for item in self.spec.get("geometry", [])}
        step_ids = {item["id"] for item in self.spec.get("steps", [])} | {"Initial"}
        known_regions = {
            name
            for geometry in self.spec.get("geometry", [])
            for name in _region_names(geometry.get("regions", []))
        }
        bad_mesh = [
            item["id"]
            for item in self.spec.get("mesh", [])
            if item.get("geometry") not in geometry_ids
        ]
        self.add(
            "references.mesh_geometry",
            "FAIL" if bad_mesh else "PASS",
            "mesh entries must reference declared geometry",
            bad_mesh or sorted(geometry_ids),
        )

        bad_steps = []
        for collection in ("boundary_conditions", "loads"):
            for item in self.spec.get(collection, []):
                if item.get("step") not in step_ids:
                    bad_steps.append(f"{collection}.{item.get('id')}->{item.get('step')}")
        for item in self.spec.get("outputs", []):
            if item.get("step") and item.get("step") not in step_ids:
                bad_steps.append(f"outputs.{item.get('id')}->{item.get('step')}")
        self.add(
            "references.step",
            "FAIL" if bad_steps else "PASS",
            "BC/load/output step references must exist",
            bad_steps or sorted(step_ids),
        )

        referenced_regions = []
        for collection in ("boundary_conditions", "loads", "outputs"):
            for item in self.spec.get(collection, []):
                region = item.get("region")
                if isinstance(region, str) and _token(region) not in {
                    "model",
                    "wholemodel",
                    "assembly",
                    "all",
                }:
                    referenced_regions.append(f"{collection}.{item.get('id')}->{region}")
        if referenced_regions and not known_regions:
            self.add(
                "references.region_catalog",
                "WARN",
                "region references cannot be checked because geometry.regions is empty",
                referenced_regions,
            )
        else:
            unknown = [
                item for item in referenced_regions if item.rsplit("->", 1)[1] not in known_regions
            ]
            self.add(
                "references.region_catalog",
                "FAIL" if unknown else "PASS",
                "named BC/load/output regions must be declared by geometry",
                unknown or sorted(known_regions),
            )

    def check_material_assignment(self) -> None:
        """确认所有可变形几何都有材料及截面/几何指派意图。"""
        if not self.deformable_ids:
            self.add(
                "materials.deformable_assignment",
                "PASS",
                "all declared geometry is rigid; material and section assignment is not required",
            )
            return
        if not self.materials:
            self.add(
                "materials.deformable_assignment",
                "FAIL",
                "deformable geometry requires a material and assignment intent",
                sorted(self.deformable_ids),
            )
            return
        assigned = [item["id"] for item in self.materials if item.get("assignments")]
        self.add(
            "materials.deformable_assignment",
            "PASS" if assigned else "FAIL",
            "at least one material must record its section/geometry assignments",
            assigned or [item["id"] for item in self.materials],
        )

    def check_mesh(
        self, expected_library: str, *, thermal: bool = False, coupled: bool = False
    ) -> None:
        """检查网格覆盖、求解器库以及热或耦合单元族。"""
        relevant = [
            item
            for item in self.spec.get("mesh", [])
            if item.get("geometry") in self.deformable_ids
        ]
        covered = {item.get("geometry") for item in relevant}
        missing = sorted(self.deformable_ids - covered)
        wrong_library = [
            f"{item.get('id')}={item.get('element_library')}"
            for item in relevant
            if item.get("element_library") != expected_library
        ]
        empty_types = [item.get("id") for item in relevant if not item.get("element_types")]
        failures = [*missing, *wrong_library, *empty_types]
        self.add(
            "mesh.coverage_and_library",
            "FAIL" if failures else "PASS",
            f"every deformable geometry needs {expected_library} elements",
            failures or [item.get("id") for item in relevant],
        )
        element_types = [
            _token(element_type).upper()
            for item in relevant
            for element_type in item.get("element_types", [])
        ]
        if thermal:
            wrong = [item for item in element_types if not item.startswith(("DC", "DS"))]
            self.add(
                "mesh.thermal_family",
                "FAIL" if wrong else "PASS",
                "heat-transfer procedures require thermal element families such as DC*/DS*",
                wrong or element_types,
            )
        if coupled:
            wrong = [
                item for item in element_types if item.startswith(("DC", "DS")) or "T" not in item
            ]
            self.add(
                "mesh.coupled_family",
                "FAIL" if wrong else "PASS",
                "fully coupled temperature-displacement procedures require coupled elements such as C3D8T",
                wrong or element_types,
            )

    def require_properties(self, names: list[str], check_id: str) -> None:
        """检查当前分析类型要求的材料属性是否全部显式声明。"""
        missing = [name for name in names if not _has_material_property(self.materials, name)]
        self.add(
            check_id,
            "FAIL" if missing else "PASS",
            "required material properties must be explicit",
            missing or names,
        )

    def check_gravity_density(self) -> None:
        """存在重力或体加速度时，检查材料密度是否已声明。"""
        gravity = [
            item["id"]
            for item in self.spec.get("loads", [])
            if "gravity" in _token(item.get("kind"))
        ]
        if gravity:
            self.add(
                "loads.gravity_density",
                "PASS" if _has_material_property(self.materials, "density") else "FAIL",
                "gravity/body acceleration requires density in the declared unit system",
                gravity,
            )

    def check_plastic_table(self) -> None:
        """检查 Abaqus 金属塑性表首行是否从零塑性应变开始。"""
        for material in self.materials:
            if not (
                _token(material.get("kind")) in _PROPERTY_ALIASES["plasticity"]
                or _has_material_property([material], "plasticity")
            ):
                continue
            table = _find_value(
                material.get("properties", {}),
                {"plastic", "plastictable", "table"},
            )
            while isinstance(table, dict) and "table" in table:
                table = table["table"]
            first_strain = None
            if (
                isinstance(table, list)
                and table
                and isinstance(table[0], (list, tuple))
                and len(table[0]) >= 2
            ):
                first_strain = table[0][1]
            if isinstance(first_strain, (int, float)):
                self.add(
                    f"materials.{material['id']}.plastic_origin",
                    "PASS" if abs(float(first_strain)) <= 1.0e-12 else "FAIL",
                    "the first Abaqus metal-plastic table row must start at zero plastic strain",
                    first_strain,
                )
            else:
                self.add(
                    f"materials.{material['id']}.plastic_origin",
                    "WARN",
                    "plasticity is declared but the first plastic-strain value cannot be verified",
                    material.get("properties"),
                )

    def check_contact(self, step: dict[str, Any] | None) -> None:
        """检查接触属性、接触形式、区域角色、初始间隙和诊断输出。"""
        contacts = [
            item
            for item in self.spec.get("connections", [])
            if "contact" in _token(item.get("kind")) or "接触" in _token(item.get("kind"))
        ]
        if not contacts:
            return
        for contact in contacts:
            check_prefix = f"contact.{contact['id']}"
            properties = contact.get("properties")
            self.add(
                f"{check_prefix}.property",
                "PASS" if isinstance(properties, dict) and properties else "FAIL",
                "contact behavior/property must be declared explicitly",
                properties,
            )
            kind = contact.get("kind")
            formulation = _find_value(properties or {}, {"formulation", "type"})
            is_general = any(
                _matches_token_alias(value, {"general", "generalcontact"})
                for value in (kind, formulation)
            )
            is_pair = any(
                _matches_token_alias(value, {"pair", "contactpair", "surfacetosurface"})
                for value in (kind, formulation)
            )
            if not is_general and not is_pair:
                self.add(
                    f"{check_prefix}.formulation",
                    "FAIL",
                    "contact must declare general or surface-to-surface pair formulation",
                    contact.get("kind"),
                    formulation,
                )
            elif is_pair:
                regions = contact.get("regions", [])
                roles = {
                    _token(item.get("role")): item.get("name") or item.get("region")
                    for item in regions
                    if isinstance(item, dict)
                }
                has_roles = bool(
                    ({"main", "secondary"} <= set(roles)) or ({"master", "slave"} <= set(roles))
                )
                names = {name for name in roles.values() if isinstance(name, str) and name}
                self.add(
                    f"{check_prefix}.pair_regions",
                    "PASS" if has_roles and len(names) >= 2 else "FAIL",
                    "pair contact requires two distinct named surfaces with main/secondary roles",
                    regions,
                )
            else:
                self.add(
                    f"{check_prefix}.formulation",
                    "PASS",
                    "general contact formulation is explicit",
                    contact.get("kind"),
                )

            clearance = _find_value(
                properties or {},
                {"initialclearance", "initialgap", "overclosure", "clearancecheck"},
            )
            self.add(
                f"{check_prefix}.initial_clearance",
                "PASS" if clearance is not None else "WARN",
                "record how initial gap/overclosure will be checked",
                clearance,
            )
            sliding = _find_value(properties or {}, {"sliding", "slidingformulation"})
            if _token(sliding) in {"finite", "finitesliding"}:
                nlgeom = _parameter(step, "nlgeom") if step else None
                if _is_false(nlgeom):
                    self.add(
                        f"{check_prefix}.finite_sliding_nlgeom",
                        "WARN",
                        "finite sliding with nlgeom disabled needs an explicit small-motion justification",
                        nlgeom,
                    )
                elif nlgeom is None:
                    self.add(
                        f"{check_prefix}.finite_sliding_nlgeom",
                        "WARN",
                        "finite sliding requires an explicit nlgeom decision; do not enable it automatically",
                    )
                else:
                    self.add(
                        f"{check_prefix}.finite_sliding_nlgeom",
                        "PASS",
                        "finite-sliding geometric-nonlinearity decision is explicit",
                        nlgeom,
                    )
        contact_outputs = self.output_variables.intersection({"CSTRESS", "CDISP", "COPEN", "CSLIP"})
        self.add(
            "contact.outputs",
            "PASS" if contact_outputs else "WARN",
            "request contact status/traction/opening/slip output for diagnosis",
            sorted(contact_outputs),
        )

    def check_static(self) -> None:
        """执行静力分析的材料、网格、刚体控制、激励和接触检查。"""
        step = self.check_step(
            "static.step", {"static", "staticstep", "staticgeneral"}, "StaticStep"
        )
        self.check_material_assignment()
        self.check_mesh("STANDARD")
        if self.deformable_ids:
            mechanical = _has_material_property(self.materials, "elasticity") or any(
                _token(item.get("kind"))
                in {"hyperelastic", "userdefined", "usermaterial", "elasticisotropic"}
                for item in self.materials
            )
            self.add(
                "static.constitutive_law",
                "PASS" if mechanical else "FAIL",
                "deformable static analysis needs a mechanical constitutive law",
                [item.get("kind") for item in self.materials],
            )
        inertia_relief = _is_true(_parameter(step, "inertiaRelief")) if step else False
        constraints = self.spec.get("boundary_conditions", [])
        self.add(
            "static.rigid_body_control",
            "PASS" if constraints or inertia_relief or not self.deformable_ids else "FAIL",
            "static analysis must control rigid-body motion or explicitly use inertia relief",
            [item.get("id") for item in constraints],
            f"inertia_relief={inertia_relief}",
        )
        driven_bc = any(
            any(
                isinstance(value, (int, float)) and value != 0
                for value in item.get("components", {}).values()
            )
            for item in constraints
        )
        self.add(
            "static.excitation",
            "PASS" if self.spec.get("loads") or driven_bc else "WARN",
            "no load or nonzero prescribed displacement is declared",
            [item.get("id") for item in self.spec.get("loads", [])],
        )
        self.check_gravity_density()
        self.check_plastic_table()
        self.check_contact(step)

    def check_modal(self) -> None:
        """执行模态分析的质量、刚度、边界意图和模态输出检查。"""
        step = self.check_step(
            "modal.step", {"frequencystep", "frequency", "modal"}, "FrequencyStep"
        )
        self.check_material_assignment()
        self.check_mesh("STANDARD")
        if self.deformable_ids:
            self.require_properties(["elasticity", "density"], "modal.material_properties")
        boundary_mode = _token(_parameter(step, "boundary_mode")) if step else ""
        constraints = self.spec.get("boundary_conditions", [])
        if boundary_mode in {"freefree", "free"}:
            status = "PASS" if not constraints else "FAIL"
            message = "free-free modal intent must not include support constraints"
        elif boundary_mode in {"constrained", "fixed", "supported"}:
            status = "PASS" if constraints else "FAIL"
            message = "constrained modal intent requires declared boundary conditions"
        elif constraints:
            status = "WARN"
            message = "declare boundary_mode='constrained' so supports are intentional"
        else:
            status = "FAIL"
            message = "no supports is only valid when boundary_mode='free_free' is explicit"
        self.add(
            "modal.boundary_intent",
            status,
            message,
            boundary_mode,
            [item.get("id") for item in constraints],
        )
        if self.spec.get("loads"):
            self.add(
                "modal.loads",
                "WARN",
                "ordinary applied loads do not drive an eigenfrequency extraction step",
                [item.get("id") for item in self.spec["loads"]],
            )
        else:
            self.add("modal.loads", "PASS", "no unnecessary modal load is declared")
        self.add(
            "modal.outputs",
            "PASS" if "U" in self.output_variables else "WARN",
            "request U to inspect mode shapes; frequency is read from frame metadata",
            sorted(self.output_variables),
        )

    def check_dynamic(self, *, explicit: bool) -> None:
        """按显式或隐式动力类型检查分析步、时长、激励和能量要求。"""
        if explicit:
            step = self.check_step(
                "explicit.step",
                {"explicitdynamicsstep", "dynamicexplicit", "dynamicexplicitstep", "explicit"},
                "ExplicitDynamicsStep",
            )
            library = "EXPLICIT"
            prefix = "explicit"
        else:
            step = self.check_step(
                "implicit_dynamic.step",
                {"implicitdynamicsstep", "dynamicimplicit", "dynamicstep", "implicitdynamic"},
                "ImplicitDynamicsStep",
            )
            library = "STANDARD"
            prefix = "implicit_dynamic"
        self.check_material_assignment()
        self.check_mesh(library)
        if self.deformable_ids:
            self.require_properties(["density"], f"{prefix}.density")
        time_period = _parameter(step, "timePeriod") if step else None
        valid_time = (
            isinstance(time_period, (int, float))
            and not isinstance(time_period, bool)
            and time_period > 0
        )
        self.add(
            f"{prefix}.time_period",
            "PASS" if valid_time else "FAIL",
            "dynamic event duration must be an explicit positive number",
            time_period,
        )
        driven_bc = any(item.get("components") for item in self.spec.get("boundary_conditions", []))
        self.add(
            f"{prefix}.excitation",
            "PASS" if self.spec.get("loads") or driven_bc else "FAIL",
            "dynamic analysis needs a load, initial condition, or driven boundary condition",
            [item.get("id") for item in self.spec.get("loads", [])],
        )
        self.check_gravity_density()
        self.check_contact(step)
        if explicit:
            required_energy = {"ALLKE", "ALLIE", "ETOTAL"}
            missing = sorted(required_energy - self.output_variables)
            self.add(
                "explicit.energy_outputs",
                "PASS" if not missing else "WARN",
                "explicit dynamics should request kinetic, internal, and total-energy histories",
                missing or sorted(required_energy),
            )
            mass_scaling = _parameter(step, "massScaling") if step else None
            if mass_scaling not in (None, False, "", []):
                metrics = {
                    _token(item.get("metric")) for item in self.spec.get("acceptance_criteria", [])
                }
                has_added_mass_gate = bool(
                    metrics.intersection({"addedmass", "massincrease", "massscaling"})
                )
                self.add(
                    "explicit.mass_scaling",
                    "PASS" if has_added_mass_gate else "WARN",
                    "mass scaling requires a declared added-mass acceptance criterion",
                    mass_scaling,
                )

    def _has_thermal_condition(self) -> bool:
        """判断边界条件或载荷中是否包含热学条件。"""
        return any(
            any(word in _token(item.get("kind")) for word in _THERMAL_KIND_WORDS)
            for collection in ("boundary_conditions", "loads")
            for item in self.spec.get(collection, [])
        )

    def check_heat(self, *, transient: bool) -> None:
        """按稳态或瞬态传热类型检查热属性、热单元、热条件和输出。"""
        step = self.check_step(
            "heat.step",
            {"heattransferstep", "heattransfer", "steadyheattransfer", "transientheattransfer"},
            "HeatTransferStep",
        )
        self.check_material_assignment()
        self.check_mesh("STANDARD", thermal=True)
        required = ["conductivity"]
        if transient:
            required.extend(["density", "specific_heat"])
        if self.deformable_ids:
            self.require_properties(required, "heat.material_properties")
        self.add(
            "heat.thermal_condition",
            "PASS" if self._has_thermal_condition() else "FAIL",
            "heat transfer needs a temperature boundary, heat source, flux, film, or radiation condition",
        )
        temperature_outputs = self.output_variables.intersection({"NT", "NT11", "TEMP"})
        self.add(
            "heat.outputs",
            "PASS" if temperature_outputs else "FAIL",
            "request nodal temperature output (normally NT/NT11)",
            sorted(self.output_variables),
        )
        if transient:
            time_period = _parameter(step, "timePeriod") if step else None
            valid_time = (
                isinstance(time_period, (int, float))
                and not isinstance(time_period, bool)
                and time_period > 0
            )
            self.add(
                "heat.time_period",
                "PASS" if valid_time else "FAIL",
                "transient heat transfer needs an explicit positive duration",
                time_period,
            )

    def check_coupled(self) -> None:
        """检查温度—位移耦合分析的材料、单元、约束和输出。"""
        step = self.check_step(
            "coupled.step",
            {
                "coupledtempdisplacementstep",
                "coupledtemperaturedisplacement",
                "coupledtempdisplacement",
            },
            "CoupledTempDisplacementStep",
        )
        self.check_material_assignment()
        self.check_mesh("STANDARD", coupled=True)
        response = _token(_parameter(step, "response")) if step else ""
        required = ["elasticity", "conductivity", "expansion"]
        if response not in {"steadystate", "steady"}:
            required.extend(["density", "specific_heat"])
        if self.deformable_ids:
            self.require_properties(required, "coupled.material_properties")
        self.add(
            "coupled.thermal_condition",
            "PASS" if self._has_thermal_condition() else "FAIL",
            "coupled analysis needs an explicit thermal boundary or source",
        )
        mechanical_bcs = [
            item["id"]
            for item in self.spec.get("boundary_conditions", [])
            if not any(word in _token(item.get("kind")) for word in _THERMAL_KIND_WORDS)
        ]
        self.add(
            "coupled.mechanical_constraint",
            "PASS" if mechanical_bcs else "FAIL",
            "coupled analysis needs explicit mechanical rigid-body control",
            mechanical_bcs,
        )
        missing_outputs = sorted({"U", "NT"} - self.output_variables)
        if "NT11" in self.output_variables:
            missing_outputs = [item for item in missing_outputs if item != "NT"]
        self.add(
            "coupled.outputs",
            "PASS" if not missing_outputs else "FAIL",
            "request both displacement and temperature outputs",
            missing_outputs or sorted(self.output_variables),
        )
        self.check_contact(step)

    def report(
        self, profiles: list[str], normalization_warnings: list[dict[str, str]]
    ) -> dict[str, Any]:
        """合并规范化警告，汇总检查数量并生成最终语义报告。"""
        for warning in normalization_warnings:
            self.add("contract.normalization", "WARN", warning["message"], warning["path"])
        counts = {
            status: sum(item["status"] == status for item in self.checks)
            for status in ("PASS", "WARN", "FAIL", "UNSUPPORTED")
        }
        if counts["FAIL"]:
            status = "FAIL"
        elif counts["UNSUPPORTED"]:
            status = "UNSUPPORTED"
        elif counts["WARN"]:
            status = "WARN"
        else:
            status = "PASS"
        return {
            "status": status,
            "profiles": profiles,
            "summary": counts,
            "checks": self.checks,
            "analysis_spec": self.spec,
        }


def semantic_preflight(raw: Any) -> dict[str, Any]:
    """先规范化原始规格，再按分析类型执行对应语义检查。"""
    normalized = normalize_analysis_spec(raw)
    if normalized["status"] == "FAIL":
        unsupported = any(
            item["code"] == "UNSUPPORTED_ANALYSIS_TYPE" for item in normalized["errors"]
        )
        return {
            "status": "UNSUPPORTED" if unsupported else "FAIL",
            "profiles": [],
            "summary": {
                "PASS": 0,
                "WARN": len(normalized["warnings"]),
                "FAIL": 0 if unsupported else len(normalized["errors"]),
                "UNSUPPORTED": len(normalized["errors"]) if unsupported else 0,
            },
            "checks": [
                {
                    "id": "contract.structure",
                    "status": "UNSUPPORTED" if unsupported else "FAIL",
                    "message": "analysis_spec structure must pass before semantic checks",
                    "evidence": [
                        f"{item['code']} {item['path']}: {item['message']}"
                        for item in normalized["errors"]
                    ],
                }
            ],
            "analysis_spec": normalized["analysis_spec"],
        }

    spec = normalized["analysis_spec"]
    checker = SemanticChecker(spec)
    checker.check_cross_references()
    analysis_type = spec["analysis_type"]
    profiles = [analysis_type]
    if analysis_type == "static":
        checker.check_static()
    elif analysis_type == "modal":
        checker.check_modal()
    elif analysis_type == "dynamic_explicit":
        checker.check_dynamic(explicit=True)
    elif analysis_type == "dynamic_implicit":
        checker.check_dynamic(explicit=False)
    elif analysis_type == "heat_transfer_steady":
        checker.check_heat(transient=False)
    elif analysis_type == "heat_transfer_transient":
        checker.check_heat(transient=True)
    elif analysis_type == "coupled_temp_displacement":
        checker.check_coupled()
    else:
        checker.add(
            "analysis.profile", "UNSUPPORTED", "no semantic profile is available", analysis_type
        )
    if any(
        "contact" in _token(item.get("kind")) or "接触" in _token(item.get("kind"))
        for item in spec.get("connections", [])
    ):
        profiles.append("contact")
    return checker.report(profiles, normalized["warnings"])
