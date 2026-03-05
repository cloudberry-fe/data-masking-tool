"""
血缘分析服务
"""
import logging
from typing import Optional, List, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.models.lineage import DataLineage
from app.models.datasource import DataSource
from app.services.datasource_service import DataSourceService
from app.utils.datasource_manager import get_datasource_manager
from app.utils.sql_parser import SQLParser

logger = logging.getLogger(__name__)


class LineageService:
    """血缘分析服务"""

    @staticmethod
    def get_lineage_graph(
        db: Session,
        datasource_id: Optional[int] = None,
        node_name: Optional[str] = None,
        depth: int = 3,
        direction: str = "BOTH"
    ) -> Dict[str, Any]:
        """
        获取血缘图谱

        Args:
            db: 数据库会话
            datasource_id: 数据源ID
            node_name: 起始节点名称
            depth: 查询深度
            direction: 方向 UPSTREAM/DOWNSTREAM/BOTH

        Returns:
            图谱数据 {nodes: [], edges: []}
        """
        query = select(DataLineage)

        if datasource_id:
            query = query.where(DataLineage.datasource_id == datasource_id)

        lineages = db.scalars(query).all()

        if not lineages:
            return {"nodes": [], "edges": []}

        # 构建节点和边
        nodes = {}
        edges = []

        for lineage in lineages:
            source_key = f"{lineage.datasource_id}:{lineage.source_node}"
            target_key = f"{lineage.datasource_id}:{lineage.target_node}"

            if source_key not in nodes:
                nodes[source_key] = {
                    "id": source_key,
                    "name": lineage.source_node,
                    "type": "TABLE",
                    "datasource_id": lineage.datasource_id
                }

            if target_key not in nodes:
                nodes[target_key] = {
                    "id": target_key,
                    "name": lineage.target_node,
                    "type": "TABLE",
                    "datasource_id": lineage.datasource_id
                }

            edges.append({
                "id": f"edge_{lineage.id}",
                "source": source_key,
                "target": target_key,
                "type": lineage.relation_type or "TRANSFORM",
                "transform_logic": lineage.transform_logic
            })

        # 如果指定了起始节点，进行过滤
        if node_name:
            nodes, edges = LineageService._filter_by_node(
                list(nodes.values()),
                edges,
                node_name,
                depth,
                direction
            )
        else:
            nodes = list(nodes.values())

        return {"nodes": nodes, "edges": edges}

    @staticmethod
    def _filter_by_node(
        all_nodes: List[Dict],
        all_edges: List[Dict],
        node_name: str,
        depth: int,
        direction: str
    ) -> tuple:
        """根据起始节点过滤图谱"""
        # 构建邻接表
        forward_adj = {}  # 正向：source -> targets
        backward_adj = {}  # 反向：target -> sources

        for edge in all_edges:
            source = edge["source"]
            target = edge["target"]

            if source not in forward_adj:
                forward_adj[source] = []
            forward_adj[source].append(target)

            if target not in backward_adj:
                backward_adj[target] = []
            backward_adj[target].append(source)

        # 找到起始节点
        start_nodes = [n for n in all_nodes if node_name.lower() in n["name"].lower()]
        if not start_nodes:
            return [], []

        # BFS遍历
        visited_nodes = set()
        visited_edges = []
        queue = []

        for node in start_nodes:
            queue.append((node["id"], 0))
            visited_nodes.add(node["id"])

        while queue:
            current_id, current_depth = queue.pop(0)

            if current_depth >= depth:
                continue

            # 下游
            if direction in ("BOTH", "DOWNSTREAM"):
                for next_id in forward_adj.get(current_id, []):
                    if next_id not in visited_nodes:
                        visited_nodes.add(next_id)
                        queue.append((next_id, current_depth + 1))

            # 上游
            if direction in ("BOTH", "UPSTREAM"):
                for prev_id in backward_adj.get(current_id, []):
                    if prev_id not in visited_nodes:
                        visited_nodes.add(prev_id)
                        queue.append((prev_id, current_depth + 1))

        # 过滤边
        for edge in all_edges:
            if edge["source"] in visited_nodes and edge["target"] in visited_nodes:
                visited_edges.append(edge)

        # 过滤节点
        nodes = [n for n in all_nodes if n["id"] in visited_nodes]

        return nodes, visited_edges

    @staticmethod
    def scan_datasource(db: Session, datasource_id: int) -> Dict[str, Any]:
        """
        扫描数据源，自动提取血缘关系

        Args:
            db: 数据库会话
            datasource_id: 数据源ID

        Returns:
            扫描结果
        """
        datasource = DataSourceService.get_datasource(db, datasource_id)
        if not datasource:
            raise ValueError("数据源不存在")

        config = DataSourceService.get_datasource_config(datasource)
        manager = get_datasource_manager()
        connector = manager.get_connector(datasource.datasource_type)

        relations = []
        errors = []

        try:
            # 1. 查询视图定义
            if datasource.datasource_type.upper() in ("MPP", "POSTGRESQL"):
                view_sql = """
                    SELECT
                        schemaname,
                        viewname,
                        definition
                    FROM pg_views
                    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                """
            elif datasource.datasource_type.upper() in ("MYSQL", "GOLDENDB"):
                view_sql = """
                    SELECT
                        TABLE_SCHEMA as schemaname,
                        TABLE_NAME as viewname,
                        VIEW_DEFINITION as definition
                    FROM information_schema.VIEWS
                    WHERE TABLE_SCHEMA = DATABASE()
                """
            else:
                view_sql = None

            if view_sql:
                try:
                    views = connector.execute_sql(config, view_sql)
                    for view in views:
                        view_name = view.get("viewname", "")
                        definition = view.get("definition", "")
                        schema = view.get("schemaname", "")

                        if definition:
                            # 解析视图定义
                            tables = SQLParser.extract_tables(definition)
                            for table in tables:
                                # 构建完整的表名
                                if '.' not in table and schema:
                                    full_table = f"{schema}.{table}"
                                else:
                                    full_table = table

                                # 构建视图的完整名称
                                if schema:
                                    full_view = f"{schema}.{view_name}"
                                else:
                                    full_view = view_name

                                relations.append({
                                    "source_node": full_table,
                                    "target_node": full_view,
                                    "relation_type": "VIEW",
                                    "transform_logic": f"View definition references {table}"
                                })
                except Exception as e:
                    errors.append(f"查询视图定义失败: {str(e)}")

            # 2. 查询外键关系
            if datasource.datasource_type.upper() in ("MPP", "POSTGRESQL"):
                fk_sql = """
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name,
                        tc.constraint_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                """
            elif datasource.datasource_type.upper() in ("MYSQL", "GOLDENDB"):
                fk_sql = """
                    SELECT
                        TABLE_NAME as table_name,
                        COLUMN_NAME as column_name,
                        REFERENCED_TABLE_NAME as foreign_table_name,
                        REFERENCED_COLUMN_NAME as foreign_column_name,
                        CONSTRAINT_NAME as constraint_name
                    FROM information_schema.KEY_COLUMN_USAGE
                    WHERE REFERENCED_TABLE_NAME IS NOT NULL
                    AND TABLE_SCHEMA = DATABASE()
                """
            else:
                fk_sql = None

            if fk_sql:
                try:
                    fks = connector.execute_sql(config, fk_sql)
                    for fk in fks:
                        relations.append({
                            "source_node": fk.get("foreign_table_name", ""),
                            "target_node": fk.get("table_name", ""),
                            "relation_type": "FOREIGN_KEY",
                            "transform_logic": f"FK: {fk.get('column_name', '')} -> {fk.get('foreign_column_name', '')}"
                        })
                except Exception as e:
                    errors.append(f"查询外键关系失败: {str(e)}")

            # 3. 保存到数据库
            saved_count = 0
            for rel in relations:
                if not rel["source_node"] or not rel["target_node"]:
                    continue

                # 检查是否已存在
                existing = db.scalar(
                    select(DataLineage).where(
                        DataLineage.datasource_id == datasource_id,
                        DataLineage.source_node == rel["source_node"],
                        DataLineage.target_node == rel["target_node"],
                        DataLineage.relation_type == rel["relation_type"]
                    )
                )

                if not existing:
                    lineage = DataLineage(
                        datasource_id=datasource_id,
                        lineage_type="AUTO",
                        source_node=rel["source_node"],
                        target_node=rel["target_node"],
                        relation_type=rel["relation_type"],
                        transform_logic=rel["transform_logic"]
                    )
                    db.add(lineage)
                    saved_count += 1

            db.commit()

            return {
                "success": True,
                "relations_found": len(relations),
                "relations_saved": saved_count,
                "errors": errors
            }

        except Exception as e:
            logger.exception("扫描数据源失败")
            return {
                "success": False,
                "relations_found": 0,
                "relations_saved": 0,
                "errors": [str(e)]
            }

    @staticmethod
    def add_relation(
        db: Session,
        datasource_id: int,
        source_node: str,
        target_node: str,
        relation_type: str = "TRANSFORM",
        transform_logic: Optional[str] = None
    ) -> DataLineage:
        """
        手动添加血缘关系

        Args:
            db: 数据库会话
            datasource_id: 数据源ID
            source_node: 源节点
            target_node: 目标节点
            relation_type: 关系类型
            transform_logic: 转换逻辑

        Returns:
            创建的血缘关系
        """
        lineage = DataLineage(
            datasource_id=datasource_id,
            lineage_type="MANUAL",
            source_node=source_node,
            target_node=target_node,
            relation_type=relation_type,
            transform_logic=transform_logic
        )
        db.add(lineage)
        db.commit()
        db.refresh(lineage)
        return lineage

    @staticmethod
    def delete_relation(db: Session, lineage_id: int) -> bool:
        """
        删除血缘关系

        Args:
            db: 数据库会话
            lineage_id: 血缘ID

        Returns:
            是否成功
        """
        lineage = db.scalar(select(DataLineage).where(DataLineage.id == lineage_id))
        if lineage:
            db.delete(lineage)
            db.commit()
            return True
        return False

    @staticmethod
    def analyze_impact(
        db: Session,
        datasource_id: int,
        node_name: str,
        depth: int = 3
    ) -> Dict[str, Any]:
        """
        影响分析 - 查找所有下游节点

        Args:
            db: 数据库会话
            datasource_id: 数据源ID
            node_name: 节点名称
            depth: 查询深度

        Returns:
            影响分析结果
        """
        return LineageService.get_lineage_graph(
            db, datasource_id, node_name, depth, "DOWNSTREAM"
        )

    @staticmethod
    def analyze_source(
        db: Session,
        datasource_id: int,
        node_name: str,
        depth: int = 3
    ) -> Dict[str, Any]:
        """
        来源分析 - 查找所有上游节点

        Args:
            db: 数据库会话
            datasource_id: 数据源ID
            node_name: 节点名称
            depth: 查询深度

        Returns:
            来源分析结果
        """
        return LineageService.get_lineage_graph(
            db, datasource_id, node_name, depth, "UPSTREAM"
        )

    @staticmethod
    def clear_lineages(db: Session, datasource_id: int) -> int:
        """
        清除数据源的所有血缘关系

        Args:
            db: 数据库会话
            datasource_id: 数据源ID

        Returns:
            删除的数量
        """
        result = db.execute(
            delete(DataLineage).where(DataLineage.datasource_id == datasource_id)
        )
        db.commit()
        return result.rowcount
