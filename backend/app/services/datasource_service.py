"""
数据源服务
"""
import logging
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, or_, func

from app.core.security import encrypt_data, decrypt_data
from app.models.datasource import DataSource, DataSourceReference, AccountMapping
from app.utils.datasource_manager import get_datasource_manager

logger = logging.getLogger(__name__)


class DataSourceService:
    """数据源服务"""

    @staticmethod
    def get_datasource(db: Session, datasource_id: int) -> Optional[DataSource]:
        """获取数据源"""
        stmt = select(DataSource).where(DataSource.id == datasource_id)
        return db.scalar(stmt)

    @staticmethod
    def get_datasources(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        datasource_type: Optional[str] = None,
        status: Optional[int] = None,
    ) -> Tuple[List[DataSource], int]:
        """获取数据源列表"""
        query = select(DataSource)

        if keyword:
            query = query.where(
                or_(
                    DataSource.datasource_name.contains(keyword),
                    DataSource.host.contains(keyword),
                )
            )
        if datasource_type:
            query = query.where(DataSource.datasource_type == datasource_type)
        if status is not None:
            query = query.where(DataSource.status == status)

        # 查询总数
        count_stmt = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_stmt)

        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(DataSource.created_at.desc()).offset(offset).limit(page_size)
        datasources = db.scalars(query).all()

        return datasources, total

    @staticmethod
    def create_datasource(
        db: Session,
        datasource_name: str,
        datasource_type: str,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        config_json: Optional[Dict[str, Any]] = None,
        enable_account_mapping: bool = False,
        created_by: Optional[int] = None,
    ) -> DataSource:
        """创建数据源"""
        password_encrypted = encrypt_data(password) if password else None

        datasource = DataSource(
            datasource_name=datasource_name,
            datasource_type=datasource_type,
            host=host,
            port=port,
            database_name=database_name,
            username=username,
            password_encrypted=password_encrypted,
            config_json=config_json,
            enable_account_mapping=enable_account_mapping,
            status=1,
            created_by=created_by,
        )
        db.add(datasource)
        db.commit()
        db.refresh(datasource)
        return datasource

    @staticmethod
    def update_datasource(
        db: Session,
        datasource_id: int,
        datasource_name: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database_name: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        config_json: Optional[Dict[str, Any]] = None,
        enable_account_mapping: Optional[bool] = None,
        status: Optional[int] = None,
    ) -> Optional[DataSource]:
        """更新数据源"""
        datasource = DataSourceService.get_datasource(db, datasource_id)
        if not datasource:
            return None

        if datasource_name is not None:
            datasource.datasource_name = datasource_name
        if host is not None:
            datasource.host = host
        if port is not None:
            datasource.port = port
        if database_name is not None:
            datasource.database_name = database_name
        if username is not None:
            datasource.username = username
        if password is not None:
            datasource.password_encrypted = encrypt_data(password)
        if config_json is not None:
            datasource.config_json = config_json
        if enable_account_mapping is not None:
            datasource.enable_account_mapping = enable_account_mapping
        if status is not None:
            datasource.status = status

        db.add(datasource)
        db.commit()
        db.refresh(datasource)
        return datasource

    @staticmethod
    def delete_datasource(db: Session, datasource_id: int) -> bool:
        """删除数据源"""
        datasource = DataSourceService.get_datasource(db, datasource_id)
        if not datasource:
            return False
        db.delete(datasource)
        db.commit()
        return True

    @staticmethod
    def get_datasource_config(datasource: DataSource) -> Dict[str, Any]:
        """获取数据源连接配置"""
        config = {
            "host": datasource.host,
            "port": datasource.port,
            "database_name": datasource.database_name,
            "username": datasource.username,
        }
        if datasource.password_encrypted:
            config["password"] = decrypt_data(datasource.password_encrypted)
        return config

    @staticmethod
    def test_connection(
        datasource_type: str,
        host: str,
        port: int,
        database_name: Optional[str],
        username: str,
        password: Optional[str],
    ) -> Tuple[bool, str, Optional[str]]:
        """测试连接"""
        config = {
            "host": host,
            "port": port,
            "database_name": database_name,
            "username": username,
            "password": password,
        }
        manager = get_datasource_manager()
        return manager.test_connection(datasource_type, config)

    @staticmethod
    def get_tables(db: Session, datasource_id: int, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取表列表"""
        datasource = DataSourceService.get_datasource(db, datasource_id)
        if not datasource:
            raise ValueError("数据源不存在")

        config = DataSourceService.get_datasource_config(datasource)
        manager = get_datasource_manager()
        return manager.get_tables(datasource.datasource_type, config, schema)

    @staticmethod
    def get_schemas(db: Session, datasource_id: int) -> List[str]:
        """获取Schema列表"""
        datasource = DataSourceService.get_datasource(db, datasource_id)
        if not datasource:
            raise ValueError("数据源不存在")

        config = DataSourceService.get_datasource_config(datasource)
        manager = get_datasource_manager()
        return manager.get_schemas(datasource.datasource_type, config)

    @staticmethod
    def get_columns(db: Session, datasource_id: int, table: str, schema: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取字段列表"""
        datasource = DataSourceService.get_datasource(db, datasource_id)
        if not datasource:
            raise ValueError("数据源不存在")

        config = DataSourceService.get_datasource_config(datasource)
        manager = get_datasource_manager()
        return manager.get_columns(datasource.datasource_type, config, table, schema)

    @staticmethod
    def get_roles(db: Session, datasource_id: int) -> List[str]:
        """获取数据库角色列表"""
        datasource = DataSourceService.get_datasource(db, datasource_id)
        if not datasource:
            raise ValueError("数据源不存在")

        config = DataSourceService.get_datasource_config(datasource)
        manager = get_datasource_manager()
        return manager.get_roles(datasource.datasource_type, config)

    # ==================== 引用详情 ====================

    @staticmethod
    def get_references(db: Session, datasource_id: int) -> List[DataSourceReference]:
        """获取数据源引用"""
        stmt = select(DataSourceReference).where(DataSourceReference.datasource_id == datasource_id)
        return db.scalars(stmt).all()

    @staticmethod
    def add_reference(
        db: Session,
        datasource_id: int,
        reference_type: str,
        reference_id: str,
        reference_name: str,
    ) -> DataSourceReference:
        """添加数据源引用"""
        ref = DataSourceReference(
            datasource_id=datasource_id,
            reference_type=reference_type,
            reference_id=reference_id,
            reference_name=reference_name,
        )
        db.add(ref)
        db.commit()
        db.refresh(ref)
        return ref

    # ==================== 账号映射 ====================

    @staticmethod
    def get_account_mappings(db: Session, datasource_id: int) -> List[AccountMapping]:
        """获取账号映射列表"""
        stmt = select(AccountMapping).where(AccountMapping.datasource_id == datasource_id)
        return db.scalars(stmt).all()

    @staticmethod
    def create_account_mapping(
        db: Session,
        datasource_id: int,
        source_account: str,
        target_account: str,
    ) -> AccountMapping:
        """创建账号映射"""
        mapping = AccountMapping(
            datasource_id=datasource_id,
            source_account=source_account,
            target_account=target_account,
        )
        db.add(mapping)
        db.commit()
        db.refresh(mapping)
        return mapping

    @staticmethod
    def delete_account_mapping(db: Session, mapping_id: int) -> bool:
        """删除账号映射"""
        stmt = select(AccountMapping).where(AccountMapping.id == mapping_id)
        mapping = db.scalar(stmt)
        if not mapping:
            return False
        db.delete(mapping)
        db.commit()
        return True
