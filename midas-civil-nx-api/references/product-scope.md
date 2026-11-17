# 产品代际与适用范围

## 结论

| 产品 | 本技能是否适用 | 依据 |
| --- | --- | --- |
| MIDAS Civil NX（CIVIL NX） | **适用**。只针对其 Open API（REST/JSON）。 | 官方 API 手册针对 NX 系列；本地手册页眉为「midas Civil NX - API 用户手册」；API Settings 与 Postman 教程以 CIVIL NX 为对象。 |
| 经典 MIDAS Civil（非 NX） | **不适用**。 | 官方产品页 FAQ（https://www.midasuser.com/en/product/civil ，查阅于 2026-11-18（Asia/Shanghai））：「MIDAS CIVIL does not provide an API. To use API services, users need to switch to MIDAS CIVIL NX.」 |
| MIDAS Gen / Gen NX | **不适用本包**。请改用 `midas-gen-nx-api`。 | 功能集合不同；禁止把 Civil NX 手册接口写成 Gen 已验证能力。 |

## 文件兼容不是 API 兼容

官方说明：经典 Civil 的 MCB 可在 Civil NX 中打开；Civil NX 的 MCBZ 不能在经典 Civil 中打开。Civil NX 仍可能另存 MCB，但官方写明该能力会随后续版本取消。

## 版本标记

- 官方目录：`ᴴˢ⁾` = Hyper-S solver only；`ᴶ⁾` = MIDAS CIVIL NX JP Version only。本地手册（2025-12-23）未出现 `-M1` / Hyper-S 或 JP 专用页，故不列为已交叉核验。
- 资料未给出固定的软件内部版本号。能力边界以官方目录编辑日期 2026-07-14 与本地手册抓取日期 2025-12-23 共同约束。
