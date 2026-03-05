"""
SQL 解析工具
从 SQL 语句中提取表名和依赖关系
"""
import re
from typing import Set, List, Dict, Optional
from dataclasses import dataclass


@dataclass
class TableReference:
    """表引用"""
    name: str
    alias: Optional[str] = None
    schema: Optional[str] = None


class SQLParser:
    """SQL 解析器，提取表依赖"""

    # SQL 关键字模式
    TABLE_PATTERNS = [
        # FROM 子句
        r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        # JOIN 子句
        r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        # INSERT INTO
        r'INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        # UPDATE
        r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        # DELETE FROM
        r'DELETE\s+FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        # CREATE TABLE ... AS SELECT ... FROM
        r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        # CREATE VIEW ... AS SELECT ... FROM
        r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
    ]

    # 需要过滤的 SQL 关键字
    SQL_KEYWORDS = {
        'SELECT', 'WHERE', 'AND', 'OR', 'ON', 'AS', 'IN', 'NOT', 'NULL',
        'TRUE', 'FALSE', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'EXISTS',
        'BETWEEN', 'LIKE', 'IS', 'GROUP', 'BY', 'ORDER', 'HAVING', 'LIMIT',
        'OFFSET', 'UNION', 'ALL', 'DISTINCT', 'WITH', 'RECURSIVE'
    }

    # 系统表前缀
    SYSTEM_TABLE_PREFIXES = {'pg_', 'information_schema', 'sys', 'mysql', 'performance_schema'}

    @classmethod
    def extract_tables(cls, sql: str) -> Set[str]:
        """
        从 SQL 中提取表名

        Args:
            sql: SQL 语句

        Returns:
            表名集合
        """
        tables = set()

        if not sql:
            return tables

        # 移除注释
        sql = cls._remove_comments(sql)

        for pattern in cls.TABLE_PATTERNS:
            matches = re.findall(pattern, sql, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                table_name = match.strip().strip('"').strip('`').strip("'")

                # 过滤系统表和关键字
                if cls._is_valid_table(table_name):
                    tables.add(table_name.lower())

        return tables

    @classmethod
    def extract_source_and_target(cls, sql: str) -> Dict[str, Set[str]]:
        """
        从 SQL 中提取源表和目标表

        Args:
            sql: SQL 语句

        Returns:
            {'source': set, 'target': set}
        """
        result = {'source': set(), 'target': set()}

        if not sql:
            return result

        sql = cls._remove_comments(sql)
        sql_upper = sql.upper()

        # 提取目标表 (INSERT INTO, UPDATE, CREATE TABLE/VIEW)
        target_patterns = [
            r'INSERT\s+INTO\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'UPDATE\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        ]

        for pattern in target_patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for match in matches:
                table_name = match.strip().strip('"').strip('`')
                if cls._is_valid_table(table_name):
                    result['target'].add(table_name.lower())

        # 提取源表 (FROM, JOIN)
        source_patterns = [
            r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
            r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)',
        ]

        for pattern in source_patterns:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for match in matches:
                table_name = match.strip().strip('"').strip('`')
                if cls._is_valid_table(table_name):
                    # 排除已经作为目标表的
                    if table_name.lower() not in result['target']:
                        result['source'].add(table_name.lower())

        return result

    @classmethod
    def parse_view_definition(cls, definition: str) -> dict:
        """
        解析视图定义，返回源表列表

        Args:
            definition: 视图定义 SQL

        Returns:
            解析结果
        """
        tables = cls.extract_tables(definition)
        return {
            "source_tables": list(tables),
            "raw_sql": definition
        }

    @classmethod
    def parse_create_statement(cls, sql: str) -> Optional[Dict]:
        """
        解析 CREATE 语句

        Args:
            sql: CREATE 语句

        Returns:
            解析结果
        """
        sql_upper = sql.upper()

        # 判断是 TABLE 还是 VIEW
        if 'CREATE TABLE' in sql_upper:
            obj_type = 'TABLE'
        elif 'CREATE VIEW' in sql_upper or 'CREATE OR REPLACE VIEW' in sql_upper:
            obj_type = 'VIEW'
        else:
            return None

        # 提取对象名
        if obj_type == 'TABLE':
            pattern = r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'
        else:
            pattern = r'CREATE\s+(?:OR\s+REPLACE\s+)?VIEW\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'

        match = re.search(pattern, sql, re.IGNORECASE)
        if not match:
            return None

        object_name = match.group(1).strip().strip('"').strip('`').lower()

        # 提取源表
        tables = cls.extract_source_and_target(sql)

        return {
            "object_type": obj_type,
            "object_name": object_name,
            "source_tables": list(tables['source']),
            "target_tables": list(tables['target']),
        }

    @classmethod
    def _remove_comments(cls, sql: str) -> str:
        """移除 SQL 注释"""
        # 移除单行注释
        sql = re.sub(r'--[^\n]*', '', sql)
        # 移除多行注释
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        return sql

    @classmethod
    def _is_valid_table(cls, name: str) -> bool:
        """检查是否为有效的表名"""
        if not name:
            return False

        name_upper = name.upper()

        # 过滤 SQL 关键字
        if name_upper in cls.SQL_KEYWORDS:
            return False

        # 过滤系统表
        name_lower = name.lower()
        for prefix in cls.SYSTEM_TABLE_PREFIXES:
            if name_lower.startswith(prefix):
                return False

        return True


class SQLDependencyAnalyzer:
    """SQL 依赖分析器"""

    @classmethod
    def analyze_dependencies(cls, sql_scripts: List[str]) -> Dict[str, Set[str]]:
        """
        分析多个 SQL 脚本的依赖关系

        Args:
            sql_scripts: SQL 脚本列表

        Returns:
            表依赖映射 {table: {dependencies}}
        """
        dependencies = {}

        for sql in sql_scripts:
            result = SQLParser.extract_source_and_target(sql)

            for target in result['target']:
                if target not in dependencies:
                    dependencies[target] = set()
                dependencies[target].update(result['source'])

        return dependencies

    @classmethod
    def build_dependency_graph(cls, dependencies: Dict[str, Set[str]]) -> Dict:
        """
        构建依赖图

        Args:
            dependencies: 依赖关系

        Returns:
            图结构 {nodes: [], edges: []}
        """
        nodes = set()
        edges = []

        for target, sources in dependencies.items():
            nodes.add(target)
            for source in sources:
                nodes.add(source)
                edges.append({
                    'source': source,
                    'target': target,
                    'type': 'DEPENDS_ON'
                })

        return {
            'nodes': [{'id': n, 'name': n} for n in nodes],
            'edges': edges
        }
