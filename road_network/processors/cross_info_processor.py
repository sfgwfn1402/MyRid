#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
路口基础信息处理器
从luwangJson/路口点.json文件中提取数据并导入到MySQL数据库的路口基础表中
"""

import json
import pymysql
from datetime import datetime
import logging
import sys
from imp import reload
reload(sys)
sys.setdefaultencoding('utf-8')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CrossInfoProcessor:
    """路口基础信息处理器"""
    
    def __init__(self, db_config):
        """
        初始化处理器
        
        Args:
            db_config: 数据库配置字典
        """
        self.db_config = db_config
        self.connection = None
        
    def connect_database(self):
        """
        连接数据库
        
        Returns:
            bool: 连接是否成功
        """
        try:
            self.connection = pymysql.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False
            )
            logger.info("数据库连接成功")
            return True
        except Exception as e:
            logger.error("数据库连接失败: {}".format(e))
            return False
    
    def create_table(self):
        """
        创建路口基础信息表
        
        Returns:
            bool: 表创建是否成功
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS t_base_cross_info (
            id CHAR(11) PRIMARY KEY COMMENT '路口ID',
            name VARCHAR(50) DEFAULT NULL COMMENT '路口名称',
            type INT(11) DEFAULT NULL COMMENT '路口类型：1丁字口；2十字口；3环岛；4畸形口；5立体交叉口；6铁路道口；7其他',
            level INT(11) DEFAULT NULL COMMENT '路口级别',
            area_code INT(6) DEFAULT NULL COMMENT '行政区划代码',
            is_signal INT(1) DEFAULT NULL COMMENT '是否信控路口：1是；0否',
            is_start INT(1) DEFAULT NULL COMMENT '是否启动优化：1是；0否',
            is_send INT(1) DEFAULT NULL COMMENT '是否下发方案：1是；0否',
            location VARCHAR(50) DEFAULT NULL COMMENT '路口位置',
            gmt_create DATETIME DEFAULT NULL COMMENT '创建时间',
            gmt_modified DATETIME DEFAULT NULL COMMENT '修改时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='路口基础信息表';
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_sql)
                self.connection.commit()
                logger.info("路口基础信息表创建成功")
                return True
        except Exception as e:
            logger.error("表创建失败: {}".format(e))
            self.connection.rollback()
            return False
    
    def load_json_data(self, file_path):
        """
        加载JSON数据文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            List[Dict]: 路口数据列表
        """
        try:
            import codecs
            with codecs.open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            logger.info("成功加载JSON文件: {}".format(file_path))
            return data.get('features', [])
        except Exception as e:
            logger.error("加载JSON文件失败: {}".format(e))
            return []
    
    def infer_cross_type(self, name):
        """
        根据路口名称推断路口类型
        
        Args:
            name: 路口名称
            
        Returns:
            int: 路口类型（1-7）
        """
        if not name:
            return 7  # 其他
            
        # 简单的规则推断，可以根据实际需求调整
        name_unicode = unicode(name, 'utf-8') if isinstance(name, str) else name
        if u"环岛" in name_unicode or u"转盘" in name_unicode:
            return 3  # 环岛
        elif u"立交" in name_unicode or u"高架" in name_unicode:
            return 5  # 立体交叉口
        elif u"铁路" in name_unicode or u"火车" in name_unicode:
            return 6  # 铁路道口
        else:
            # 默认为十字口，实际应该根据更复杂的规则判断
            return 2  # 十字口
    
    def infer_area_code(self, coordinates):
        """
        根据坐标推断行政区划代码
        
        Args:
            coordinates: [经度, 纬度]
            
        Returns:
            int: 行政区划代码
        """
        # 这里是示例，实际应该根据坐标查询对应的行政区划
        # 武汉市的行政区划代码示例
        return 420100  # 武汉市市辖区
    
    def process_feature_to_record(self, feature):
        """
        将GeoJSON特征转换为数据库记录
        
        Args:
            feature: GeoJSON特征对象
            
        Returns:
            Dict: 数据库记录
        """
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        coordinates = geometry.get('coordinates', [0, 0])
        
        current_time = datetime.now()
        
        # 构建数据库记录
        record = {
            'id': properties.get('lkid', ''),
            'name': properties.get('lkmc', ''),
            'type': self.infer_cross_type(properties.get('lkmc', '')),
            'level': 1,  # 默认级别，可以根据需求调整
            'area_code': self.infer_area_code(coordinates),
            'is_signal': 0,  # 默认非信控路口
            'is_start': 0,   # 默认未启动优化
            'is_send': 0,    # 默认未下发方案
            'location': "经度:{:.6f}, 纬度:{:.6f}".format(coordinates[0], coordinates[1]),
            'gmt_create': current_time,
            'gmt_modified': current_time
        }
        
        return record
    
    def insert_records(self, records):
        """
        批量插入记录到数据库
        
        Args:
            records: 数据库记录列表
            
        Returns:
            bool: 插入是否成功
        """
        if not records:
            logger.warning("没有要插入的记录")
            return False
        
        insert_sql = """
        INSERT INTO t_base_cross_info 
        (id, name, type, level, area_code, is_signal, is_start, is_send, location, gmt_create, gmt_modified)
        VALUES (%(id)s, %(name)s, %(type)s, %(level)s, %(area_code)s, %(is_signal)s, %(is_start)s, %(is_send)s, %(location)s, %(gmt_create)s, %(gmt_modified)s)
        ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        type = VALUES(type),
        level = VALUES(level),
        area_code = VALUES(area_code),
        location = VALUES(location),
        gmt_modified = VALUES(gmt_modified)
        """
        
        try:
            with self.connection.cursor() as cursor:
                # 批量插入
                cursor.executemany(insert_sql, records)
                self.connection.commit()
                
                logger.info("成功插入 {} 条记录".format(len(records)))
                return True
        except Exception as e:
            logger.error("插入记录失败: {}".format(e))
            self.connection.rollback()
            return False
    
    def process_all(self, json_file_path):
        """
        处理所有数据：加载JSON -> 转换 -> 插入数据库
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            bool: 处理是否成功
        """
        logger.info("开始处理路口基础信息数据...")
        
        # 1. 连接数据库
        if not self.connect_database():
            return False
        
        # 2. 创建表
        if not self.create_table():
            return False
        
        # 3. 加载JSON数据
        features = self.load_json_data(json_file_path)
        if not features:
            logger.error("未加载到任何数据")
            return False
        
        # 4. 转换数据
        records = []
        for feature in features:
            record = self.process_feature_to_record(feature)
            if record['id']:  # 只处理有ID的记录
                records.append(record)
        
        logger.info("转换了 {} 条记录".format(len(records)))
        
        # 5. 插入数据库
        success = self.insert_records(records)
        
        # 6. 关闭连接
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")
        
        return success
    
    def query_statistics(self):
        """
        查询统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.connection:
            if not self.connect_database():
                return {}
        
        try:
            with self.connection.cursor() as cursor:
                # 总记录数
                cursor.execute("SELECT COUNT(*) as total FROM t_base_cross_info")
                total = cursor.fetchone()['total']
                
                # 按类型统计
                cursor.execute("""
                    SELECT type, COUNT(*) as count 
                    FROM t_base_cross_info 
                    GROUP BY type 
                    ORDER BY type
                """)
                type_stats = cursor.fetchall()
                
                # 按区域统计
                cursor.execute("""
                    SELECT area_code, COUNT(*) as count 
                    FROM t_base_cross_info 
                    GROUP BY area_code 
                    ORDER BY count DESC
                """)
                area_stats = cursor.fetchall()
                
                return {
                    'total': total,
                    'type_stats': type_stats,
                    'area_stats': area_stats
                }
        except Exception as e:
            logger.error("查询统计信息失败: {}".format(e))
            return {}

def main():
    """主函数"""
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '12345678',
        'database': 'luwang'
    }
    
    # JSON文件路径
    json_file_path = 'luwangJson/路口点.json'
    
    # 创建处理器
    processor = CrossInfoProcessor(db_config)
    
    # 处理数据
    if processor.process_all(json_file_path):
        logger.info("数据处理完成！")
        
        # 查询统计信息
        stats = processor.query_statistics()
        if stats:
            print("\n=== 导入统计信息 ===")
            print("总记录数: {}".format(stats['total']))
            
            print("\n路口类型统计:")
            type_names = {
                1: "丁字口", 2: "十字口", 3: "环岛", 4: "畸形口", 
                5: "立体交叉口", 6: "铁路道口", 7: "其他"
            }
            for stat in stats['type_stats']:
                type_name = type_names.get(stat['type'], "类型{}".format(stat['type']))
                print("  {}: {}个".format(type_name, stat['count']))
            
            print("\n区域统计:")
            for stat in stats['area_stats'][:5]:  # 显示前5个
                print("  区域代码{}: {}个".format(stat['area_code'], stat['count']))
    else:
        logger.error("数据处理失败！")

if __name__ == "__main__":
    main() 