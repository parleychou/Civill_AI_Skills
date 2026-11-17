# JSON 与方法约定

依据官方 MIDAS API Online Manual 与本地 Civil NX《基本信息》。这是 NX 系列的共同约定。

## 五类端点

| 前缀 | 官方说明 | 请求要点 |
| --- | --- | --- |
| `/doc/...` | 文档级操作 | **仅 POST**。Body 以 `Argument` 为键；Argument 为空时手册允许发送 `{}`。 |
| `/db/...` | 保存在 NX 系列文件中的数据，相当于 MCT/MGT 功能 | 一般 GET/POST/PUT/DELETE。新建文件必需项（单位、结构类型等）通常只有 GET/PUT。GET 的第一层键是端点名；POST/PUT 的第一层键必须是 `Assign`，然后是数字键（截面 ID、组合序号等）。单位系统等唯一数据的数字键只有 `"1"`。 |
| `/ope/...` | 操作类；可走 GUI，或读取不入库的预处理量 | 以各接口页为准。 |
| `/view/...` | 模型视图 | 可独立使用；Capture 可与 Angle、Active、Display、Resultgraphic 一起使用。 |
| `/post/...` 与 `post/TABLE` | 提取前后处理表格 | 大量结果表共用一个端点，用 `TABLE_TYPE` 区分。详见 `results.md`。 |

## 数据类型（本地《基本信息》）

Integer、String（如 `"LINEAR"`、`"COMP"`）、Boolean（True/False）、Real。

## 删除单个对象

`{base URL} + command/key no.`。示例：删除 10 号节点 → Method Delete，URI `{base URL} + db/node/10`。

## 资料不一致时

先查 `endpoint-index.md` 属于「双方共有」「仅本地手册」还是「仅官方目录」。需要字段时只使用带出处的示例或对应 references，禁止编造枚举值。
