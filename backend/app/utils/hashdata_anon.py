"""
HashData Lightning + Anon 脱敏引擎集成
基于 HashData Lightning (MPP) 的 Anon 插件实现高性能数据脱敏
支持 PostgreSQL anon 扩展的所有脱敏函数
"""
import logging
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class MaskingAlgorithmCategory(Enum):
    """脱敏算法分类"""
    FAKE = "FAKE"  # 假数据生成
    RANDOM = "RANDOM"  # 随机值
    PARTIAL = "PARTIAL"  # 部分混淆
    PSEUDO = "PSEUDO"  # 假名化
    HASH = "HASH"  # 哈希
    NOISE = "NOISE"  # 噪声
    GENERALIZE = "GENERALIZE"  # 泛化
    CONDITIONAL = "CONDITIONAL"  # 条件脱敏


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
class AlgorithmParam:
    """算法参数定义"""
    name: str
    type: str  # int, float, text, date, array, bool
    description: str
    required: bool = False
    default: Any = None


@dataclass
class MaskingAlgorithm:
    """脱敏算法定义"""
    code: str
    name: str
    description: str
    category: str
    params: List[AlgorithmParam] = field(default_factory=list)
    return_type: str = "text"


# 完整的 ANON 脱敏算法定义
PREDEFINED_ALGORITHMS = [
    # ==================== 假数据生成 ====================
    MaskingAlgorithm(
        code="anon.fake_address",
        name="假地址",
        description="生成完整的假地址",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.fake_city",
        name="假城市",
        description="生成假城市名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.fake_country",
        name="假国家",
        description="生成假国家名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.fake_company",
        name="假公司",
        description="生成假公司名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.fake_email",
        name="假邮箱",
        description="生成有效的假邮箱地址",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.fake_first_name",
        name="假名",
        description="生成假名字",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.fake_last_name",
        name="假姓",
        description="生成假姓氏",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.fake_iban",
        name="假IBAN",
        description="生成有效的假IBAN",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.fake_postcode",
        name="假邮编",
        description="生成假邮编",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.fake_siret",
        name="假SIRET",
        description="生成有效的假SIRET",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_phone_number",
        name="假电话号码",
        description="生成假电话号码",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_credit_card_number",
        name="假信用卡号",
        description="生成假信用卡号",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_ip",
        name="假IP地址",
        description="生成假IP地址",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_ipv4",
        name="假IPv4地址",
        description="生成假IPv4地址",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_ipv6",
        name="假IPv6地址",
        description="生成假IPv6地址",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_mac_address",
        name="假MAC地址",
        description="生成假MAC地址",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_username",
        name="假用户名",
        description="生成假用户名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_uuidv4",
        name="假UUID",
        description="生成假UUID v4",
        category="FAKE",
        return_type="uuid"
    ),
    MaskingAlgorithm(
        code="anon.dummy_latitude",
        name="假纬度",
        description="生成假纬度坐标",
        category="FAKE",
        return_type="float"
    ),
    MaskingAlgorithm(
        code="anon.dummy_longitude",
        name="假经度",
        description="生成假经度坐标",
        category="FAKE",
        return_type="float"
    ),
    MaskingAlgorithm(
        code="anon.dummy_name",
        name="假姓名",
        description="生成假完整姓名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_city_name",
        name="假城市名",
        description="生成假城市名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_street_name",
        name="假街道名",
        description="生成假街道名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_company_name",
        name="假公司名",
        description="生成假公司名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_color",
        name="假颜色",
        description="生成假颜色名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_profession",
        name="假职业",
        description="生成假职业名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_state_name",
        name="假省份",
        description="生成假省份名",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_country_code",
        name="假国家代码",
        description="生成假国家代码",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_currency_code",
        name="假货币代码",
        description="生成假货币代码",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_isbn",
        name="假ISBN",
        description="生成假ISBN",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_timezone",
        name="假时区",
        description="生成假时区",
        category="FAKE",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.dummy_bic",
        name="假BIC",
        description="生成假BIC代码",
        category="FAKE",
        return_type="text"
    ),

    # ==================== 随机值 ====================
    MaskingAlgorithm(
        code="anon.random_string",
        name="随机字符串",
        description="生成指定长度的随机字符串",
        category="RANDOM",
        params=[
            AlgorithmParam(name="length", type="int", description="字符串长度", default=10)
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.random_int_between",
        name="随机整数",
        description="生成指定范围内的随机整数",
        category="RANDOM",
        params=[
            AlgorithmParam(name="min", type="int", description="最小值", required=True),
            AlgorithmParam(name="max", type="int", description="最大值", required=True)
        ],
        return_type="int"
    ),
    MaskingAlgorithm(
        code="anon.random_bigint_between",
        name="随机大整数",
        description="生成指定范围内的随机大整数",
        category="RANDOM",
        params=[
            AlgorithmParam(name="min", type="bigint", description="最小值", required=True),
            AlgorithmParam(name="max", type="bigint", description="最大值", required=True)
        ],
        return_type="bigint"
    ),
    MaskingAlgorithm(
        code="anon.random_date",
        name="随机日期",
        description="生成随机日期",
        category="RANDOM",
        return_type="date"
    ),
    MaskingAlgorithm(
        code="anon.random_date_between",
        name="随机日期范围",
        description="生成指定范围内的随机日期",
        category="RANDOM",
        params=[
            AlgorithmParam(name="start_date", type="date", description="开始日期", required=True),
            AlgorithmParam(name="end_date", type="date", description="结束日期", required=True)
        ],
        return_type="date"
    ),
    MaskingAlgorithm(
        code="anon.random_zip",
        name="随机邮编",
        description="生成5位随机邮编",
        category="RANDOM",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.random_phone",
        name="随机电话",
        description="生成随机电话号码",
        category="RANDOM",
        params=[
            AlgorithmParam(name="prefix", type="text", description="电话前缀", default="01")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.random_id",
        name="随机ID",
        description="生成随机唯一BIGINT值",
        category="RANDOM",
        return_type="bigint"
    ),
    MaskingAlgorithm(
        code="anon.random_id_int",
        name="随机INT ID",
        description="生成随机唯一INT值",
        category="RANDOM",
        return_type="int"
    ),
    MaskingAlgorithm(
        code="anon.random_in",
        name="随机选择",
        description="从数组中随机选择一个值",
        category="RANDOM",
        params=[
            AlgorithmParam(name="values", type="array", description="候选值数组(逗号分隔)", required=True)
        ],
        return_type="any"
    ),
    MaskingAlgorithm(
        code="anon.random_hash",
        name="随机哈希",
        description="生成随机哈希值",
        category="RANDOM",
        params=[
            AlgorithmParam(name="seed", type="text", description="种子值", required=True)
        ],
        return_type="text"
    ),

    # ==================== 部分混淆 ====================
    MaskingAlgorithm(
        code="anon.partial",
        name="部分替换",
        description="保留部分字符，其余用指定字符替换",
        category="PARTIAL",
        params=[
            AlgorithmParam(name="prefix_len", type="int", description="保留前缀长度", default=2),
            AlgorithmParam(name="mask_char", type="text", description="掩码字符", default="*"),
            AlgorithmParam(name="suffix_len", type="int", description="保留后缀长度", default=2)
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.partial_email",
        name="部分邮箱",
        description="部分混淆邮箱地址",
        category="PARTIAL",
        return_type="text"
    ),

    # ==================== 假名化 ====================
    MaskingAlgorithm(
        code="anon.pseudo_first_name",
        name="假名化名字",
        description="生成确定性的假名字(相同输入产生相同输出)",
        category="PSEUDO",
        params=[
            AlgorithmParam(name="seed", type="text", description="种子值(通常为原字段名)", required=True),
            AlgorithmParam(name="salt", type="text", description="盐值", default="")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.pseudo_last_name",
        name="假名化姓氏",
        description="生成确定性的假姓氏",
        category="PSEUDO",
        params=[
            AlgorithmParam(name="seed", type="text", description="种子值", required=True),
            AlgorithmParam(name="salt", type="text", description="盐值", default="")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.pseudo_email",
        name="假名化邮箱",
        description="生成确定性的假邮箱",
        category="PSEUDO",
        params=[
            AlgorithmParam(name="seed", type="text", description="种子值", required=True),
            AlgorithmParam(name="salt", type="text", description="盐值", default="")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.pseudo_city",
        name="假名化城市",
        description="生成确定性的假城市",
        category="PSEUDO",
        params=[
            AlgorithmParam(name="seed", type="text", description="种子值", required=True),
            AlgorithmParam(name="salt", type="text", description="盐值", default="")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.pseudo_company",
        name="假名化公司",
        description="生成确定性的假公司名",
        category="PSEUDO",
        params=[
            AlgorithmParam(name="seed", type="text", description="种子值", required=True),
            AlgorithmParam(name="salt", type="text", description="盐值", default="")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.pseudo_iban",
        name="假名化IBAN",
        description="生成确定性的假IBAN",
        category="PSEUDO",
        params=[
            AlgorithmParam(name="seed", type="text", description="种子值", required=True),
            AlgorithmParam(name="salt", type="text", description="盐值", default="")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.pseudo_siret",
        name="假名化SIRET",
        description="生成确定性的假SIRET",
        category="PSEUDO",
        params=[
            AlgorithmParam(name="seed", type="text", description="种子值", required=True),
            AlgorithmParam(name="salt", type="text", description="盐值", default="")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.pseudo_country",
        name="假名化国家",
        description="生成确定性的假国家",
        category="PSEUDO",
        params=[
            AlgorithmParam(name="seed", type="text", description="种子值", required=True),
            AlgorithmParam(name="salt", type="text", description="盐值", default="")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.pseudo_shift",
        name="ID位移",
        description="对ID进行位移处理",
        category="PSEUDO",
        return_type="bigint"
    ),
    MaskingAlgorithm(
        code="anon.pseudo_xor",
        name="ID异或",
        description="对ID进行异或处理",
        category="PSEUDO",
        return_type="bigint"
    ),

    # ==================== 哈希 ====================
    MaskingAlgorithm(
        code="anon.hash",
        name="哈希",
        description="使用预设盐值和算法进行哈希",
        category="HASH",
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.digest",
        name="自定义哈希",
        description="使用自定义盐值和算法进行哈希",
        category="HASH",
        params=[
            AlgorithmParam(name="salt", type="text", description="盐值", required=True),
            AlgorithmParam(name="algorithm", type="text", description="算法(md5,sha1,sha256)", default="sha256")
        ],
        return_type="text"
    ),

    # ==================== 噪声 ====================
    MaskingAlgorithm(
        code="anon.noise",
        name="数值噪声",
        description="对数值添加随机偏移",
        category="NOISE",
        params=[
            AlgorithmParam(name="ratio", type="float", description="偏移比例(如0.33表示±33%)", default=0.1)
        ],
        return_type="numeric"
    ),
    MaskingAlgorithm(
        code="anon.dnoise",
        name="日期噪声",
        description="对日期/时间添加随机偏移",
        category="NOISE",
        params=[
            AlgorithmParam(name="interval", type="text", description="最大偏移间隔(如'30 days')", default="30 days")
        ],
        return_type="date"
    ),

    # ==================== 泛化 ====================
    MaskingAlgorithm(
        code="anon.generalize_int4range",
        name="整数泛化",
        description="将整数泛化为范围",
        category="GENERALIZE",
        params=[
            AlgorithmParam(name="step", type="int", description="泛化步长", default=10)
        ],
        return_type="int4range"
    ),
    MaskingAlgorithm(
        code="anon.generalize_int8range",
        name="大整数泛化",
        description="将bigint泛化为范围",
        category="GENERALIZE",
        params=[
            AlgorithmParam(name="step", type="bigint", description="泛化步长", default=100)
        ],
        return_type="int8range"
    ),
    MaskingAlgorithm(
        code="anon.generalize_numrange",
        name="数值泛化",
        description="将numeric泛化为范围",
        category="GENERALIZE",
        params=[
            AlgorithmParam(name="step", type="float", description="泛化步长", default=10.0)
        ],
        return_type="numrange"
    ),
    MaskingAlgorithm(
        code="anon.generalize_tsrange",
        name="时间泛化",
        description="将时间戳泛化为范围",
        category="GENERALIZE",
        params=[
            AlgorithmParam(name="step", type="text", description="泛化单位(year,decade,century)", default="decade")
        ],
        return_type="tsrange"
    ),

    # ==================== 条件脱敏 ====================
    MaskingAlgorithm(
        code="anon.ternary",
        name="条件脱敏",
        description="基于条件进行脱敏",
        category="CONDITIONAL",
        params=[
            AlgorithmParam(name="condition", type="text", description="条件表达式", required=True),
            AlgorithmParam(name="true_value", type="text", description="条件为真时的值", required=True),
            AlgorithmParam(name="false_value", type="text", description="条件为假时的值", required=True)
        ],
        return_type="any"
    ),

    # ==================== 其他 ====================
    MaskingAlgorithm(
        code="anon.lorem_ipsum",
        name="Lorem Ipsum",
        description="生成Lorem Ipsum文本",
        category="FAKE",
        params=[
            AlgorithmParam(name="type", type="text", description="类型(paragraphs,words,characters)", default="words"),
            AlgorithmParam(name="count", type="int", description="数量", default=10)
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="anon.image_blur",
        name="图像模糊",
        description="对图像数据应用模糊效果",
        category="PARTIAL",
        params=[
            AlgorithmParam(name="sigma", type="float", description="模糊程度", default=5.0)
        ],
        return_type="bytea"
    ),

    # ==================== 简化版算法（兼容旧版） ====================
    MaskingAlgorithm(
        code="MASK",
        name="掩码脱敏",
        description="保留部分信息，其他用掩码替换",
        category="PARTIAL",
        params=[
            AlgorithmParam(name="prefix_length", type="int", description="前缀保留长度", default=3),
            AlgorithmParam(name="suffix_length", type="int", description="后缀保留长度", default=4),
            AlgorithmParam(name="mask_char", type="text", description="掩码字符", default="*")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="HASH",
        name="哈希脱敏",
        description="使用SHA-256哈希算法不可逆脱敏",
        category="HASH",
        params=[
            AlgorithmParam(name="salt", type="text", description="盐值", default="")
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="REPLACE",
        name="替换脱敏",
        description="使用固定值替换",
        category="PARTIAL",
        params=[
            AlgorithmParam(name="replacement", type="text", description="替换值", required=True)
        ],
        return_type="text"
    ),
    MaskingAlgorithm(
        code="NULL",
        name="空值脱敏",
        description="将字段置为NULL",
        category="PARTIAL",
        return_type="any"
    ),
    MaskingAlgorithm(
        code="ROUND",
        name="取整脱敏",
        description="数值取整",
        category="NOISE",
        params=[
            AlgorithmParam(name="precision", type="int", description="精度，负数表示10的倍数取整", default=-3)
        ],
        return_type="numeric"
    ),
    MaskingAlgorithm(
        code="OFFSET",
        name="偏移脱敏",
        description="数值固定偏移",
        category="NOISE",
        params=[
            AlgorithmParam(name="offset", type="float", description="偏移量", default=0),
            AlgorithmParam(name="min_value", type="float", description="最小值"),
            AlgorithmParam(name="max_value", type="float", description="最大值")
        ],
        return_type="numeric"
    ),
]


class HashDataAnonManager:
    """HashData Anon 脱敏引擎管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.connection = None

    def _get_connection_config(self, datasource_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        config = datasource_config or self.config
        return {
            "host": config.get("host", "localhost"),
            "port": config.get("port", 5432),
            "database": config.get("database", "hashdata"),
            "user": config.get("username", "gpadmin"),
            "password": config.get("password", ""),
        }

    def _get_connection(self, datasource_config: Optional[Dict[str, Any]] = None):
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
        """检查 Anon 插件是否安装"""
        try:
            conn = self._get_connection(datasource_config)
            cursor = conn.cursor()
            cursor.execute("SELECT extname, extversion FROM pg_extension WHERE extname = 'anon';")
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                return True, f"Anon插件已安装 (版本: {result[1]})"
            return False, "Anon插件未安装，请先安装：CREATE EXTENSION anon;"
        except Exception as e:
            logger.exception("检查Anon插件失败")
            return False, f"检查失败: {str(e)}"

    def get_algorithms(self) -> List[MaskingAlgorithm]:
        """获取所有可用的脱敏算法"""
        return PREDEFINED_ALGORITHMS

    def get_algorithm_by_code(self, code: str) -> Optional[MaskingAlgorithm]:
        """根据编码获取算法"""
        for algo in PREDEFINED_ALGORITHMS:
            if algo.code.lower() == code.lower():
                return algo
        return None

    def get_algorithms_by_category(self, category: str) -> List[MaskingAlgorithm]:
        """根据分类获取算法"""
        return [algo for algo in PREDEFINED_ALGORITHMS if algo.category == category]

    def _generate_anon_function_call(self, col_config: MaskingColumnConfig) -> str:
        """
        生成 ANON 函数调用 SQL

        Args:
            col_config: 字段脱敏配置

        Returns:
            函数调用 SQL 字符串
        """
        column = col_config.column_name
        algorithm = col_config.algorithm
        params = col_config.params or {}

        # 获取算法定义
        algo_def = self.get_algorithm_by_code(algorithm)

        # 如果是简化版算法，使用内部实现
        if algorithm.upper() in ["MASK", "HASH", "REPLACE", "NULL", "ROUND", "OFFSET"]:
            return self._generate_simple_masking_sql(column, algorithm.upper(), params)

        # 构建 ANON 函数调用
        func_name = algorithm  # 如 anon.fake_email, anon.partial 等

        # 处理参数
        param_values = []
        if algo_def:
            for param_def in algo_def.params:
                param_name = param_def.name
                if param_name in params:
                    value = params[param_name]
                    # 根据类型格式化值
                    if param_def.type in ["int", "bigint", "float"]:
                        param_values.append(str(value))
                    elif param_def.type == "text":
                        param_values.append(f"'{value}'")
                    elif param_def.type == "array":
                        # 数组类型，格式化为 PostgreSQL 数组
                        if isinstance(value, str):
                            items = [f"'{v.strip()}'" for v in value.split(",")]
                        else:
                            items = [f"'{v}'" for v in value]
                        param_values.append(f"ARRAY[{', '.join(items)}]")
                    else:
                        param_values.append(f"'{value}'")
                elif param_def.default is not None:
                    if param_def.type in ["int", "bigint", "float"]:
                        param_values.append(str(param_def.default))
                    else:
                        param_values.append(f"'{param_def.default}'")

        if param_values:
            return f"{func_name}({', '.join(param_values)})"
        else:
            return f"{func_name}()"

    def _generate_simple_masking_sql(self, column: str, algorithm: str, params: Dict[str, Any]) -> str:
        """生成简化版脱敏 SQL"""
        if algorithm == "MASK":
            prefix_len = params.get("prefix_length", 3)
            suffix_len = params.get("suffix_length", 4)
            mask_char = params.get("mask_char", "*")
            return f"anon.partial({column}::text, {prefix_len}, '{mask_char}', {suffix_len})"

        elif algorithm == "HASH":
            salt = params.get("salt", "")
            if salt:
                return f"anon.digest({column}::text, '{salt}', 'sha256')"
            return f"anon.hash({column}::text)"

        elif algorithm == "REPLACE":
            replacement = params.get("replacement", "***")
            return f"'{replacement}'"

        elif algorithm == "NULL":
            return "NULL"

        elif algorithm == "ROUND":
            precision = params.get("precision", -3)
            if precision < 0:
                factor = 10 ** abs(precision)
                return f"round({column} / {factor}) * {factor}"
            return f"round({column}, {precision})"

        elif algorithm == "OFFSET":
            offset = params.get("offset", 0)
            min_val = params.get("min_value")
            max_val = params.get("max_value")

            if min_val is not None and max_val is not None:
                return f"greatest({min_val}, least({max_val}, {column} + {offset}))"
            return f"({column} + {offset})"

        return f"{column}"

    def generate_masking_sql(
        self,
        table_config: MaskingTableConfig,
        source_schema: str = "public",
        target_schema: str = "public",
        include_unmasked_columns: bool = True
    ) -> str:
        """
        生成完整的脱敏 SQL 语句

        Args:
            table_config: 表脱敏配置
            source_schema: 源 Schema
            target_schema: 目标 Schema
            include_unmasked_columns: 是否包含未配置脱敏的字段

        Returns:
            完整的脱敏 SQL 语句
        """
        source_table_full = f"{source_schema}.{table_config.source_table}"
        target_table_full = f"{target_schema}.{table_config.target_table}"

        # 构建脱敏字段映射
        masked_columns = {}
        for col_config in table_config.columns:
            masked_columns[col_config.column_name] = self._generate_anon_function_call(col_config)

        # 生成 SQL
        sql_parts = [
            "-- ========================================",
            f"-- 数据脱敏任务: {table_config.source_table} -> {table_config.target_table}",
            "-- 生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "-- ========================================",
            "",
            "-- 确保Anon插件已加载",
            "CREATE EXTENSION IF NOT EXISTS anon;",
            "",
        ]

        # 获取源表所有字段
        if include_unmasked_columns:
            sql_parts.extend([
                "-- 创建目标表（复制源表结构）",
                f"DROP TABLE IF EXISTS {target_table_full};",
                f"CREATE TABLE {target_table_full} (LIKE {source_table_full} INCLUDING ALL);",
                "",
                "-- 插入脱敏后的数据",
                f"INSERT INTO {target_table_full}",
                f"SELECT * FROM {source_table_full};",
                "",
            ])

            # 更新脱敏字段
            if masked_columns:
                sql_parts.append("-- 更新脱敏字段")
                for col_name, masking_expr in masked_columns.items():
                    sql_parts.append(f"UPDATE {target_table_full} SET {col_name} = {masking_expr};")
        else:
            # 只选择配置的字段
            select_parts = []
            for col_config in table_config.columns:
                masking_expr = self._generate_anon_function_call(col_config)
                select_parts.append(f"    {masking_expr} AS {col_config.column_name}")

            where_clause = f" WHERE {table_config.where_condition}" if table_config.where_condition else ""

            sql_parts.extend([
                "-- 创建目标表并插入脱敏数据",
                f"DROP TABLE IF EXISTS {target_table_full};",
                f"CREATE TABLE {target_table_full} AS",
                "SELECT",
                ",\n".join(select_parts),
                f"FROM {source_table_full}{where_clause};",
            ])

        sql_parts.append("")
        sql_parts.append("-- 脱敏完成")
        sql_parts.append(f"-- 处理表: {source_table_full} -> {target_table_full}")

        return "\n".join(sql_parts)

    def execute_masking(
        self,
        table_config: MaskingTableConfig,
        datasource_config: Optional[Dict[str, Any]] = None,
        source_schema: str = "public",
        target_schema: str = "public"
    ) -> Dict[str, Any]:
        """
        执行脱敏任务

        Args:
            table_config: 表脱敏配置
            datasource_config: 数据源配置
            source_schema: 源 Schema
            target_schema: 目标 Schema

        Returns:
            执行结果
        """
        from datetime import datetime

        try:
            # 生成 SQL
            sql = self.generate_masking_sql(
                table_config,
                source_schema,
                target_schema,
                include_unmasked_columns=True
            )

            logger.info(f"执行脱敏SQL:\n{sql}")

            # 获取连接
            conn = self._get_connection(datasource_config)
            cursor = conn.cursor()

            # 执行 SQL（分条执行）
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement and not statement.startswith("--"):
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        logger.warning(f"SQL执行警告: {e}")
                        conn.rollback()
                        cursor = conn.cursor()

            conn.commit()

            # 获取处理行数
            cursor.execute(f"SELECT count(*) FROM {target_schema}.{table_config.target_table}")
            rowcount = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return {
                "success": True,
                "rowcount": rowcount,
                "message": f"脱敏完成，处理 {rowcount} 条记录",
                "sql": sql
            }

        except Exception as e:
            logger.exception("执行脱敏失败")
            return {
                "success": False,
                "error": str(e),
                "message": f"脱敏失败: {str(e)}"
            }

    def preview_masking(
        self,
        table_config: MaskingTableConfig,
        datasource_config: Optional[Dict[str, Any]] = None,
        source_schema: str = "public",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        预览脱敏结果

        Args:
            table_config: 表脱敏配置
            datasource_config: 数据源配置
            source_schema: 源 Schema
            limit: 预览行数

        Returns:
            预览结果
        """
        try:
            source_table_full = f"{source_schema}.{table_config.source_table}"

            # 构建预览 SQL
            select_parts = []
            for col_config in table_config.columns:
                masking_expr = self._generate_anon_function_call(col_config)
                select_parts.append(f"{masking_expr} AS {col_config.column_name}")

            sql = f"""
            SELECT {', '.join(select_parts)}
            FROM {source_table_full}
            LIMIT {limit};
            """

            conn = self._get_connection(datasource_config)
            cursor = conn.cursor()
            cursor.execute(sql)

            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()

            cursor.close()
            conn.close()

            return {
                "success": True,
                "columns": columns,
                "rows": [list(row) for row in rows],
                "sql": sql
            }

        except Exception as e:
            logger.exception("预览脱敏失败")
            return {
                "success": False,
                "error": str(e),
                "message": f"预览失败: {str(e)}"
            }


# 单例
_hashdata_anon_manager: Optional[HashDataAnonManager] = None


def get_hashdata_anon_manager(config: Optional[Dict[str, Any]] = None) -> HashDataAnonManager:
    """获取HashData Anon管理器单例"""
    global _hashdata_anon_manager
    if _hashdata_anon_manager is None:
        _hashdata_anon_manager = HashDataAnonManager(config)
    return _hashdata_anon_manager


# 为了兼容性，提供算法定义导出
def get_all_algorithms() -> List[Dict[str, Any]]:
    """获取所有算法的字典列表（用于API返回）"""
    result = []
    for algo in PREDEFINED_ALGORITHMS:
        algo_dict = {
            "code": algo.code,
            "name": algo.name,
            "description": algo.description,
            "category": algo.category,
            "returnType": algo.return_type,
            "params": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default
                }
                for p in algo.params
            ]
        }
        result.append(algo_dict)
    return result


def get_algorithm_categories() -> List[Dict[str, str]]:
    """获取算法分类列表"""
    return [
        {"code": "FAKE", "name": "假数据生成", "description": "生成逼真的假数据"},
        {"code": "RANDOM", "name": "随机值", "description": "生成随机数据"},
        {"code": "PARTIAL", "name": "部分混淆", "description": "保留部分信息"},
        {"code": "PSEUDO", "name": "假名化", "description": "确定性假名替换"},
        {"code": "HASH", "name": "哈希", "description": "单向哈希转换"},
        {"code": "NOISE", "name": "噪声", "description": "添加随机噪声"},
        {"code": "GENERALIZE", "name": "泛化", "description": "将精确值泛化为范围"},
        {"code": "CONDITIONAL", "name": "条件脱敏", "description": "基于条件进行脱敏"},
    ]
