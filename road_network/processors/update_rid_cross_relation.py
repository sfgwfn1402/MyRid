#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
更新路段基础信息表的路口关联和方向信息
"""

import json
import pymysql
import math
import logging
import sys
from imp import reload
reload(sys)
sys.setdefaultencoding('utf-8')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RidCrossUpdater:
    """路段路口关联更新器"""
    
    def __init__(self, db_config):
        """
        初始化更新器
        
        Args:
            db_config: 数据库配置字典
        """
        self.db_config = db_config
        self.connection = None
        self.cross_mapping = {}  # 路口名称到ID的映射
        
    def connect_database(self):
        """连接数据库"""
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
    
    def load_cross_mapping(self):
        """加载路口名称到ID的映射"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT id, name FROM t_base_cross_info")
                crosses = cursor.fetchall()
                
                for cross in crosses:
                    self.cross_mapping[cross['name']] = cross['id']
                
                logger.info("加载了 {} 个路口映射".format(len(self.cross_mapping)))
                return True
        except Exception as e:
            logger.error("加载路口映射失败: {}".format(e))
            return False
    
    def find_cross_id_by_roads(self, road1, road2):
        """
        根据两条道路名称查找路口ID
        
        Args:
            road1: 道路1名称
            road2: 道路2名称
            
        Returns:
            str: 路口ID，如果未找到返回None
        """
        # 尝试不同的匹配模式
        patterns = [
            "{}与{}交叉口".format(road1, road2),
            "{}与{}交叉口".format(road2, road1),
            "{}-{}交叉口".format(road1, road2),
            "{}-{}交叉口".format(road2, road1)
        ]
        
        for pattern in patterns:
            if pattern in self.cross_mapping:
                return self.cross_mapping[pattern]
        
        # 模糊匹配
        for cross_name, cross_id in self.cross_mapping.items():
            if road1 in cross_name and road2 in cross_name:
                return cross_id
        
        return None
    
    def calculate_direction_from_angle(self, angle):
        """
        根据角度计算方向编码
        
        Args:
            angle: 角度（0-359度，正北为0）
            
        Returns:
            int: 方向编码（1-8）
        """
        # 将角度标准化到0-360范围
        angle = angle % 360
        
        # 8个方向的角度范围（每个方向45度）
        if 337.5 <= angle or angle < 22.5:
            return 1  # 北
        elif 22.5 <= angle < 67.5:
            return 2  # 东北
        elif 67.5 <= angle < 112.5:
            return 3  # 东
        elif 112.5 <= angle < 157.5:
            return 4  # 东南
        elif 157.5 <= angle < 202.5:
            return 5  # 南
        elif 202.5 <= angle < 247.5:
            return 6  # 西南
        elif 247.5 <= angle < 292.5:
            return 7  # 西
        elif 292.5 <= angle < 337.5:
            return 8  # 西北
        else:
            return 1  # 默认北
    
    def calculate_angle_from_coordinates(self, start_coord, end_coord):
        """
        根据起终点坐标计算角度
        
        Args:
            start_coord: 起点坐标 [lon, lat]
            end_coord: 终点坐标 [lon, lat]
            
        Returns:
            float: 角度（0-359度，正北为0）
        """
        if not start_coord or not end_coord:
            return 0.0
        
        # 计算坐标差
        dx = end_coord[0] - start_coord[0]  # 经度差
        dy = end_coord[1] - start_coord[1]  # 纬度差
        
        # 计算弧度角
        angle_rad = math.atan2(dx, dy)
        
        # 转换为度数（正北为0度）
        angle_deg = math.degrees(angle_rad)
        
        # 确保角度在0-360范围内
        if angle_deg < 0:
            angle_deg += 360
        
        return angle_deg
    
    def get_polygon_center_points(self, wkt):
        """
        从WKT多边形中提取起终点坐标
        
        Args:
            wkt: WKT格式的多边形字符串
            
        Returns:
            tuple: (start_coord, end_coord)
        """
        if not wkt or not wkt.startswith('POLYGON'):
            return None, None
        
        try:
            # 提取坐标点
            coords_str = wkt.replace('POLYGON((', '').replace(')...', '').replace('))', '')
            if coords_str.endswith('...'):
                coords_str = coords_str[:-3]
            
            points = []
            for point_str in coords_str.split(', '):
                if point_str.strip():
                    coords = point_str.strip().split(' ')
                    if len(coords) >= 2:
                        points.append([float(coords[0]), float(coords[1])])
            
            if len(points) >= 2:
                # 返回第一个和中间的点作为起终点
                start_point = points[0]
                end_point = points[len(points)//2] if len(points) > 2 else points[-1]
                return start_point, end_point
            
        except Exception as e:
            logger.warning("解析WKT坐标失败: {}".format(e))
        
        return None, None
    
    def update_rid_cross_relations(self):
        """更新路段的路口关联和方向信息"""
        try:
            with self.connection.cursor() as cursor:
                # 获取所有路段记录
                cursor.execute("SELECT id, name, wkt FROM t_base_rid_info")
                rids = cursor.fetchall()
                
                updated_count = 0
                
                for rid in rids:
                    rid_id = rid['id']
                    rid_name = rid['name']
                    wkt = rid['wkt']
                    
                    if not rid_name:
                        continue
                    
                    # 解析路段名称获取道路信息
                    roads = rid_name.split('-')
                    if len(roads) < 2:
                        continue
                    
                    start_cross_id = None
                    end_cross_id = None
                    
                    # 查找起点路口
                    if len(roads) >= 2:
                        start_cross_id = self.find_cross_id_by_roads(roads[0], roads[1])
                    
                    # 查找终点路口  
                    if len(roads) >= 3:
                        end_cross_id = self.find_cross_id_by_roads(roads[1], roads[2])
                    elif len(roads) == 2:
                        # 如果只有两条道路，终点路口与起点路口相同
                        end_cross_id = start_cross_id
                    
                    # 从WKT中提取起终点坐标
                    start_coord, end_coord = self.get_polygon_center_points(wkt)
                    
                    # 计算角度和方向
                    start_angle = 0.0
                    end_angle = 0.0
                    out_dir = 1
                    in_dir = 1
                    
                    if start_coord and end_coord:
                        start_angle = self.calculate_angle_from_coordinates(start_coord, end_coord)
                        end_angle = (start_angle + 180) % 360  # 终点角度是起点角度的反向
                        
                        out_dir = self.calculate_direction_from_angle(start_angle)
                        in_dir = self.calculate_direction_from_angle(end_angle)
                    
                    # 更新数据库记录
                    update_sql = """
                    UPDATE t_base_rid_info 
                    SET start_cross_id = %s,
                        end_cross_id = %s,
                        out_dir = %s,
                        in_dir = %s,
                        start_angle = %s,
                        end_angle = %s,
                        gmt_modified = NOW()
                    WHERE id = %s
                    """
                    
                    cursor.execute(update_sql, (
                        start_cross_id, end_cross_id, out_dir, in_dir,
                        start_angle, end_angle, rid_id
                    ))
                    
                    updated_count += 1
                    
                    logger.info("更新路段 {}: 起点路口={}, 终点路口={}, 驶出方向={}, 驶入方向={}".format(
                        rid_id[:15], start_cross_id, end_cross_id, out_dir, in_dir
                    ))
                
                self.connection.commit()
                logger.info("成功更新 {} 条路段记录".format(updated_count))
                return True
                
        except Exception as e:
            logger.error("更新路段关联失败: {}".format(e))
            self.connection.rollback()
            return False
    
    def query_update_statistics(self):
        """查询更新后的统计信息"""
        try:
            with self.connection.cursor() as cursor:
                # 统计有路口关联的记录数
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(start_cross_id) as has_start_cross,
                        COUNT(end_cross_id) as has_end_cross
                    FROM t_base_rid_info
                """)
                cross_stats = cursor.fetchone()
                
                # 统计方向分布
                cursor.execute("""
                    SELECT out_dir, COUNT(*) as count 
                    FROM t_base_rid_info 
                    GROUP BY out_dir 
                    ORDER BY out_dir
                """)
                out_dir_stats = cursor.fetchall()
                
                cursor.execute("""
                    SELECT in_dir, COUNT(*) as count 
                    FROM t_base_rid_info 
                    GROUP BY in_dir 
                    ORDER BY in_dir
                """)
                in_dir_stats = cursor.fetchall()
                
                return {
                    'cross_stats': cross_stats,
                    'out_dir_stats': out_dir_stats,
                    'in_dir_stats': in_dir_stats
                }
        except Exception as e:
            logger.error("查询统计信息失败: {}".format(e))
            return {}
    
    def process_all(self):
        """执行完整的更新流程"""
        logger.info("开始更新路段路口关联和方向信息...")
        
        # 1. 连接数据库
        if not self.connect_database():
            return False
        
        # 2. 加载路口映射
        if not self.load_cross_mapping():
            return False
        
        # 3. 更新路段关联
        if not self.update_rid_cross_relations():
            return False
        
        # 4. 查询统计信息
        stats = self.query_update_statistics()
        if stats:
            print("\n=== 更新统计信息 ===")
            cross_stats = stats['cross_stats']
            print("总路段数: {}".format(cross_stats['total']))
            print("有起点路口的路段: {}".format(cross_stats['has_start_cross']))
            print("有终点路口的路段: {}".format(cross_stats['has_end_cross']))
            
            print("\n驶出方向统计:")
            direction_names = {
                1: "北", 2: "东北", 3: "东", 4: "东南",
                5: "南", 6: "西南", 7: "西", 8: "西北"
            }
            for stat in stats['out_dir_stats']:
                dir_name = direction_names.get(stat['out_dir'], "方向{}".format(stat['out_dir']))
                print("  {}: {}条".format(dir_name, stat['count']))
            
            print("\n驶入方向统计:")
            for stat in stats['in_dir_stats']:
                dir_name = direction_names.get(stat['in_dir'], "方向{}".format(stat['in_dir']))
                print("  {}: {}条".format(dir_name, stat['count']))
        
        # 5. 关闭连接
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")
        
        return True

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
    
    # 创建更新器
    updater = RidCrossUpdater(db_config)
    
    # 执行更新
    if updater.process_all():
        logger.info("路段关联更新完成！")
    else:
        logger.error("路段关联更新失败！")

if __name__ == "__main__":
    main() 