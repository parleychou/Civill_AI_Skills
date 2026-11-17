# 限制、未核验项与常见混淆

- **未在真实 MIDAS Civil NX 上实测** 任何请求。本包只做资料汇编与离线 JSON/路径自检。
- **经典 MIDAS Civil 没有本 API**（官方产品页 FAQ，查阅于 2026-11-18（Asia/Shanghai））。
- **不是 Gen 技能。** 即使官方总目录同时写了 CIVIL NX 和 GEN NX，本包也不把 Gen 当作已验证范围。
- Hyper-S（`-M1`）与官方标注的 Civil NX 日本版专用项：本地手册未收录，默认不支持。
- 仅官方目录出现、本地 Civil NX 手册没有的楼层/建筑抗震抗风/墙与钢设计等项：不列为已交叉核验的 Civil NX 能力。
- `/doc/STAGAS` 仅出现在官方目录。
- 不要把 Smart Report 的 `TABLE_NAME` 当成官方 `TABLE_TYPE`。
- `UNIT` 温度键在单位系统页为 `TEMPER`，在官方 POST/TABLE 说明中为 `TEMP`。按所调用的接口页填写，不要混用后假装一定成功。
- 用户补充的 wolai「JSON数据手册」入口未能读到正文，见 `sources.md`。
- 示例路径 `C:\\MIDAS\\...` 来自手册，不是用户环境路径。
- `/doc/SAVE` 只保存当前文件，不等于备份；需要备份时应保留独立的原始模型副本。`/doc/SAVEAS` 会切换当前文件，路径和覆盖范围必须明确。
- 404 应同时检查连接状态、Base URL 和路由/方法，不能一概解释为未连接。本地手册对 404 的表述只是原因之一。
