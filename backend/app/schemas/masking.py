"""
数据脱敏相关Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, AliasChoices
from datetime import datetime
from app.schemas.common import TimestampMixin


# 脱敏算法定义 - 基于 PostgreSQL anon 扩展
# 算法分类
MASKING_ALGORITHM_CATEGORIES = [
    {"code": "FAKE", "name": "假数据生成", "description": "生成逼真的假数据"},
    {"code": "RANDOM", "name": "随机值", "description": "生成随机数据"},
    {"code": "PARTIAL", "name": "部分混淆", "description": "保留部分信息"},
    {"code": "PSEUDO", "name": "假名化", "description": "确定性假名替换"},
    {"code": "HASH", "name": "哈希", "description": "单向哈希转换"},
    {"code": "NOISE", "name": "噪声", "description": "添加随机噪声"},
    {"code": "GENERALIZE", "name": "泛化", "description": "将精确值泛化为范围"},
    {"code": "CONDITIONAL", "name": "条件脱敏", "description": "基于条件进行脱敏"},
]

# 完整的脱敏算法定义
MASKING_ALGORITHMS = [
    # ==================== 假数据生成 ====================
    {
        "code": "anon.fake_address",
        "name": "假地址",
        "category": "FAKE",
        "description": "生成完整的假地址",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.fake_city",
        "name": "假城市",
        "category": "FAKE",
        "description": "生成假城市名",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.fake_country",
        "name": "假国家",
        "category": "FAKE",
        "description": "生成假国家名",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.fake_company",
        "name": "假公司",
        "category": "FAKE",
        "description": "生成假公司名",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.fake_email",
        "name": "假邮箱",
        "category": "FAKE",
        "description": "生成有效的假邮箱地址",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.fake_first_name",
        "name": "假名",
        "category": "FAKE",
        "description": "生成假名字",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.fake_last_name",
        "name": "假姓",
        "category": "FAKE",
        "description": "生成假姓氏",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.fake_iban",
        "name": "假IBAN",
        "category": "FAKE",
        "description": "生成有效的假IBAN",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.fake_postcode",
        "name": "假邮编",
        "category": "FAKE",
        "description": "生成假邮编",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.fake_siret",
        "name": "假SIRET",
        "category": "FAKE",
        "description": "生成有效的假SIRET",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.dummy_phone_number",
        "name": "假电话号码",
        "category": "FAKE",
        "description": "生成假电话号码",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.dummy_credit_card_number",
        "name": "假信用卡号",
        "category": "FAKE",
        "description": "生成假信用卡号",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.dummy_ip",
        "name": "假IP地址",
        "category": "FAKE",
        "description": "生成假IP地址",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.dummy_mac_address",
        "name": "假MAC地址",
        "category": "FAKE",
        "description": "生成假MAC地址",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.dummy_username",
        "name": "假用户名",
        "category": "FAKE",
        "description": "生成假用户名",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.dummy_uuidv4",
        "name": "假UUID",
        "category": "FAKE",
        "description": "生成假UUID v4",
        "params": [],
        "return_type": "uuid"
    },
    {
        "code": "anon.dummy_latitude",
        "name": "假纬度",
        "category": "FAKE",
        "description": "生成假纬度坐标",
        "params": [],
        "return_type": "float"
    },
    {
        "code": "anon.dummy_longitude",
        "name": "假经度",
        "category": "FAKE",
        "description": "生成假经度坐标",
        "params": [],
        "return_type": "float"
    },

    # ==================== 随机值 ====================
    {
        "code": "anon.random_string",
        "name": "随机字符串",
        "category": "RANDOM",
        "description": "生成指定长度的随机字符串",
        "params": [
            {"name": "length", "type": "int", "default": 10, "description": "字符串长度"}
        ],
        "return_type": "text"
    },
    {
        "code": "anon.random_int_between",
        "name": "随机整数",
        "category": "RANDOM",
        "description": "生成指定范围内的随机整数",
        "params": [
            {"name": "min", "type": "int", "required": True, "description": "最小值"},
            {"name": "max", "type": "int", "required": True, "description": "最大值"}
        ],
        "return_type": "int"
    },
    {
        "code": "anon.random_bigint_between",
        "name": "随机大整数",
        "category": "RANDOM",
        "description": "生成指定范围内的随机大整数",
        "params": [
            {"name": "min", "type": "bigint", "required": True, "description": "最小值"},
            {"name": "max", "type": "bigint", "required": True, "description": "最大值"}
        ],
        "return_type": "bigint"
    },
    {
        "code": "anon.random_date",
        "name": "随机日期",
        "category": "RANDOM",
        "description": "生成随机日期",
        "params": [],
        "return_type": "date"
    },
    {
        "code": "anon.random_date_between",
        "name": "随机日期范围",
        "category": "RANDOM",
        "description": "生成指定范围内的随机日期",
        "params": [
            {"name": "start_date", "type": "date", "required": True, "description": "开始日期"},
            {"name": "end_date", "type": "date", "required": True, "description": "结束日期"}
        ],
        "return_type": "date"
    },
    {
        "code": "anon.random_zip",
        "name": "随机邮编",
        "category": "RANDOM",
        "description": "生成5位随机邮编",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.random_phone",
        "name": "随机电话",
        "category": "RANDOM",
        "description": "生成随机电话号码",
        "params": [
            {"name": "prefix", "type": "text", "default": "01", "description": "电话前缀"}
        ],
        "return_type": "text"
    },
    {
        "code": "anon.random_id",
        "name": "随机ID",
        "category": "RANDOM",
        "description": "生成随机唯一BIGINT值",
        "params": [],
        "return_type": "bigint"
    },
    {
        "code": "anon.random_in",
        "name": "随机选择",
        "category": "RANDOM",
        "description": "从数组中随机选择一个值",
        "params": [
            {"name": "values", "type": "array", "required": True, "description": "候选值数组"}
        ],
        "return_type": "any"
    },

    # ==================== 部分混淆 ====================
    {
        "code": "anon.partial",
        "name": "部分替换",
        "category": "PARTIAL",
        "description": "保留部分字符，其余用指定字符替换",
        "params": [
            {"name": "prefix_len", "type": "int", "default": 2, "description": "保留前缀长度"},
            {"name": "mask_char", "type": "text", "default": "*", "description": "掩码字符"},
            {"name": "suffix_len", "type": "int", "default": 2, "description": "保留后缀长度"}
        ],
        "return_type": "text"
    },
    {
        "code": "anon.partial_email",
        "name": "部分邮箱",
        "category": "PARTIAL",
        "description": "部分混淆邮箱地址",
        "params": [],
        "return_type": "text"
    },

    # ==================== 假名化 ====================
    {
        "code": "anon.pseudo_first_name",
        "name": "假名化名字",
        "category": "PSEUDO",
        "description": "生成确定性的假名字(相同输入产生相同输出)",
        "params": [
            {"name": "seed", "type": "text", "required": True, "description": "种子值"},
            {"name": "salt", "type": "text", "default": "", "description": "盐值"}
        ],
        "return_type": "text"
    },
    {
        "code": "anon.pseudo_last_name",
        "name": "假名化姓氏",
        "category": "PSEUDO",
        "description": "生成确定性的假姓氏",
        "params": [
            {"name": "seed", "type": "text", "required": True, "description": "种子值"},
            {"name": "salt", "type": "text", "default": "", "description": "盐值"}
        ],
        "return_type": "text"
    },
    {
        "code": "anon.pseudo_email",
        "name": "假名化邮箱",
        "category": "PSEUDO",
        "description": "生成确定性的假邮箱",
        "params": [
            {"name": "seed", "type": "text", "required": True, "description": "种子值"},
            {"name": "salt", "type": "text", "default": "", "description": "盐值"}
        ],
        "return_type": "text"
    },
    {
        "code": "anon.pseudo_city",
        "name": "假名化城市",
        "category": "PSEUDO",
        "description": "生成确定性的假城市",
        "params": [
            {"name": "seed", "type": "text", "required": True, "description": "种子值"},
            {"name": "salt", "type": "text", "default": "", "description": "盐值"}
        ],
        "return_type": "text"
    },
    {
        "code": "anon.pseudo_company",
        "name": "假名化公司",
        "category": "PSEUDO",
        "description": "生成确定性的假公司名",
        "params": [
            {"name": "seed", "type": "text", "required": True, "description": "种子值"},
            {"name": "salt", "type": "text", "default": "", "description": "盐值"}
        ],
        "return_type": "text"
    },
    {
        "code": "anon.pseudo_iban",
        "name": "假名化IBAN",
        "category": "PSEUDO",
        "description": "生成确定性的假IBAN",
        "params": [
            {"name": "seed", "type": "text", "required": True, "description": "种子值"},
            {"name": "salt", "type": "text", "default": "", "description": "盐值"}
        ],
        "return_type": "text"
    },
    {
        "code": "anon.pseudo_shift",
        "name": "ID位移",
        "category": "PSEUDO",
        "description": "对ID进行位移处理",
        "params": [],
        "return_type": "bigint"
    },

    # ==================== 哈希 ====================
    {
        "code": "anon.hash",
        "name": "哈希",
        "category": "HASH",
        "description": "使用预设盐值和算法进行哈希",
        "params": [],
        "return_type": "text"
    },
    {
        "code": "anon.digest",
        "name": "自定义哈希",
        "category": "HASH",
        "description": "使用自定义盐值和算法进行哈希",
        "params": [
            {"name": "salt", "type": "text", "required": True, "description": "盐值"},
            {"name": "algorithm", "type": "text", "default": "sha256", "description": "算法(md5,sha1,sha256)"}
        ],
        "return_type": "text"
    },

    # ==================== 噪声 ====================
    {
        "code": "anon.noise",
        "name": "数值噪声",
        "category": "NOISE",
        "description": "对数值添加随机偏移",
        "params": [
            {"name": "ratio", "type": "float", "default": 0.1, "description": "偏移比例(如0.33表示±33%)"}
        ],
        "return_type": "numeric"
    },
    {
        "code": "anon.dnoise",
        "name": "日期噪声",
        "category": "NOISE",
        "description": "对日期/时间添加随机偏移",
        "params": [
            {"name": "interval", "type": "interval", "default": "30 days", "description": "最大偏移间隔"}
        ],
        "return_type": "date"
    },

    # ==================== 泛化 ====================
    {
        "code": "anon.generalize_int4range",
        "name": "整数泛化",
        "category": "GENERALIZE",
        "description": "将整数泛化为范围",
        "params": [
            {"name": "step", "type": "int", "default": 10, "description": "泛化步长"}
        ],
        "return_type": "int4range"
    },
    {
        "code": "anon.generalize_tsrange",
        "name": "时间泛化",
        "category": "GENERALIZE",
        "description": "将时间戳泛化为范围",
        "params": [
            {"name": "step", "type": "text", "default": "decade", "description": "泛化单位(year,decade,century)"}
        ],
        "return_type": "tsrange"
    },

    # ==================== 条件脱敏 ====================
    {
        "code": "anon.ternary",
        "name": "条件脱敏",
        "category": "CONDITIONAL",
        "description": "基于条件进行脱敏",
        "params": [
            {"name": "condition", "type": "bool", "required": True, "description": "条件表达式"},
            {"name": "true_value", "type": "any", "required": True, "description": "条件为真时的值"},
            {"name": "false_value", "type": "any", "required": True, "description": "条件为假时的值"}
        ],
        "return_type": "any"
    },

    # ==================== 其他 ====================
    {
        "code": "anon.lorem_ipsum",
        "name": "Lorem Ipsum",
        "category": "FAKE",
        "description": "生成Lorem Ipsum文本",
        "params": [
            {"name": "type", "type": "text", "default": "words", "description": "类型(paragraphs,words,characters)"},
            {"name": "count", "type": "int", "default": 10, "description": "数量"}
        ],
        "return_type": "text"
    },
    {
        "code": "anon.image_blur",
        "name": "图像模糊",
        "category": "PARTIAL",
        "description": "对图像数据应用模糊效果",
        "params": [
            {"name": "sigma", "type": "float", "default": 5.0, "description": "模糊程度"}
        ],
        "return_type": "bytea"
    },
]


class MaskingAlgorithm(BaseModel):
    """脱敏算法"""

    code: str = Field(..., description="算法编码")
    name: str = Field(..., description="算法名称")
    description: Optional[str] = Field(default=None, description="算法描述")


# ==================== 脱敏任务 ====================

class MaskingTaskBase(BaseModel):
    """脱敏任务基础"""

    task_name: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="任务名称",
        validation_alias=AliasChoices('task_name', 'taskName'),
        serialization_alias='taskName'
    )
    task_code: Optional[str] = Field(
        default=None,
        max_length=64,
        description="任务编码",
        validation_alias=AliasChoices('task_code', 'taskCode'),
        serialization_alias='taskCode'
    )
    description: Optional[str] = Field(default=None, description="任务描述")
    datasource_id: int = Field(
        ...,
        description="数据源ID",
        validation_alias=AliasChoices('datasource_id', 'datasourceId'),
        serialization_alias='datasourceId'
    )
    masking_mode: str = Field(
        default="STATIC",
        description="脱敏模式: STATIC(静态脱敏), GENERALIZE(泛化脱敏)",
        validation_alias=AliasChoices('masking_mode', 'maskingMode'),
        serialization_alias='maskingMode'
    )
    source_schema: Optional[str] = Field(
        default=None,
        max_length=128,
        description="源Schema",
        validation_alias=AliasChoices('source_schema', 'sourceSchema'),
        serialization_alias='sourceSchema'
    )
    target_schema: Optional[str] = Field(
        default=None,
        max_length=128,
        description="目标Schema",
        validation_alias=AliasChoices('target_schema', 'targetSchema'),
        serialization_alias='targetSchema'
    )
    task_type: str = Field(
        default="TABLE",
        description="任务类型",
        validation_alias=AliasChoices('task_type', 'taskType'),
        serialization_alias='taskType'
    )
    schedule_type: str = Field(
        default="MANUAL",
        description="调度类型：MANUAL/CRON",
        validation_alias=AliasChoices('schedule_type', 'scheduleType'),
        serialization_alias='scheduleType'
    )
    cron_expression: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Cron表达式",
        validation_alias=AliasChoices('cron_expression', 'cronExpression'),
        serialization_alias='cronExpression'
    )


class MaskingTaskCreate(MaskingTaskBase):
    """创建脱敏任务"""
    pass


class MaskingTaskUpdate(BaseModel):
    """更新脱敏任务"""

    task_name: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('task_name', 'taskName'),
        serialization_alias='taskName'
    )
    description: Optional[str] = None
    source_schema: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('source_schema', 'sourceSchema'),
        serialization_alias='sourceSchema'
    )
    target_schema: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('target_schema', 'targetSchema'),
        serialization_alias='targetSchema'
    )
    schedule_type: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices('schedule_type', 'scheduleType'),
        serialization_alias='scheduleType'
    )
    cron_expression: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('cron_expression', 'cronExpression'),
        serialization_alias='cronExpression'
    )
    status: Optional[str] = None


class MaskingTaskResponse(MaskingTaskBase, TimestampMixin):
    """脱敏任务响应"""

    id: int
    status: str
    created_by: Optional[int] = Field(
        default=None,
        serialization_alias='createdBy'
    )
    tables: List["MaskingTableResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==================== 脱敏表配置 ====================

class MaskingTableBase(BaseModel):
    """脱敏表基础"""

    table_name: str = Field(
        ...,
        max_length=128,
        description="表名",
        validation_alias=AliasChoices('table_name', 'tableName'),
        serialization_alias='tableName'
    )
    source_table: Optional[str] = Field(
        default=None,
        max_length=128,
        description="源表名",
        validation_alias=AliasChoices('source_table', 'sourceTable'),
        serialization_alias='sourceTable'
    )
    target_table: Optional[str] = Field(
        default=None,
        max_length=128,
        description="目标表名",
        validation_alias=AliasChoices('target_table', 'targetTable'),
        serialization_alias='targetTable'
    )
    order_no: int = Field(
        default=0,
        description="执行顺序",
        validation_alias=AliasChoices('order_no', 'orderNo'),
        serialization_alias='orderNo'
    )
    enabled: bool = Field(default=True, description="是否启用")


class MaskingTableCreate(MaskingTableBase):
    """创建脱敏表"""

    task_id: int = Field(
        ...,
        description="任务ID",
        validation_alias=AliasChoices('task_id', 'taskId'),
        serialization_alias='taskId'
    )


class MaskingTableUpdate(BaseModel):
    """更新脱敏表"""

    source_table: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('source_table', 'sourceTable'),
        serialization_alias='sourceTable'
    )
    target_table: Optional[str] = Field(
        default=None,
        max_length=128,
        validation_alias=AliasChoices('target_table', 'targetTable'),
        serialization_alias='targetTable'
    )
    order_no: Optional[int] = Field(
        default=None,
        validation_alias=AliasChoices('order_no', 'orderNo'),
        serialization_alias='orderNo'
    )
    enabled: Optional[bool] = None


class MaskingTableResponse(MaskingTableBase):
    """脱敏表响应"""

    id: int
    task_id: int = Field(
        serialization_alias='taskId'
    )
    columns: List["MaskingColumnResponse"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==================== 脱敏字段配置 ====================

class MaskingColumnBase(BaseModel):
    """脱敏字段基础"""

    column_name: str = Field(
        ...,
        max_length=128,
        description="字段名",
        validation_alias=AliasChoices('column_name', 'columnName'),
        serialization_alias='columnName'
    )
    data_type: Optional[str] = Field(
        default=None,
        max_length=64,
        description="数据类型",
        validation_alias=AliasChoices('data_type', 'dataType'),
        serialization_alias='dataType'
    )
    masking_algorithm: str = Field(
        ...,
        max_length=64,
        description="脱敏算法",
        validation_alias=AliasChoices('masking_algorithm', 'maskingAlgorithm'),
        serialization_alias='maskingAlgorithm'
    )
    algorithm_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="算法参数",
        validation_alias=AliasChoices('algorithm_params', 'algorithmParams'),
        serialization_alias='algorithmParams'
    )
    description: Optional[str] = Field(default=None, max_length=512, description="说明")


class MaskingColumnCreate(MaskingColumnBase):
    """创建脱敏字段"""

    table_id: int = Field(
        ...,
        description="表配置ID",
        validation_alias=AliasChoices('table_id', 'tableId'),
        serialization_alias='tableId'
    )


class MaskingColumnUpdate(BaseModel):
    """更新脱敏字段"""

    data_type: Optional[str] = Field(
        default=None,
        max_length=64,
        validation_alias=AliasChoices('data_type', 'dataType'),
        serialization_alias='dataType'
    )
    masking_algorithm: Optional[str] = Field(
        default=None,
        max_length=64,
        validation_alias=AliasChoices('masking_algorithm', 'maskingAlgorithm'),
        serialization_alias='maskingAlgorithm'
    )
    algorithm_params: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias=AliasChoices('algorithm_params', 'algorithmParams'),
        serialization_alias='algorithmParams'
    )
    description: Optional[str] = Field(default=None, max_length=512)


class MaskingColumnResponse(MaskingColumnBase):
    """脱敏字段响应"""

    id: int
    table_id: int = Field(
        serialization_alias='tableId'
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==================== 脱敏模板 ====================

class MaskingTemplateBase(BaseModel):
    """脱敏模板基础"""

    template_name: str = Field(
        ...,
        max_length=128,
        description="模板名称",
        validation_alias=AliasChoices('template_name', 'templateName'),
        serialization_alias='templateName'
    )
    template_code: Optional[str] = Field(
        default=None,
        max_length=64,
        description="模板编码",
        validation_alias=AliasChoices('template_code', 'templateCode'),
        serialization_alias='templateCode'
    )
    description: Optional[str] = Field(default=None, description="模板描述")
    config_json: Optional[Dict[str, Any]] = Field(
        default=None,
        description="模板配置",
        validation_alias=AliasChoices('config_json', 'configJson'),
        serialization_alias='configJson'
    )


class MaskingTemplateCreate(MaskingTemplateBase):
    """创建脱敏模板"""
    pass


class MaskingTemplateResponse(MaskingTemplateBase, TimestampMixin):
    """脱敏模板响应"""

    id: int
    created_by: Optional[int] = Field(
        default=None,
        serialization_alias='createdBy'
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ==================== 任务执行 ====================

class MaskingTaskExecutionResponse(BaseModel):
    """脱敏任务执行记录响应"""

    id: int
    task_id: int = Field(
        serialization_alias='taskId'
    )
    execution_no: str = Field(
        serialization_alias='executionNo'
    )
    trigger_type: str = Field(
        serialization_alias='triggerType'
    )
    start_time: Optional[datetime] = Field(
        default=None,
        serialization_alias='startTime'
    )
    end_time: Optional[datetime] = Field(
        default=None,
        serialization_alias='endTime'
    )
    status: str
    total_records: int = Field(
        default=0,
        serialization_alias='totalRecords'
    )
    success_records: int = Field(
        default=0,
        serialization_alias='successRecords'
    )
    failed_records: int = Field(
        default=0,
        serialization_alias='failedRecords'
    )
    error_message: Optional[str] = Field(
        default=None,
        serialization_alias='errorMessage'
    )
    created_at: datetime = Field(
        serialization_alias='createdAt'
    )

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class MaskingTaskExecuteRequest(BaseModel):
    """脱敏任务执行请求"""

    task_id: int = Field(
        ...,
        description="任务ID",
        validation_alias=AliasChoices('task_id', 'taskId'),
        serialization_alias='taskId'
    )
    remark: Optional[str] = Field(default=None, description="备注")


# 更新前向引用
MaskingTaskResponse.model_rebuild()
MaskingTableResponse.model_rebuild()
