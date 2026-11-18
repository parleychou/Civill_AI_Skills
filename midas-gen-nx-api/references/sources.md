# 来源与查阅记录

本技能只覆盖已文档化的 **MIDAS Gen NX** Open API。经典 MIDAS Gen 不自动继承该能力。查阅日期：2026-11-18（Asia/Shanghai）。

## 官方（已读取正文）

| 资料 | URL | 页面元数据 | 本次用途 |
| --- | --- | --- | --- |
| MIDAS API Online Manual | https://support.midasuser.com/hc/en-us/articles/33016922742937-MIDAS-API-Online-Manual | Created 2024-05-28；Edited 2026-07-14 | 开篇写明手册相对 MIDAS NX 系列，包括 CIVIL NX 和 GEN NX |
| How to work MIDAS CIVIL NX Open API | https://support.midasuser.com/hc/en-us/articles/30212837484441-How-to-work-MIDAS-CIVIL-NX-Open-API | Edited 2024-06-17 | NX Open API 的服务器中转与 `MAPI-Key` 机制（文中以 CIVIL NX 为例） |
| API Settings（CIVIL NX 英文页） | https://support.midasuser.com/hc/en-us/articles/27745256204057-API-Settings | 2024-01-18 | NX 产品内 API Settings 的交互（文中产品名为 CIVIL NX） |
| API Settings（GEN NX 韩文页） | https://support.midasuser.com/hc/ko/articles/54016661596057-API-Settings | 생성/편집 2026-01-07 | 明确在 **MIDAS GEN NX** 中用 Apps → API → API Settings 连接 |
| Midas Setting；How can I integrate it with CIVIL NX or GEN NX | https://support.midasuser.com/hc/en-us/articles/32835654744345-Midas-Setting ； https://support.midasuser.com/hc/en-us/articles/45625180842009-How-can-I-integrate-it-with-CIVIL-NX-or-GEN-NX | 查阅于 2026-11-18（Asia/Shanghai） | 连接对象写为 CIVIL NX 或 GEN NX |
| Base URL and API-KEY | https://support.midasuser.com/hc/en-us/articles/30508934444569-Base-URL-and-API-KEY | Edited 2024-06-17 | 地址与密钥必须从当前产品读取 |
| Designing with Intent: POST/TABLE | https://support.midasuser.com/hc/en-us/articles/45171987915929-Designing-with-Intent-The-Vision-Behind-POST-TABLE | Edited 2026-07-30 | 结果表约定。叙述以 CIVIL NX 为主，**不是** Gen NX 实测证据 |
| Example: Python | https://support.midasuser.com/hc/en-us/articles/30230181806361-Example-Python | Edited 2024-10-28 | 共享 JSON 形状参考；原文运行于 CIVIL NX |
| MIDAS GEN NX 产品页 | https://www.midasuser.com/en/product/gen-nx | 查阅于 2026-11-18（Asia/Shanghai） | 宣传 GEN NX 可与 Excel、Python 等通过 API 集成 |
| MIDAS GEN（经典）产品页 FAQ | https://www.midasuser.com/en/product/gen | 查阅于 2026-11-18（Asia/Shanghai） | 仍写新的 GEN API 正在开发，预期 2025 年以 Web REST 发布。不能证明经典 Gen 已具备与 Gen NX 相同的 API。 |

## 未提供或不完整的 Gen 专用手册

- 用户本地 JSON 手册页眉为 **midas Civil NX - API 用户手册**（抓取 2025-12-23），不是 Gen 专用手册。其中字段示例只可作为 NX 常见 JSON 形状的旁证，必须标注来源。
- https://www.wolai.com/midasit/jo4S89xebTa4nvoQTbgB8H 标题为「midas Gen API 使用手册」，2026-11-18（Asia/Shanghai） 仅读到 HTML `<title>`，正文因「网络可能有一点问题，请重新加载」未加载。**不能声称已获取正文。**
- 用户补充的 https://www.wolai.com/midasit/snbusAxfpoirfTh6663jAV 标题为「JSON数据手册」，同样未能读到正文。

## 未做的事

未在真实 Gen NX 或经典 Gen 上实测；未保存任何真实密钥或 Base URL。


## 本包 0.2.1 的可离线检索资料

- `references/verified-gen.jsonl`：已读正文的 GEN NX 连接/产品页事实与明确缺口（不含编造的 Gen 专用字段表）。
- `references/official-shared.jsonl`：官方 NX 系列 JSON Manual 中本次成功读取的 UNIT / NODE / ELEM / MATL / SECT-Common / Section Table / POST/TABLE 字段。证据级别为 **shared**，不是 Gen 实机验证。
- 默认检索不包含 Civil 手册字段目录，也不把 `examples/` 中的 Civil JSON 当作 Gen 契约。`--include-cross-product` 只会显示包内已有的 Civil 示例与 `references/unverified-cross-product.md`。
- wolai《midas Gen API 使用手册》仍未能读到正文，不能填补 Gen 专用字段。
