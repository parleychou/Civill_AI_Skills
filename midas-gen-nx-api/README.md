# MIDAS Gen NX API Skill（资料受限 / 待验证初版）

面向 **MIDAS Gen NX** Open API（REST/JSON）的技能包。中文说明为主。

**本包不是完整的 Gen API 成品。** 当前为资料受限、待实机验证的初版：已读到 Gen NX 连接说明和 NX 总目录，但没有完整读取 Gen 专用字段手册；多数示例来自 Civil NX，只能旁证，**不能直接执行**。

- 技能名：`MIDAS Gen NX API`
- 目录 slug：`midas-gen-nx-api`
- 不要把 Gen NX 默认当成经典 MIDAS Gen；也不要把旧 FAQ 或计划发布时间当成当前所有版本的结论
- 不适用于 MIDAS Civil / Civil NX（请使用独立包 `midas-civil-nx-api`）
- **未在真实 Gen NX 会话中实测**

## 安装

```text
your-project/skills/midas-gen-nx-api/
├── SKILL.md
├── README.md
├── references/
├── examples/
└── scripts/verify_offline.py
```

也可使用 `midas-gen-nx-api.zip` 上传到技能平台（保持包内该结构）。

## 离线检索

默认只搜已证实的 Gen 连接资料和官方 NX 共享字段，不依赖本机 Civil 手册：

```bash
python3 scripts/search_index.py NODE
python3 scripts/search_index.py 材料
python3 scripts/search_index.py 结果 TABLE_TYPE
```

若要对照 Civil 示例，必须显式加上 `--include-cross-product`，并把命中项视为未验证对照，而不是可执行契约。

## 使用前

1. 确认产品是 Gen NX。在 Apps → API → API Settings 中确认已 Connect，从当前会话取得 Base URL。密钥只通过安全输入或运行环境提供，不要在聊天中索要明文，也不要写入仓库。
2. 来自 Civil NX 的示例必须先取得 Gen 文档或已验证导出结构并逐字段核对，才能执行写入；仅声明来源不够。资料不足时只提供草案、缺口和验证步骤，不调用该写接口。
3. 对已经核验适用的操作，修改前备份到独立文件。`SAVE` 不等于备份，`SAVEAS` 会切换当前文件。结果需人工复核。404 应同时检查连接、Base URL 和路由。

## 离线自检

```bash
python3 scripts/verify_offline.py
```

该脚本不连接 MIDAS，也不访问网络，**不能证明 Gen 兼容性**。

## 资料

详见 `references/sources.md`、`references/product-scope.md` 与 `references/endpoint-index.md`。

## 打包上传

发布用 zip 的根目录应是本技能文件夹本身（内含 `SKILL.md`）。本结构遵循通用 Agent Skill 约定。本次未额外查阅 WorkBuddy 专用打包规范；若平台另有要求，按官方说明调整后再上传。
