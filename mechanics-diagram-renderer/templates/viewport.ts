/**
 * 物理世界坐标 (m, Y 向上) ↔ Canvas 像素坐标 (px, Y 向下) 的视口映射
 *
 * 三条硬性要求：
 *   1. X/Y 必须用**同一个** scale，否则结构会被拉伸变形，斜杆角度全错。
 *   2. Y 轴必须翻转。
 *   3. 必须处理 devicePixelRatio，否则高分屏上线条发虚。
 */

export interface Viewport {
  /** 像素 / 米，X 与 Y 共用 */
  readonly scale: number;
  readonly offsetX: number;
  readonly offsetY: number;
  /** CSS 像素尺寸（非物理像素） */
  readonly width: number;
  readonly height: number;
  readonly xMin: number;
  readonly yMin: number;
}

export interface Point2D {
  readonly x: number;
  readonly y: number;
}

/**
 * x_screen = (x_world - x_min) * scale + offsetX
 * y_screen = height - [ (y_world - y_min) * scale + offsetY ]
 */
export function worldToScreen(wx: number, wy: number, vp: Viewport): Point2D {
  return {
    x: (wx - vp.xMin) * vp.scale + vp.offsetX,
    y: vp.height - ((wy - vp.yMin) * vp.scale + vp.offsetY),
  };
}

/** 世界坐标下的**方向向量**转屏幕方向：只翻转 Y，不加平移 */
export function worldDirToScreen(dx: number, dy: number): Point2D {
  return { x: dx, y: -dy };
}

/**
 * 自适应视口：把结构等比例居中铺满画布，四周留 padding。
 * padding 需同时容纳支座图元与内力图外伸量，建议不小于 60px。
 */
export function fitViewport(
  points: readonly Point2D[],
  width: number,
  height: number,
  padding = 60
): Viewport {
  if (points.length === 0) throw new Error("视口拟合需要至少一个节点坐标。");
  if (width <= 2 * padding || height <= 2 * padding) {
    throw new Error(`画布尺寸 ${width}x${height} 不足以容纳 ${padding}px 边距。`);
  }

  const xs = points.map(p => p.x);
  const ys = points.map(p => p.y);
  const xMin = Math.min(...xs);
  const xMax = Math.max(...xs);
  const yMin = Math.min(...ys);
  const yMax = Math.max(...ys);

  const spanX = xMax - xMin;
  const spanY = yMax - yMin;
  const usableW = width - 2 * padding;
  const usableH = height - 2 * padding;

  // 单跨连续梁 spanY 为 0，退化情况下不能用它算比例
  const scaleX = spanX > 1e-9 ? usableW / spanX : Number.POSITIVE_INFINITY;
  const scaleY = spanY > 1e-9 ? usableH / spanY : Number.POSITIVE_INFINITY;
  const scale = Math.min(scaleX, scaleY);
  if (!Number.isFinite(scale)) {
    throw new Error("所有节点重合，无法确定绘图比例。");
  }

  return {
    scale,
    offsetX: padding + (usableW - spanX * scale) / 2,
    offsetY: padding + (usableH - spanY * scale) / 2,
    width,
    height,
    xMin,
    yMin,
  };
}

/**
 * 内力图比例尺：把最大内力映射为指定像素高度。
 * 同一张图上 BMD / SFD / AFD 各自独立取比例，但**同类图必须全模型统一**，
 * 否则各杆之间的大小关系会失真。
 */
export function forceScale(maxAbsValue: number, targetPixels: number): number {
  if (!(targetPixels > 0)) throw new Error("目标像素高度必须为正。");
  if (!(maxAbsValue > 0)) return 0; // 内力恒为 0，图形退化为基线
  return targetPixels / maxAbsValue;
}

/**
 * 按 devicePixelRatio 配置画布，返回已缩放好的 2D 上下文。
 * 之后所有绘图指令都用 CSS 像素坐标书写。
 */
export function setupCanvas(
  canvas: HTMLCanvasElement,
  cssWidth: number,
  cssHeight: number
): CanvasRenderingContext2D {
  const dpr = globalThis.devicePixelRatio || 1;
  canvas.width = Math.round(cssWidth * dpr);
  canvas.height = Math.round(cssHeight * dpr);
  canvas.style.width = `${cssWidth}px`;
  canvas.style.height = `${cssHeight}px`;

  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("无法获取 Canvas 2D 上下文。");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  return ctx;
}
