"""
HashData Lightning + Anon 脱敏引擎集成
基于 HashData Lightning (MPP) 的 Anon 插件实现高性能数据脱敏
"""
import logging
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MaskingAlgorithmType(Enum):
    """脱敏算法类型"""
    REPLACE = "REPLACE"
    MASK = "MASK"
    HASH = "HASH"
    ENCRYPT = "ENCRYPT"
    ROUND = "ROUND"
    OFFSET = "OFFSET"
    SHUFFLE = "SHUFFLE"
    NULL = "NULL"
    SUBSTITUTION = "SUBSTITUTION"
    PRESERVATION = "PRESERVATION"


@dataclass
class MaskingColumnConfig:
    """字段脱敏配置"""
    column_name: str
    algorithm: str
    params: Optional[Dict[str, Any]] = None


@dataclass
class MaskingTableConfig:
    """表脱敏配置"""
    source_table: str
    target_table: str
    columns: List[MaskingColumnConfig]
    where_condition: Optional[str] = None


@dataclass
class MaskingAlgorithm:
    """脱敏算法定义"""
    code: str
    name: str
    description: str
    params_schema: Optional[Dict[str, Any]] = None


# 预定义脱敏算法
PREDEFINED_ALGORITHMS = [
    MaskingAlgorithm(
        code="MASK",
        name="掩码脱敏",
        description="保留部分信息，其他用掩码替换",
        params_schema={
            "type": "object",
            "properties": {
                "prefix_length": {"type": "integer", "default": 3, "description": "前缀保留长度"},
                "suffix_length": {"type": "integer", "default": 4, "description": "后缀保留长度"},
                "mask_char": {"type": "string", "default": "*", "description": "掩码字符"}
            }
        }
    ),
    MaskingAlgorithm(
        code="HASH",
        name="哈希脱敏",
        description="使用SHA-256哈希算法不可逆脱敏",
        params_schema={
            "type": "object",
            "properties": {
                "salt": {"type": "string", "description": "盐值"}
            }
        }
    ),
    MaskingAlgorithm(
        code="REPLACE",
        name="替换脱敏",
        description="使用固定值替换",
        params_schema={
            "type": "object",
            "properties": {
                "replacement": {"type": "string", "description": "替换值"}
            }
        }
    ),
    MaskingAlgorithm(
        code="NULL",
        name="空值脱敏",
        description="将字段置为NULL"
    ),
    MaskingAlgorithm(
        code="ROUND",
        name="取整脱敏",
        description="数值取整",
        params_schema={
            "type": "object",
            "properties": {
                "precision": {"type": "integer", "default": -3, "description": "精度，负数表示10的倍数取整"}
            }
        }
    ),
    MaskingAlgorithm(
        code="OFFSET",
        name="偏移脱敏",
        description="数值固定偏移",
        params_schema={
            "type": "object",
            "properties": {
                "offset": {"type": "number", "description": "偏移量"},
                "min_value": {"type": "number", "description": "最小值"},
                "max_value": {"type": "number", "description": "最大值"}
            }
        }
    ),
    MaskingAlgorithm(
        code="PRESERVATION",
        name="格式保持脱敏",
        description="保持数据格式的脱敏",
        params_schema={
            "type": "object",
            "properties": {
                "preserve_format": {"type": "boolean", "default": True, "description": "是否保持格式"}
            }
        }
    ),
    MaskingAlgorithm(
        code="SHUFFLE",
        name="洗牌脱敏",
        description="列内数据随机打乱"
    ),
    MaskingAlgorithm(
        code="SUBSTITUTION",
        name="字典替换",
        description="使用字典数据替换",
        params_schema={
            "type": "object",
            "properties": {
                "dictionary": {"type": "string", "description": "字典名称"}
            }
        }
    ),
    MaskingAlgorithm(
        code="ENCRYPT",
        name="加密脱敏",
        description="可逆加密",
        params_schema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "加密密钥"}
            }
        }
    ),
]


class HashDataAnonManager:
    """HashData Anon 脱敏引擎管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化脱敏管理器

        Args:
            config: HashData Lightning 连接配置
        """
        self.config = config or {}
        self.connection = None

    def _get_connection_config(self, datasource_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取连接配置"""
        config = datasource_config or self.config
        return {
            "host": config.get("host", "localhost"),
            "port": config.get("port", 5432),
            "database": config.get("database", "hashdata"),
            "user": config.get("username", "gpadmin"),
            "password": config.get("password", ""),
        }

    def _get_connection(self, datasource_config: Optional[Dict[str, Any]] = None):
        """获取数据库连接"""
        try:
            import psycopg2
            conn_config = self._get_connection_config(datasource_config)
            return psycopg2.connect(**conn_config)
        except ImportError:
            raise RuntimeError("需要安装 psycopg2-binary 库")
        except Exception as e:
            logger.exception(f"连接HashData失败: {e}")
            raise

    def check_anon_extension(self, datasource_config: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """
        检查 Anon 插件是否安装

        Returns:
            (是否安装, 消息)
        """
        try:
            conn = self._get_connection(datasource_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT extname FROM pg_extension WHERE extname = 'anon';
            """)
            result = cursor.fetchone()

            if result:
                cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'anon';")
                version = cursor.fetchone()[0] if cursor.description else "unknown"
                cursor.close()
                conn.close()
                return True, f"Anon插件已安装 (版本: {version})"
            else:
                cursor.close()
                conn.close()
                return False, "Anon插件未安装，请先安装：CREATE EXTENSION anon;"
        except Exception as e:
            logger.exception("检查Anon插件失败")
            return False, f"检查失败: {str(e)}"

    def generate_masking_sql(self, table_config: MaskingTableConfig, source_schema: str = "public", target_schema: str = "public") -> str:
        """
        生成脱敏SQL语句

        Args:
            table_config: 表脱敏配置
            source_schema: 源Schema
            target_schema: 目标Schema

        Returns:
            脱敏SQL语句
        """
        source_table_full = f"{source_schema}.{table_config.source_table}"
        target_table_full = f"{target_schema}.{table_config.target_table}"

        # 构建字段选择列表
        select_clauses = []

        # 首先需要获取源表的所有字段（为了简化示例，这里假设我们只处理配置了的字段）
        # 实际应用中应该先查询表结构，未配置的字段原样输出

        for col_config in table_config.columns:
            clause = self._generate_column_masking_sql(col_config)
            select_clauses.append(clause)

        # 构建完整SQL
        where_clause = f" WHERE {table_config.where_condition}" if table_config.where_condition else ""

        sql = f"""
-- 数据脱敏任务: {table_config.source_table} -> {table_config.target_table}
-- 方式1: CREATE TABLE AS SELECT (如果目标表不存在)
CREATE TABLE IF NOT EXISTS {target_table_full} AS
SELECT {', '.join(select_clauses)}
FROM {source_table_full}{where_clause};

-- 方式2: 或者使用 INSERT INTO (如果目标表已存在)
-- INSERT INTO {target_table_full}
-- SELECT {', '.join(select_clauses)}
-- FROM {source_table_full}{where_clause};
"""
        return sql

    def _generate_column_masking_sql(self, col_config: MaskingColumnConfig) -> str:
        """
        生成单个字段的脱敏SQL

        注：这是一个演示实现，展示了如何构建脱敏SQL
        实际生产环境中，应该使用 HashData Anon 插件的内置函数
        """
        column = col_config.column_name
        algorithm = col_config.algorithm.upper()
        params = col_config.params or {}

        if algorithm == "MASK":
            # 掩码脱敏：保留前3位和后4位，中间用*替换
            prefix = params.get("prefix_length", 3)
            suffix = params.get("suffix_length", 4)
            mask_char = params.get("mask_char", "*")
            return f"""
                CASE
                    WHEN LENGTH({column}::TEXT) <= {prefix + suffix}
                    THEN RPAD('{mask_char}', LENGTH({column}::TEXT), '{mask_char}')
                    ELSE CONCAT(
                        SUBSTRING({column}::TEXT FROM 1 FOR {prefix}),
                        RPAD('', GREATEST(LENGTH({column}::TEXT) - {prefix + suffix}, 0), '{mask_char}'),
                        SUBSTRING({column}::TEXT FROM LENGTH({column}::TEXT) - {suffix} + 1 FOR {suffix})
                    )
                END AS {column}
            """

        elif algorithm == "HASH":
            # 哈希脱敏：使用SHA256
            salt = params.get("salt", "")
            if salt:
                return f"encode(sha256(({column}::TEXT || '{salt}')::bytea), 'hex') AS {column}"
            return f"encode(sha256({column}::TEXT::bytea), 'hex') AS {column}"

        elif algorithm == "REPLACE":
            # 替换脱敏
            replacement = params.get("replacement", "***")
            return f"'{replacement}' AS {column}"

        elif algorithm == "NULL":
            # 空值脱敏
            return f"NULL AS {column}"

        elif algorithm == "ROUND":
            # 取整脱敏
            precision = params.get("precision", -3)
            if precision < 0:
                # 按10的倍数取整，如-3表示千位取整
                return f"ROUND({column} / {10 ** abs(precision)}) * {10 ** abs(precision)} AS {column}"
            return f"ROUND({column}, {precision}) AS {column}"

        elif algorithm == "OFFSET":
            # 偏移脱敏
            offset = params.get("offset", 0)
            min_val = params.get("min_value")
            max_val = params.get("max_value")

            if min_val is not None and max_val is not None:
                return f"GREATEST({min_val}, LEAST({max_val}, {column} + {offset})) AS {column}"
            return f"({column} + {offset}) AS {column}"

        elif algorithm == "PRESERVATION":
            # 格式保持脱敏（简单实现）
            return f"""
                CASE
                    WHEN {column} ~ '^[0-9]+$' THEN translate({column}::TEXT, '0123456789', '5678901234')
                    WHEN {column} ~ '^[a-zA-Z]+$' THEN translate({column}::TEXT,
                        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
                        'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm')
                    ELSE {column}
                END AS {column}
            """

        else:
            # 默认原样返回
            return f"{column} AS {column}"

    def generate_anon_plugin_sql(self, table_config: MaskingTableConfig, source_schema: str = "public", target_schema: str = "public") -> str:
        """
        生成使用 Anon 插件的脱敏SQL（推荐方式）

        这个方法展示了如何使用 Anon 插件的内置脱敏函数
        """
        source_table_full = f"{source_schema}.{table_config.source_table}"
        target_table_full = f"{target_schema}.{table_config.target_table}"

        sql_parts = [f"-- 使用 HashData Anon 插件进行脱敏", ""]

        # 1. 确保加载 Anon 插件
        sql_parts.append("-- 确保Anon插件已加载")
        sql_parts.append("CREATE EXTENSION IF NOT EXISTS anon;")
        sql_parts.append("")

        # 2. 创建目标表（如果不存在）
        sql_parts.append("-- 创建目标表结构")
        sql_parts.append(f"CREATE TABLE IF NOT EXISTS {target_table_full} (LIKE {source_table_full} INCLUDING ALL);")
        sql_parts.append("")

        # 3. 构建字段脱敏表达式
        update_clauses = []
        for col_config in table_config.columns:
            clause = self._generate_anon_column_sql(col_config)
            if clause:
                update_clauses.append(clause)

        if update_clauses:
            sql_parts.append("-- 执行脱敏更新")
            sql_parts.append(f"INSERT INTO {target_table_full}")
            sql_parts.append("SELECT")

            # 获取源表所有字段，对脱敏字段应用函数
            # 这里简化处理，实际需要先查询表结构
            select_clauses = []
            for col_config in table_config.columns:
                select_clauses.append(self._generate_anon_select_sql(col_config))

            sql_parts.append("    " + ",\n    ".join(select_clauses))
            sql_parts.append(f"FROM {source_table_full};")

        return "\n".join(sql_parts)

    def _generate_anon_column_sql(self, col_config: MaskingColumnConfig) -> Optional[str]:
        """生成Anon插件的字段脱敏SQL"""
        column = col_config.column_name
        algorithm = col_config.algorithm.upper()
        params = col_config.params or {}

        # Anon 插件常用函数:
        # anon.partial_email(text) - 邮箱脱敏
        # anon.partial_phone(text) - 手机号脱敏
        # anon.random_first_name() - 随机名
        # anon.random_last_name() - 随机姓
        # anon.random_string(integer) - 随机字符串
        # anon.random_date_between(date, date) - 随机日期
        # anon.digest(text, text) - 哈希

        if algorithm == "MASK":
            return f"{column} = anon.partial('{column}', 3, 4)"

        elif algorithm == "HASH":
            salt = params.get("salt", "")
            if salt:
                return f"{column} = encode(digest({column}::text || '{salt}', 'sha256'), 'hex')"
            return f"{column} = encode(digest({column}::text, 'sha256'), 'hex')"

        elif algorithm == "NULL":
            return f"{column} = NULL"

        return None

    def _generate_anon_select_sql(self, col_config: MaskingColumnConfig) -> str:
        """生成Anon插件的SELECT字段SQL"""
        column = col_config.column_name
        algorithm = col_config.algorithm.upper()
        params = col_config.params or {}

        if algorithm == "MASK":
            prefix = params.get("prefix_length", 3)
            suffix = params.get("suffix_length", 4)
            return f"anon.partial({column}::text, {prefix}, {suffix}) AS {column}"

        elif algorithm == "HASH":
            salt = params.get("salt", "")
            if salt:
                return f"encode(digest(({column}::text || '{salt}'), 'sha256'), 'hex') AS {column}"
            return f"encode(digest({column}::text, 'sha256'), 'hex') AS {column}"

        elif algorithm == "REPLACE":
            replacement = params.get("replacement", "***")
            return f"'{replacement}' AS {column}"

        elif algorithm == "NULL":
            return f"NULL AS {column}"

        elif algorithm == "ROUND":
            precision = params.get("precision", -3)
            if precision < 0:
                return f"round({column} / {10 ** abs(precision)}) * {10 ** abs(precision)} AS {column}"
            return f"round({column}, {precision}) AS {column}"

        elif algorithm == "OFFSET":
            offset = params.get("offset", 0)
            return f"({column} + {offset}) AS {column}"

        else:
            return f"{column} AS {column}"

    def execute_masking(self, table_config: MaskingTableConfig, datasource_config: Optional[Dict[str, Any]] = None, use_anon_plugin: bool = True) -> Dict[str, Any]:
        """
        执行脱敏任务

        Args:
            table_config: 表脱敏配置
            datasource_config: 数据源配置
            use_anon_plugin: 是否使用Anon插件

        Returns:
            执行结果
        """
        try:
            conn = self._get_connection(datasource_config)
            cursor = conn.cursor()

            # 生成SQL
            if use_anon_plugin:
                sql = self.generate_anon_plugin_sql(table_config)
            else:
                sql = self.generate_masking_sql(table_config)

            logger.info(f"执行脱敏SQL:\n{sql}")

            # 执行SQL
            cursor.execute(sql)
            conn.commit()

            # 获取影响行数
            rowcount = cursor.rowcount

            cursor.close()
            conn.close()

            return {
                "success": True,
                "rowcount": rowcount,
                "message": f"脱敏完成，处理 {rowcount} 条记录"
            }

        except Exception as e:
            logger.exception("执行脱敏失败")
            return {
                "success": False,
                "error": str(e),
                "message": f"脱敏失败: {str(e)}"
            }

    def get_algorithms(self) -> List[MaskingAlgorithm]:
        """获取所有可用的脱敏算法"""
        return PREDEFINED_ALGORITHMS

    def get_algorithm_by_code(self, code: str) -> Optional[MaskingAlgorithm]:
        """根据编码获取算法"""
        for algo in PREDEFINED_ALGORITHMS:
            if algo.code.upper() == code.upper():
                return algo
        return None


# 单例
_hashdata_anon_manager: Optional[HashDataAnonManager] = None


def get_hashdata_anon_manager(config: Optional[Dict[str, Any]] = None) -> HashDataAnonManager:
    """获取HashData Anon管理器单例"""
    global _hashdata_anon_manager
    if _hashdata_anon_manager is None:
        _hashdata_anon_manager = HashDataAnonManager(config)
    return _hashdata_anon_manager
