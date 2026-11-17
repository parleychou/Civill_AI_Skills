# MIDAS Civil NX API Skill（初版）

面向 **MIDAS Civil NX** Open API（REST/JSON）的通用可复用技能包。中文说明为主。本包是已交叉核验资料后的**初版**，官方手册与本地 Civil NX JSON 手册已对照，但**尚未在真实 Civil NX 会话中实测**。

- 技能名：`MIDAS Civil NX API`
- 目录 slug：`midas-civil-nx-api`
- 不适用于经典 MIDAS Civil（官方说明经典 Civil 不提供 API；同时不要把旧 FAQ 当成未来版本的永久结论，仍以用户当前产品与文档为准）
- 不适用于 MIDAS Gen / Gen NX（请使用独立包 `midas-gen-nx-api`，且该包目前只是资料受限、待验证初版）

## 安装

把本目录放到 Agent 的 skills 目录下，并确保存在 `SKILL.md`：

```text
your-project/skills/midas-civil-nx-api/
├── SKILL.md
├── README.md
├── references/
├── examples/
└── scripts/verify_offline.py
```

或直接使用发布用的 `midas-civil-nx-api.zip`（压缩包根目录内即上述文件，上传到技能平台时保持这一结构）。

在 Claude Code / Cursor 等支持 Agent Skills 的环境中加载后，当任务涉及 Civil NX 建模、改模型、分析或读结果时使用本技能。

## 使用前

1. 确认产品是 Civil NX，并且已在 Apps → API → API Settings 中 Connect。从当前会话取得 Base URL；密钥只通过安全输入或运行环境提供，不要在聊天中索要明文，也不要写入仓库或本目录。
2. 修改前保留独立的原始模型副本。`SAVE` 只保存当前文件，不等于备份；`SAVEAS` 会切换当前文件，须确认新路径和是否覆盖。
3. `examples/` 里的 JSON 只是带出处的模板，不是可无条件执行的模型。分析结果需人工复核。HTTP 成功或 JSON 可解析都不等于建模或分析正确。404 应同时检查连接、Base URL 和路由。

## 离线自检

```bash
python3 scripts/verify_offline.py
```

该脚本只检查文件、链接与 JSON 是否可解析，**不会**连接 MIDAS 或访问网络，也不能证明真实会话可用。

## 资料

详见 `references/sources.md`。官方手册与本地 Civil NX JSON 手册的端点对照见 `references/endpoint-index.md`。

本包只收录短 JSON 示例与转写约定，完整接口页请阅读官方手册。示例中的 `C:\MIDAS\...` 是手册占位路径。

## 打包上传

发布用 zip 的根目录应是本技能文件夹本身（内含 `SKILL.md`，而不是再套一层无 `SKILL.md` 的空目录）。本结构遵循通用 Agent Skill 约定：YAML frontmatter 的 `name` / `description`，正文放流程，细节放 `references/`。本次未额外查阅 WorkBuddy 开放平台的专用打包规范，以免拖延交付；若平台另有要求，按官方说明调整后再上传。
