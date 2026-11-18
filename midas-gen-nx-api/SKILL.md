---
name: midas-gen-nx-api
display_name: MIDAS Gen NX API
display_name_en: MIDAS Gen NX API
description: >-
  当用户要通过 MIDAS Gen NX Open API 连接、查阅官方 NX 共享目录或核验字段时使用。不适用于经典 Gen，也不混用 Civil
  接口。本包为资料受限初版：没有完整 Gen 专用字段手册，默认检索只返回已证实的 Gen 连接资料与官方 NX 共享字段；Civil
  对照需显式开启且不得当作 Gen 可执行契约。尚未在真实 Gen NX 会话中实测。
description_zh: >-
  面向 MIDAS Gen NX Open API 的资料受限初版。默认只能检索已证实的连接方法与官方 NX 共享字段；缺少 Gen 专用手册的字段会如实标为缺口。尚未实机验证。
description_en: >-
  Limited draft skill for the MIDAS Gen NX Open API. Default offline search only returns
  verified GEN NX connection facts and official NX-series shared field pages. It does not
  include a complete Gen-specific field manual. Civil material is opt-in and is never a
  Gen write contract. Not yet tested against a live Gen NX session.
examples_zh:
  - "先确认这是 Gen NX，并说明如何从 API Settings 取得 Base URL 和密钥（不要把密钥写进对话）"
  - "只根据官方 NX 共享页查询 UNIT / NODE / MATL 字段，并标明尚未在 Gen 上实测"
  - "如果要用 Civil 手册对照，必须先声明这不是 Gen 可执行契约，再列出需要在 Gen 文档中核验的字段"
examples_en:
  - "Confirm the product is Gen NX and walk through API Settings without exposing the key"
  - "Look up shared official UNIT, NODE, or MATL fields and flag them as untested on Gen"
  - "If Civil examples are requested, mark them unverified cross-product and do not execute writes"
version: "0.2.2"
author: 周文琪
---
# MIDAS Gen NX Open API

## 范围与证据限制
用于 MIDAS Gen NX，先确认实际产品与版本。不要把 Gen NX 默认当成经典 Gen，也不要混用 Civil NX。本包**未在真实 Gen NX 会话中实测**。已读资料确认 Gen NX 连接说明和 NX 总目录，但**没有完整读取 Gen 专用字段手册**。

默认离线检索只使用 `verified` 与官方 NX `shared` 资料（`references/verified-gen.jsonl`、`references/official-shared.jsonl`）。包内若仍有来自 Civil 的示例，必须加 `--include-cross-product` 才会出现，且只能当对照，**不能当作 Gen 可执行契约**。不要用 Civil 例子伪装 Gen 字段已经齐备。

## 工作流程
1. 先读 `references/product-scope.md`、`references/sources.md`、`references/limitations.md`。用 `python scripts/search_index.py <关键词>` 检索；旧 FAQ 和计划发布时间不代表当前所有版本。
2. 在当前 Gen NX API 设置确认连接状态，获取 Base URL；密钥走安全输入或环境，不索要聊天明文、不写日志或技能文件。请求头包含 `Content-Type: application/json`、`MAPI-Key`，不猜端口或主机。
3. 用检索结果和 `references/endpoint-index.md` 找候选路由，再读取当前 Gen NX 对应的接口正文核对 HTTP 方法、字段、枚举、适用版本。官方共享页仍需在当前产品上确认。官方页若出现未绑定到具体行的 “CIVIL NX only / GEN NX only” 脚注，要如实标明，不得猜测对应字段。
4. 读取 `examples/PROVENANCE.md` 前须知道这些示例大多来自 Civil NX。未取得 Gen 文档或已验证导出结构并逐字段核对前，不得执行这些写入。资料不足时只提供草案、缺口和验证步骤，不调用该写接口。
5. 对已经验证适用的操作，先 GET 确认当前模型、单位、坐标和编号。修改前备份到独立文件；`SAVE` 不等于备份，`SAVEAS` 会切换当前文件，路径和覆盖范围必须明确。
6. 只操作用户授权对象，预览差异，小范围测试，检查编号冲突并回读。不默认 DELETE/清空/新建覆盖。分析前核对边界、工况及组合，提取结果注明单位与来源，工程结果必须人工复核。
7. 检查状态码、响应体、回读结果及分析警告。404 应同时检查当前会话连接、Base URL 和路由。HTTP 成功和 JSON 解析通过都不能证明工程正确。

## 配套资料
详见 `references/connection-and-safety.md`、`references/conventions.md`、`references/documents.md`、`references/modeling.md`、`references/analysis.md`、`references/results.md`、`references/endpoint-index.md`、`references/limitations.md`。运行 `python scripts/verify_offline.py` 仅做离线检查，不能证明 Gen 兼容性。需要 Civil 对照时显式运行 `python scripts/search_index.py <关键词> --include-cross-product`，并阅读命中项上的警告。

不得将桥梁专项、钢束、移动荷载、Hyper-S 或日本版专用接口默认用于 Gen；不修改 MIDAS 安装，不向无关第三方上传模型，不保存真实密钥。
