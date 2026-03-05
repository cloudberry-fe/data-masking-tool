"""
数据源连接管理器
支持多种数据库类型的连接管理
"""
import logging
from typing import Optional, Dict, Any, List, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseDatasourceConnector(ABC):
    """数据源连接器基类"""

    @abstractmethod
    def test_connection(self, config: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """
        测试连接

        Returns:
            (是否成功, 消息, 版本信息)
        """
        pass

    @abstractmethod
    def get_schemas(self, config: Dict[str, Any]) -> List[str]:
        """获取Schema列表"""
        pass

    @abstractmethod
    def get_tables(self, config: Dict[str, Any], schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表列表"""
        pass

    @abstractmethod
    def get_columns(self, config: Dict[str, Any], table: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取字段列表"""
        pass

    @abstractmethod
    def get_roles(self, config: Dict[str, Any]) -> List[str]:
        """获取数据库角色列表"""
        pass

    @abstractmethod
    def execute_sql(self, config: Dict[str, Any], sql: str) -> List[Dict[str, Any]]:
        """执行SQL"""
        pass


class PostgreSQLConnector(BaseDatasourceConnector):
    """PostgreSQL/HashData连接器"""

    def test_connection(self, config: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=config.get("host"),
                port=config.get("port", 5432),
                database=config.get("database_name"),
                user=config.get("username"),
                password=config.get("password"),
                connect_timeout=10,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return True, "连接成功", version
        except ImportError:
            return False, "psycopg2未安装", None
        except Exception as e:
            logger.exception("PostgreSQL连接测试失败")
            return False, f"连接失败: {str(e)}", None

    def get_schemas(self, config: Dict[str, Any]) -> List[str]:
        """获取PostgreSQL Schema列表"""
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=config.get("host"),
                port=config.get("port", 5432),
                database=config.get("database_name"),
                user=config.get("username"),
                password=config.get("password"),
            )
            cursor = conn.cursor()

            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                ORDER BY schema_name
            """)

            schemas = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()
            return schemas
        except Exception as e:
            logger.exception("获取Schema列表失败")
            raise

    def get_tables(self, config: Dict[str, Any], schema: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=config.get("host"),
                port=config.get("port", 5432),
                database=config.get("database_name"),
                user=config.get("username"),
                password=config.get("password"),
            )
            cursor = conn.cursor()

            search_schema = schema or "public"
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name
            """, (search_schema,))

            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "table_name": row[0],
                    "table_comment": ""
                })

            cursor.close()
            conn.close()
            return tables
        except Exception as e:
            logger.exception("获取表列表失败")
            raise

    def get_columns(self, config: Dict[str, Any], table: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = psycopg2.connect(
                host=config.get("host"),
                port=config.get("port", 5432),
                database=config.get("database_name"),
                user=config.get("username"),
                password=config.get("password"),
            )
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            search_schema = schema or "public"
            cursor.execute("""
                SELECT
                    c.column_name,
                    c.data_type,
                    c.is_nullable = 'YES' AS is_nullable,
                    c.character_maximum_length,
                    c.numeric_precision,
                    c.numeric_scale
                FROM information_schema.columns c
                WHERE c.table_schema = %s AND c.table_name = %s
                ORDER BY c.ordinal_position
            """, (search_schema, table))

            columns = []
            for row in cursor.fetchall():
                # 构建完整的数据类型
                data_type = row["data_type"]
                if row.get("character_maximum_length"):
                    data_type = f"{data_type}({row['character_maximum_length']})"
                elif row.get("numeric_precision"):
                    if row.get("numeric_scale"):
                        data_type = f"{data_type}({row['numeric_precision']},{row['numeric_scale']})"
                    else:
                        data_type = f"{data_type}({row['numeric_precision']})"

                columns.append({
                    "column_name": row["column_name"],
                    "data_type": data_type,
                    "is_nullable": row.get("is_nullable", True)
                })

            cursor.close()
            conn.close()
            return columns
        except Exception as e:
            logger.exception("获取字段列表失败")
            raise

    def get_roles(self, config: Dict[str, Any]) -> List[str]:
        """获取PostgreSQL角色列表"""
        try:
            import psycopg2

            conn = psycopg2.connect(
                host=config.get("host"),
                port=config.get("port", 5432),
                database=config.get("database_name"),
                user=config.get("username"),
                password=config.get("password"),
            )
            cursor = conn.cursor()

            # 查询所有非系统角色
            cursor.execute("""
                SELECT rolname
                FROM pg_roles
                WHERE rolname NOT LIKE 'pg_%'
                AND rolname NOT LIKE 'gp_%'
                ORDER BY rolname
            """)

            roles = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()
            return roles
        except Exception as e:
            logger.exception("获取角色列表失败")
            raise

    def execute_sql(self, config: Dict[str, Any], sql: str) -> List[Dict[str, Any]]:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            conn = psycopg2.connect(
                host=config.get("host"),
                port=config.get("port", 5432),
                database=config.get("database_name"),
                user=config.get("username"),
                password=config.get("password"),
            )
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(sql)

            results = []
            if cursor.description:
                for row in cursor.fetchall():
                    results.append(dict(row))

            conn.commit()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            logger.exception("执行SQL失败")
            raise


class MySQLConnector(BaseDatasourceConnector):
    """MySQL连接器"""

    def test_connection(self, config: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        try:
            import pymysql
            conn = pymysql.connect(
                host=config.get("host"),
                port=config.get("port", 3306),
                database=config.get("database_name"),
                user=config.get("username"),
                password=config.get("password"),
                connect_timeout=10,
            )
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return True, "连接成功", version
        except ImportError:
            return False, "pymysql未安装", None
        except Exception as e:
            logger.exception("MySQL连接测试失败")
            return False, f"连接失败: {str(e)}", None

    def get_schemas(self, config: Dict[str, Any]) -> List[str]:
        """获取MySQL数据库列表（MySQL中schema等同于database）"""
        try:
            import pymysql

            conn = pymysql.connect(
                host=config.get("host"),
                port=config.get("port", 3306),
                user=config.get("username"),
                password=config.get("password"),
            )
            cursor = conn.cursor()

            cursor.execute("SHOW DATABASES")

            schemas = [row[0] for row in cursor.fetchall()
                      if row[0] not in ('information_schema', 'mysql', 'performance_schema', 'sys')]

            cursor.close()
            conn.close()
            return schemas
        except Exception as e:
            logger.exception("获取数据库列表失败")
            raise

    def get_tables(self, config: Dict[str, Any], schema: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            import pymysql
            from pymysql.cursors import DictCursor

            conn = pymysql.connect(
                host=config.get("host"),
                port=config.get("port", 3306),
                database=config.get("database_name"),
                user=config.get("username"),
                password=config.get("password"),
                cursorclass=DictCursor,
            )
            cursor = conn.cursor()

            db_name = schema or config.get("database_name")
            cursor.execute("""
                SELECT
                    TABLE_NAME AS table_name,
                    TABLE_COMMENT AS table_comment
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                ORDER BY TABLE_NAME
            """, (db_name,))

            tables = []
            for row in cursor.fetchall():
                tables.append({
                    "table_name": row["table_name"],
                    "table_comment": row.get("table_comment") or ""
                })

            cursor.close()
            conn.close()
            return tables
        except Exception as e:
            logger.exception("获取表列表失败")
            raise

    def get_columns(self, config: Dict[str, Any], table: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            import pymysql
            from pymysql.cursors import DictCursor

            conn = pymysql.connect(
                host=config.get("host"),
                port=config.get("port", 3306),
                database=config.get("database_name"),
                user=config.get("username"),
                password=config.get("password"),
                cursorclass=DictCursor,
            )
            cursor = conn.cursor()

            db_name = schema or config.get("database_name")
            cursor.execute("""
                SELECT
                    COLUMN_NAME AS column_name,
                    DATA_TYPE AS data_type,
                    IS_NULLABLE = 'YES' AS is_nullable,
                    COLUMN_COMMENT AS column_comment
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """, (db_name, table))

            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "column_name": row["column_name"],
                    "data_type": row["data_type"],
                    "column_comment": row.get("column_comment") or "",
                    "is_nullable": row.get("is_nullable", True)
                })

            cursor.close()
            conn.close()
            return columns
        except Exception as e:
            logger.exception("获取字段列表失败")
            raise

    def get_roles(self, config: Dict[str, Any]) -> List[str]:
        """获取MySQL用户列表"""
        try:
            import pymysql

            conn = pymysql.connect(
                host=config.get("host"),
                port=config.get("port", 3306),
                user=config.get("username"),
                password=config.get("password"),
            )
            cursor = conn.cursor()

            cursor.execute("SELECT user FROM mysql.user")
            roles = [row[0] for row in cursor.fetchall()]

            cursor.close()
            conn.close()
            return roles
        except Exception as e:
            logger.exception("获取用户列表失败")
            raise

    def execute_sql(self, config: Dict[str, Any], sql: str) -> List[Dict[str, Any]]:
        try:
            import pymysql
            from pymysql.cursors import DictCursor

            conn = pymysql.connect(
                host=config.get("host"),
                port=config.get("port", 3306),
                database=config.get("database_name"),
                user=config.get("username"),
                password=config.get("password"),
                cursorclass=DictCursor,
            )
            cursor = conn.cursor()
            cursor.execute(sql)

            results = []
            if cursor.description:
                for row in cursor.fetchall():
                    results.append(dict(row))

            conn.commit()
            cursor.close()
            conn.close()
            return results
        except Exception as e:
            logger.exception("执行SQL失败")
            raise


class OracleConnector(BaseDatasourceConnector):
    """Oracle连接器（占位实现）"""

    def test_connection(self, config: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        try:
            # 这里是简化实现，实际需要oracledb
            return False, "Oracle连接器需要oracledb库，请安装后使用", None
        except Exception as e:
            return False, f"连接失败: {str(e)}", None

    def get_schemas(self, config: Dict[str, Any]) -> List[str]:
        raise NotImplementedError("Oracle连接器待实现")

    def get_roles(self, config: Dict[str, Any]) -> List[str]:
        raise NotImplementedError("Oracle连接器待实现")

    def get_tables(self, config: Dict[str, Any], schema: Optional[str] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("Oracle连接器待实现")

    def get_columns(self, config: Dict[str, Any], table: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        raise NotImplementedError("Oracle连接器待实现")

    def execute_sql(self, config: Dict[str, Any], sql: str) -> List[Dict[str, Any]]:
        raise NotImplementedError("Oracle连接器待实现")


class DatasourceManager:
    """数据源管理器"""

    _connectors: Dict[str, BaseDatasourceConnector] = {}

    def __init__(self):
        self._register_connectors()

    def _register_connectors(self):
        """注册连接器"""
        self._connectors["MPP"] = PostgreSQLConnector()
        self._connectors["POSTGRESQL"] = PostgreSQLConnector()
        self._connectors["MYSQL"] = MySQLConnector()
        self._connectors["ORACLE"] = OracleConnector()
        self._connectors["GOLDENDB"] = MySQLConnector()  # GoldenDB兼容MySQL协议
        self._connectors["DM"] = OracleConnector()  # 达梦兼容Oracle协议

    def get_connector(self, datasource_type: str) -> BaseDatasourceConnector:
        """获取连接器"""
        connector = self._connectors.get(datasource_type.upper())
        if not connector:
            raise ValueError(f"不支持的数据源类型: {datasource_type}")
        return connector

    def test_connection(self, datasource_type: str, config: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """测试连接"""
        connector = self.get_connector(datasource_type)
        return connector.test_connection(config)

    def get_schemas(self, datasource_type: str, config: Dict[str, Any]) -> List[str]:
        """获取Schema列表"""
        connector = self.get_connector(datasource_type)
        return connector.get_schemas(config)

    def get_tables(self, datasource_type: str, config: Dict[str, Any], schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表列表"""
        connector = self.get_connector(datasource_type)
        return connector.get_tables(config, schema)

    def get_columns(self, datasource_type: str, config: Dict[str, Any], table: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取字段列表"""
        connector = self.get_connector(datasource_type)
        return connector.get_columns(config, table, schema)

    def get_roles(self, datasource_type: str, config: Dict[str, Any]) -> List[str]:
        """获取数据库角色列表"""
        connector = self.get_connector(datasource_type)
        return connector.get_roles(config)

    def execute_sql(self, datasource_type: str, config: Dict[str, Any], sql: str) -> List[Dict[str, Any]]:
        """执行SQL"""
        connector = self.get_connector(datasource_type)
        return connector.execute_sql(config, sql)


# 单例
_datasource_manager: Optional[DatasourceManager] = None


def get_datasource_manager() -> DatasourceManager:
    """获取数据源管理器单例"""
    global _datasource_manager
    if _datasource_manager is None:
        _datasource_manager = DatasourceManager()
    return _datasource_manager
