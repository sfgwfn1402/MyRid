# -*- coding: utf-8 -*-
"""
数据库配置文件
可在此统一管理数据库连接参数
"""

# MySQL数据库配置
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'luwang',
    'username': 'root',
    'password': '12345678',
    'charset': 'utf8mb4'
}

# 数据库连接URL (用于SQLAlchemy等ORM)
DATABASE_URL = "mysql+pymysql://{}:{}@{}:{}/{}?charset={}".format(
    DATABASE_CONFIG['username'],
    DATABASE_CONFIG['password'],
    DATABASE_CONFIG['host'],
    DATABASE_CONFIG['port'],
    DATABASE_CONFIG['database'],
    DATABASE_CONFIG['charset']
)

# 表名配置
TABLE_CONFIG = {
    'cross_info': 't_base_cross_info',
    'rid_info': 't_base_rid_info'
}

# 数据文件路径配置
DATA_CONFIG = {
    'cross_json': '../luwangJson/路口点.json',
    'rid_json': '../luwangJson/路段面.json'
}

def get_database_connection():
    """获取数据库连接"""
    import pymysql
    return pymysql.connect(
        host=DATABASE_CONFIG['host'],
        port=DATABASE_CONFIG['port'],
        user=DATABASE_CONFIG['username'],
        password=DATABASE_CONFIG['password'],
        database=DATABASE_CONFIG['database'],
        charset=DATABASE_CONFIG['charset']
    )