#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
区域基础信息处理器
处理路口形状、路口点、绿化带等区域数据，导入到t_base_area_info表
"""

import json
import codecs
import pymysql
from datetime import datetime
import sys
import os

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from road_network.config.database_config import get_database_connection

class AreaInfoProcessor:
    """区域基础信息处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.connection = None
        self.cursor = None
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'by_type': {}
        }
    
    def connect_database(self):
        """连接数据库"""
        try:
            self.connection = get_database_connection()
            self.cursor = self.connection.cursor()
            print("数据库连接成功")
            return True
        except Exception as e:
            print("数据库连接失败: {}".format(e))
            return False
    
    def load_json_data(self, file_path):
        """加载JSON数据文件"""
        try:
            with codecs.open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
        except Exception as e:
            print("加载文件失败 {}: {}".format(file_path, e))
            return None
    
    def determine_area_type(self, feature_type, feature_name):
        """根据特征类型和名称确定区域类型"""
        if feature_type == "ChinaIntersectionShape":
            return 6  # 道路
        elif feature_type == "ChinaGreenBelt":
            return 5  # 热点区域
        elif feature_type == "ParkingSpace":
            return 5  # 热点区域
        elif feature_type == "BusStation":
            return 6  # 道路
        elif feature_type == "SafetyIsland":
            return 6  # 道路
        elif "商圈" in feature_name:
            return 3  # 商圈
        elif "交警" in feature_name:
            return 2  # 交警辖区
        elif "交通小区" in feature_name:
            return 4  # 交通小区
        else:
            return 1  # 行政区划（默认）
    
    def extract_geometry_center(self, geometry):
        """提取几何中心点"""
        if geometry.get('type') == 'Point':
            coords = geometry.get('coordinates', [])
            if len(coords) >= 2:
                return "{:.6f},{:.6f}".format(coords[0], coords[1])
        elif geometry.get('type') == 'Polygon':
            coords = geometry.get('coordinates', [])
            if coords and len(coords[0]) > 0:
                # 计算多边形的中心点（简单平均）
                total_x = sum(point[0] for point in coords[0])
                total_y = sum(point[1] for point in coords[0])
                count = len(coords[0])
                return "{:.6f},{:.6f}".format(total_x/count, total_y/count)
        return None
    
    def convert_geometry_to_wkt(self, geometry):
        """将GeoJSON几何转换为WKT格式"""
        if geometry.get('type') == 'Point':
            coords = geometry.get('coordinates', [])
            if len(coords) >= 2:
                return "POINT({} {})".format(coords[0], coords[1])
        
        elif geometry.get('type') == 'Polygon':
            coords = geometry.get('coordinates', [])
            if coords and len(coords[0]) > 0:
                # 只取第一个环（外环）
                ring = coords[0]
                wkt_coords = []
                for point in ring:
                    # 只取经纬度，忽略高程
                    wkt_coords.append("{} {}".format(point[0], point[1]))
                return "POLYGON(({})".format(','.join(wkt_coords))
        
        elif geometry.get('type') == 'MultiPolygon':
            coords = geometry.get('coordinates', [])
            if coords:
                polygons = []
                for polygon in coords:
                    if polygon and len(polygon[0]) > 0:
                        ring = polygon[0]  # 只取外环
                        wkt_coords = []
                        for point in ring:
                            wkt_coords.append("{} {}".format(point[0], point[1]))
                        polygons.append("({})".format(','.join(wkt_coords)))
                return "MULTIPOLYGON(({})".format(','.join(polygons))
        
        return None
    
    def process_feature(self, feature, area_type_name):
        """处理单个特征要素"""
        try:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            # 提取基础信息
            feature_id = properties.get('featureId')
            lkid = properties.get('lkid', '')
            lkmc = properties.get('lkmc', '')
            ldid = properties.get('ldid', '')
            feature_type = properties.get('featureType', '')
            
            # 根据数据类型确定名称和代码
            if lkmc:
                name = lkmc
                code = lkid[:6] if lkid else '000000'
                parent_code = lkid[:4] + '00' if len(lkid) > 4 else '0000'
            elif ldid:
                name = "{}区域".format(area_type_name)
                code = ldid[:6] if ldid else '000000'
                parent_code = ldid[:4] + '00' if len(ldid) > 4 else '0000'
            else:
                name = "{}区域".format(area_type_name)
                code = '000000'
                parent_code = '0000'
            
            # 生成唯一ID
            area_id = feature_id if feature_id else hash(str(lkid) + str(ldid)) % 1000000
            
            # 确定区域类型
            area_type = self.determine_area_type(feature_type, name)
            
            # 提取几何中心点
            center_point = self.extract_geometry_center(geometry)
            
            # 转换几何为WKT
            wkt_geometry = self.convert_geometry_to_wkt(geometry)
            
            # 构建插入数据
            insert_data = {
                'id': area_id,
                'code': code,
                'name': name,
                'road_name': name,
                'type': area_type,
                'parent_code': parent_code,
                'location': center_point,
                'polylines': wkt_geometry,
                'remark': "{}数据，特征ID: {}".format(area_type_name, feature_id),
                'gmt_create': datetime.now(),
                'gmt_modified': datetime.now()
            }
            
            return insert_data
            
        except Exception as e:
            print("处理特征失败: {}".format(e))
            return None
    
    def insert_area_info(self, area_data):
        """插入区域信息到数据库"""
        try:
            sql = """
            INSERT INTO t_base_area_info 
            (id, code, name, road_name, type, parent_code, location, polylines, 
             remark, gmt_create, gmt_modified) 
            VALUES 
            (%(id)s, %(code)s, %(name)s, %(road_name)s, %(type)s, %(parent_code)s, 
             %(location)s, %(polylines)s, %(remark)s, %(gmt_create)s, %(gmt_modified)s)
            """
            
            self.cursor.execute(sql, area_data)
            return True
            
        except Exception as e:
            print("插入数据失败: {}".format(e))
            return False
    
    def process_file(self, file_path, area_type_name):
        """处理单个JSON文件"""
        print("\n开始处理{}文件: {}".format(area_type_name, file_path))
        
        # 加载JSON数据
        data = self.load_json_data(file_path)
        if not data:
            return
        
        features = data.get('features', [])
        file_stats = {'total': 0, 'success': 0, 'error': 0}
        
        for feature in features:
            file_stats['total'] += 1
            self.stats['total_processed'] += 1
            
            # 处理特征
            area_data = self.process_feature(feature, area_type_name)
            if not area_data:
                file_stats['error'] += 1
                self.stats['error_count'] += 1
                continue
            
            # 插入数据库
            if self.insert_area_info(area_data):
                file_stats['success'] += 1
                self.stats['success_count'] += 1
            else:
                file_stats['error'] += 1
                self.stats['error_count'] += 1
        
        # 更新统计信息
        self.stats['by_type'][area_type_name] = file_stats
        
        print("{}处理完成: 总数={}, 成功={}, 失败={}".format(
            area_type_name, file_stats['total'], file_stats['success'], file_stats['error']))
    
    def process_all_files(self):
        """处理所有区域数据文件"""
        # 定义要处理的文件列表
        files_to_process = [
            ('../../luwangJson/路口形状.json', '路口形状'),
            ('../../luwangJson/路口点.json', '路口点'),
            ('../../luwangJson/绿化带.json', '绿化带'),
            ('../../luwangJson/停车位.json', '停车位'),
            ('../../luwangJson/公交车站.json', '公交车站'),
            ('../../luwangJson/安全岛.json', '安全岛')
        ]
        
        for file_path, area_type_name in files_to_process:
            if os.path.exists(file_path):
                self.process_file(file_path, area_type_name)
            else:
                print("文件不存在: {}".format(file_path))
    
    def print_statistics(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("区域基础信息处理统计")
        print("="*60)
        print("总处理数量: {}".format(self.stats['total_processed']))
        print("成功数量: {}".format(self.stats['success_count']))
        print("失败数量: {}".format(self.stats['error_count']))
        print("成功率: {:.2f}%".format(
            (self.stats['success_count'] / self.stats['total_processed'] * 100) 
            if self.stats['total_processed'] > 0 else 0))
        
        print("\n按类型统计:")
        for area_type, stats in self.stats['by_type'].items():
            print("  {}: 总数={}, 成功={}, 失败={}".format(
                area_type, stats['total'], stats['success'], stats['error']))
        
        print("="*60)
    
    def run(self):
        """运行处理器"""
        print("开始处理区域基础信息数据...")
        
        # 连接数据库
        if not self.connect_database():
            return
        
        try:
            # 处理所有文件
            self.process_all_files()
            
            # 提交事务
            self.connection.commit()
            
            # 打印统计信息
            self.print_statistics()
            
        except Exception as e:
            print("处理过程中发生错误: {}".format(e))
            if self.connection:
                self.connection.rollback()
        
        finally:
            # 关闭连接
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print("数据库连接已关闭")


if __name__ == "__main__":
    processor = AreaInfoProcessor()
    processor.run() 