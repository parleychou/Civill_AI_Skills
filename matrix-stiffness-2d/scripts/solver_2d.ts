/**
 * 2D 平面杆系直接刚度法（矩阵位移法）求解引擎
 *
 * 符号约定（全文件统一，修改前请先读 SKILL.md「符号约定」一节）：
 *   - 整体坐标：X 向右为正，Y 向上为正，转角 θz 逆时针为正。
 *   - 节点自由度顺序：[u, v, θz]，第 n 号节点占用 3n, 3n+1, 3n+2。
 *   - 局部坐标：x 轴由节点 i 指向节点 j，y 轴为 x 轴逆时针旋转 90°。
 *   - 杆间均布荷载 q：作用于局部 -y 方向的线荷载集度，q > 0 表示"压向杆件下侧"。
 *   - 杆端力 F = [Ni, Vi, Mi, Nj, Vj, Mj]：节点作用于杆端的力，方向与局部自由度正向一致。
 */

export interface Node2D {
  readonly id: number;
  readonly x: number; // m
  readonly y: number; // m
  /** [dx 约束, dy 约束, rz 约束]，true 表示该自由度被支座锁死为 0 */
  readonly fixity: readonly [boolean, boolean, boolean];
}

export interface Element2D {
  readonly id: number;
  readonly nodeI: number;
  readonly nodeJ: number;
  readonly E: number; // 弹性模量 Pa
  readonly A: number; // 截面面积 m^2
  readonly I: number; // 截面惯性矩 m^4
  /** 局部 -y 方向均布荷载集度 N/m，无荷载填 0 */
  readonly q: number;
  /** i 端弯矩释放（铰接）。两端都释放即为桁架二力杆。默认 false */
  readonly releaseI?: boolean;
  /** j 端弯矩释放（铰接）。默认 false */
  readonly releaseJ?: boolean;
}

export interface NodeLoad2D {
  readonly nodeId: number;
  readonly fx: number; // N，整体 X 正向
  readonly fy: number; // N，整体 Y 正向
  readonly mz: number; // N*m，逆时针为正
}

/** 杆端力（局部坐标），单位 N / N*m */
export interface MemberEndForces {
  readonly Ni: number;
  readonly Vi: number;
  readonly Mi: number;
  readonly Nj: number;
  readonly Vj: number;
  readonly Mj: number;
  /** 杆件轴力，受拉为正（= -Ni），便于直接绘制轴力图 */
  readonly axial: number;
  /** 杆长 m，供内力图采样复用 */
  readonly length: number;
}

export interface SolverResult2D {
  readonly displacements: Record<number, { dx: number; dy: number; rz: number }>;
  readonly memberForces: Record<number, MemberEndForces>;
  /** 仅约束自由度上有值；未约束方向恒为 0 */
  readonly reactions: Record<number, { rx: number; ry: number; rm: number }>;
}

/** 单元几何与刚度中间量，装配与内力回代共用，避免重复推导 */
interface ElementKinematics {
  readonly L: number;
  readonly kLocal: readonly (readonly number[])[];
  readonly T: readonly (readonly number[])[];
  readonly f0Local: readonly number[];
  readonly dofs: readonly number[];
}

export function solveStructure2D(
  nodes: readonly Node2D[],
  elements: readonly Element2D[],
  loads: readonly NodeLoad2D[]
): SolverResult2D {
  validateModel(nodes, elements, loads);

  const indexOfNode = new Map(nodes.map((n, i) => [n.id, i]));
  const numDOFs = nodes.length * 3;

  const K = Array.from({ length: numDOFs }, () => new Float64Array(numDOFs));
  const P = new Float64Array(numDOFs);

  for (const ld of loads) {
    const base = indexOfNode.get(ld.nodeId)! * 3;
    P[base] += ld.fx;
    P[base + 1] += ld.fy;
    P[base + 2] += ld.mz;
  }

  const kinematics = elements.map(elem => buildElementKinematics(elem, nodes, indexOfNode));

  elements.forEach((elem, e) => {
    const { kLocal, T, f0Local, dofs } = kinematics[e];

    // Kg = T^T * kl * T
    const kGlobal = multiplyMatrices(transpose(T), multiplyMatrices(kLocal, T));
    for (let r = 0; r < 6; r++) {
      for (let col = 0; col < 6; col++) {
        K[dofs[r]][dofs[col]] += kGlobal[r][col];
      }
    }

    // 等效节点荷载 = -T^T * 固端力
    if (elem.q !== 0) {
      const f0Global = multiplyMatrixVector(transpose(T), f0Local);
      for (let r = 0; r < 6; r++) P[dofs[r]] -= f0Global[r];
    }
  });

  // 边界条件：划行划列（缩减自由度），保留原始 K 用于反力回代
  let stiffnessScale = 0;
  for (let i = 0; i < numDOFs; i++) stiffnessScale = Math.max(stiffnessScale, Math.abs(K[i][i]));
  const looseTol = stiffnessScale * 1e-12;

  const freeDOFs: number[] = [];
  for (let i = 0; i < nodes.length; i++) {
    for (let d = 0; d < 3; d++) {
      const dof = i * 3 + d;
      if (nodes[i].fixity[d]) continue;

      // 全铰接节点（纯桁架）的转角自由度没有任何刚度贡献，
      // 直接剔除而不是让总刚奇异；但若其上有荷载则确属几何可变。
      let rowMax = 0;
      for (let c = 0; c < numDOFs; c++) rowMax = Math.max(rowMax, Math.abs(K[dof][c]));
      if (rowMax <= looseTol) {
        if (Math.abs(P[dof]) > 1e-9) {
          throw new Error(
            `节点 ${nodes[i].id} 的第 ${d + 1} 个自由度无任何刚度却承受荷载：结构为几何可变体系。`
          );
        }
        continue;
      }
      freeDOFs.push(dof);
    }
  }
  if (freeDOFs.length === 0) {
    throw new Error("模型全部自由度均被约束，无可解未知量。");
  }

  const Kff = freeDOFs.map(r => {
    const row = new Float64Array(freeDOFs.length);
    for (let c = 0; c < freeDOFs.length; c++) row[c] = K[r][freeDOFs[c]];
    return row;
  });
  const Pf = new Float64Array(freeDOFs.map(r => P[r]));

  const Uf = solveLinearSystem(Kff, Pf);

  const U = new Float64Array(numDOFs);
  freeDOFs.forEach((dof, i) => {
    U[dof] = Uf[i];
  });

  // 反力：R = K*U - P，仅在约束自由度上取值
  const KU = new Float64Array(numDOFs);
  for (let r = 0; r < numDOFs; r++) {
    let sum = 0;
    for (let c = 0; c < numDOFs; c++) sum += K[r][c] * U[c];
    KU[r] = sum;
  }

  const displacements: SolverResult2D["displacements"] = {};
  const reactions: SolverResult2D["reactions"] = {};
  nodes.forEach((node, i) => {
    displacements[node.id] = { dx: U[i * 3], dy: U[i * 3 + 1], rz: U[i * 3 + 2] };
    reactions[node.id] = {
      rx: node.fixity[0] ? KU[i * 3] - P[i * 3] : 0,
      ry: node.fixity[1] ? KU[i * 3 + 1] - P[i * 3 + 1] : 0,
      rm: node.fixity[2] ? KU[i * 3 + 2] - P[i * 3 + 2] : 0,
    };
  });

  const memberForces: SolverResult2D["memberForces"] = {};
  elements.forEach((elem, e) => {
    const { kLocal, T, f0Local, dofs, L } = kinematics[e];
    const uGlobal = dofs.map(dof => U[dof]);
    const uLocal = multiplyMatrixVector(T, uGlobal);
    const f = multiplyMatrixVector(kLocal, uLocal).map((v, i) => v + f0Local[i]);
    memberForces[elem.id] = {
      Ni: f[0], Vi: f[1], Mi: f[2],
      Nj: f[3], Vj: f[4], Mj: f[5],
      axial: -f[0],
      length: L,
    };
  });

  return { displacements, memberForces, reactions };
}

function buildElementKinematics(
  elem: Element2D,
  nodes: readonly Node2D[],
  indexOfNode: ReadonlyMap<number, number>
): ElementKinematics {
  const iIdx = indexOfNode.get(elem.nodeI)!;
  const jIdx = indexOfNode.get(elem.nodeJ)!;
  const ni = nodes[iIdx];
  const nj = nodes[jIdx];

  const L = Math.hypot(nj.x - ni.x, nj.y - ni.y);
  const c = (nj.x - ni.x) / L;
  const s = (nj.y - ni.y) / L;

  const EA_L = (elem.E * elem.A) / L;
  const EI12_L3 = (12 * elem.E * elem.I) / (L * L * L);
  const EI6_L2 = (6 * elem.E * elem.I) / (L * L);
  const EI4_L = (4 * elem.E * elem.I) / L;
  const EI2_L = (2 * elem.E * elem.I) / L;

  const kLocal = [
    [EA_L, 0, 0, -EA_L, 0, 0],
    [0, EI12_L3, EI6_L2, 0, -EI12_L3, EI6_L2],
    [0, EI6_L2, EI4_L, 0, -EI6_L2, EI2_L],
    [-EA_L, 0, 0, EA_L, 0, 0],
    [0, -EI12_L3, -EI6_L2, 0, EI12_L3, -EI6_L2],
    [0, EI6_L2, EI2_L, 0, -EI6_L2, EI4_L],
  ];

  const T = [
    [c, s, 0, 0, 0, 0],
    [-s, c, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 0],
    [0, 0, 0, c, s, 0],
    [0, 0, 0, -s, c, 0],
    [0, 0, 0, 0, 0, 1],
  ];

  // 两端固定梁在局部 -y 均布荷载 q 下的固端力
  const f0Local = [
    0, (elem.q * L) / 2, (elem.q * L * L) / 12,
    0, (elem.q * L) / 2, (-elem.q * L * L) / 12,
  ];

  // 杆端铰接：对被释放的转角自由度做静力凝聚，使该端弯矩恒为 0
  const released: number[] = [];
  if (elem.releaseI) released.push(2);
  if (elem.releaseJ) released.push(5);
  const { k: kReleased, f0: f0Released } = condenseReleases(kLocal, f0Local, released);

  const dofs = [
    iIdx * 3, iIdx * 3 + 1, iIdx * 3 + 2,
    jIdx * 3, jIdx * 3 + 1, jIdx * 3 + 2,
  ];

  return { L, kLocal: kReleased, T, f0Local: f0Released, dofs };
}

/**
 * 静力凝聚杆端释放自由度：
 *   k* = k - k[:,r] k[r,:] / k[r,r]，  f0* = f0 - k[:,r] f0[r] / k[r,r]
 * 逐个释放，凝聚后第 r 行列清零，该端对应的杆端力自动为 0。
 */
function condenseReleases(
  kLocal: readonly (readonly number[])[],
  f0Local: readonly number[],
  released: readonly number[]
): { k: number[][]; f0: number[] } {
  let k = kLocal.map(row => [...row]);
  let f0 = [...f0Local];

  for (const r of released) {
    const krr = k[r][r];
    if (Math.abs(krr) < 1e-30) continue; // 已被前一次释放清零，无需重复凝聚
    const col = k.map(row => row[r]);
    const row = [...k[r]];
    const fr = f0[r];

    k = k.map((kRow, i) => kRow.map((v, j) => v - (col[i] * row[j]) / krr));
    f0 = f0.map((v, i) => v - (col[i] * fr) / krr);

    for (let i = 0; i < 6; i++) {
      k[i][r] = 0;
      k[r][i] = 0;
    }
    f0[r] = 0;
  }

  return { k, f0 };
}

function validateModel(
  nodes: readonly Node2D[],
  elements: readonly Element2D[],
  loads: readonly NodeLoad2D[]
): void {
  if (nodes.length < 2) throw new Error("模型至少需要 2 个节点。");
  if (elements.length < 1) throw new Error("模型至少需要 1 个单元。");

  const seen = new Set<number>();
  for (const n of nodes) {
    if (seen.has(n.id)) throw new Error(`节点编号重复：${n.id}`);
    seen.add(n.id);
    if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) {
      throw new Error(`节点 ${n.id} 坐标非法。`);
    }
  }

  const nodeById = new Map(nodes.map(n => [n.id, n]));
  const elemIds = new Set<number>();
  for (const el of elements) {
    if (elemIds.has(el.id)) throw new Error(`单元编号重复：${el.id}`);
    elemIds.add(el.id);

    const ni = nodeById.get(el.nodeI);
    const nj = nodeById.get(el.nodeJ);
    if (!ni) throw new Error(`单元 ${el.id} 引用了不存在的节点 ${el.nodeI}`);
    if (!nj) throw new Error(`单元 ${el.id} 引用了不存在的节点 ${el.nodeJ}`);

    const L = Math.hypot(nj.x - ni.x, nj.y - ni.y);
    if (L < 1e-9) throw new Error(`单元 ${el.id} 长度为零（节点 ${el.nodeI} 与 ${el.nodeJ} 重合）。`);
    if (!(el.E > 0)) throw new Error(`单元 ${el.id} 的 E 必须为正数。`);
    if (!(el.A > 0)) throw new Error(`单元 ${el.id} 的 A 必须为正数。`);
    if (!(el.I > 0)) throw new Error(`单元 ${el.id} 的 I 必须为正数。`);
    if (!Number.isFinite(el.q)) throw new Error(`单元 ${el.id} 的 q 非法。`);
  }

  for (const ld of loads) {
    if (!nodeById.has(ld.nodeId)) {
      throw new Error(`节点荷载引用了不存在的节点 ${ld.nodeId}`);
    }
    if (!Number.isFinite(ld.fx) || !Number.isFinite(ld.fy) || !Number.isFinite(ld.mz)) {
      throw new Error(`节点 ${ld.nodeId} 的荷载值非法。`);
    }
  }
}

// ---------------- 矩阵运算工具 ----------------

function transpose(m: readonly (readonly number[])[]): number[][] {
  return m[0].map((_, i) => m.map(row => row[i]));
}

function multiplyMatrices(
  a: readonly (readonly number[])[],
  b: readonly (readonly number[])[]
): number[][] {
  const res: number[][] = Array.from({ length: a.length }, () => new Array(b[0].length).fill(0));
  for (let i = 0; i < a.length; i++) {
    for (let k = 0; k < b.length; k++) {
      const aik = a[i][k];
      if (aik === 0) continue;
      for (let j = 0; j < b[0].length; j++) res[i][j] += aik * b[k][j];
    }
  }
  return res;
}

function multiplyMatrixVector(
  m: readonly (readonly number[])[],
  v: readonly number[]
): number[] {
  return m.map(row => row.reduce((sum, val, i) => sum + val * v[i], 0));
}

/**
 * 高斯消元 + 列主元。奇异（几何可变 / 约束不足）时抛错，
 * 而不是静默返回 NaN —— 这是初学者最容易踩的坑。
 */
function solveLinearSystem(A: readonly Float64Array[], b: Float64Array): Float64Array {
  const n = b.length;
  const M = A.map((row, i) => {
    const r = new Float64Array(n + 1);
    r.set(row);
    r[n] = b[i];
    return r;
  });

  let scale = 0;
  for (let i = 0; i < n; i++) scale = Math.max(scale, Math.abs(M[i][i]));
  const tolerance = Math.max(scale, 1) * 1e-12;

  for (let p = 0; p < n; p++) {
    let maxRow = p;
    for (let i = p + 1; i < n; i++) {
      if (Math.abs(M[i][p]) > Math.abs(M[maxRow][p])) maxRow = i;
    }
    if (Math.abs(M[maxRow][p]) < tolerance) {
      throw new Error(
        `总刚度矩阵奇异（自由度 ${p} 主元近似为 0）：结构可能约束不足或存在几何可变机构。`
      );
    }
    const swap = M[p];
    M[p] = M[maxRow];
    M[maxRow] = swap;

    const pivot = M[p][p];
    for (let j = p; j <= n; j++) M[p][j] /= pivot;
    for (let i = 0; i < n; i++) {
      if (i === p) continue;
      const factor = M[i][p];
      if (factor === 0) continue;
      for (let j = p; j <= n; j++) M[i][j] -= factor * M[p][j];
    }
  }

  const x = new Float64Array(n);
  for (let i = 0; i < n; i++) x[i] = M[i][n];
  return x;
}
