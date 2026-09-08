"""YJK数据库读写与校验模块。"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


REFERENCE_LINKS = {
    "StdFlrID": "tblStdFlr",
    "SectID": None,
    "GridID": "tblGrid",
    "AxisID": "tblAxis",
    "JtID": "tblJoint",
    "Jt1ID": "tblJoint",
    "Jt2ID": "tblJoint",
    "SlabID": "tblSlab",
}

EXACT_REFERENCE_LINKS = {
    ("tblLoadSeg", "SectID"): [("tblLoadSect", "ID"), ("tblSkinLoadSect", "ID")],
    ("tblLoadSeg", "idDef"): [("tblLoadSect", "idNew"), ("tblSkinLoadSect", "idNew")],
}

SECT_TABLE_BY_SEGMENT = {
    "tblWallSeg": "tblWallSect",
    "tblWallHole": "tblWallHoleDef",
    "tblBeamSeg": "tblBeamSect",
    "tblSubBeam": "tblBeamSect",
    "tblSlabHole": "tblSlabHoleDef",
    "tblCantiSlab": "tblCantiSlabDef",
    "tblColSeg": "tblColSect",
    "tblBraceSeg": "tblBraceSect",
    "tblLoadSeg": "tblLoadSect",
    "tblStairSeg": "tblStairDef",
}

NON_UNIQUE_REFERENCE_COLUMNS = {
    ("tblProperty", "ID"),
    ("tblProperty", "idNew"),
}


class YJKDatabase:
    """YJK数据库读写类。"""

    def __init__(self, db_path: str, encoding: str = "gbk"):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.text_factory = lambda b: b.decode(encoding, errors="ignore")
        self.cursor = self.conn.cursor()

    def close(self):
        """关闭数据库连接。"""
        self.conn.close()

    def get_tables(self) -> List[str]:
        """获取所有业务表名。"""
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        return [row[0] for row in self.cursor.fetchall()]

    def get_table_columns(self, table_name: str) -> List[str]:
        """获取表字段名列表。"""
        self.cursor.execute(f"PRAGMA table_info('{table_name}')")
        return [row[1] for row in self.cursor.fetchall()]

    def get_tables_with_column(self, column_name: str) -> List[str]:
        """获取包含指定字段的表。"""
        return [table for table in self.get_tables() if column_name in self.get_table_columns(table)]

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """获取表结构信息。"""
        self.cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns = []
        for row in self.cursor.fetchall():
            columns.append(
                {
                    "name": row[1],
                    "type": row[2],
                    "notnull": row[3],
                    "dflt_value": row[4],
                    "pk": row[5],
                }
            )

        self.cursor.execute(f"PRAGMA index_list('{table_name}')")
        indexes = []
        for row in self.cursor.fetchall():
            idx_name = row[1]
            self.cursor.execute(f"PRAGMA index_info('{idx_name}')")
            idx_cols = [r[2] for r in self.cursor.fetchall()]
            indexes.append({"name": idx_name, "unique": row[2], "columns": idx_cols})

        return {"columns": columns, "indexes": indexes}

    def column_has_unique_constraint(self, table_name: str, column_name: str) -> bool:
        """判断字段是否具备主键或单列唯一约束。"""
        table_info = self.get_table_info(table_name)
        for column in table_info["columns"]:
            if column["name"] == column_name and column["pk"]:
                return True
        for index in table_info["indexes"]:
            if index["unique"] and index["columns"] == [column_name]:
                return True
        return False

    def get_row_count(self, table_name: str) -> int:
        """获取表记录数。"""
        self.cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
        return int(self.cursor.fetchone()[0])

    def query(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[tuple]:
        """执行查询。"""
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)
        return self.cursor.fetchall()

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None):
        """执行更新。"""
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)
        self.conn.commit()

    def _fetch_all_dicts(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[Dict[str, Any]]:
        if params:
            self.cursor.execute(sql, params)
        else:
            self.cursor.execute(sql)
        cols = [desc[0] for desc in self.cursor.description]
        return [dict(zip(cols, row)) for row in self.cursor.fetchall()]

    def _normalize_scalar_int(self, value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.lstrip("-").isdigit():
                return int(stripped)
            return None
        return None

    def _get_runtime_column_types(self, table_name: str, column_name: str) -> List[str]:
        self.cursor.execute(
            f"SELECT DISTINCT typeof({column_name}) FROM '{table_name}' WHERE {column_name} IS NOT NULL ORDER BY 1"
        )
        return [row[0] for row in self.cursor.fetchall()]

    def _column_is_scalar_numeric(self, table_name: str, column_name: str) -> bool:
        runtime_types = self._get_runtime_column_types(table_name, column_name)
        if not runtime_types:
            return True
        return all(value_type in {"integer", "real", "text"} for value_type in runtime_types)

    def _get_column_min(self, table_name: str, column_name: str, non_negative_only: bool = False) -> Optional[int]:
        if not self._column_is_scalar_numeric(table_name, column_name):
            return None
        self.cursor.execute(f"SELECT {column_name} FROM '{table_name}' WHERE {column_name} IS NOT NULL")
        values = []
        for (value,) in self.cursor.fetchall():
            normalized = self._normalize_scalar_int(value)
            if normalized is not None and (not non_negative_only or normalized >= 0):
                values.append(normalized)
        return min(values) if values else None

    def _get_column_max(self, table_name: str, column_name: str) -> Optional[int]:
        if not self._column_is_scalar_numeric(table_name, column_name):
            return None
        self.cursor.execute(f"SELECT {column_name} FROM '{table_name}' WHERE {column_name} IS NOT NULL")
        values = []
        for (value,) in self.cursor.fetchall():
            normalized = self._normalize_scalar_int(value)
            if normalized is not None:
                values.append(normalized)
        return max(values) if values else None

    def _get_duplicate_values(self, table_name: str, column_name: str) -> List[int]:
        if not self._column_is_scalar_numeric(table_name, column_name):
            return []
        self.cursor.execute(
            f"""
            SELECT {column_name}
            FROM '{table_name}'
            WHERE {column_name} IS NOT NULL
            GROUP BY {column_name}
            HAVING COUNT(*) > 1
            ORDER BY {column_name}
            """
        )
        duplicates = []
        for (value,) in self.cursor.fetchall():
            normalized = self._normalize_scalar_int(value)
            if normalized is not None:
                duplicates.append(normalized)
        return duplicates

    def _resolve_reference_specs(self, table_name: str, column_name: str) -> List[tuple[str, str]]:
        if (table_name, column_name) in EXACT_REFERENCE_LINKS:
            return EXACT_REFERENCE_LINKS[(table_name, column_name)]
        if column_name != "SectID":
            reference_table = REFERENCE_LINKS.get(column_name)
        else:
            reference_table = SECT_TABLE_BY_SEGMENT.get(table_name)
        if not reference_table:
            return []
        return [(reference_table, "ID")]

    def get_global_id_baseline(self) -> Dict[str, Any]:
        """统计参考库中全局ID和idNew的最小值。"""
        tables_with_id = self.get_tables_with_column("ID")
        tables_with_idnew = self.get_tables_with_column("idNew")

        id_mins = []
        for table in tables_with_id:
            min_value = self._get_column_min(table, "ID")
            if min_value is not None:
                id_mins.append({"table": table, "min": min_value})

        idnew_mins = []
        for table in tables_with_idnew:
            min_value = self._get_column_min(table, "idNew")
            if min_value is not None:
                idnew_mins.append({"table": table, "min": min_value})

        return {
            "reference_database": self.db_path,
            "tables_with_id": tables_with_id,
            "tables_with_idnew": tables_with_idnew,
            "min_id": min((item["min"] for item in id_mins), default=None),
            "min_idnew": min((item["min"] for item in idnew_mins), default=None),
            "id_table_mins": id_mins,
            "idnew_table_mins": idnew_mins,
        }

    def get_schema_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """获取库的表结构快照。"""
        snapshot = {}
        for table in self.get_tables():
            snapshot[table] = {
                "columns": self.get_table_columns(table),
                "row_count": self.get_row_count(table),
            }
        return snapshot

    def get_strict_minimum_profile(self) -> Dict[str, Any]:
        """基于参考库提取严格最小模型轮廓。"""
        table_counts = {}
        for table in self.get_tables():
            table_counts[table] = self.get_row_count(table)
        non_empty_tables = {table: count for table, count in table_counts.items() if count > 0}
        return {
            "reference_database": self.db_path,
            "table_counts": table_counts,
            "non_empty_tables": non_empty_tables,
        }

    def get_space_layer_summary(self) -> Dict[str, Any]:
        """汇总 YJK 空间层（StdFlrID / ID = -1）相关节点、网格和轴线特征。"""
        stdflr_columns = self.get_table_columns("tblStdFlr") if "tblStdFlr" in self.get_tables() else []
        joint_columns = self.get_table_columns("tblJoint") if "tblJoint" in self.get_tables() else []
        grid_columns = self.get_table_columns("tblGrid") if "tblGrid" in self.get_tables() else []
        axis_columns = self.get_table_columns("tblAxis") if "tblAxis" in self.get_tables() else []

        stdflr_space_rows = 0
        if "ID" in stdflr_columns:
            stdflr_space_rows = self.query("SELECT COUNT(*) FROM tblStdFlr WHERE ID = -1")[0][0]

        joint_count = 0
        if "StdFlrID" in joint_columns:
            joint_count = self.query("SELECT COUNT(*) FROM tblJoint WHERE StdFlrID = -1")[0][0]

        grid_count = 0
        grid_axis_nonzero = 0
        if "StdFlrID" in grid_columns:
            grid_count = self.query("SELECT COUNT(*) FROM tblGrid WHERE StdFlrID = -1")[0][0]
            if "AxisID" in grid_columns:
                grid_axis_nonzero = self.query(
                    "SELECT COUNT(*) FROM tblGrid WHERE StdFlrID = -1 AND AxisID IS NOT NULL AND AxisID > 0"
                )[0][0]

        axis_count = 0
        if "StdFlrID" in axis_columns:
            axis_count = self.query("SELECT COUNT(*) FROM tblAxis WHERE StdFlrID = -1")[0][0]

        return {
            "exists": bool(stdflr_space_rows or joint_count or grid_count or axis_count),
            "stdflr_count": int(stdflr_space_rows),
            "joint_count": int(joint_count),
            "grid_count": int(grid_count),
            "axis_count": int(axis_count),
            "grid_axis_nonzero_count": int(grid_axis_nonzero),
            "topology": (
                "space-layer-node-grid"
                if joint_count > 0 and grid_count > 0 and axis_count == 0
                else "standard-like"
            ),
        }

    def get_next_global_identifiers(self) -> Dict[str, Optional[int]]:
        """获取当前数据库中下一个可分配的全局 ID / idNew。"""
        id_max = []
        idnew_max = []
        for table in self.get_tables_with_column("ID"):
            value = self._get_column_max(table, "ID")
            if value is not None:
                id_max.append(value)
        for table in self.get_tables_with_column("idNew"):
            value = self._get_column_max(table, "idNew")
            if value is not None:
                idnew_max.append(value)

        baseline = self.get_global_id_baseline()
        next_id = max(id_max) + 1 if id_max else baseline["min_id"]
        next_idnew = max(idnew_max) + 1 if idnew_max else baseline["min_idnew"]
        return {"next_id": next_id, "next_idnew": next_idnew}

    def allocate_global_ids(self, count: int = 1) -> Dict[str, int]:
        """根据当前数据库状态分配一段连续的全局 ID / idNew。"""
        if count < 1:
            raise ValueError("count must be >= 1")
        next_values = self.get_next_global_identifiers()
        return {
            "start_id": int(next_values["next_id"]),
            "start_idnew": int(next_values["next_idnew"]),
            "end_id": int(next_values["next_id"] + count - 1),
            "end_idnew": int(next_values["next_idnew"] + count - 1),
            "count": count,
        }

    def insert_row(self, table_name: str, row_data: Dict[str, Any], auto_allocate_ids: bool = False) -> Dict[str, Any]:
        """插入一行数据；可选自动补全 ID / idNew。"""
        payload = dict(row_data)
        columns = self.get_table_columns(table_name)
        allocation = None
        if auto_allocate_ids:
            if "ID" in columns and "ID" not in payload:
                allocation = self.allocate_global_ids(1)
                payload["ID"] = allocation["start_id"]
            if "idNew" in columns and "idNew" not in payload:
                if allocation is None:
                    allocation = self.allocate_global_ids(1)
                payload["idNew"] = allocation["start_idnew"]

        insert_columns = [column for column in columns if column in payload]
        if not insert_columns:
            raise ValueError(f"no matching columns found for table {table_name}")

        placeholders = ", ".join(["?"] * len(insert_columns))
        sql = f"INSERT INTO '{table_name}' ({', '.join(insert_columns)}) VALUES ({placeholders})"
        self.execute(sql, tuple(payload[column] for column in insert_columns))
        return payload

    def _validate_required_tables(self, target_db: "YJKDatabase") -> Dict[str, Any]:
        reference_tables = self.get_tables()
        target_tables = target_db.get_tables()
        minimum_required_tables = [table for table in reference_tables if self.get_row_count(table) > 0]
        missing_tables = [table for table in reference_tables if table not in target_tables]
        missing_minimum_tables = [table for table in minimum_required_tables if table not in target_tables]
        empty_reference_tables = [table for table in reference_tables if self.get_row_count(table) == 0]
        return {
            "reference_count": len(reference_tables),
            "target_count": len(target_tables),
            "minimum_required_tables": minimum_required_tables,
            "missing_tables": missing_tables,
            "missing_minimum_tables": missing_minimum_tables,
            "extra_tables": [table for table in target_tables if table not in reference_tables],
            "reference_empty_tables": empty_reference_tables,
        }

    def _validate_id_rules(self, target_db: "YJKDatabase") -> Dict[str, Any]:
        baseline = self.get_global_id_baseline()
        duplicate_id_tables = []
        duplicate_idnew_tables = []
        below_baseline_id = []
        below_baseline_idnew = []
        non_scalar_id_tables = []
        non_scalar_idnew_tables = []

        for table in target_db.get_tables_with_column("ID"):
            if not target_db._column_is_scalar_numeric(table, "ID"):
                non_scalar_id_tables.append({"table": table, "types": target_db._get_runtime_column_types(table, "ID")})
                continue
            if (table, "ID") not in NON_UNIQUE_REFERENCE_COLUMNS and target_db.column_has_unique_constraint(
                table, "ID"
            ):
                duplicates = target_db._get_duplicate_values(table, "ID")
                if duplicates:
                    duplicate_id_tables.append({"table": table, "values": duplicates[:10]})
            min_value = target_db._get_column_min(table, "ID", non_negative_only=True)
            if baseline["min_id"] is not None and min_value is not None and min_value < baseline["min_id"]:
                below_baseline_id.append({"table": table, "min": min_value})

        for table in target_db.get_tables_with_column("idNew"):
            if not target_db._column_is_scalar_numeric(table, "idNew"):
                non_scalar_idnew_tables.append(
                    {"table": table, "types": target_db._get_runtime_column_types(table, "idNew")}
                )
                continue
            if (table, "idNew") not in NON_UNIQUE_REFERENCE_COLUMNS and target_db.column_has_unique_constraint(
                table, "idNew"
            ):
                duplicates = target_db._get_duplicate_values(table, "idNew")
                if duplicates:
                    duplicate_idnew_tables.append({"table": table, "values": duplicates[:10]})
            min_value = target_db._get_column_min(table, "idNew", non_negative_only=True)
            if baseline["min_idnew"] is not None and min_value is not None and min_value < baseline["min_idnew"]:
                below_baseline_idnew.append({"table": table, "min": min_value})

        return {
            "baseline": baseline,
            "duplicate_id_tables": duplicate_id_tables,
            "duplicate_idnew_tables": duplicate_idnew_tables,
            "below_baseline_id": below_baseline_id,
            "below_baseline_idnew": below_baseline_idnew,
            "non_scalar_id_tables": non_scalar_id_tables,
            "non_scalar_idnew_tables": non_scalar_idnew_tables,
        }

    def _validate_foreign_keys(self, target_db: "YJKDatabase") -> List[Dict[str, Any]]:
        findings = []
        for table in target_db.get_tables():
            columns = target_db.get_table_columns(table)
            for column_name in columns:
                reference_specs = [
                    (reference_table, reference_key)
                    for reference_table, reference_key in target_db._resolve_reference_specs(table, column_name)
                    if reference_table in target_db.get_tables()
                ]
                if not reference_specs:
                    continue
                match_conditions = [f"target_{idx}.{reference_key} IS NOT NULL" for idx, (_, reference_key) in enumerate(reference_specs)]
                join_sql = []
                for idx, (reference_table, reference_key) in enumerate(reference_specs):
                    join_sql.append(
                        f"LEFT JOIN '{reference_table}' AS target_{idx} ON source.{column_name} = target_{idx}.{reference_key}"
                    )
                rows = target_db.query(
                    f"""
                    SELECT COUNT(*)
                    FROM '{table}' AS source
                    {' '.join(join_sql)}
                    WHERE source.{column_name} IS NOT NULL
                      AND source.{column_name} > 0
                      AND NOT ({' OR '.join(match_conditions)})
                    """
                )
                invalid_count = int(rows[0][0])
                if invalid_count:
                    findings.append(
                        {
                            "table": table,
                            "column": column_name,
                            "reference_specs": [
                                {"table": reference_table, "key": reference_key}
                                for reference_table, reference_key in reference_specs
                            ],
                            "invalid_count": invalid_count,
                        }
                    )
        return findings

    def validate_target_database(self, target_db_path: str) -> Dict[str, Any]:
        """按当前数据库作为参考库，校验目标数据库。"""
        target_db = YJKDatabase(target_db_path)
        try:
            return {
                "reference_database": self.db_path,
                "target_database": str(target_db_path),
                "required_tables": self._validate_required_tables(target_db),
                "id_checks": self._validate_id_rules(target_db),
                "foreign_key_checks": self._validate_foreign_keys(target_db),
                "space_layer": target_db.get_space_layer_summary(),
            }
        finally:
            target_db.close()

    def validate_strict_minimum_model(self, target_db_path: str) -> Dict[str, Any]:
        """按 dtlmodel 严格最小模型轮廓校验目标库。"""
        profile = self.get_strict_minimum_profile()
        target_db = YJKDatabase(target_db_path)
        try:
            target_tables = set(target_db.get_tables())
            missing_tables = [table for table in profile["table_counts"] if table not in target_tables]
            mismatched_tables = []
            for table, expected_count in profile["table_counts"].items():
                if table not in target_tables:
                    continue
                actual_count = target_db.get_row_count(table)
                if actual_count != expected_count:
                    mismatched_tables.append(
                        {
                            "table": table,
                            "expected_count": expected_count,
                            "actual_count": actual_count,
                        }
                    )
            return {
                "reference_database": self.db_path,
                "target_database": str(target_db_path),
                "missing_tables": missing_tables,
                "mismatched_tables": mismatched_tables,
                "strict_profile": profile["non_empty_tables"],
            }
        finally:
            target_db.close()

    def suggest_minimum_model_repairs(self, target_db_path: str) -> Dict[str, Any]:
        """为最小模型缺项和关系异常生成修复建议。"""
        report = self.validate_target_database(target_db_path)
        minimum_missing = report["required_tables"]["missing_minimum_tables"]
        foreign_key_repairs = []
        for finding in report["foreign_key_checks"]:
            reference_targets = ", ".join(
                f"{item['table']}.{item['key']}" for item in finding["reference_specs"]
            )
            foreign_key_repairs.append(
                {
                    "table": finding["table"],
                    "column": finding["column"],
                    "reference_targets": reference_targets,
                    "invalid_count": finding["invalid_count"],
                    "suggestion": (
                        f"核对 {finding['table']}.{finding['column']} 的来源数据，"
                        f"补齐 {reference_targets} 对应记录或回填为有效引用"
                    ),
                }
            )

        table_repairs = []
        for table in minimum_missing:
            table_repairs.append(
                {
                    "table": table,
                    "suggestion": f"从参考库 dtlmodel.db 提取 {table} 的最小结构与必要字段，补建该表并填充最少记录",
                }
            )

        return {
            "target_database": str(target_db_path),
            "missing_minimum_tables": minimum_missing,
            "table_repairs": table_repairs,
            "foreign_key_repairs": foreign_key_repairs,
        }

    # ========== 便捷方法 ==========

    def get_all_floors(self) -> List[Dict[str, Any]]:
        return self._fetch_all_dicts("SELECT * FROM tblFloor")

    def get_all_std_floors(self) -> List[Dict[str, Any]]:
        return self._fetch_all_dicts("SELECT * FROM tblStdFlr")

    def get_all_columns(self) -> List[Dict[str, Any]]:
        return self._fetch_all_dicts("SELECT * FROM tblColSeg")

    def get_all_beams(self) -> List[Dict[str, Any]]:
        return self._fetch_all_dicts("SELECT * FROM tblBeamSeg")

    def get_all_walls(self) -> List[Dict[str, Any]]:
        return self._fetch_all_dicts("SELECT * FROM tblWallSeg")

    def get_all_slabs(self) -> List[Dict[str, Any]]:
        return self._fetch_all_dicts("SELECT * FROM tblSlab")

    def get_project_para(self) -> Dict[int, Any]:
        self.cursor.execute("SELECT ID, ParaVal FROM tblProjectPara")
        return dict(self.cursor.fetchall())

    def get_column_sections(self) -> List[Dict[str, Any]]:
        return self._fetch_all_dicts("SELECT * FROM tblColSect")

    def get_beam_sections(self) -> List[Dict[str, Any]]:
        return self._fetch_all_dicts("SELECT * FROM tblBeamSect")

    def get_wall_sections(self) -> List[Dict[str, Any]]:
        return self._fetch_all_dicts("SELECT * FROM tblWallSect")

    def get_joints(self, std_flr_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if std_flr_id is not None:
            return self._fetch_all_dicts("SELECT * FROM tblJoint WHERE StdFlrID=?", (std_flr_id,))
        return self._fetch_all_dicts("SELECT * FROM tblJoint")

    def get_axes(self, std_flr_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if std_flr_id is not None:
            return self._fetch_all_dicts("SELECT * FROM tblAxis WHERE StdFlrID=?", (std_flr_id,))
        return self._fetch_all_dicts("SELECT * FROM tblAxis")

    def get_grids(self, std_flr_id: Optional[int] = None) -> List[Dict[str, Any]]:
        if std_flr_id is not None:
            return self._fetch_all_dicts("SELECT * FROM tblGrid WHERE StdFlrID=?", (std_flr_id,))
        return self._fetch_all_dicts("SELECT * FROM tblGrid")


if __name__ == "__main__":
    reference_path = Path("dtlmodel.db")
    if not reference_path.exists():
        reference_path = Path("数据文件说明") / "8#楼住宅.ydb"

    db = YJKDatabase(str(reference_path))
    try:
        baseline = db.get_global_id_baseline()
        print(f"reference database: {baseline['reference_database']}")
        print(f"tables: {len(db.get_tables())}")
        print(f"min ID: {baseline['min_id']}")
        print(f"min idNew: {baseline['min_idnew']}")
    finally:
        db.close()
