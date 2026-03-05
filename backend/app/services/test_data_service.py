"""
测试数据生成服务
从生产数据学习特征，生成逼真的测试数据
"""
import logging
import random
import string
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.test_data import TestDataTask, TestDataProfile, TestDataExecution
from app.services.datasource_service import DataSourceService
from app.utils.datasource_manager import get_datasource_manager

logger = logging.getLogger(__name__)


class TestDataService:
    """测试数据生成服务"""

    # 支持的生成器类型
    GENERATOR_TYPES = {
        # Faker 生成器
        "fake_name": "姓名",
        "fake_email": "邮箱",
        "fake_phone": "电话",
        "fake_address": "地址",
        "fake_company": "公司",
        "fake_id_card": "身份证号",
        "fake_bank_card": "银行卡号",
        "fake_credit_card": "信用卡号",
        # 数值生成器
        "sequence": "序列",
        "random_int": "随机整数",
        "random_float": "随机浮点数",
        "random_date": "随机日期",
        "random_datetime": "随机时间",
        # 字符串生成器
        "random_string": "随机字符串",
        "uuid": "UUID",
        "regex_pattern": "正则表达式",
        # 保持原值
        "keep_original": "保持原值",
    }

    def __init__(self):
        self._faker = None

    @property
    def faker(self):
        """延迟加载 Faker"""
        if self._faker is None:
            try:
                from faker import Faker
                self._faker = Faker('zh_CN')
            except ImportError:
                logger.warning("Faker 库未安装，部分生成器不可用")
                self._faker = None
        return self._faker

    def analyze_table(self, db: Session, datasource_id: int, table_name: str, schema: str = None) -> Dict[str, Any]:
        """
        分析表的数据特征

        Args:
            db: 数据库会话
            datasource_id: 数据源ID
            table_name: 表名
            schema: Schema名

        Returns:
            分析结果
        """
        datasource = DataSourceService.get_datasource(db, datasource_id)
        if not datasource:
            raise ValueError("数据源不存在")

        config = DataSourceService.get_datasource_config(datasource)
        manager = get_datasource_manager()

        # 获取列信息
        columns = manager.get_columns(datasource.datasource_type, config, table_name, schema)

        # 分析每列的特征
        column_profiles = []
        for col in columns:
            col_name = col.get("column_name")
            data_type = col.get("data_type", "").lower()

            # 采样数据
            sample_sql = f"""
                SELECT {col_name}
                FROM {table_name}
                WHERE {col_name} IS NOT NULL
                LIMIT 1000
            """

            try:
                samples = manager.execute_sql(datasource.datasource_type, config, sample_sql)
                values = [row.get(col_name) for row in samples if row.get(col_name) is not None]

                if values:
                    profile = self._analyze_column(values, data_type)
                    generator = self._detect_generator(col_name, data_type, profile)
                else:
                    profile = {"data_type": data_type, "null_ratio": 1.0}
                    generator = "keep_original"

                column_profiles.append({
                    "column_name": col_name,
                    "data_type": data_type,
                    "is_nullable": col.get("is_nullable", True),
                    "profile": profile,
                    "suggested_generator": generator
                })
            except Exception as e:
                logger.error(f"分析列 {col_name} 失败: {e}")
                column_profiles.append({
                    "column_name": col_name,
                    "data_type": data_type,
                    "is_nullable": col.get("is_nullable", True),
                    "profile": {},
                    "suggested_generator": "keep_original"
                })

        # 获取行数
        count_sql = f"SELECT COUNT(*) as cnt FROM {table_name}"
        try:
            result = manager.execute_sql(datasource.datasource_type, config, count_sql)
            row_count = result[0].get("cnt", 0) if result else 0
        except:
            row_count = 0

        return {
            "table_name": table_name,
            "columns": column_profiles,
            "row_count": row_count
        }

    def _analyze_column(self, values: list, data_type: str) -> Dict[str, Any]:
        """分析列数据特征"""
        profile = {
            "data_type": data_type,
            "null_ratio": 0.0,
        }

        if not values:
            profile["null_ratio"] = 1.0
            return profile

        n = len(values)

        # 检测数值类型
        is_numeric = any(kw in data_type for kw in ['int', 'float', 'numeric', 'decimal', 'double', 'number'])

        # 检测日期类型
        is_date = any(kw in data_type for kw in ['date', 'time', 'timestamp'])

        # 检测字符串类型
        is_string = any(kw in data_type for kw in ['char', 'varchar', 'text', 'string'])

        if is_numeric:
            try:
                numeric_values = [float(v) for v in values if v is not None]
                if numeric_values:
                    profile.update({
                        "min": min(numeric_values),
                        "max": max(numeric_values),
                        "mean": sum(numeric_values) / len(numeric_values),
                    })
                    # 计算标准差
                    mean = profile["mean"]
                    variance = sum((x - mean) ** 2 for x in numeric_values) / len(numeric_values)
                    profile["std_dev"] = variance ** 0.5

                    # 计算四分位数
                    sorted_values = sorted(numeric_values)
                    profile["quartiles"] = [
                        sorted_values[int(len(sorted_values) * 0.25)],
                        sorted_values[int(len(sorted_values) * 0.5)],
                        sorted_values[int(len(sorted_values) * 0.75)]
                    ]
            except (ValueError, TypeError):
                pass

        elif is_date:
            # 日期类型分析
            dates = []
            for v in values:
                if isinstance(v, datetime):
                    dates.append(v)
                elif isinstance(v, str):
                    try:
                        # 尝试解析常见日期格式
                        for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d']:
                            try:
                                dates.append(datetime.strptime(v, fmt))
                                break
                            except ValueError:
                                continue
                    except:
                        pass

            if dates:
                profile.update({
                    "min_date": min(dates).isoformat(),
                    "max_date": max(dates).isoformat(),
                })

        elif is_string:
            # 字符串类型分析
            str_values = [str(v) for v in values if v is not None]
            if str_values:
                lengths = [len(v) for v in str_values]
                profile.update({
                    "avg_length": sum(lengths) / len(lengths),
                    "max_length": max(lengths),
                    "min_length": min(lengths),
                    "unique_ratio": len(set(str_values)) / len(str_values),
                    "patterns": self._analyze_patterns(str_values)
                })

        return profile

    def _analyze_patterns(self, values: List[str]) -> List[Dict[str, Any]]:
        """分析字符串模式"""
        patterns = Counter()
        for v in values:
            pattern = self._detect_pattern(v)
            patterns[pattern] += 1

        return [{"pattern": p, "count": c} for p, c in patterns.most_common(5)]

    def _detect_pattern(self, value: str) -> str:
        """检测字符串模式"""
        if not value:
            return "empty"

        # 邮箱
        if '@' in value and '.' in value.split('@')[-1]:
            return "email"

        # URL
        if value.startswith(('http://', 'https://')):
            return "url"

        # 中国手机号
        if len(value) == 11 and value.isdigit() and value.startswith('1'):
            return "phone_cn"

        # 中国身份证
        if len(value) == 18 and value[:-1].isdigit():
            return "id_card_cn"

        # 纯数字
        if value.isdigit():
            return "numeric"

        # 纯字母
        if value.isalpha():
            return "alpha"

        # 混合
        if any(c.isdigit() for c in value) and any(c.isalpha() for c in value):
            return "alphanumeric"

        return "text"

    def _detect_generator(self, col_name: str, data_type: str, profile: Dict) -> str:
        """检测建议的生成器类型"""
        col_lower = col_name.lower()

        # 根据列名推断
        if any(kw in col_lower for kw in ['name', '姓名', '名字']):
            return "fake_name"
        if any(kw in col_lower for kw in ['email', '邮箱', '邮件']):
            return "fake_email"
        if any(kw in col_lower for kw in ['phone', 'tel', 'mobile', '电话', '手机']):
            return "fake_phone"
        if any(kw in col_lower for kw in ['address', '地址', '住址']):
            return "fake_address"
        if any(kw in col_lower for kw in ['company', '公司', '企业']):
            return "fake_company"
        if any(kw in col_lower for kw in ['id_card', '身份证']):
            return "fake_id_card"

        # 根据数据类型推断
        if 'id' in col_lower or 'key' in col_lower:
            return "sequence"

        if any(kw in data_type for kw in ['int', 'number']):
            return "random_int"

        if any(kw in data_type for kw in ['float', 'double', 'decimal']):
            return "random_float"

        if any(kw in data_type for kw in ['date', 'time']):
            return "random_datetime"

        return "random_string"

    def _get_generator_for_type(self, col_name: str, data_type: str) -> str:
        """
        根据列名和数据类型获取合适的生成器

        Args:
            col_name: 列名
            data_type: 数据类型

        Returns:
            生成器类型
        """
        data_type = data_type.lower() if data_type else ""

        # 根据列名推断（优先级更高）
        col_lower = col_name.lower()
        if any(kw in col_lower for kw in ['name', '姓名', '名字']):
            return "fake_name"
        if any(kw in col_lower for kw in ['email', '邮箱', '邮件']):
            return "fake_email"
        if any(kw in col_lower for kw in ['phone', 'tel', 'mobile', '电话', '手机']):
            return "fake_phone"
        if any(kw in col_lower for kw in ['address', '地址', '住址']):
            return "fake_address"

        # 根据数据类型推断
        if any(kw in data_type for kw in ['int', 'serial', 'bigserial', 'smallint', 'bigint']):
            return "random_int"
        if any(kw in data_type for kw in ['float', 'double', 'decimal', 'numeric', 'real']):
            return "random_float"
        if 'date' in data_type and 'time' not in data_type:
            return "random_date"
        if any(kw in data_type for kw in ['time', 'timestamp']):
            return "random_datetime"
        if 'bool' in data_type:
            return "random_int"  # 用0/1表示布尔值

        return "random_string"

    def _ensure_generator_type_compatibility(self, generator: str, data_type: str) -> str:
        """
        确保生成器与数据类型兼容

        Args:
            generator: 当前生成器
            data_type: 数据类型

        Returns:
            兼容的生成器类型
        """
        data_type = data_type.lower() if data_type else ""

        # 数值类型必须使用数值生成器
        numeric_types = ['int', 'serial', 'bigserial', 'smallint', 'bigint', 'float', 'double', 'decimal', 'numeric', 'real']
        is_numeric = any(kw in data_type for kw in numeric_types)

        # 字符串生成器列表
        string_generators = ['random_string', 'fake_name', 'fake_email', 'fake_phone', 'fake_address', 'fake_company']

        if is_numeric and generator in string_generators:
            # 数值类型但配置了字符串生成器，自动切换到数值生成器
            if any(kw in data_type for kw in ['int', 'serial', 'bigserial', 'smallint', 'bigint']):
                logger.warning(f"生成器 '{generator}' 与数据类型 '{data_type}' 不兼容，自动切换为 'random_int'")
                return "random_int"
            else:
                logger.warning(f"生成器 '{generator}' 与数据类型 '{data_type}' 不兼容，自动切换为 'random_float'")
                return "random_float"

        return generator

    def generate_value(
        self,
        generator_type: str,
        profile: Dict[str, Any],
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        根据生成器类型生成值

        Args:
            generator_type: 生成器类型
            profile: 数据特征
            params: 生成器参数

        Returns:
            生成的值
        """
        params = params or {}

        # 检查是否生成 NULL
        null_ratio = profile.get("null_ratio", 0)
        if null_ratio > 0 and random.random() < null_ratio:
            return None

        # Faker 生成器
        if generator_type == "fake_name" and self.faker:
            return self.faker.name()
        elif generator_type == "fake_email" and self.faker:
            return self.faker.email()
        elif generator_type == "fake_phone" and self.faker:
            return self.faker.phone_number()
        elif generator_type == "fake_address" and self.faker:
            return self.faker.address()
        elif generator_type == "fake_company" and self.faker:
            return self.faker.company()
        elif generator_type == "fake_id_card" and self.faker:
            return self.faker.ssn()
        elif generator_type == "fake_bank_card" and self.faker:
            return self.faker.credit_card_number()

        # 序列生成器
        elif generator_type == "sequence":
            start = params.get("start", profile.get("min", 1))
            step = params.get("step", 1)
            # 返回一个范围内的随机值
            end = params.get("end", start + 10000)
            return random.randint(int(start), int(end))

        # 随机整数
        elif generator_type == "random_int":
            min_val = params.get("min", profile.get("min", 0))
            max_val = params.get("max", profile.get("max", 1000))
            return random.randint(int(min_val), int(max_val))

        # 随机浮点数
        elif generator_type == "random_float":
            min_val = params.get("min", profile.get("min", 0))
            max_val = params.get("max", profile.get("max", 1000))
            decimals = params.get("decimals", 2)
            return round(random.uniform(float(min_val), float(max_val)), decimals)

        # 随机日期
        elif generator_type == "random_date":
            return self._generate_date(profile, params)

        # 随机时间
        elif generator_type == "random_datetime":
            return self._generate_datetime(profile, params)

        # 随机字符串
        elif generator_type == "random_string":
            length = params.get("length", int(profile.get("avg_length", 10)))
            chars = params.get("chars", string.ascii_letters + string.digits)
            return ''.join(random.choices(chars, k=length))

        # UUID
        elif generator_type == "uuid":
            import uuid
            return str(uuid.uuid4())

        # 正则表达式
        elif generator_type == "regex_pattern":
            pattern = params.get("pattern", ".*")
            try:
                import rstr
                return rstr.xeger(pattern)
            except ImportError:
                return self._generate_string(profile)

        # 默认：生成随机字符串
        else:
            return self._generate_string(profile)

    def _generate_date(self, profile: Dict, params: Dict) -> str:
        """生成日期"""
        start_date = params.get("start_date")
        end_date = params.get("end_date")

        if not start_date:
            start_date = profile.get("min_date")
        if not end_date:
            end_date = profile.get("max_date")

        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            delta = (end_date - start_date).days
            random_days = random.randint(0, delta)
            result_date = start_date + timedelta(days=random_days)
            return result_date.strftime('%Y-%m-%d')

        # 默认生成近一年的日期
        end = datetime.now()
        start = end - timedelta(days=365)
        delta = (end - start).days
        random_days = random.randint(0, delta)
        return (start + timedelta(days=random_days)).strftime('%Y-%m-%d')

    def _generate_datetime(self, profile: Dict, params: Dict) -> str:
        """生成日期时间"""
        start_date = params.get("start_date")
        end_date = params.get("end_date")

        if not start_date:
            start_date = profile.get("min_date")
        if not end_date:
            end_date = profile.get("max_date")

        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            delta = end_date - start_date
            random_seconds = random.randint(0, int(delta.total_seconds()))
            result_date = start_date + timedelta(seconds=random_seconds)
            return result_date.strftime('%Y-%m-%d %H:%M:%S')

        end = datetime.now()
        start = end - timedelta(days=365)
        delta = end - start
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return (start + timedelta(seconds=random_seconds)).strftime('%Y-%m-%d %H:%M:%S')

    def _generate_string(self, profile: Dict) -> str:
        """生成随机字符串"""
        avg_length = int(profile.get("avg_length", 10))
        length = max(1, avg_length + random.randint(-2, 2))
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def generate_preview(
        self,
        db: Session,
        task_id: int,
        row_count: int = 10
    ) -> Dict[str, Any]:
        """
        生成预览数据

        Args:
            db: 数据库会话
            task_id: 任务ID
            row_count: 预览行数

        Returns:
            预览数据
        """
        task = db.scalar(select(TestDataTask).where(TestDataTask.id == task_id))
        if not task:
            raise ValueError("任务不存在")

        if not task.table_configs or not task.table_configs.get("tables"):
            raise ValueError("未配置表")

        result = {}

        for table_config in task.table_configs["tables"]:
            table_name = table_config.get("target_table", table_config.get("source_table"))
            columns = table_config.get("columns", [])

            # 获取列特征
            profiles = db.scalars(
                select(TestDataProfile).where(
                    TestDataProfile.task_id == task_id,
                    TestDataProfile.table_name == table_name
                )
            ).all()

            profile_map = {p.column_name: p for p in profiles}

            # 生成预览数据
            rows = []
            col_names = [c.get("name") for c in columns]

            for _ in range(min(row_count, 10)):
                row = {}
                for col in columns:
                    col_name = col.get("name")
                    generator = col.get("generator", "random_string")
                    params = col.get("params", {})

                    # 获取已有的特征
                    profile_obj = profile_map.get(col_name)
                    profile = profile_obj.profile_data if profile_obj and profile_obj.profile_data else {}

                    row[col_name] = self.generate_value(generator, profile, params)

                rows.append(row)

            result[table_name] = {
                "columns": col_names,
                "rows": rows
            }

        return result

    def execute_generation(
        self,
        task_id: int,
        execution_id: int
    ) -> None:
        """
        执行测试数据生成

        Args:
            task_id: 任务ID
            execution_id: 执行ID
        """
        # 创建独立的数据库会话
        db = SessionLocal()
        error_messages = []  # 收集所有错误信息

        try:
            task = db.scalar(select(TestDataTask).where(TestDataTask.id == task_id))
            execution = db.scalar(select(TestDataExecution).where(TestDataExecution.id == execution_id))

            if not task or not execution:
                return

            # 更新执行状态
            execution.status = "RUNNING"
            execution.start_time = datetime.now()
            db.commit()

            # 获取数据源配置
            source_ds = DataSourceService.get_datasource(db, task.source_datasource_id)
            target_ds = DataSourceService.get_datasource(db, task.target_datasource_id)

            if not source_ds or not target_ds:
                raise ValueError("数据源不存在")

            source_config = DataSourceService.get_datasource_config(source_ds)
            target_config = DataSourceService.get_datasource_config(target_ds)

            manager = get_datasource_manager()

            total_records = 0
            success_records = 0
            failed_records = 0
            completed_tables = 0

            if not task.table_configs or not task.table_configs.get("tables"):
                raise ValueError("未配置表")

            # 获取特征配置
            profiles = db.scalars(
                select(TestDataProfile).where(TestDataProfile.task_id == task_id)
            ).all()
            profile_map = {(p.table_name, p.column_name): p for p in profiles}

            for table_config in task.table_configs["tables"]:
                # 支持两种命名格式
                source_table = table_config.get("source_table") or table_config.get("sourceTable")
                source_schema = table_config.get("source_schema") or table_config.get("sourceSchema") or "public"
                target_table = table_config.get("target_table") or table_config.get("targetTable") or source_table
                target_schema = table_config.get("target_schema") or table_config.get("targetSchema") or "public"
                row_count = table_config.get("row_count") or table_config.get("rowCount") or 100
                columns = table_config.get("columns", [])

                # 如果源表名包含 schema，则解析出来
                if source_table and "." in source_table:
                    parts = source_table.split(".", 1)
                    source_schema = parts[0]
                    source_table = parts[1]

                # 构建完整的表名
                full_source_table = f"{source_schema}.{source_table}" if source_schema else source_table
                full_target_table = f"{target_schema}.{target_table}" if target_schema else target_table

                logger.info(f"开始处理表: {full_source_table} -> {full_target_table}, 行数: {row_count}")

                try:
                    # 获取源表的列信息
                    source_columns = manager.get_columns(source_ds.datasource_type, source_config, source_table, source_schema)
                    logger.info(f"源表列数: {len(source_columns)}")

                    if not source_columns:
                        error_msg = f"无法获取源表 {full_source_table} 的列信息"
                        logger.error(error_msg)
                        error_messages.append(error_msg)
                        failed_records += row_count
                        continue

                    # 构建列名到数据类型的映射
                    column_type_map = {col["column_name"]: col.get("data_type", "").lower() for col in source_columns}

                    # 如果没有配置列，使用源表的所有列，并根据数据类型自动选择生成器
                    if not columns:
                        columns = []
                        for col in source_columns:
                            col_name = col["column_name"]
                            col_type = col.get("data_type", "").lower()
                            # 根据数据类型选择生成器
                            generator = self._get_generator_for_type(col_name, col_type)
                            columns.append({"name": col_name, "generator": generator})
                        logger.info(f"使用自动列配置: {[c['name'] + ':' + c['generator'] for c in columns]}")
                    else:
                        # 检查并修正生成器与数据类型的兼容性
                        for col in columns:
                            col_name = col.get("name")
                            col_type = column_type_map.get(col_name, "")
                            generator = col.get("generator", "random_string")
                            # 如果生成器与数据类型不兼容，自动修正
                            col["generator"] = self._ensure_generator_type_compatibility(generator, col_type)

                    # 先创建目标表（基于列定义创建，而不是复制源表结构）
                    # 因为源表和目标表可能在不同的数据库
                    try:
                        # 构建建表SQL
                        column_defs = []
                        for col in source_columns:
                            col_name = col.get("column_name")
                            col_type = col.get("data_type", "text").lower()

                            # 映射常见数据类型到标准PostgreSQL类型
                            if "integer" in col_type or "serial" in col_type or "smallint" in col_type or "bigint" in col_type:
                                # 整数类型不带长度
                                if "big" in col_type:
                                    col_type = "BIGINT"
                                elif "small" in col_type:
                                    col_type = "SMALLINT"
                                else:
                                    col_type = "INTEGER"
                            elif "numeric" in col_type or "decimal" in col_type:
                                # NUMERIC可以带精度
                                precision = col.get("numeric_precision")
                                scale = col.get("numeric_scale")
                                if precision and scale:
                                    col_type = f"NUMERIC({precision},{scale})"
                                elif precision:
                                    col_type = f"NUMERIC({precision})"
                                else:
                                    col_type = "NUMERIC(10,2)"
                            elif "float" in col_type or "double" in col_type or "real" in col_type:
                                col_type = "DOUBLE PRECISION"
                            elif "varchar" in col_type or "character varying" in col_type:
                                char_len = col.get("character_maximum_length")
                                if char_len:
                                    col_type = f"VARCHAR({char_len})"
                                else:
                                    col_type = "VARCHAR(255)"
                            elif "char" in col_type or "character" in col_type:
                                char_len = col.get("character_maximum_length")
                                if char_len and char_len > 1:
                                    col_type = f"CHAR({char_len})"
                                else:
                                    col_type = "VARCHAR(255)"  # 避免使用 CHAR(1)
                            elif "text" in col_type:
                                col_type = "TEXT"
                            elif "timestamp" in col_type:
                                col_type = "TIMESTAMP"
                            elif "date" in col_type:
                                col_type = "DATE"
                            elif "boolean" in col_type or "bool" in col_type:
                                col_type = "BOOLEAN"
                            else:
                                # 默认使用 TEXT 类型
                                col_type = "TEXT"

                            column_defs.append(f"{col_name} {col_type}")

                        # 如果表已存在，先删除
                        drop_sql = f"DROP TABLE IF EXISTS {full_target_table}"
                        manager.execute_sql(target_ds.datasource_type, target_config, drop_sql)

                        create_table_sql = f"""CREATE TABLE {full_target_table} ({', '.join(column_defs)})"""
                        manager.execute_sql(target_ds.datasource_type, target_config, create_table_sql)
                        logger.info(f"目标表创建成功: {full_target_table}")
                    except Exception as e:
                        error_msg = f"创建目标表失败: {str(e)}"
                        logger.warning(error_msg)
                        error_messages.append(error_msg)
                        # 表可能已存在，继续尝试插入数据

                    # 生成并插入数据
                    batch_size = 100
                    for batch_start in range(0, row_count, batch_size):
                        batch_end = min(batch_start + batch_size, row_count)
                        batch_rows = []

                        for _ in range(batch_start, batch_end):
                            row = {}
                            for col in columns:
                                col_name = col.get("name")
                                generator = col.get("generator", "random_string")
                                params = col.get("params", {})

                                profile_obj = profile_map.get((target_table, col_name))
                                profile = profile_obj.profile_data if profile_obj and profile_obj.profile_data else {}

                                row[col_name] = self.generate_value(generator, profile, params)

                            batch_rows.append(row)

                        # 构建插入SQL
                        if batch_rows:
                            col_names = list(batch_rows[0].keys())
                            values_str = ", ".join([
                                f"({', '.join([self._sql_value(v) for v in row.values()])})"
                                for row in batch_rows
                            ])

                            insert_sql = f"""INSERT INTO {full_target_table} ({', '.join(col_names)}) VALUES {values_str}"""

                            try:
                                manager.execute_sql(target_ds.datasource_type, target_config, insert_sql)
                                success_records += len(batch_rows)
                                logger.debug(f"成功插入 {len(batch_rows)} 行到 {full_target_table}")
                            except Exception as e:
                                error_msg = f"插入数据到 {full_target_table} 失败: {str(e)}"
                                logger.error(error_msg)
                                error_messages.append(error_msg)
                                failed_records += len(batch_rows)

                        total_records = success_records + failed_records

                    completed_tables += 1
                    logger.info(f"表 {full_target_table} 处理完成，成功: {success_records}, 失败: {failed_records}")

                    # 更新进度
                    execution.completed_tables = completed_tables
                    execution.total_records = total_records
                    execution.success_records = success_records
                    execution.failed_records = failed_records
                    db.commit()

                except Exception as e:
                    error_msg = f"生成表 {target_table} 数据失败: {str(e)}"
                    logger.exception(error_msg)
                    error_messages.append(error_msg)
                    failed_records += row_count

            # 完成后根据成功/失败情况设置状态
            execution.end_time = datetime.now()
            execution.total_tables = len(task.table_configs.get("tables", []))
            execution.completed_tables = completed_tables
            execution.total_records = total_records
            execution.success_records = success_records
            execution.failed_records = failed_records

            # 根据执行结果设置状态和错误信息
            if failed_records == 0 and success_records > 0:
                execution.status = "SUCCESS"
                task.status = "READY"
            elif success_records == 0 and failed_records > 0:
                execution.status = "FAILED"
                execution.error_message = "所有记录处理失败:\n" + "\n".join(error_messages[:10])  # 最多显示10条错误
                task.status = "FAILED"
            else:
                execution.status = "PARTIAL_SUCCESS"
                execution.error_message = f"部分记录处理失败 ({failed_records}/{total_records}):\n" + "\n".join(error_messages[:10])
                task.status = "READY"

            db.commit()

        except Exception as e:
            logger.exception("执行测试数据生成失败")
            if execution:
                execution.status = "FAILED"
                execution.end_time = datetime.now()
                execution.error_message = str(e)
                db.commit()
            if task:
                task.status = "FAILED"
                db.commit()
        finally:
            # 关闭数据库会话
            db.close()

    def _sql_value(self, value: Any) -> str:
        """将值转换为SQL格式"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f"'{value.replace(chr(39), chr(39)+chr(39))}'"
        elif isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        elif isinstance(value, (datetime,)):
            return f"'{value.isoformat()}'"
        else:
            return str(value)


# 单例
_test_data_service: Optional[TestDataService] = None


def get_test_data_service() -> TestDataService:
    """获取测试数据服务单例"""
    global _test_data_service
    if _test_data_service is None:
        _test_data_service = TestDataService()
    return _test_data_service
