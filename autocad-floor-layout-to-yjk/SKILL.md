---
name: autocad-floor-layout-to-yjk
description: AutoCAD 建筑平面图提取与单层结构平面布置转 YJK 模型工作流 Skill。支持轴网提取、墙柱梁识别与 YDB 模型转换。
---

# AutoCAD Floor Layout To YJK Model

## Overview

本 Skill 用于从单层建筑平面图 DWG 提取轴网与几何边界，并自动完成结构构件布置与 YJK 模型（.ydb）转换。

## Core Capabilities

1. **CAD 图元提取**：通过 pyautocad / COM 接口提取轴网、轴号、墙体与柱位。
2. **结构平面布置**：根据开间与进深规则自动布置主梁、次梁与楼板。
3. **YJK 模型转换**：将结构几何与截面参数写入 YJK 数据库表。
