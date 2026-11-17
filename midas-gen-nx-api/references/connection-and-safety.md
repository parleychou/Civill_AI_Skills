# 连接方式、请求约定与安全规则

依据官方文档。不假定任何 Base URL、端口或 MAPI-Key。查阅日：2026-11-18（Asia/Shanghai）。

## 运行结构

官方《How to work MIDAS CIVIL NX Open API》说明：产品**不与应用程序直接本地接口**。客户端用 HTTP REST 访问服务器，服务器再经 WebSocket 与已连接的产品会话通信。文中写明中介为云端服务器（AWS）。因此：

- 不要假设 `localhost` 或固定端口可用
- 不要把 Base URL 或 MAPI-Key 写进通用技能、示例或仓库
- 不同 MAPI-Key 对应不同产品会话
- MAPI-Key 是临时密钥，泄露可能意味着远程控制正在运行的产品；按密钥保管，用完不落盘

## 在产品中取得参数

**Civil NX**（官方 API Settings 英文页、Postman 教程）：

1. 启动 CIVIL NX，打开或新建模型
2. Apps → Connect
3. Apps 选项卡 → API 组 → API Settings
4. Status 须为 Connected（否则先 Connect）。可选 Connect API on Startup
5. 分别 Copy Base URL 与 MAPI-Key；Refresh 会重新生成密钥

**Gen NX**（官方韩文 API Settings，生成/编辑于 2026-01-07）：同样在 [Apps] → [API] → [API Settings] 中复制 Base URL、MAPI-Key，Connect 后状态变为 Connected。

Grasshopper / MIDAS GH 的说明也要求在 CIVIL NX 或 GEN NX 的 API Settings 中复制这两项。那是插件步骤，不是本技能的必经路径。

在产品界面里使用 Copy 按钮后，密钥应进入安全输入或运行环境，而不是粘贴到聊天、示例文件或仓库。

## 请求格式

- 完整 URL = `{Base URL}` + 接口路径（手册写作 `{base url} + db/UNIT` 等）
- Header：`Content-Type: application/json`，以及 **`MAPI-Key: <当前产品复制的密钥>`**（键名就是 `MAPI-Key`）
- GET / DELETE：官方 Postman 教程写明通常不需要 Body
- POST / PUT：发送 JSON Body
- 路径大小写：官方目录多用 `/doc/NEW`、`/db/UNIT`；官方 Python 示例使用 `/doc/new`、`/db/unit`；本地 Civil NX 手册也常见小写。**以当前产品接口页为准**；失败时可尝试另一种大小写并记录响应

## 官方 HTTP 状态码（本地 Civil NX《基本信息》）

| 状态码 | 手册含义 |
| --- | --- |
| 200 | 请求成功到达模型 |
| 201 | Created，请求已送达模型 |
| 400 | Bad Request，命令或 Body 错误 |
| 403 | Forbidden，该 API 命令未对用户开放 |
| 404 | Not found。本地 Civil NX《基本信息》把 404 写作「Client did not connect to API server.」这只是手册中的一种说明，不是唯一原因。实际应同时检查：当前会话是否已 Connect、Base URL 是否来自该会话、以及路由/方法是否正确。不要把 404 一概解释为未连接。 |

## 安全与工程纪律

1. **读取优先**：能用 GET 就先 GET。
2. **修改前必须保留独立的原始模型副本。** `/doc/SAVE` 只是保存当前文件，**不等于备份**。`/doc/SAVEAS` 会把当前会话切到新路径，必须先确认新路径以及是否覆盖已有文件。未指定备份位置时先询问，不得擅自覆盖，也不得用手册占位路径（如 `C:\\MIDAS\\FSM.mcb`）去写用户磁盘。
3. **变更范围要由用户明确**：只改被点名的节点号、单元号、工况等，不做整库覆盖。
4. **删除不是默认操作**：手册允许删除全部，或按 `{base URL} + command/key no.` 删除单个对象（示例：Delete `{base URL} + db/node/10`）。必须用户明确要求并复述范围。
5. **分析结果必须人工复核**。
6. **不保存、不硬编码、不写入日志或技能包的真实密钥**，也不在聊天中索要明文密钥。若脚本需要连接，只从安全输入或当前运行环境读取，用完不落盘。本包自检脚本不会发起请求。
7. **不调用付费第三方 API，不把模型上传到本 API 以外的服务。**
