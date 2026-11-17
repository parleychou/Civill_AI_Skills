# 产品代际与适用范围（资料受限 / 待验证初版）

## 结论

| 产品 | 本技能是否适用 | 依据 |
| --- | --- | --- |
| MIDAS Gen NX（GEN NX） | **仅作资料受限、待实机验证的初版，不是完整 Gen API 成品。** 官方已为 GEN NX 提供 API Settings 与 NX 系列总目录。字段级示例大多来自共享目录或 Civil NX 文本，不得写成已在 GEN NX 核验，也不得在未逐字段核验前执行这些写入示例。 | GEN NX 产品页宣传 API；韩文 API Settings（2026-01-07）面向 GEN NX；官方 API 手册开篇包括 GEN NX。 |
| 经典 MIDAS Gen（非 NX） | **不得默认适用。** | 经典 GEN 产品页 FAQ 在 2026-11-18（Asia/Shanghai） 查阅时仍写：新的 GEN API 正在开发，预期 2025 年以 Web server-based REST API 发布。本技能 **不把 Gen NX 默认视作 Gen**。 |
| MIDAS Civil / Civil NX | **不适用本包**。请改用 `midas-civil-nx-api`。 | 即使部分端点字符串相同，也必须按产品使用对应技能。 |

## 资料完整度

有官方目录与 GEN NX 连接方法，可指导如何连接、如何理解五类端点的一般约定。没有已读正文的 Gen 专用字段手册，因此本包不能当作完整 Gen API 文档或可直接执行的接口库。共享约定可以讨论；若具体枚举或示例只出现在 Civil NX 文本中，必须先取得 Gen 接口正文或已验证导出结构并逐字段核对，才能执行写入。资料不足时只提供草案、缺口和验证步骤，不调用该写接口。仅向用户声明来源并不足以允许执行。

官方限制标记：`ᴴˢ⁾` Hyper-S only；`ᴶ⁾` 在手册中标注为 MIDAS CIVIL NX JP Version only，即使同页列出也不要当成 Gen NX 能力。
