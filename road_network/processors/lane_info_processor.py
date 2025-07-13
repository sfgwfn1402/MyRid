# -*- coding: utf-8 -*-
"""
车道基础信息处理器
处理luwangJson/车道.json文件，将车道信息导入到MySQL数据库t_base_lane_info表中
"""

import json
import pymysql
from datetime import datetime
import codecs

class LaneInfoProcessor:
    def __init__(self, db_config):
        """
        初始化车道信息处理器
        
        Args:
            db_config: 数据库配置字典
        """
        self.db_config = db_config
        self.connection = None
        
    def connect_database(self):
        """连接数据库"""
        try:
            self.connection = pymysql.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['username'],
                password=self.db_config['password'],
                database=self.db_config['database'],
                charset='utf8mb4'
            )
            print("数据库连接成功")
        except Exception as e:
            print("数据库连接失败: {}".format(e))
            raise
    
    def create_table(self):
        """创建车道基础信息表"""
        create_sql = """
        CREATE TABLE IF NOT EXISTS t_base_lane_info (
            id CHAR(28) NOT NULL PRIMARY KEY COMMENT '车道编号（渠化编号-车道序号）',
            code VARCHAR(28) NOT NULL COMMENT '车道代码',
            sort INT(11) NOT NULL COMMENT '车道序号，从左车道开始编号11,12,13...',
            type INT(11) NOT NULL COMMENT '车道类型：1路段车道，2进口车道，3出口车道，4左转弯待转区，6直行待行区',
            dir INT(11) DEFAULT 1 COMMENT '车道方向：1北，2东北，3东，4东南，5南，6西南，7西，8西北',
            turn INT(11) NOT NULL COMMENT '车道转向：1左转，2直行，3右转，4掉头，5直左，6直右，7左直右，8左右，9左转掉头，10直行掉头，11右转掉头，12左直掉头，13直右掉头，14左直右掉头，15左右掉头',
            category INT(11) NOT NULL COMMENT '车道类别：1机动车，2非机动车，3公交专用，4可变，5潮汐',
            cross_id CHAR(11) DEFAULT '' COMMENT '路口ID',
            rid CHAR(23) DEFAULT '' COMMENT '路段编号',
            segment_id CHAR(26) NOT NULL COMMENT '渠化编号',
            length DOUBLE DEFAULT 0 COMMENT '车道长度',
            width DOUBLE DEFAULT 0 COMMENT '车道宽度',
            wkt TEXT COMMENT '空间对象',
            gmt_create DATETIME NOT NULL COMMENT '创建时间',
            gmt_modified DATETIME NOT NULL COMMENT '修改时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='车道基础信息表';
        """
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(create_sql)
            self.connection.commit()
            print("车道基础信息表创建成功")
        except Exception as e:
            print("创建表失败: {}".format(e))
            raise
        finally:
            cursor.close()
    
    def infer_turn_direction(self, lane_type, lane_function, allowed_vehicles):
        """
        推断车道转向
        
        Args:
            lane_type: 车道类型
            lane_function: 车道功能
            allowed_vehicles: 允许车辆类型
            
        Returns:
            int: 转向编码
        """
        # 默认直行
        turn_direction = 2
        
        # 根据车道类型推断
        if lane_type == 4:  # 左转弯待转区
            turn_direction = 1  # 左转
        elif lane_type == 6:  # 直行待行区
            turn_direction = 2  # 直行
        elif lane_type == 3:  # 出口车道
            turn_direction = 3  # 右转（出口通常是右转）
        
        return turn_direction
    
    def infer_category(self, lane_function, allowed_vehicles):
        """
        推断车道类别
        
        Args:
            lane_function: 车道功能
            allowed_vehicles: 允许车辆类型
            
        Returns:
            int: 类别编码
        """
        # 根据允许车辆类型推断
        if allowed_vehicles == u"机动车":
            return 1  # 机动车
        elif allowed_vehicles == u"非机动车":
            return 2  # 非机动车
        elif u"公交" in allowed_vehicles:
            return 3  # 公交专用
        else:
            return 1  # 默认机动车
    
    def extract_cross_id(self, segment_id, rid):
        """
        从渠化段编号或路段编号提取路口ID
        
        Args:
            segment_id: 渠化段编号
            rid: 路段编号
            
        Returns:
            str: 路口ID
        """
        # 优先从渠化段编号提取
        if segment_id and len(segment_id) >= 11:
            return segment_id[:11]
        
        # 从路段编号提取
        if rid and len(rid) >= 11:
            return rid[:11]
        
        return ""
    
    def geometry_to_wkt(self, geometry):
        """
        将GeoJSON几何对象转换为WKT格式
        
        Args:
            geometry: GeoJSON几何对象
            
        Returns:
            str: WKT格式字符串
        """
        if not geometry or geometry.get('type') != 'MultiPolygon':
            return ""
        
        coordinates = geometry.get('coordinates', [])
        if not coordinates:
            return ""
        
        # 构建WKT字符串
        polygon_parts = []
        
        for polygon in coordinates:
            rings = []
            for ring in polygon:
                points = []
                for point in ring:
                    if len(point) >= 2:
                        points.append("{} {}".format(point[0], point[1]))
                
                if points:
                    rings.append("({})".format(','.join(points)))
            
            if rings:
                polygon_parts.append("({})".format(','.join(rings)))
        
        if polygon_parts:
            return "MULTIPOLYGON({})".format(','.join(polygon_parts))
        
        return ""
    
    def process_lane_data(self, json_file_path):
        """
        处理车道数据
        
        Args:
            json_file_path: JSON文件路径
        """
        cursor = None
        try:
            # 读取JSON文件 - 使用codecs.open支持UTF-8编码
            with codecs.open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            features = data.get('features', [])
            print("共找到 {} 条车道记录".format(len(features)))
            
            # 插入数据的SQL语句
            insert_sql = """
            INSERT INTO t_base_lane_info (
                id, code, sort, type, dir, turn, category, cross_id, rid, segment_id,
                length, width, wkt, gmt_create, gmt_modified
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            """
            
            cursor = self.connection.cursor()
            successful_count = 0
            
            current_time = datetime.now()
            
            for feature in features:
                try:
                    properties = feature.get('properties', {})
                    geometry = feature.get('geometry', {})
                    
                    # 提取基本信息
                    lane_id = properties.get('cdid', '')
                    lane_code = properties.get('cdid', '')
                    lane_sort = int(properties.get('cdsxh', 11))
                    lane_type = int(properties.get('cdlb', 1))
                    lane_dir = int(properties.get('cdfx', 1))
                    lane_function = int(properties.get('cdgn', 1))
                    rid = properties.get('ldid', '')
                    segment_id = properties.get('qhdid', '')
                    lane_length = float(properties.get('cdcd', 0))
                    lane_width = float(properties.get('cdkd', 3.5))
                    allowed_vehicles = properties.get('yxcllx', u'机动车')
                    
                    # 推断转向和类别
                    turn_direction = self.infer_turn_direction(lane_type, lane_function, allowed_vehicles)
                    category = self.infer_category(lane_function, allowed_vehicles)
                    
                    # 提取路口ID
                    cross_id = self.extract_cross_id(segment_id, rid)
                    
                    # 转换几何数据
                    wkt = self.geometry_to_wkt(geometry)
                    
                    # 插入数据
                    cursor.execute(insert_sql, (
                        lane_id, lane_code, lane_sort, lane_type, lane_dir,
                        turn_direction, category, cross_id, rid, segment_id,
                        lane_length, lane_width, wkt, current_time, current_time
                    ))
                    
                    successful_count += 1
                    
                    if successful_count % 100 == 0:
                        print("已处理 {} 条车道记录".format(successful_count))
                        
                except Exception as e:
                    print("处理车道记录失败: {}".format(e))
                    print("车道ID: {}".format(properties.get('cdid', 'unknown')))
                    continue
            
            # 提交事务
            self.connection.commit()
            print("车道数据处理完成！成功导入 {} 条记录".format(successful_count))
            
        except Exception as e:
            print("处理车道数据失败: {}".format(e))
            if self.connection:
                self.connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
    
    def get_statistics(self):
        """获取车道统计信息"""
        try:
            cursor = self.connection.cursor()
            
            # 基本统计
            cursor.execute("SELECT COUNT(*) FROM t_base_lane_info")
            total_count = cursor.fetchone()[0]
            
            # 按类型统计
            cursor.execute("""
                SELECT type, COUNT(*) as count 
                FROM t_base_lane_info 
                GROUP BY type 
                ORDER BY type
            """)
            type_stats = cursor.fetchall()
            
            # 按方向统计
            cursor.execute("""
                SELECT dir, COUNT(*) as count 
                FROM t_base_lane_info 
                GROUP BY dir 
                ORDER BY dir
            """)
            dir_stats = cursor.fetchall()
            
            # 按转向统计
            cursor.execute("""
                SELECT turn, COUNT(*) as count 
                FROM t_base_lane_info 
                GROUP BY turn 
                ORDER BY turn
            """)
            turn_stats = cursor.fetchall()
            
            # 按类别统计
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM t_base_lane_info 
                GROUP BY category 
                ORDER BY category
            """)
            category_stats = cursor.fetchall()
            
            print("\n=== 车道统计信息 ===")
            print("总车道数: {}".format(total_count))
            
            print("\n按类型统计:")
            type_names = {1: '路段车道', 2: '进口车道', 3: '出口车道', 4: '左转弯待转区', 6: '直行待行区'}
            for type_id, count in type_stats:
                type_name = type_names.get(type_id, '未知类型{}'.format(type_id))
                print("  {}: {}".format(type_name, count))
            
            print("\n按方向统计:")
            dir_names = {1: '北', 2: '东北', 3: '东', 4: '东南', 5: '南', 6: '西南', 7: '西', 8: '西北'}
            for dir_id, count in dir_stats:
                dir_name = dir_names.get(dir_id, '未知方向{}'.format(dir_id))
                print("  {}: {}".format(dir_name, count))
            
            print("\n按转向统计:")
            turn_names = {1: '左转', 2: '直行', 3: '右转', 4: '掉头', 5: '直左', 6: '直右', 7: '左直右', 8: '左右'}
            for turn_id, count in turn_stats:
                turn_name = turn_names.get(turn_id, '未知转向{}'.format(turn_id))
                print("  {}: {}".format(turn_name, count))
            
            print("\n按类别统计:")
            category_names = {1: '机动车', 2: '非机动车', 3: '公交专用', 4: '可变', 5: '潮汐'}
            for category_id, count in category_stats:
                category_name = category_names.get(category_id, '未知类别{}'.format(category_id))
                print("  {}: {}".format(category_name, count))
            
        except Exception as e:
            print("获取统计信息失败: {}".format(e))
        finally:
            cursor.close()
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            print("数据库连接已关闭")

def main():
    """主函数"""
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'database': 'luwang',
        'username': 'root',
        'password': '12345678'
    }
    
    # JSON文件路径
    json_file_path = '../../luwangJson/车道.json'
    
    # 创建处理器实例
    processor = LaneInfoProcessor(db_config)
    
    try:
        # 连接数据库
        processor.connect_database()
        
        # 创建表
        processor.create_table()
        
        # 处理车道数据
        processor.process_lane_data(json_file_path)
        
        # 获取统计信息
        processor.get_statistics()
        
    except Exception as e:
        print("程序执行失败: {}".format(e))
    finally:
        # 关闭连接
        processor.close_connection()

if __name__ == "__main__":
    main() 