"""Profile checks for a shaped Abaqus analysis_spec.

Structure is checked first. A document that fails structure does not receive
profile checks. Contact is an added profile, not an analysis_type.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from spec_shape import shape_document

_RIGID_KINDS = {"analyticalrigid", "discreterigid", "rigid", "rigidbody"}
_THERMAL_WORDS = ("temperature", "heat", "film", "radiation", "thermal")
_PROPERTY_ALIASES = {
    "density": {"density", "rho", "密度"},
    "elasticity": {"elastic", "elasticity", "youngsmodulus", "弹性", "弹性模量"},
    "conductivity": {"conductivity", "thermalconductivity", "导热系数"},
    "specific_heat": {"specificheat", "heatcapacity", "比热", "比热容"},
    "expansion": {"expansion", "thermalexpansion", "cte", "热膨胀", "热膨胀系数"},
    "plasticity": {"plastic", "plasticity", "plastictable", "塑性"},
}
_WHOLE_MODEL_REGIONS = {"model", "wholemodel", "assembly", "all"}
_PROFILE_CHECKS = {
    "static": "static",
    "modal": "modal",
    "dynamic_explicit": "explicit",
    "dynamic_implicit": "implicit",
    "heat_transfer_steady": "heat_steady",
    "heat_transfer_transient": "heat_transient",
    "coupled_temp_displacement": "coupled",
}


def compact(value: Any) -> str:
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(value or "").casefold())


def alias_hit(value: Any, aliases: set[str]) -> bool:
    token = compact(value)
    return bool(token) and any(alias == token or alias in token for alias in aliases)


def walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield compact(key)
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def find_named(value: Any, aliases: set[str]) -> Any:
    if isinstance(value, dict):
        for key, child in value.items():
            if compact(key) in aliases:
                return child
            found = find_named(child, aliases)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_named(child, aliases)
            if found is not None:
                return found
    return None


def property_declared(materials: list[dict[str, Any]], property_name: str) -> bool:
    aliases = _PROPERTY_ALIASES[property_name]
    for material in materials:
        if compact(material.get("kind")) in aliases:
            return True
        if aliases.intersection(walk_keys(material.get("properties", {}))):
            return True
    return False


def step_parameter(step: dict[str, Any], name: str) -> Any:
    return find_named(step.get("parameters", {}), {compact(name)})


def region_names(values: Any) -> set[str]:
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


def is_on(value: Any) -> bool:
    if value is True:
        return True
    return compact(value) in {"true", "on", "yes", "1", "enabled"}


def is_off(value: Any) -> bool:
    if value is False:
        return True
    return compact(value) in {"false", "off", "no", "0", "disabled"}


class ProfileReview:
    def __init__(self, analysis_spec: dict[str, Any]):
        self.spec = analysis_spec
        self.checks: list[dict[str, Any]] = []

    def add(self, check_id: str, status: str, message: str, *evidence: Any) -> None:
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
        return self.spec.get("materials", [])

    @property
    def deformable_ids(self) -> set[str]:
        return {
            item["id"]
            for item in self.spec.get("geometry", [])
            if compact(item.get("kind")) not in _RIGID_KINDS
        }

    @property
    def output_variables(self) -> set[str]:
        return {
            str(variable).upper()
            for output in self.spec.get("outputs", [])
            for variable in output.get("variables", [])
        }

    def find_step(self, accepted_kinds: set[str]) -> dict[str, Any] | None:
        return next(
            (
                step
                for step in self.spec.get("steps", [])
                if compact(step.get("kind")) in accepted_kinds
            ),
            None,
        )

    def require_step(
        self, check_id: str, accepted_kinds: set[str], expected: str
    ) -> dict[str, Any] | None:
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

    def finish(self, profiles: list[str], warnings: list[dict[str, str]]) -> dict[str, Any]:
        for warning in warnings:
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


def check_cross_references(review: ProfileReview) -> None:
    geometry_ids = {item["id"] for item in review.spec.get("geometry", [])}
    step_ids = {item["id"] for item in review.spec.get("steps", [])} | {"Initial"}
    known_regions = {
        name
        for geometry in review.spec.get("geometry", [])
        for name in region_names(geometry.get("regions", []))
    }
    bad_mesh = [
        item["id"]
        for item in review.spec.get("mesh", [])
        if item.get("geometry") not in geometry_ids
    ]
    review.add(
        "references.mesh_geometry",
        "FAIL" if bad_mesh else "PASS",
        "mesh entries must reference declared geometry",
        bad_mesh or sorted(geometry_ids),
    )
    bad_steps = []
    for collection in ("boundary_conditions", "loads"):
        for item in review.spec.get(collection, []):
            if item.get("step") not in step_ids:
                bad_steps.append(f"{collection}.{item.get('id')}->{item.get('step')}")
    for item in review.spec.get("outputs", []):
        if item.get("step") and item.get("step") not in step_ids:
            bad_steps.append(f"outputs.{item.get('id')}->{item.get('step')}")
    review.add(
        "references.step",
        "FAIL" if bad_steps else "PASS",
        "BC/load/output step references must exist",
        bad_steps or sorted(step_ids),
    )
    referenced_regions = []
    for collection in ("boundary_conditions", "loads", "outputs"):
        for item in review.spec.get(collection, []):
            region = item.get("region")
            if isinstance(region, str) and compact(region) not in _WHOLE_MODEL_REGIONS:
                referenced_regions.append(f"{collection}.{item.get('id')}->{region}")
    if referenced_regions and not known_regions:
        review.add(
            "references.region_catalog",
            "WARN",
            "region references cannot be checked because geometry.regions is empty",
            referenced_regions,
        )
        return
    unknown = [item for item in referenced_regions if item.rsplit("->", 1)[1] not in known_regions]
    review.add(
        "references.region_catalog",
        "FAIL" if unknown else "PASS",
        "named BC/load/output regions must be declared by geometry",
        unknown or sorted(known_regions),
    )


def check_material_assignment(review: ProfileReview) -> None:
    if not review.deformable_ids:
        review.add(
            "materials.deformable_assignment",
            "PASS",
            "all declared geometry is rigid; material and section assignment is not required",
        )
        return
    if not review.materials:
        review.add(
            "materials.deformable_assignment",
            "FAIL",
            "deformable geometry requires a material and assignment intent",
            sorted(review.deformable_ids),
        )
        return
    assigned = [item["id"] for item in review.materials if item.get("assignments")]
    review.add(
        "materials.deformable_assignment",
        "PASS" if assigned else "FAIL",
        "at least one material must record its section/geometry assignments",
        assigned or [item["id"] for item in review.materials],
    )


def check_mesh(
    review: ProfileReview,
    expected_library: str,
    *,
    thermal: bool = False,
    coupled: bool = False,
) -> None:
    relevant = [
        item
        for item in review.spec.get("mesh", [])
        if item.get("geometry") in review.deformable_ids
    ]
    covered = {item.get("geometry") for item in relevant}
    missing = sorted(review.deformable_ids - covered)
    wrong_library = [
        f"{item.get('id')}={item.get('element_library')}"
        for item in relevant
        if item.get("element_library") != expected_library
    ]
    empty_types = [item.get("id") for item in relevant if not item.get("element_types")]
    failures = [*missing, *wrong_library, *empty_types]
    review.add(
        "mesh.coverage_and_library",
        "FAIL" if failures else "PASS",
        f"every deformable geometry needs {expected_library} elements",
        failures or [item.get("id") for item in relevant],
    )
    element_types = [
        compact(element_type).upper()
        for item in relevant
        for element_type in item.get("element_types", [])
    ]
    if thermal:
        wrong = [item for item in element_types if not item.startswith(("DC", "DS"))]
        review.add(
            "mesh.thermal_family",
            "FAIL" if wrong else "PASS",
            "heat-transfer procedures require thermal element families such as DC*/DS*",
            wrong or element_types,
        )
    if coupled:
        wrong = [item for item in element_types if item.startswith(("DC", "DS")) or "T" not in item]
        review.add(
            "mesh.coupled_family",
            "FAIL" if wrong else "PASS",
            "fully coupled temperature-displacement procedures require coupled elements such as C3D8T",
            wrong or element_types,
        )


def require_properties(review: ProfileReview, names: list[str], check_id: str) -> None:
    missing = [name for name in names if not property_declared(review.materials, name)]
    review.add(
        check_id,
        "FAIL" if missing else "PASS",
        "required material properties must be explicit",
        missing or names,
    )


def check_gravity_density(review: ProfileReview) -> None:
    gravity = [
        item["id"]
        for item in review.spec.get("loads", [])
        if "gravity" in compact(item.get("kind"))
    ]
    if not gravity:
        return
    review.add(
        "loads.gravity_density",
        "PASS" if property_declared(review.materials, "density") else "FAIL",
        "gravity/body acceleration requires density in the declared unit system",
        gravity,
    )


def check_plastic_table(review: ProfileReview) -> None:
    for material in review.materials:
        declared = compact(material.get("kind")) in _PROPERTY_ALIASES["plasticity"] or property_declared(
            [material], "plasticity"
        )
        if not declared:
            continue
        table = find_named(material.get("properties", {}), {"plastic", "plastictable", "table"})
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
            review.add(
                f"materials.{material['id']}.plastic_origin",
                "PASS" if abs(float(first_strain)) <= 1.0e-12 else "FAIL",
                "the first Abaqus metal-plastic table row must start at zero plastic strain",
                first_strain,
            )
        else:
            review.add(
                f"materials.{material['id']}.plastic_origin",
                "WARN",
                "plasticity is declared but the first plastic-strain value cannot be verified",
                material.get("properties"),
            )


def contact_items(spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item
        for item in spec.get("connections", [])
        if "contact" in compact(item.get("kind")) or "接触" in compact(item.get("kind"))
    ]


def check_contact(review: ProfileReview, step: dict[str, Any] | None) -> None:
    contacts = contact_items(review.spec)
    if not contacts:
        return
    for contact in contacts:
        prefix = f"contact.{contact['id']}"
        properties = contact.get("properties")
        review.add(
            f"{prefix}.property",
            "PASS" if isinstance(properties, dict) and properties else "FAIL",
            "contact behavior/property must be declared explicitly",
            properties,
        )
        kind = contact.get("kind")
        formulation = find_named(properties or {}, {"formulation", "type"})
        is_general = any(
            alias_hit(value, {"general", "generalcontact"}) for value in (kind, formulation)
        )
        is_pair = any(
            alias_hit(value, {"pair", "contactpair", "surfacetosurface"})
            for value in (kind, formulation)
        )
        if not is_general and not is_pair:
            review.add(
                f"{prefix}.formulation",
                "FAIL",
                "contact must declare general or surface-to-surface pair formulation",
                contact.get("kind"),
                formulation,
            )
        elif is_pair:
            regions = contact.get("regions", [])
            roles = {
                compact(item.get("role")): item.get("name") or item.get("region")
                for item in regions
                if isinstance(item, dict)
            }
            has_roles = bool(({"main", "secondary"} <= set(roles)) or ({"master", "slave"} <= set(roles)))
            names = {name for name in roles.values() if isinstance(name, str) and name}
            review.add(
                f"{prefix}.pair_regions",
                "PASS" if has_roles and len(names) >= 2 else "FAIL",
                "pair contact requires two distinct named surfaces with main/secondary roles",
                regions,
            )
        else:
            review.add(
                f"{prefix}.formulation",
                "PASS",
                "general contact formulation is explicit",
                contact.get("kind"),
            )
        clearance = find_named(
            properties or {},
            {"initialclearance", "initialgap", "overclosure", "clearancecheck"},
        )
        review.add(
            f"{prefix}.initial_clearance",
            "PASS" if clearance is not None else "WARN",
            "record how initial gap/overclosure will be checked",
            clearance,
        )
        sliding = find_named(properties or {}, {"sliding", "slidingformulation"})
        if compact(sliding) not in {"finite", "finitesliding"}:
            continue
        nlgeom = step_parameter(step, "nlgeom") if step else None
        if is_off(nlgeom):
            review.add(
                f"{prefix}.finite_sliding_nlgeom",
                "WARN",
                "finite sliding with nlgeom disabled needs an explicit small-motion justification",
                nlgeom,
            )
        elif nlgeom is None:
            review.add(
                f"{prefix}.finite_sliding_nlgeom",
                "WARN",
                "finite sliding requires an explicit nlgeom decision; do not enable it automatically",
            )
        else:
            review.add(
                f"{prefix}.finite_sliding_nlgeom",
                "PASS",
                "finite-sliding geometric-nonlinearity decision is explicit",
                nlgeom,
            )
    contact_outputs = review.output_variables.intersection({"CSTRESS", "CDISP", "COPEN", "CSLIP"})
    review.add(
        "contact.outputs",
        "PASS" if contact_outputs else "WARN",
        "request contact status/traction/opening/slip output for diagnosis",
        sorted(contact_outputs),
    )


def check_static(review: ProfileReview) -> None:
    step = review.require_step(
        "static.step", {"static", "staticstep", "staticgeneral"}, "StaticStep"
    )
    check_material_assignment(review)
    check_mesh(review, "STANDARD")
    if review.deformable_ids:
        mechanical = property_declared(review.materials, "elasticity") or any(
            compact(item.get("kind"))
            in {"hyperelastic", "userdefined", "usermaterial", "elasticisotropic"}
            for item in review.materials
        )
        review.add(
            "static.constitutive_law",
            "PASS" if mechanical else "FAIL",
            "deformable static analysis needs a mechanical constitutive law",
            [item.get("kind") for item in review.materials],
        )
    inertia_relief = is_on(step_parameter(step, "inertiaRelief")) if step else False
    constraints = review.spec.get("boundary_conditions", [])
    review.add(
        "static.rigid_body_control",
        "PASS" if constraints or inertia_relief or not review.deformable_ids else "FAIL",
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
    review.add(
        "static.excitation",
        "PASS" if review.spec.get("loads") or driven_bc else "WARN",
        "no load or nonzero prescribed displacement is declared",
        [item.get("id") for item in review.spec.get("loads", [])],
    )
    check_gravity_density(review)
    check_plastic_table(review)
    check_contact(review, step)


def check_modal(review: ProfileReview) -> None:
    step = review.require_step(
        "modal.step", {"frequencystep", "frequency", "modal"}, "FrequencyStep"
    )
    check_material_assignment(review)
    check_mesh(review, "STANDARD")
    if review.deformable_ids:
        require_properties(review, ["elasticity", "density"], "modal.material_properties")
    boundary_mode = compact(step_parameter(step, "boundary_mode")) if step else ""
    constraints = review.spec.get("boundary_conditions", [])
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
    review.add(
        "modal.boundary_intent",
        status,
        message,
        boundary_mode,
        [item.get("id") for item in constraints],
    )
    if review.spec.get("loads"):
        review.add(
            "modal.loads",
            "WARN",
            "ordinary applied loads do not drive an eigenfrequency extraction step",
            [item.get("id") for item in review.spec["loads"]],
        )
    else:
        review.add("modal.loads", "PASS", "no unnecessary modal load is declared")
    review.add(
        "modal.outputs",
        "PASS" if "U" in review.output_variables else "WARN",
        "request U to inspect mode shapes; frequency is read from frame metadata",
        sorted(review.output_variables),
    )


def check_dynamic(review: ProfileReview, *, explicit: bool) -> None:
    if explicit:
        step = review.require_step(
            "explicit.step",
            {"explicitdynamicsstep", "dynamicexplicit", "dynamicexplicitstep", "explicit"},
            "ExplicitDynamicsStep",
        )
        library = "EXPLICIT"
        prefix = "explicit"
    else:
        step = review.require_step(
            "implicit_dynamic.step",
            {"implicitdynamicsstep", "dynamicimplicit", "dynamicstep", "implicitdynamic"},
            "ImplicitDynamicsStep",
        )
        library = "STANDARD"
        prefix = "implicit_dynamic"
    check_material_assignment(review)
    check_mesh(review, library)
    if review.deformable_ids:
        require_properties(review, ["density"], f"{prefix}.density")
    time_period = step_parameter(step, "timePeriod") if step else None
    valid_time = (
        isinstance(time_period, (int, float))
        and not isinstance(time_period, bool)
        and time_period > 0
    )
    review.add(
        f"{prefix}.time_period",
        "PASS" if valid_time else "FAIL",
        "dynamic event duration must be an explicit positive number",
        time_period,
    )
    driven_bc = any(item.get("components") for item in review.spec.get("boundary_conditions", []))
    review.add(
        f"{prefix}.excitation",
        "PASS" if review.spec.get("loads") or driven_bc else "FAIL",
        "dynamic analysis needs a load, initial condition, or driven boundary condition",
        [item.get("id") for item in review.spec.get("loads", [])],
    )
    check_gravity_density(review)
    check_contact(review, step)
    if not explicit:
        return
    required_energy = {"ALLKE", "ALLIE", "ETOTAL"}
    missing = sorted(required_energy - review.output_variables)
    review.add(
        "explicit.energy_outputs",
        "PASS" if not missing else "WARN",
        "explicit dynamics should request kinetic, internal, and total-energy histories",
        missing or sorted(required_energy),
    )
    mass_scaling = step_parameter(step, "massScaling") if step else None
    if mass_scaling in (None, False, "", []):
        return
    metrics = {compact(item.get("metric")) for item in review.spec.get("acceptance_criteria", [])}
    has_added_mass_gate = bool(metrics.intersection({"addedmass", "massincrease", "massscaling"}))
    review.add(
        "explicit.mass_scaling",
        "PASS" if has_added_mass_gate else "WARN",
        "mass scaling requires a declared added-mass acceptance criterion",
        mass_scaling,
    )


def has_thermal_condition(review: ProfileReview) -> bool:
    return any(
        any(word in compact(item.get("kind")) for word in _THERMAL_WORDS)
        for collection in ("boundary_conditions", "loads")
        for item in review.spec.get(collection, [])
    )


def check_heat(review: ProfileReview, *, transient: bool) -> None:
    step = review.require_step(
        "heat.step",
        {"heattransferstep", "heattransfer", "steadyheattransfer", "transientheattransfer"},
        "HeatTransferStep",
    )
    check_material_assignment(review)
    check_mesh(review, "STANDARD", thermal=True)
    required = ["conductivity"]
    if transient:
        required.extend(["density", "specific_heat"])
    if review.deformable_ids:
        require_properties(review, required, "heat.material_properties")
    review.add(
        "heat.thermal_condition",
        "PASS" if has_thermal_condition(review) else "FAIL",
        "heat transfer needs a temperature boundary, heat source, flux, film, or radiation condition",
    )
    temperature_outputs = review.output_variables.intersection({"NT", "NT11", "TEMP"})
    review.add(
        "heat.outputs",
        "PASS" if temperature_outputs else "FAIL",
        "request nodal temperature output (normally NT/NT11)",
        sorted(review.output_variables),
    )
    if not transient:
        return
    time_period = step_parameter(step, "timePeriod") if step else None
    valid_time = (
        isinstance(time_period, (int, float))
        and not isinstance(time_period, bool)
        and time_period > 0
    )
    review.add(
        "heat.time_period",
        "PASS" if valid_time else "FAIL",
        "transient heat transfer needs an explicit positive duration",
        time_period,
    )


def check_coupled(review: ProfileReview) -> None:
    step = review.require_step(
        "coupled.step",
        {
            "coupledtempdisplacementstep",
            "coupledtemperaturedisplacement",
            "coupledtempdisplacement",
        },
        "CoupledTempDisplacementStep",
    )
    check_material_assignment(review)
    check_mesh(review, "STANDARD", coupled=True)
    response = compact(step_parameter(step, "response")) if step else ""
    required = ["elasticity", "conductivity", "expansion"]
    if response not in {"steadystate", "steady"}:
        required.extend(["density", "specific_heat"])
    if review.deformable_ids:
        require_properties(review, required, "coupled.material_properties")
    review.add(
        "coupled.thermal_condition",
        "PASS" if has_thermal_condition(review) else "FAIL",
        "coupled analysis needs an explicit thermal boundary or source",
    )
    mechanical_bcs = [
        item["id"]
        for item in review.spec.get("boundary_conditions", [])
        if not any(word in compact(item.get("kind")) for word in _THERMAL_WORDS)
    ]
    review.add(
        "coupled.mechanical_constraint",
        "PASS" if mechanical_bcs else "FAIL",
        "coupled analysis needs explicit mechanical rigid-body control",
        mechanical_bcs,
    )
    missing_outputs = sorted({"U", "NT"} - review.output_variables)
    if "NT11" in review.output_variables:
        missing_outputs = [item for item in missing_outputs if item != "NT"]
    review.add(
        "coupled.outputs",
        "PASS" if not missing_outputs else "FAIL",
        "request both displacement and temperature outputs",
        missing_outputs or sorted(review.output_variables),
    )
    check_contact(review, step)


def _structure_failure(shaped: dict[str, Any]) -> dict[str, Any]:
    unsupported = any(item["code"] == "UNSUPPORTED_ANALYSIS_TYPE" for item in shaped["errors"])
    return {
        "status": "UNSUPPORTED" if unsupported else "FAIL",
        "profiles": [],
        "summary": {
            "PASS": 0,
            "WARN": len(shaped["warnings"]),
            "FAIL": 0 if unsupported else len(shaped["errors"]),
            "UNSUPPORTED": len(shaped["errors"]) if unsupported else 0,
        },
        "checks": [
            {
                "id": "contract.structure",
                "status": "UNSUPPORTED" if unsupported else "FAIL",
                "message": "analysis_spec structure must pass before semantic checks",
                "evidence": [
                    f"{item['code']} {item['path']}: {item['message']}" for item in shaped["errors"]
                ],
            }
        ],
        "analysis_spec": shaped["analysis_spec"],
    }


def review_spec(raw: Any) -> dict[str, Any]:
    """Shape the document, then run the checks for its analysis type."""
    shaped = shape_document(raw)
    if shaped["status"] == "FAIL":
        return _structure_failure(shaped)
    spec = shaped["analysis_spec"]
    review = ProfileReview(spec)
    check_cross_references(review)
    analysis_type = spec["analysis_type"]
    profiles = [analysis_type]
    branch = _PROFILE_CHECKS.get(analysis_type)
    if branch == "static":
        check_static(review)
    elif branch == "modal":
        check_modal(review)
    elif branch == "explicit":
        check_dynamic(review, explicit=True)
    elif branch == "implicit":
        check_dynamic(review, explicit=False)
    elif branch == "heat_steady":
        check_heat(review, transient=False)
    elif branch == "heat_transient":
        check_heat(review, transient=True)
    elif branch == "coupled":
        check_coupled(review)
    else:
        review.add("analysis.profile", "UNSUPPORTED", "no semantic profile is available", analysis_type)
    if contact_items(spec):
        profiles.append("contact")
    return review.finish(profiles, shaped["warnings"])
