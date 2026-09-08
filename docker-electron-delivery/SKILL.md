---
name: docker-electron-delivery
description: 结构分析软件 Web 容器化与 Electron 跨平台桌面客户端双形态打包交付指南与脚手架。
---

# 结构求解器双形态打包与交付 (docker-electron-delivery)

## 交付形态 1：Docker 容器化 (Web 端私有化部署)
- **体积目标**：< 25MB (Multi-stage 构建，基于 `node:22-alpine` 编译 + `nginx:alpine` 静态托管)。
- **安全与性能**：启用 Gzip / Brotli 压缩，开启浏览器 Cache-Control。

## 交付形态 2：Electron 桌面端 (离线原生 .exe / .dmg)
- **使用场景**：施工现场/断网环境、需要直接读取本地 CAD/DWG/SQLite 文件的重度桌面客户端。
- **架构原则**：主进程（Node.js OS API 访问）+ 渲染进程（Vue 3 / Canvas 界面），通过 IPC 通信桥接。
