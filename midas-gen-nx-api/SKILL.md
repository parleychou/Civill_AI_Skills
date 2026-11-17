---
name: MIDAS Gen NX API
description: >-
  当用户要研究或使用 MIDAS Gen NX REST/JSON API 进行建模、分析、设计或结果提取时使用。当前为待实机验证的初版；缺少 Gen
  专用字段正文，不能直接执行 Civil 示例。
---
# MIDAS Gen NX Open API（初版）

## 范围与证据限制
用于 MIDAS Gen NX，先确认实际产品与版本。不要把 Gen NX 默认当成经典 Gen，也不要混用 Civil NX。本包未在真实 Gen NX 会话中实测。已读资料确认 Gen NX 连接说明和 NX 总目录，但没有完整读取 Gen 专用字段手册；多数示例来自 Civil NX，只能旁证，不能当成 Gen 已验证用法。

## 工作流程
1. 先读 `references/product-scope.md`、`sources.md`、`limitations.md`。旧 FAQ 和计划发布时间不代表当前所有版本，依据用户实际软件及当前官方文档确认能力。
2. 在当前 Gen NX API 设置确认连接状态，获取 Base URL；密钥走安全输入或环境，不索要聊天明文、不写日志或技能文件。请求头包含 `Content-Type: application/json`、`MAPI-Key`，不猜端口或主机。
3. 用 `references/endpoint-index.md` 找候选路由，再读取当前 Gen NX 对应的接口正文核对 HTTP 方法、字段、枚举、适用版本。NX 共享目录不代表每一产品支持全部接口，楼层/墙/设计等名称也不构成支持证据。
4. 读取 `examples/PROVENANCE.md`。来自 Civil NX 的节点、单元、材料、单位、梁模型等示例，必须先取得 Gen 文档或已验证导出结构逐字段核对，才能执行；仅向用户声明来源不足以允许执行未经核验的写入。资料不足时只提供草案、缺口和验证步骤，不调用该写接口。
5. 对已经验证适用的操作，先 GET 确认当前模型、单位、坐标和编号。修改前备份到独立文件；SAVE 不等于备份，SAVEAS 会切换当前文件，路径和覆盖范围必须明确。
6. 只操作用户授权对象，预览差异，小范围测试，检查编号冲突并回读。不默认 DELETE/清空/新建覆盖。分析前核对边界、工况及组合，提取结果注明单位与来源，工程结果必须人工复核。
7. 检查状态码、响应体、回读结果及分析警告。404 应同时检查当前会话连接、Base URL 和路由，不等同于唯一原因。HTTP 成功和 JSON 解析通过都不能证明工程正确。

## 配套资料
详见 `references/connection-and-safety.md`、`conventions.md`、`documents.md`、`modeling.md`、`analysis.md`、`results.md`、`endpoint-index.md`、`limitations.md`。示例在 `examples/`，每个必须保留来源。`python scripts/verify_offline.py` 仅做离线检查，不能证明 Gen 兼容性。

不得将桥梁专项、钢束、移动荷载、Hyper-S 或日本版专用接口默认用于 Gen；不修改 MIDAS 安装，不向无关第三方上传模型，不保存真实密钥。
