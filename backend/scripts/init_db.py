"""
数据库初始化脚本
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base, SessionLocal
from app.models import *
from app.services.auth_service import AuthService


def init_database():
    """初始化数据库"""
    print("正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库表创建完成！")

    print("\n正在初始化默认数据...")
    db = SessionLocal()
    try:
        AuthService.init_default_data(db)
        print("默认数据初始化完成！")
        print("\n默认登录账号:")
        print("  用户名: admin")
        print("  密码: admin123")
    except Exception as e:
        print(f"初始化默认数据失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
