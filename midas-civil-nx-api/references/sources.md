# 来源与查阅记录

接口与约定均可追溯到下列已实际读取的资料。未能读到正文的来源会明确标出。查阅日期：2026-11-18（Asia/Shanghai）。

## 官方（已读取正文）

| 资料 | URL | 页面元数据 | 本次用途 |
| --- | --- | --- | --- |
| MIDAS API Online Manual | https://support.midasuser.com/hc/en-us/articles/33016922742937-MIDAS-API-Online-Manual | Created 2024-05-28；Edited 2026-07-14 | NX 系列（CIVIL NX 与 GEN NX）端点目录与 JSON 约定 |
| How to work MIDAS CIVIL NX Open API | https://support.midasuser.com/hc/en-us/articles/30212837484441-How-to-work-MIDAS-CIVIL-NX-Open-API | Created 2024-03-22；Edited 2024-06-17 | 运行方式：REST → 服务器中转 → 产品 WebSocket；请求头 `MAPI-Key` |
| API Settings | https://support.midasuser.com/hc/en-us/articles/27745256204057-API-Settings | Created/Edited 2024-01-18 | Civil NX 中复制 Base URL / MAPI-Key、Connect 状态 |
| Base URL and API-KEY | https://support.midasuser.com/hc/en-us/articles/30508934444569-Base-URL-and-API-KEY | Created 2024-03-28；Edited 2024-06-17 | Base URL 随产品/地区/服务器而变，必须从产品内读取 |
| Let's start MIDAS Open API with Postman | https://support.midasuser.com/hc/en-us/articles/30511293352473-Let-s-start-MIDAS-Open-API-with-Postman | Created 2024-03-28；Edited 2024-06-17 | 先 Apps → Connect；GET `/db/UNIT` 与 PUT 示例 |
| Designing with Intent: POST/TABLE | https://support.midasuser.com/hc/en-us/articles/45171987915929-Designing-with-Intent-The-Vision-Behind-POST-TABLE | Created 2025-03-31；Edited 2026-07-30 | `post/TABLE` 单端点多表；`TABLE_TYPE` 为必要键 |
| Example: Python | https://support.midasuser.com/hc/en-us/articles/30230181806361-Example-Python | Created 2024-03-22；Edited 2024-10-28 | 官方简单梁流程；原文写明运行于 MIDAS CIVIL NX |
| MIDAS CIVIL NX 产品页 FAQ | https://www.midasuser.com/en/product/civil | 查阅于 2026-11-18（Asia/Shanghai） | 「MIDAS CIVIL does not provide an API. To use API services, users need to switch to MIDAS CIVIL NX.」 |

## 本地手册（已只读提取，非逐字节原件镜像）

用户提供的 Civil NX JSON 手册副本（Markdown）：430 个 `.md`，约 3.24 MB。其中 429 个位于子目录「JSON手册」；另 2 个（`createclasses.md`、`modifymulticards.md`）是 C# 类型生成说明，不是官方接口正文，本技能不写入其个性化路径或生成规则。

- 页眉：midas Civil NX - API 用户手册 / midas Civil NX Online Support
- 文件头「爬取时间」：2025-12-23 13:14:07 至 15:17:16
- 单页来源：`https://www.wolai.com/midasit/...`（428 个文件带 wolai URL）
- 已解析到 Input URI：412 / 429 页
- 提取方式：只读解析文本后在本包汇编索引与示例，**不是**原目录逐字节复制

## 用户补充的 wolai 入口（未能读到正文）

https://www.wolai.com/midasit/snbusAxfpoirfTh6663jAV — 公开 HTML 壳可访问，标题为「JSON数据手册」。正文为前端渲染；直接抓取无手册正文，无头浏览器仅显示「网络可能有一点问题，请重新加载」。公开 API 返回「没有找到内容 - 404」。**不能声称已获取该页正文。** 接口细节以本地已抓取的同系列页面与官方 support 手册为准。

## 未做的事

未在真实 Civil NX 运行时实测；未读取或写入任何真实 MAPI-Key、Base URL 或模型文件。
