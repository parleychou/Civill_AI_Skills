# 文档级接口（/doc）

官方写明：全部为 POST，Body 从 `Argument` 起；空参数可用 `{}`。

| 官方目录端点 | 本地 Civil NX 手册中的写法 | 本地方法 | 说明 |
| --- | --- | --- | --- |
| `/doc/NEW` | `/doc/new` | POST | 新项目。本地示例如 `{}` |
| `/doc/OPEN` | `/doc/open` | POST | 打开项目。本地示例 `{"Argument":"C:\\MIDAS\\FSM.mcb"}`（手册占位路径） |
| `/doc/CLOSE` | `/doc/close` | POST | 关闭项目 |
| `/doc/SAVE` | `/doc/save` | POST | 保存当前文件。**不等于备份**，也不会单独留出原始副本。 |
| `/doc/SAVEAS` | `/doc/saveas` | POST | 另存为；Argument 为路径字符串。会切换当前文件，必须先确认新路径和是否覆盖。手册示例路径只是占位。 |
| `/doc/STAGAS` | （本地手册未收录） | 以官方页为准 | Save Current Stage As；仅出现在官方 NX 目录 |
| `/doc/IMPORT` | `/doc/import` | POST | Import to Json |
| `/doc/IMPORTMXT` | `/doc/importmxt` | POST | Import to mct/mgt |
| `/doc/EXPORT` | `/doc/export` | POST | Export to Json |
| `/doc/EXPORTMXT` | `/doc/exportmxt` | POST | Export to mct/mgt |
| `/doc/ANAL` | `/doc/Anal` | POST | 运行分析。本地示例：普通分析 `{}`；Pushover 为 `{"Argument":{"TYPE":"Pushover"}}` |

官方 Python 示例在 **CIVIL NX** 中使用 `POST /doc/new` 与 `{}` 创建新文件。该示例若被 Gen 技能包引用，必须标明出处是 Civil NX。
