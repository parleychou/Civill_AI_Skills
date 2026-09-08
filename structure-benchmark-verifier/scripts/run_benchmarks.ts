/**
 * 结构力学基准题库自动回归验证
 *
 * 运行： node --experimental-strip-types skills/structure-benchmark-verifier/scripts/run_benchmarks.ts
 * 全部通过退出码 0，任一项超差退出码 1，可直接接入 CI 或 pre-commit hook。
 *
 * 若求解器不在默认位置，改下面两行 import 的路径即可（需导出同名同签名的函数）。
 */

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

import { solveStructure2D } from "../../matrix-stiffness-2d/scripts/solver_2d.ts";
import { sectionForcesAt, sampleMemberDiagram } from "../../matrix-stiffness-2d/scripts/member_diagram.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const CASES_PATH = resolve(HERE, "../benchmarks/standard_cases.json");

/** 整体平衡残差判定阈值相对于荷载合力的比例 */
const EQUILIBRIUM_REL_TOL = 1e-9;

interface Check {
  quantity:
    | "displacement" | "reaction" | "moment" | "shear" | "axial" | "endForce"
    | "maxMoment" | "maxSaggingMoment" | "maxHoggingMoment";
  node?: number;
  element?: number;
  component?: string;
  x?: number;
  expected: number;
  expectedX?: number;
  relTol?: number;
  absTol?: number;
  formula?: string;
}

interface Failure {
  readonly label: string;
  readonly expected: number;
  readonly actual: number;
  readonly error: string;
}

function main(): void {
  const suite = JSON.parse(readFileSync(CASES_PATH, "utf8"));
  if (suite.schemaVersion !== "2.0") {
    throw new Error(`题库 schemaVersion 不匹配：期望 2.0，实际 ${suite.schemaVersion}`);
  }

  let passed = 0;
  const failures: Failure[] = [];

  for (const testCase of suite.cases) {
    const { nodes, elements, loads } = testCase.model;
    const result = solveStructure2D(nodes, elements, loads);
    const qOf = new Map<number, number>(elements.map((e: any) => [e.id, e.q]));

    // 无需解析解的硬性检查：整体静力平衡
    const equilibrium = checkEquilibrium(nodes, elements, loads, result);
    for (const f of equilibrium) failures.push({ ...f, label: `${testCase.id} 整体平衡 ${f.label}` });
    if (equilibrium.length === 0) passed++;

    for (const check of testCase.checks as Check[]) {
      const label = `${testCase.id} ${describeCheck(check)}`;
      let actual: number;
      try {
        actual = evaluateCheck(check, result, qOf);
      } catch (err) {
        failures.push({ label, expected: check.expected, actual: NaN, error: (err as Error).message });
        continue;
      }

      const verdict = compare(actual, check.expected, check.relTol, check.absTol);
      if (verdict.ok) {
        passed++;
      } else {
        failures.push({ label, expected: check.expected, actual, error: verdict.message });
      }

      // 弯矩极值检查额外校核极值位置
      if (check.expectedX !== undefined) {
        const station = extremeMoment(check, result, qOf);
        const xVerdict = compare(station.x, check.expectedX, 1e-6, 1e-9);
        if (xVerdict.ok) passed++;
        else failures.push({
          label: `${label} 极值位置`,
          expected: check.expectedX,
          actual: station.x,
          error: xVerdict.message,
        });
      }
    }
  }

  report(passed, failures);
  process.exit(failures.length === 0 ? 0 : 1);
}

function evaluateCheck(
  check: Check,
  result: ReturnType<typeof solveStructure2D>,
  qOf: ReadonlyMap<number, number>
): number {
  switch (check.quantity) {
    case "displacement": {
      const d = result.displacements[check.node!];
      if (!d) throw new Error(`找不到节点 ${check.node}`);
      return pick(d as unknown as Record<string, number>, check.component!);
    }
    case "reaction": {
      const r = result.reactions[check.node!];
      if (!r) throw new Error(`找不到节点 ${check.node}`);
      return pick(r as unknown as Record<string, number>, check.component!);
    }
    case "endForce": {
      const f = result.memberForces[check.element!];
      if (!f) throw new Error(`找不到单元 ${check.element}`);
      return pick(f as unknown as Record<string, number>, check.component!);
    }
    case "moment":
    case "shear":
    case "axial": {
      const f = result.memberForces[check.element!];
      if (!f) throw new Error(`找不到单元 ${check.element}`);
      const s = sectionForcesAt(f, qOf.get(check.element!)!, check.x!);
      return check.quantity === "moment" ? s.M : check.quantity === "shear" ? s.V : s.N;
    }
    case "maxMoment":
    case "maxSaggingMoment":
    case "maxHoggingMoment":
      return extremeMoment(check, result, qOf).M;
  }
}

/** maxMoment / maxSaggingMoment / maxHoggingMoment 共用的极值截面提取 */
function extremeMoment(
  check: Check,
  result: ReturnType<typeof solveStructure2D>,
  qOf: ReadonlyMap<number, number>
) {
  const f = result.memberForces[check.element!];
  if (!f) throw new Error(`找不到单元 ${check.element}`);
  const diagram = sampleMemberDiagram(f, qOf.get(check.element!)!, 20);
  if (check.quantity === "maxSaggingMoment") return diagram.maxSaggingMoment;
  if (check.quantity === "maxHoggingMoment") return diagram.maxHoggingMoment;
  return diagram.maxAbsMoment;
}

function pick(obj: Record<string, number>, key: string): number {
  const v = obj[key];
  if (typeof v !== "number") throw new Error(`未知分量 "${key}"`);
  return v;
}

/** ΣFx = ΣFy = ΣM_O = 0，反力与外荷载（含杆间均布荷载）必须自洽 */
function checkEquilibrium(
  nodes: any[],
  elements: any[],
  loads: any[],
  result: ReturnType<typeof solveStructure2D>
): Failure[] {
  const nodeById = new Map<number, any>(nodes.map(n => [n.id, n]));
  let fx = 0, fy = 0, mo = 0, magnitude = 0;

  for (const ld of loads) {
    const n = nodeById.get(ld.nodeId);
    fx += ld.fx;
    fy += ld.fy;
    mo += ld.mz + n.x * ld.fy - n.y * ld.fx;
    magnitude += Math.abs(ld.fx) + Math.abs(ld.fy);
  }

  for (const el of elements) {
    if (!el.q) continue;
    const ni = nodeById.get(el.nodeI);
    const nj = nodeById.get(el.nodeJ);
    const L = Math.hypot(nj.x - ni.x, nj.y - ni.y);
    // 局部 -y 单位向量在整体坐标下的分量
    const c = (nj.x - ni.x) / L;
    const s = (nj.y - ni.y) / L;
    const total = el.q * L;
    const gx = total * s;    // -(-s) * total
    const gy = -total * c;
    const cx = (ni.x + nj.x) / 2;
    const cy = (ni.y + nj.y) / 2;
    fx += gx;
    fy += gy;
    mo += cx * gy - cy * gx;
    magnitude += Math.abs(gx) + Math.abs(gy);
  }

  for (const n of nodes) {
    const r = result.reactions[n.id];
    fx += r.rx;
    fy += r.ry;
    mo += r.rm + n.x * r.ry - n.y * r.rx;
    magnitude += Math.abs(r.rx) + Math.abs(r.ry);
  }

  const tol = Math.max(magnitude, 1) * EQUILIBRIUM_REL_TOL;
  const out: Failure[] = [];
  const push = (name: string, value: number) => {
    if (Math.abs(value) > tol) {
      out.push({ label: name, expected: 0, actual: value, error: `残差 ${value.toExponential(3)} 超过阈值 ${tol.toExponential(3)}` });
    }
  };
  push("ΣFx", fx);
  push("ΣFy", fy);
  push("ΣM_O", mo);
  return out;
}

function compare(
  actual: number,
  expected: number,
  relTol = 1e-4,
  absTol = 0
): { ok: boolean; message: string } {
  if (!Number.isFinite(actual)) {
    return { ok: false, message: `结果非有限值：${actual}` };
  }
  const diff = Math.abs(actual - expected);
  if (absTol > 0 && diff <= absTol) return { ok: true, message: "" };
  if (expected === 0) {
    const limit = absTol > 0 ? absTol : 1e-9;
    return diff <= limit
      ? { ok: true, message: "" }
      : { ok: false, message: `期望 0，实际 ${actual.toExponential(3)}（绝对容差 ${limit.toExponential(1)}）` };
  }
  const rel = diff / Math.abs(expected);
  return rel <= relTol
    ? { ok: true, message: "" }
    : { ok: false, message: `相对误差 ${(rel * 100).toFixed(4)}% 超过容差 ${(relTol * 100).toFixed(4)}%` };
}

function describeCheck(check: Check): string {
  const target = check.node !== undefined ? `节点${check.node}` : `单元${check.element}`;
  const at = check.x !== undefined ? `@x=${check.x}` : "";
  return `${check.quantity}.${check.component ?? ""}${at} (${target})`;
}

function report(passed: number, failures: readonly Failure[]): void {
  const lines = [
    "",
    "═══ 结构力学基准回归验证 ═══",
    `通过 ${passed} 项，失败 ${failures.length} 项`,
    "",
  ];
  for (const f of failures) {
    lines.push(`✗ ${f.label}`);
    lines.push(`    期望 ${f.expected}   实际 ${f.actual}`);
    lines.push(`    ${f.error}`);
  }
  if (failures.length === 0) lines.push("✓ 全部基准用例通过");
  process.stdout.write(lines.join("\n") + "\n");
}

main();
