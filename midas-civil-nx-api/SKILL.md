---
name: MIDAS Civil NX API
description: >-
  当用户要通过 MIDAS Civil NX Open API（REST/JSON）建模、修改模型、运行分析或提取结果时使用。先核对产品版本；不适用于经典
  Civil，也不混用 Gen 接口。
---
# MIDAS Civil NX Open API

## 适用范围
用于 MIDAS Civil NX，不用于经典 Civil 或 Gen。依据官方 NX API 手册和 Civil NX JSON 手册整理，尚未在真实 MIDAS 会话中实测。先读 `references/product-scope.md`、`sources.md` 和 `limitations.md`，确认用户的产品、版本及 API 能力，不把旧 FAQ 当成未来版本的永久结论。

## 工作流程
1. 从 `references/endpoint-index.md`、对应主题参考页和 `examples/PROVENANCE.md` 查找所需接口及字段。禁止凭记忆补齐枚举，不混用 Hyper-S、日本版或其他产品专用接口。
2. 在产品 API 设置确认连接状态，从当前会话获取 Base URL；密钥通过安全输入或运行环境提供，不能索要明文聊天、硬编码、写入日志或技能包。请求头为 `Content-Type: application/json` 和 `MAPI-Key`。不得假设本机端口或固定主机。
3. 先读后改，确认单位、坐标、对象编号和引用关系。修改前保留独立的原始模型副本；`SAVE` 仅保存当前文件，不等于备份。`SAVEAS` 会切换当前文件，要先确认新路径和是否覆盖。未指定备份位置时先询问，不擅自覆盖。
4. 仅执行用户授权的对象和操作。参考 `references/conventions.md`：`/doc/*` 常用 POST/Argument，`/db/*` 写入常用 Assign/数字键，结果表按实际接口页构造。路径大小写、方法和字段均按当前产品文档验证。示例只是模板，不是可无条件执行的模型。
5. 默认不删除、不清空、不新建替换现有会话。创建节点、单元、材料、截面、荷载前检查编号冲突；大批修改先预览差异，小范围验证，再执行并回读。
6. 分析前核验约束、荷载工况及组合。提取结果需标注单位、工况/组合、坐标系及筛选条件，工程结论必须人工复核。
7. 不将 HTTP 成功或 JSON 可解析等同于建模/分析正确；检查响应体、回读模型及分析警告。404 同时检查连接、Base URL 和路由，不能一概解释为未连接。

## 资料与验证
按需读取 `references/connection-and-safety.md`、`documents.md`、`modeling.md`、`analysis.md`、`results.md`。示例在 `examples/`，来源见 `examples/PROVENANCE.md`。运行 `python scripts/verify_offline.py` 只能验证离线结构与示例，不证明真实 MIDAS 可用。

不修改 MIDAS 安装，不向无关服务上传模型，不泄露或持久化真实密钥。发现资料冲突或未覆盖字段时停止对应操作并说明缺口，不编造接口。
