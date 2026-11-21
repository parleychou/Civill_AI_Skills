"""查 SketchUp Ruby API 官方文档。逐级缩小范围：分类 → 类 → 方法。

    catalog                    一级目录：按用途分的类别
    catalog <分类>             分类里的类和一句话说明
    class <类名> [类名…]       类的说明、常量、全部方法（含继承来的方法名）
    method <类名#方法名> […]   签名、参数、返回值、最低版本、示例；类方法写 类名.方法名
    guide <专题名>             专题全文：导入导出选项、生成几何的方式等
    search <关键词>            不知道在哪个分类时，按类名、方法名、设置键、常量名、说明检索；文档是英文的，设置键的补充说明可用中文
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import sys

import sqlite3

def connect_db(path):
    """Connect to SQLite database with standard sqlite3 or fallback to vault."""
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM sqlite_master LIMIT 1")
        return conn
    except Exception:
        try:
            from PKPMAgent.skill_kit.vault import connect_db as v_connect
            return v_connect(path)
        except Exception as e:
            raise RuntimeError(f"Could not open database at {path}: {e}")


DB_PATH = Path(__file__).resolve().parents[1] / "references" / "sketchup_api.db"
# 检索结果里 LayOut API 排在后面：建模用不到，但类名常和 SketchUp 的重名（Page、Entities、Style）。
SECONDARY = "Layout::"
# 建模代码用不到的类别和常量组，检索时排在同一档结果的后面
REMOTE_CATEGORIES = {"layout", "ui", "observers", "system"}
REMOTE_CONSTANTS = re.compile(r"Observer|command IDs|Tool|messagebox|Menu|status_text")
# 一次查多个类或方法时，各段之间的分隔
SEPARATOR = "\n\n" + "─" * 40 + "\n\n"


def connection():
    conn = connect_db(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def secondary(name: str) -> bool:
    return name.startswith(SECONDARY) or name == "Layout"


def ident(row) -> str:
    return f"{row['class_name']}{'#' if row['scope'] == 'instance' else '.'}{row['name']}"


# ── 名称解析 ─────────────────

def find_classes(conn, name: str) -> list[sqlite3.Row]:
    """全名精确匹配；否则按最后一段匹配（Face → Sketchup::Face），LayOut 的排在后面。"""
    exact = conn.execute("SELECT * FROM classes WHERE name = ? COLLATE NOCASE AND kind != 'guide'", (name,)).fetchall()
    if exact:
        return exact
    rows = conn.execute("SELECT * FROM classes WHERE kind != 'guide'").fetchall()
    tail = name.casefold().rpartition("::")[2]
    found = [row for row in rows if row["name"].casefold().rpartition("::")[2] == tail]
    return sorted(found, key=lambda row: (secondary(row["name"]), row["name"]))


def resolve_class(conn, name: str) -> tuple[sqlite3.Row | None, str]:
    found = find_classes(conn, name)
    if not found:
        return None, f"没有类或模块 {name}。用 search <英文关键词> 查找。"
    primary = [row for row in found if not secondary(row["name"])]
    if len(found) == 1 or len(primary) == 1:
        chosen = primary[0] if primary else found[0]
        others = [row["name"] for row in found if row["name"] != chosen["name"]]
        return chosen, (f"（另有同名的 {'、'.join(others)}，需要时写全名）" if others else "")
    return None, f"{name} 有多个：{'、'.join(row['name'] for row in found)}。请写全名。"


def lineage(conn, cls: sqlite3.Row) -> list[str]:
    """自身、父类链、混入的模块（只含库里有的）。"""
    names = [cls["name"]] + json.loads(cls["ancestors"]) + json.loads(cls["includes"])
    return [name for name in names if conn.execute("SELECT 1 FROM classes WHERE name = ?", (name,)).fetchone()]


def split_target(target: str, name: str | None) -> tuple[str | None, str, str | None]:
    """'Face#pushpull' / 'Sketchup.active_model' / ('Face', 'pushpull') → (类名, 方法名, scope)。"""
    if name:
        return target, name, None
    match = re.fullmatch(r"(.+?)(#|\.)([^#.]+)", target)
    if match and not re.fullmatch(r"\d+", match.group(3)):
        return match.group(1), match.group(3), "instance" if match.group(2) == "#" else "class"
    return None, target, None


# ── 命令 ─────────────────

def cmd_catalog(conn, category: str | None) -> str:
    if not category:
        rows = conn.execute("""SELECT k.id, k.title, k.description, count(c.name) AS total FROM categories k
                               LEFT JOIN classes c ON c.category = k.id GROUP BY k.id ORDER BY k.position""").fetchall()
        lines = [f"{row['id']} — {row['title']}：{row['description']}（{row['total']} 个）" for row in rows]
        return "\n".join(lines + ["下一步：catalog <分类>，如 catalog entities"])
    row = conn.execute("SELECT * FROM categories WHERE id = ? COLLATE NOCASE", (category,)).fetchone()
    if row is None:
        ids = [r["id"] for r in conn.execute("SELECT id FROM categories ORDER BY position")]
        return f"没有分类 {category}。分类有：{', '.join(ids)}"
    rows = conn.execute("SELECT name, kind, summary, version FROM classes WHERE category = ? ORDER BY name",
                        (row["id"],)).fetchall()
    lines = [f"{row['id']} — {row['title']}：{row['description']}", ""]
    lines += [f"{item['name']} — {item['summary']}" + (f"（{item['version']}）" if item["version"] else "") for item in rows]
    hint = "guide <专题名>" if row["id"] == "guides" else "class <类名>，如 class " + rows[0]["name"].rpartition("::")[2]
    return "\n".join(lines + ["", f"下一步：{hint}"])


def stem(token: str) -> str:
    """去掉常见词尾，rotate 也能搜到 rotation、scale 搜到 scaling。"""
    for suffix in ("ing", "es", "ed", "e", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[:-len(suffix)]
    return token


def cmd_search(conn, keyword: str, limit: int, offset: int) -> str:
    term = " ".join(keyword.casefold().split())
    if not term:
        raise SystemExit("search 需要关键词")
    tokens = [stem(token) for token in re.split(r"[\s_]+", term.replace("::", " ").replace("#", " ")) if token]

    def has_all(text: str) -> bool:
        text = text.casefold()
        return all(token in text for token in tokens)

    def hits(text: str) -> int:
        text = text.casefold()
        return sum(text.count(token) for token in tokens)

    # 排序：名称完全相同 → 类名、方法名、设置键、常量名含全部关键词 → 类名+方法名含全部关键词 → 摘要、设置键说明含 → 正文含。
    # 同一档里建模用得到的在前；名称命中时名字短的在前，正文命中时关键词出现多的在前。
    found = []
    categories = {}
    for row in conn.execute("SELECT name, kind, title, summary, overview, constants, category FROM classes"):
        name = row["name"].casefold()
        categories[row["name"]] = row["category"]
        remote = secondary(row["name"]) or row["category"] in REMOTE_CATEGORIES
        for group in json.loads(row["constants"]):
            for constant in group["names"]:
                folded = constant.casefold()
                score = 0 if term == folded else 1 if has_all(folded) else None
                if score is None:
                    continue
                written = constant if row["name"] == "TopLevel" else f"{row['name']}::{constant}"
                where = "顶层常量，不加模块前缀" if row["name"] == "TopLevel" else f"{row['name']} 的常量"
                far = remote or bool(REMOTE_CONSTANTS.search(group["group"]))
                if far and score == 1:
                    score = 4  # 观察者、命令 ID 这类常量建模用不到，名称含关键词也只当正文命中
                found.append((score, far, 0, len(folded), written, f"constant {written} — {where}（{group['group']}）"))
        if term in (name, name.rpartition("::")[2]):
            score, rank = 0, len(name)
        elif has_all(name.replace("::", "")) or has_all(row["title"]):
            score, rank = 1, len(name)
        elif has_all(row["overview"]):
            score, rank = 4, -hits(row["overview"])
        else:
            continue
        label = f"guide {row['name']}" if row["kind"] == "guide" else f"{row['kind']} {row['name']}"
        found.append((score, remote, 0, rank, row["name"], f"{label} — {row['summary']}"))
    for row in conn.execute("SELECT class_name, name, description FROM keys"):
        written = f'{row["class_name"].rpartition("::")[2]}["{row["name"]}"]'
        folded = row["name"].casefold()
        if term == folded:
            score, rank = 0, len(folded)
        elif has_all(folded):
            score, rank = 1, len(folded)
        elif has_all(row["description"]):
            score, rank = 3, -hits(row["description"])
        else:
            continue
        found.append((score, False, 1, rank, written, f"key {written} — {row['description']}"))
    for row in conn.execute("SELECT class_name, name, scope, summary, description, tags, version FROM methods"):
        full = ident(row).casefold()
        name = row["name"].casefold()
        if term in (name, full) or full.endswith("::" + term):
            score, rank = 0, len(name)
        elif has_all(name):
            score, rank = 1, len(name)
        elif len(tokens) > 1 and has_all(full):
            score, rank = 2, len(name)
        elif has_all(row["summary"]):
            score, rank = 3, -hits(row["summary"])
        elif has_all(row["description"] + " " + row["tags"]):
            score, rank = 4, -hits(row["description"] + " " + row["tags"])
        else:
            continue
        remote = (secondary(row["class_name"]) or categories.get(row["class_name"]) in REMOTE_CATEGORIES
                  or row["summary"].startswith("Deprecated"))
        found.append((score, remote, 1, rank, ident(row),
                      f"{ident(row)} — {row['summary']}" + (f"（{row['version']}）" if row["version"] else "")))
    found.sort(key=lambda item: item[:5])
    page = found[offset:offset + limit]
    if not page:
        if re.search(r"[㐀-鿿]", term):
            return "没有结果。官方文档是英文的，中文只能搜到设置键的补充说明；换英文关键词，如 edge、shadow、section、camera。"
        return "没有结果。换个英文说法，或用更短的关键词（如 shadow、section、material、camera）。"
    lines = [item[-1] for item in page]
    if offset + limit < len(found):
        lines.append(f"…共 {len(found)} 条，用 --offset {offset + limit} 看后面的")
    lines.append("详情：method <类名#方法名> 或 class <类名>")
    return "\n".join(lines)


def cmd_class(conn, name: str) -> str:
    cls, note = resolve_class(conn, name)
    if cls is None:
        return note
    category = conn.execute("SELECT title FROM categories WHERE id = ?", (cls["category"],)).fetchone()
    lines = [f"{cls['kind']} {cls['name']}" + (f" < {cls['superclass']}" if cls["superclass"] else "")
             + (f"（{cls['version']}）" if cls["version"] else "") + note,
             f"分类：{cls['category']} {category['title']}"]
    includes = json.loads(cls["includes"])
    if includes:
        lines.append(f"混入：{'、'.join(includes)}")
    if cls["overview"]:
        lines += ["", cls["overview"]]
    keys = conn.execute("SELECT name, description FROM keys WHERE class_name = ? ORDER BY rowid", (cls["name"],)).fetchall()
    if keys:
        lines += ["", "设置键说明（【补充】官方只列键名，以下已在 SketchUp 2026 上核对；没列出的键见上面的官方列表）："]
        lines += [f"  {row['name']} — {row['description']}" for row in keys]
    for group in json.loads(cls["constants"]):
        lines += ["", f"常量（{group['group']}）：{', '.join(group['names'])}"]
    for scope, title in (("class", "类方法"), ("instance", "实例方法")):
        rows = conn.execute("SELECT * FROM methods WHERE class_name = ? AND scope = ? ORDER BY name",
                            (cls["name"], scope)).fetchall()
        if rows:
            lines += ["", f"{title}："]
            lines += [f"  {'#' if scope == 'instance' else '.'}{row['name']} — {row['summary']}"
                      + (f"（{row['version']}）" if row["version"] else "") for row in rows]
    for ancestor in lineage(conn, cls)[1:]:
        names = [row["name"] for row in conn.execute(
            "SELECT name FROM methods WHERE class_name = ? AND scope = 'instance' ORDER BY name", (ancestor,))]
        if names:
            lines += ["", f"继承自 {ancestor}：{', '.join(names)}"]
    return "\n".join(lines + ["", f"下一步：method {cls['name'].rpartition('::')[2]}#<方法名>"])


def cmd_method(conn, target: str, name: str | None) -> str:
    class_name, method_name, scope = split_target(target, name)
    if method_name == "new" and scope == "class":  # 文档里构造函数记作 #initialize，调用时写 类名.new
        method_name, scope = "initialize", "instance"
    if class_name is None:
        rows = conn.execute("SELECT * FROM methods WHERE name = ? ORDER BY class_name", (method_name,)).fetchall()
        if not rows:
            return f"没有叫 {method_name} 的方法。用 search {method_name} 查找。"
        if len(rows) > 1:
            rows = sorted(rows, key=lambda row: (secondary(row["class_name"]), row["class_name"]))
            return "有多个类定义了这个方法，写成 类名#方法名 再查：\n" + "\n".join(
                f"{ident(row)} — {row['summary']}" for row in rows)
        return render_method(rows[0], "")
    cls, note = resolve_class(conn, class_name)
    if cls is None:
        return note
    for owner in lineage(conn, cls):
        sql = "SELECT * FROM methods WHERE class_name = ? AND name = ?" + (" AND scope = ?" if scope else "")
        rows = conn.execute(sql, (owner, method_name, scope) if scope else (owner, method_name)).fetchall()
        if rows:
            inherited = f"（{cls['name']} 继承自 {owner}）" if owner != cls["name"] else ""
            return "\n\n".join(render_method(row, inherited + note) for row in rows)
    return f"{cls['name']} 及其父类没有方法 {method_name}。用 class {cls['name']} 看全部方法。"


def render_tags(tags: dict) -> list[str]:
    lines = []
    for key, title in (("parameters", "参数"), ("options", "选项（Hash 的键）"), ("yield_parameters", "块参数")):
        items = tags.get(key, [])
        if items:
            lines.append(f"{title}：")
        for item in items:
            text = f"  {item.get('name', '')}"
            if item.get("types"):
                text += f" ({item['types']})"
            if item.get("default"):
                text += f" 默认 {item['default']}"
            if item.get("description"):
                text += f" — {item['description']}"
            lines.append(text)
    for key, title in (("returns", "返回"), ("raises", "抛出"), ("yields", "块")):
        for item in tags.get(key, []):
            lines.append(f"{title}：{item.get('types', '')}" + (f" — {item['description']}" if item.get("description") else ""))
    for note in tags.get("notes", []):
        lines.append(f"注意：{note}")
    for bug in tags.get("known_bugs", []):
        lines.append(f"已知问题：{bug.get('description', '')}")
    if tags.get("deprecated"):
        lines.append(f"已弃用：{tags['deprecated']}")
    if tags.get("see_also"):
        lines.append("参见：" + "、".join(item.get("description", item.get("name", "")) for item in tags["see_also"]))
    for example in tags.get("examples", []):
        lines += [f"示例{'：' + example['title'] if example.get('title') else ''}", f"```ruby\n{example['code']}\n```"]
    return lines


def render_method(row, note: str) -> str:
    lines = [ident(row) + note, *json.loads(row["signatures"])]
    if row["version"]:
        lines.append(f"最低版本：{row['version']}")
    if row["description"]:
        lines += ["", row["description"]]
    tags = render_tags(json.loads(row["tags"]))
    if tags:
        lines += [""] + tags
    for overload in json.loads(row["overloads"]):
        lines += ["", f"── 调用形式：{overload['signature']}"]
        if overload["description"]:
            lines.append(overload["description"])
        lines += render_tags(overload["tags"])
    return "\n".join(lines)


def cmd_guide(conn, name: str) -> str:
    row = conn.execute("SELECT * FROM classes WHERE kind = 'guide' AND name = ? COLLATE NOCASE", (name,)).fetchone()
    return row["overview"] if row else f"没有专题 {name}。catalog guides 列出全部专题。"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="\n".join(__doc__.splitlines()[2:]))
    commands = parser.add_subparsers(dest="command", required=True)
    catalog = commands.add_parser("catalog", help="不带参数列出一级目录；带分类列出其中的类")
    catalog.add_argument("category", nargs="?", help="如 entities、components、geom")
    search = commands.add_parser("search", help="用英文关键词检索方法、类、设置键和专题；设置键的补充说明可用中文")
    search.add_argument("keyword", nargs="+")
    search.add_argument("--limit", type=int, default=20)
    search.add_argument("--offset", type=int, default=0)
    cls = commands.add_parser("class", help="类或模块的说明和方法列表，可一次查多个")
    cls.add_argument("names", nargs="+", help="如 Face、Sketchup::Face、Geom::Transformation")
    method = commands.add_parser("method", help="方法详情，可一次查多个")
    method.add_argument("targets", nargs="+", help="如 Face#pushpull、Sketchup.active_model、View#write_image；"
                                                   "只写方法名会列出定义它的类；也可以把类名和方法名分开写：Face pushpull")
    guide = commands.add_parser("guide", help="专题全文")
    guide.add_argument("name", help="如 exporter_options；catalog guides 列出全部专题")
    args = parser.parse_args(argv)
    if getattr(args, "limit", 1) <= 0 or getattr(args, "offset", 0) < 0:
        parser.error("limit 必须为正，offset 不能为负")
    with closing(connection()) as conn:
        if args.command == "catalog":
            print(cmd_catalog(conn, args.category))
        elif args.command == "search":
            print(cmd_search(conn, " ".join(args.keyword), args.limit, args.offset))
        elif args.command == "class":
            print(SEPARATOR.join(cmd_class(conn, name) for name in args.names))
        elif args.command == "method":
            targets = args.targets
            if len(targets) == 2 and not any(mark in "".join(targets) for mark in "#."):
                pairs = [(targets[0], targets[1])]  # Face pushpull
            else:
                pairs = [(target, None) for target in targets]
            print(SEPARATOR.join(cmd_method(conn, target, name) for target, name in pairs))
        else:
            print(cmd_guide(conn, args.name))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
