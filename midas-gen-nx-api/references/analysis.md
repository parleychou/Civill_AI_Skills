# 分析控制与执行

## 执行分析

- 端点：官方 `/doc/ANAL`，本地手册写作 `doc/Anal`，方法 POST。
- 普通分析示例：`{}`
- Pushover：`{"Argument":{"TYPE":"Pushover"}}`
- 来源：本地 Civil NX 手册「[Anal] Perform Analysis」（抓取 2025-12-23）

分析可能耗时。本技能不在离线环境代为执行，也不把返回成功当成计算结果已经可靠。本地手册中的 `/doc/Anal` 空 Body 与 Pushover `TYPE` 示例出自 Civil NX，未核验前不要在 Gen NX 中直接发送。

## 分析控制（/db）

双方共有的控制项包括主控制 `ACTL`、P-Delta、屈曲、特征值、移动荷载（含中国/英国/欧洲/印度/横向等本地页）、沉降、非线性、施工阶段、边界改变、水化热控制等，见索引。

官方目录另有一批 `-M1`（Hyper-S solver only）控制端点，本地 Civil NX 手册未收录。两套技能都不要把它们当作默认能力。

施工阶段、移动荷载控制更偏 Civil；在本初版中默认不作为 Gen NX 已支持能力。即便用户的 GEN NX 接口页后来列出相同路径，也要按该页字段核验后再用。
