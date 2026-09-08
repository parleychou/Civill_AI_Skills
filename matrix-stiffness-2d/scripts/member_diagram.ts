/**
 * 杆件内力沿杆长的连续分布采样
 *
 * 直接刚度法只解出杆端力，跨间任意截面的内力必须由杆端力 + 荷载特解叠加得到。
 * 只用杆端弯矩线性插值会漏掉均布荷载的抛物线部分 —— 这是最常见的出图错误。
 *
 * 由杆端力 [Ni, Vi, Mi] 与局部 -y 均布荷载 q，取 i 端为原点、沿局部 x 距离 x 处：
 *   N(x) = -Ni                          （受拉为正，无轴向分布荷载时为常量）
 *   V(x) = Vi - q * x                   （顺时针使微元转动为正）
 *   M(x) = -Mi + Vi * x - q * x^2 / 2   （下侧受拉即"正弯矩"，与土木习惯一致）
 */

import type { MemberEndForces } from "./solver_2d.ts";

export interface SectionForces {
  /** 距 i 端的局部坐标 m */
  readonly x: number;
  readonly N: number; // N，受拉为正
  readonly V: number; // N
  readonly M: number; // N*m，下侧受拉为正
}

export interface MemberDiagram {
  readonly samples: readonly SectionForces[];
  /** 绝对值最大的弯矩截面，用于自动标注 */
  readonly maxAbsMoment: SectionForces;
  /** 最大正弯矩（下侧受拉）截面 */
  readonly maxSaggingMoment: SectionForces;
  /** 最大负弯矩（上侧受拉）截面 */
  readonly maxHoggingMoment: SectionForces;
  /** 绝对值最大的剪力截面 */
  readonly maxAbsShear: SectionForces;
}

export function sectionForcesAt(
  forces: MemberEndForces,
  q: number,
  x: number
): SectionForces {
  return {
    x,
    N: -forces.Ni,
    V: forces.Vi - q * x,
    M: -forces.Mi + forces.Vi * x - (q * x * x) / 2,
  };
}

/**
 * 沿杆长均匀采样内力，并额外插入剪力零点（弯矩极值截面），
 * 保证抛物线顶点不会因采样间隔而被漏掉。
 */
export function sampleMemberDiagram(
  forces: MemberEndForces,
  q: number,
  segments = 20
): MemberDiagram {
  if (!Number.isFinite(q)) throw new Error("均布荷载 q 非法。");
  if (segments < 2) throw new Error("采样段数至少为 2。");

  const L = forces.length;
  const stations = new Set<number>();
  for (let i = 0; i <= segments; i++) stations.add((i / segments) * L);

  // 剪力零点 x* = Vi / q 即为弯矩驻点
  if (q !== 0) {
    const xExtreme = forces.Vi / q;
    if (xExtreme > 0 && xExtreme < L) stations.add(xExtreme);
  }

  const samples = [...stations]
    .sort((a, b) => a - b)
    .map(x => sectionForcesAt(forces, q, x));

  const maxAbsMoment = samples.reduce((best, s) =>
    Math.abs(s.M) > Math.abs(best.M) ? s : best
  );
  const maxSaggingMoment = samples.reduce((best, s) => (s.M > best.M ? s : best));
  const maxHoggingMoment = samples.reduce((best, s) => (s.M < best.M ? s : best));
  const maxAbsShear = samples.reduce((best, s) =>
    Math.abs(s.V) > Math.abs(best.V) ? s : best
  );

  return { samples, maxAbsMoment, maxSaggingMoment, maxHoggingMoment, maxAbsShear };
}
