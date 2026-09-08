/**
 * Canvas 2D 结构力学制图：受拉侧弯矩图、剪力图、轴力图与支座/节点图元
 *
 * 全部函数接收**世界坐标**（米）+ Viewport，内部再换算成像素。
 * 绝不要把像素长度当成杆长代入力学公式 —— 那是单位灾难的源头。
 */

import {
  type Point2D,
  type Viewport,
  worldToScreen,
} from "./viewport.ts";

/** 沿杆长的内力采样点：x 为距 i 端的距离(m)，value 为该截面内力 */
export interface DiagramSample {
  readonly x: number;
  readonly value: number;
}

/** 杆件世界坐标几何 */
export interface MemberGeometry {
  readonly start: Point2D; // 节点 i (m)
  readonly end: Point2D;   // 节点 j (m)
}

export interface DiagramStyle {
  readonly stroke: string;
  readonly fill: string;
  readonly hatch: boolean;
  readonly lineWidth: number;
}

export const BMD_STYLE: DiagramStyle = {
  stroke: "#2563EB", fill: "rgba(59,130,246,0.15)", hatch: true, lineWidth: 1.5,
};
export const SFD_STYLE: DiagramStyle = {
  stroke: "#DC2626", fill: "rgba(220,38,38,0.12)", hatch: false, lineWidth: 1.5,
};
export const AFD_STYLE: DiagramStyle = {
  stroke: "#059669", fill: "rgba(5,150,105,0.12)", hatch: false, lineWidth: 1.5,
};

interface MemberFrame {
  readonly p1: Point2D;      // i 端屏幕坐标
  readonly p2: Point2D;      // j 端屏幕坐标
  readonly lengthWorld: number;
  /** 局部 x 轴的屏幕单位向量 */
  readonly tangent: Point2D;
  /** 局部 -y 轴（正弯矩受拉侧）的屏幕单位向量 */
  readonly tensionNormal: Point2D;
}

/**
 * 建立杆件的屏幕局部坐标系。
 *
 * 核心结论：设世界坐标下 c = Δx/L, s = Δy/L，则
 *   局部 -y 方向（M>0 的受拉侧）在屏幕上是 (s, c)。
 * 因为世界方向 (dx,dy) 映射到屏幕方向是 (dx,-dy)，而局部 -y 的世界方向为 (s,-c)。
 *
 * 这条规则对水平梁、竖直柱、斜杆一律成立，无需分情况讨论：
 *   - 水平梁 (c=1,s=0)：正弯矩画在杆下方 ✓
 *   - 竖直柱 (c=0,s=1，i 在下)：正弯矩画在杆右侧 ✓
 * 颠倒 i/j 编号时 M 的符号与法线方向**同时**反转，图形物理位置不变。
 */
function buildFrame(geom: MemberGeometry, vp: Viewport): MemberFrame {
  const dx = geom.end.x - geom.start.x;
  const dy = geom.end.y - geom.start.y;
  const lengthWorld = Math.hypot(dx, dy);
  if (lengthWorld < 1e-9) throw new Error("杆件两端重合，无法建立局部坐标系。");

  const c = dx / lengthWorld;
  const s = dy / lengthWorld;

  return {
    p1: worldToScreen(geom.start.x, geom.start.y, vp),
    p2: worldToScreen(geom.end.x, geom.end.y, vp),
    lengthWorld,
    tangent: { x: c, y: -s },
    tensionNormal: { x: s, y: c },
  };
}

/** 把 (沿杆长 x, 内力值) 映射到屏幕点；normalSign = -1 用于剪力/轴力（画在局部 +y 侧） */
function plotPoint(
  frame: MemberFrame,
  vp: Viewport,
  x: number,
  value: number,
  valueScale: number,
  normalSign: 1 | -1
): Point2D {
  const along = x * vp.scale;
  const off = value * valueScale * normalSign;
  return {
    x: frame.p1.x + frame.tangent.x * along + frame.tensionNormal.x * off,
    y: frame.p1.y + frame.tangent.y * along + frame.tensionNormal.y * off,
  };
}

function baselinePoint(frame: MemberFrame, vp: Viewport, x: number): Point2D {
  return plotPoint(frame, vp, x, 0, 0, 1);
}

function drawDiagram(
  ctx: CanvasRenderingContext2D,
  geom: MemberGeometry,
  samples: readonly DiagramSample[],
  vp: Viewport,
  valueScale: number,
  style: DiagramStyle,
  normalSign: 1 | -1
): void {
  if (samples.length < 2) throw new Error("内力图至少需要 2 个采样点。");
  const frame = buildFrame(geom, vp);
  const pts = samples.map(s => plotPoint(frame, vp, s.x, s.value, valueScale, normalSign));

  ctx.save();

  if (style.hatch) {
    // 垂直于杆轴的密排细线（土木制图惯例）
    ctx.strokeStyle = style.stroke;
    ctx.globalAlpha = 0.35;
    ctx.lineWidth = 0.75;
    ctx.beginPath();
    samples.forEach((s, i) => {
      const base = baselinePoint(frame, vp, s.x);
      ctx.moveTo(base.x, base.y);
      ctx.lineTo(pts[i].x, pts[i].y);
    });
    ctx.stroke();
    ctx.globalAlpha = 1;
  }

  ctx.beginPath();
  ctx.moveTo(frame.p1.x, frame.p1.y);
  for (const p of pts) ctx.lineTo(p.x, p.y);
  ctx.lineTo(frame.p2.x, frame.p2.y);
  ctx.closePath();
  ctx.fillStyle = style.fill;
  ctx.fill();

  // 只描内力轮廓线，不描基线（基线由杆件本身表示）
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (const p of pts.slice(1)) ctx.lineTo(p.x, p.y);
  ctx.strokeStyle = style.stroke;
  ctx.lineWidth = style.lineWidth;
  ctx.stroke();

  ctx.restore();
}

/**
 * 弯矩图：画在受拉侧，**不标正负号**。
 * samples 的 value 取"下侧受拉为正"的弯矩 M(x)，单位 N*m。
 */
export function drawMomentDiagram(
  ctx: CanvasRenderingContext2D,
  geom: MemberGeometry,
  samples: readonly DiagramSample[],
  vp: Viewport,
  momentScale: number,
  style: DiagramStyle = BMD_STYLE
): void {
  drawDiagram(ctx, geom, samples, vp, momentScale, style, 1);
}

/** 剪力图：正值画在局部 +y 侧，**必须标正负号** */
export function drawShearDiagram(
  ctx: CanvasRenderingContext2D,
  geom: MemberGeometry,
  samples: readonly DiagramSample[],
  vp: Viewport,
  shearScale: number,
  style: DiagramStyle = SFD_STYLE
): void {
  drawDiagram(ctx, geom, samples, vp, shearScale, style, -1);
}

/** 轴力图：受拉为正，画在局部 +y 侧，**必须标正负号** */
export function drawAxialDiagram(
  ctx: CanvasRenderingContext2D,
  geom: MemberGeometry,
  samples: readonly DiagramSample[],
  vp: Viewport,
  axialScale: number,
  style: DiagramStyle = AFD_STYLE
): void {
  drawDiagram(ctx, geom, samples, vp, axialScale, style, -1);
}

/**
 * 内力数值标注。文字**永远水平书写**，不随杆件旋转，否则竖杆上的字会倒置。
 * showSign=false 用于弯矩图（受拉侧已表达了物理含义）。
 */
export function drawValueLabel(
  ctx: CanvasRenderingContext2D,
  geom: MemberGeometry,
  vp: Viewport,
  x: number,
  value: number,
  valueScale: number,
  options: { showSign?: boolean; normalSign?: 1 | -1; unit?: string; digits?: number } = {}
): void {
  const { showSign = true, normalSign = 1, unit = "kN·m", digits = 2 } = options;
  const frame = buildFrame(geom, vp);
  const anchor = plotPoint(frame, vp, x, value, valueScale, normalSign);
  const pad = 6;

  const magnitude = Math.abs(value) / 1000; // N -> kN, N*m -> kN*m
  const text = showSign
    ? `${value < 0 ? "-" : "+"}${magnitude.toFixed(digits)}`
    : magnitude.toFixed(digits);

  ctx.save();
  ctx.font = "12px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const px = anchor.x + frame.tensionNormal.x * pad * normalSign;
  const py = anchor.y + frame.tensionNormal.y * pad * normalSign;

  const width = ctx.measureText(`${text} ${unit}`).width;
  ctx.fillStyle = "rgba(255,255,255,0.85)";
  ctx.fillRect(px - width / 2 - 3, py - 9, width + 6, 18);
  ctx.fillStyle = "#0F172A";
  ctx.fillText(`${text} ${unit}`, px, py);
  ctx.restore();
}

// ---------------- 支座与节点图元 ----------------

/**
 * 支座图元统一以世界坐标节点为基准绘制。
 * groundAngle：接地面法线相对屏幕"向上"的旋转角（弧度）。
 *   0     → 支座在节点下方（最常见）
 *   π/2   → 支座在节点左侧（用于水平约束）
 */
function withSupportFrame(
  ctx: CanvasRenderingContext2D,
  node: Point2D,
  vp: Viewport,
  groundAngle: number,
  draw: () => void
): void {
  const p = worldToScreen(node.x, node.y, vp);
  ctx.save();
  ctx.translate(p.x, p.y);
  ctx.rotate(groundAngle);
  ctx.strokeStyle = "#1E293B";
  ctx.fillStyle = "#E2E8F0";
  ctx.lineWidth = 1.5;
  ctx.lineCap = "round";
  draw();
  ctx.restore();
}

/** 接地剖面线：45° 均匀斜线 */
function drawGroundHatch(ctx: CanvasRenderingContext2D, y: number, halfWidth: number, step = 7): void {
  ctx.beginPath();
  ctx.moveTo(-halfWidth, y);
  ctx.lineTo(halfWidth, y);
  ctx.stroke();

  ctx.beginPath();
  for (let x = -halfWidth; x <= halfWidth - step; x += step) {
    ctx.moveTo(x, y + step);
    ctx.lineTo(x + step, y);
  }
  ctx.lineWidth = 1;
  ctx.stroke();
}

/** 固定铰支座：尖端指向节点的三角形 + 接地剖面线 */
export function drawPinnedSupport(
  ctx: CanvasRenderingContext2D,
  node: Point2D,
  vp: Viewport,
  size = 16,
  groundAngle = 0
): void {
  withSupportFrame(ctx, node, vp, groundAngle, () => {
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-size * 0.55, size);
    ctx.lineTo(size * 0.55, size);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
    drawGroundHatch(ctx, size, size * 0.9);
  });
}

/** 活动铰支座：三角形 + 滚轴 + 接地剖面线 */
export function drawRollerSupport(
  ctx: CanvasRenderingContext2D,
  node: Point2D,
  vp: Viewport,
  size = 16,
  groundAngle = 0
): void {
  withSupportFrame(ctx, node, vp, groundAngle, () => {
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(-size * 0.55, size);
    ctx.lineTo(size * 0.55, size);
    ctx.closePath();
    ctx.fill();
    ctx.stroke();

    const r = size * 0.18;
    for (const cx of [-size * 0.33, size * 0.33]) {
      ctx.beginPath();
      ctx.arc(cx, size + r, r, 0, Math.PI * 2);
      ctx.fillStyle = "#FFFFFF";
      ctx.fill();
      ctx.stroke();
    }
    drawGroundHatch(ctx, size + 2 * r, size * 0.9);
  });
}

/** 固定端支座：垂直于杆端的粗实线基底 + 45° 剖面线 */
export function drawFixedSupport(
  ctx: CanvasRenderingContext2D,
  node: Point2D,
  vp: Viewport,
  size = 16,
  groundAngle = 0
): void {
  withSupportFrame(ctx, node, vp, groundAngle, () => {
    ctx.lineWidth = 2.5;
    drawGroundHatch(ctx, 0, size);
  });
}

/** 铰结点：空心白色小圆圈，半径 4~6px */
export function drawHingeJoint(
  ctx: CanvasRenderingContext2D,
  node: Point2D,
  vp: Viewport,
  radius = 5
): void {
  const p = worldToScreen(node.x, node.y, vp);
  ctx.save();
  ctx.beginPath();
  ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
  ctx.fillStyle = "#FFFFFF";
  ctx.fill();
  ctx.strokeStyle = "#1E293B";
  ctx.lineWidth = 1.5;
  ctx.stroke();
  ctx.restore();
}

/** 刚结点：加粗实心点 */
export function drawRigidJoint(
  ctx: CanvasRenderingContext2D,
  node: Point2D,
  vp: Viewport,
  radius = 3.5
): void {
  const p = worldToScreen(node.x, node.y, vp);
  ctx.save();
  ctx.beginPath();
  ctx.arc(p.x, p.y, radius, 0, Math.PI * 2);
  ctx.fillStyle = "#1E293B";
  ctx.fill();
  ctx.restore();
}

/** 杆件轴线 */
export function drawMember(
  ctx: CanvasRenderingContext2D,
  geom: MemberGeometry,
  vp: Viewport,
  color = "#0F172A",
  lineWidth = 2.5
): void {
  const p1 = worldToScreen(geom.start.x, geom.start.y, vp);
  const p2 = worldToScreen(geom.end.x, geom.end.y, vp);
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(p1.x, p1.y);
  ctx.lineTo(p2.x, p2.y);
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.stroke();
  ctx.restore();
}
