"""02_connect_and_basic_shapes.py
示例 2：探测 Rhino 安装环境、建立 COM 连接并生成基础几何图元。

功能覆盖：
- 自动从 Windows 注册表扫描已安装的 Rhino 8 / 7 / 6 路径
- 检查后台当前运行的 Rhino 进程
- 建立安全 COM 连接获取 IRhinoScript 强类型句柄
- 演示图层管理与 RGB 颜色定义（rgb(r, g, b)）
- 批量创建点、线、圆、球体、圆柱体等标量图元
- 启用/恢复视口重绘保护（EnableRedraw）
"""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_ROOT))

from rhinorouter import (
    find_rhino_install_paths,
    find_rhino_process,
    get_rhino,
    rgb,
)


def main():
    print("=== Rhino 环境检测与基础建模示例 ===\n")

    # 1. 扫描本机安装环境
    installs = find_rhino_install_paths()
    print(f"[1. 本机已安装 Rhino 版本] 共检测到 {len(installs)} 个安装:")
    for ver_str, path in installs:
        print(f"  - Rhino {ver_str}: {path}")

    # 2. 检查是否有活跃的 Rhino 进程
    pid, cwd, exe, cmdline = find_rhino_process()
    should_launch = "--launch" in sys.argv
    if pid:
        print(f"\n[2. 活跃进程] 检测到正在运行的 Rhino 实例 (PID={pid}): {exe}")
    else:
        print("\n[2. 活跃进程] 当前无运行中的 Rhino 进程。")
        if not should_launch:
            print("  [提示] 运行 python 02_connect_and_basic_shapes.py --launch 可在本地自动唤起 Rhino 窗口。")

    # 3. 尝试建立连接
    print("\n[3. 正在尝试连接 Rhino COM 接口...]")
    result = get_rhino(auto_spawn=should_launch)
    if isinstance(result, str):
        print(f"  [连接提示] {result}")
        print("  当前未建立图形会话属于正常现象；在宿主图形环境下启动 Rhino 即可直接连接附着。")
        return

    rhino, rs, version = result
    print(f"  [连接成功] 成功附着到 Rhino {version} 实例！")

    # 4. 基础建模与图层配置
    # 注意：涉及大量图元时使用 EnableRedraw 加速，且必须使用 try...finally 恢复
    try:
        rs.EnableRedraw(False)

        # 4.1 新建图层
        layer_name = "AI_Demo_Layer"
        if not rs.IsLayer(layer_name):
            rs.AddLayer(layer_name, rgb(0, 150, 255))
            print(f"  - 已创建图层: {layer_name}")
        rs.CurrentLayer(layer_name)

        # 4.2 创建基础点与线段
        pt_id = rs.AddPoint([0, 0, 0])
        line_id = rs.AddLine([0, 0, 0], [100, 0, 0])
        print(f"  - 点与线段已创建: Point ID={pt_id}, Line ID={line_id}")

        # 4.3 创建圆 (WorldXY 平面, 半径 50)
        circle_id = rs.AddCircle([0, 0, 0], 50)
        print(f"  - 圆已创建: Circle ID={circle_id}")

        # 4.4 创建球体与圆柱体
        sphere_id = rs.AddSphere([0, 0, 50], 30)
        cyl_id = rs.AddCylinder([150, 0, 0], [150, 0, 100], 25)
        print(f"  - 实体已创建: Sphere ID={sphere_id}, Cylinder ID={cyl_id}")

    finally:
        rs.EnableRedraw(True)
        print("  - 视口重绘已恢复")


if __name__ == "__main__":
    main()
