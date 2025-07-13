#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交通要素JSON数据处理器
将地图部门提供的JSON文件数据处理后写入决策系统数据库

基于MyRid项目扩展开发
"""

import json
import os
import math
from typing import Dict, List, Tuple, Any
from shapely.geometry import Point, LineString, Polygon, shape
from shapely.ops import transform
import pyproj
import psycopg2
import pandas as pd

# 复用MyRid项目的数据库连接模块
from lib.dbconn import db_conn, batch_insert

class TrafficFeatureProcessor:
    """交通要素数据处理器"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """
        初始化处理器
        
        Args:
            db_config: 数据库配置信息
        """
        self.db_config = db_config
        self.connection = None
        
        # 坐标转换器（假设JSON数据为WGS84）
        self.transformer = pyproj.Transformer.from_crs(
            "EPSG:4326",  # WGS84
            "EPSG:3857",  # Web Mercator (用于计算)
            always_xy=True
        )
        
        # JSON文件与数据库表的映射关系
        self.json_to_table_mapping = {
            "路口点.json": "t_base_cross_info",
            "路段中心线.json": "t_base_segment_info", 
            "车道.json": "t_base_lane_info",
            "地面箭头.json": "t_base_arrow_info",
            "路口形状.json": "t_base_cross_area",
            "标线.json": "t_base_marking_info",
            "渠化段.json": "t_base_channelization_info"
        }
        
        # 方向编码映射（8个方向）
        self.direction_mapping = {
            "北": 1, "东北": 2, "东": 3, "东南": 4,
            "南": 5, "西南": 6, "西": 7, "西北": 8
        }
        
        # 转向类型映射
        self.turn_type_mapping = {
            "直行": "s", "左转": "l", "右转": "r", "掉头": "u"
        }

    def connect_database(self):
        """连接数据库"""
        try:
            self.connection = db_conn(
                self.db_config['host'],
                self.db_config['port'], 
                self.db_config['user'],
                self.db_config['pw'],
                self.db_config['dbname']
            )
            print("✅ 数据库连接成功")
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            raise

    def load_geojson(self, file_path: str) -> Dict[str, Any]:
        """
        加载GeoJSON文件
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            GeoJSON数据字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 成功加载 {file_path}")
            return data
        except Exception as e:
            print(f"❌ 加载文件失败 {file_path}: {e}")
            return {}

    def process_intersection_points(self, geojson_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理路口点数据
        
        Args:
            geojson_data: 路口点GeoJSON数据
            
        Returns:
            处理后的路口数据列表
        """
        processed_data = []
        
        for feature in geojson_data.get('features', []):
            try:
                # 提取属性信息
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                
                if geometry.get('type') != 'Point':
                    continue
                
                # 提取坐标
                coords = geometry.get('coordinates', [])
                if len(coords) != 2:
                    continue
                
                lon, lat = coords
                
                # 构建路口基础表数据
                intersection_data = {
                    'intersection_id': properties.get('lkid', ''),
                    'intersection_name': properties.get('lkmc', ''),
                    'feature_id': properties.get('featureId', 0),
                    'longitude': lon,
                    'latitude': lat,
                    'geometry': f"POINT({lon} {lat})",
                    'feature_type': properties.get('featureType', ''),
                    'create_time': 'NOW()',
                    'update_time': 'NOW()'
                }
                
                processed_data.append(intersection_data)
                
            except Exception as e:
                print(f"❌ 处理路口点数据出错: {e}")
                continue
        
        print(f"✅ 处理路口点数据完成，共 {len(processed_data)} 条")
        return processed_data

    def process_road_segments(self, geojson_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理路段中心线数据
        
        Args:
            geojson_data: 路段中心线GeoJSON数据
            
        Returns:
            处理后的路段数据列表
        """
        processed_data = []
        
        for feature in geojson_data.get('features', []):
            try:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                
                if geometry.get('type') != 'LineString':
                    continue
                
                # 创建Shapely LineString对象
                line = shape(geometry)
                
                # 计算路段长度（米）
                line_projected = transform(self.transformer.transform, line)
                length_meters = line_projected.length
                
                # 获取起止点坐标
                coords = geometry.get('coordinates', [])
                if len(coords) < 2:
                    continue
                
                start_point = coords[0]
                end_point = coords[-1]
                
                # 构建路段基础表数据
                segment_data = {
                    'segment_id': properties.get('segmentId', ''),
                    'segment_name': properties.get('segmentName', ''),
                    'road_class': properties.get('roadClass', ''),
                    'start_longitude': start_point[0],
                    'start_latitude': start_point[1], 
                    'end_longitude': end_point[0],
                    'end_latitude': end_point[1],
                    'length_meters': round(length_meters, 2),
                    'geometry': f"LINESTRING({','.join(f'{p[0]} {p[1]}' for p in coords)})",
                    'create_time': 'NOW()',
                    'update_time': 'NOW()'
                }
                
                processed_data.append(segment_data)
                
            except Exception as e:
                print(f"❌ 处理路段数据出错: {e}")
                continue
        
        print(f"✅ 处理路段数据完成，共 {len(processed_data)} 条")
        return processed_data

    def process_direction_arrows(self, geojson_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        处理地面箭头数据，生成转向关系
        
        Args:
            geojson_data: 地面箭头GeoJSON数据
            
        Returns:
            处理后的转向关系数据列表
        """
        processed_data = []
        
        for feature in geojson_data.get('features', []):
            try:
                properties = feature.get('properties', {})
                geometry = feature.get('geometry', {})
                
                if geometry.get('type') != 'Point':
                    continue
                
                coords = geometry.get('coordinates', [])
                if len(coords) != 2:
                    continue
                
                # 提取箭头属性
                arrow_type = properties.get('arrowType', '')
                direction = properties.get('direction', '')
                intersection_id = properties.get('intersectionId', '')
                
                # 根据箭头类型确定转向类型
                turn_type = self._determine_turn_type(arrow_type)
                
                # 根据位置和方向确定驶入/驶出方向
                in_dir, out_dir = self._calculate_directions(
                    coords[0], coords[1], direction, turn_type
                )
                
                # 生成转向关系ID
                turn_id = f"{intersection_id}_{in_dir}_{turn_type}"
                
                # 构建转向关系表数据
                turn_data = {
                    'id': turn_id,
                    'intersection_id': intersection_id,
                    'turn_type': turn_type,
                    'in_dir': in_dir,
                    'out_dir': out_dir,
                    'arrow_longitude': coords[0],
                    'arrow_latitude': coords[1],
                    'create_time': 'NOW()',
                    'update_time': 'NOW()'
                }
                
                processed_data.append(turn_data)
                
            except Exception as e:
                print(f"❌ 处理箭头数据出错: {e}")
                continue
        
        print(f"✅ 处理转向关系数据完成，共 {len(processed_data)} 条")
        return processed_data

    def _determine_turn_type(self, arrow_type: str) -> str:
        """
        根据箭头类型确定转向类型
        
        Args:
            arrow_type: 箭头类型描述
            
        Returns:
            转向类型编码
        """
        arrow_type = arrow_type.lower()
        
        if '直行' in arrow_type or 'straight' in arrow_type:
            return 's'
        elif '左转' in arrow_type or 'left' in arrow_type:
            return 'l'
        elif '右转' in arrow_type or 'right' in arrow_type:
            return 'r'
        elif '掉头' in arrow_type or 'uturn' in arrow_type:
            return 'u'
        else:
            return 's'  # 默认直行

    def _calculate_directions(self, lon: float, lat: float, 
                            direction: str, turn_type: str) -> Tuple[int, int]:
        """
        计算驶入和驶出方向
        
        Args:
            lon: 经度
            lat: 纬度  
            direction: 方向描述
            turn_type: 转向类型
            
        Returns:
            (驶入方向编码, 驶出方向编码)
        """
        # 简化处理：根据方向字符串确定
        # 实际应用中需要结合路口几何形状精确计算
        
        direction_map = {
            '北': 1, '东北': 2, '东': 3, '东南': 4,
            '南': 5, '西南': 6, '西': 7, '西北': 8
        }
        
        # 默认驶入方向
        in_dir = direction_map.get(direction, 1)
        
        # 根据转向类型计算驶出方向
        if turn_type == 's':  # 直行
            out_dir = in_dir
        elif turn_type == 'l':  # 左转
            out_dir = (in_dir + 2) % 8 if (in_dir + 2) % 8 != 0 else 8
        elif turn_type == 'r':  # 右转
            out_dir = (in_dir - 2) % 8 if (in_dir - 2) % 8 != 0 else 8
        elif turn_type == 'u':  # 掉头
            out_dir = (in_dir + 4) % 8 if (in_dir + 4) % 8 != 0 else 8
        else:
            out_dir = in_dir
        
        return in_dir, out_dir

    def insert_to_database(self, table_name: str, data_list: List[Dict[str, Any]]):
        """
        批量插入数据到数据库
        
        Args:
            table_name: 目标表名
            data_list: 要插入的数据列表
        """
        if not data_list:
            print(f"⚠️ {table_name} 没有数据需要插入")
            return
        
        try:
            # 构建插入SQL
            columns = list(data_list[0].keys())
            placeholders = ', '.join(['%s'] * len(columns))
            sql = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
            """
            
            # 准备数据
            values_list = []
            for item in data_list:
                values = []
                for col in columns:
                    value = item[col]
                    if value == 'NOW()':
                        values.append('NOW()')
                    else:
                        values.append(value)
                values_list.append(values)
            
            # 批量插入
            batch_insert(self.connection, sql, values_list, commit=True)
            print(f"✅ {table_name} 数据插入成功，共 {len(data_list)} 条")
            
        except Exception as e:
            print(f"❌ {table_name} 数据插入失败: {e}")

    def process_all_json_files(self, json_directory: str):
        """
        处理所有JSON文件
        
        Args:
            json_directory: JSON文件目录
        """
        print("🚀 开始处理所有JSON文件...")
        
        # 连接数据库
        self.connect_database()
        
        # 处理顺序（按依赖关系排序）
        processing_order = [
            ("路口点.json", self.process_intersection_points),
            ("路段中心线.json", self.process_road_segments),
            ("地面箭头.json", self.process_direction_arrows),
            # 可以继续添加其他处理器
        ]
        
        for json_filename, processor_func in processing_order:
            json_path = os.path.join(json_directory, json_filename)
            
            if not os.path.exists(json_path):
                print(f"⚠️ 文件不存在: {json_path}")
                continue
            
            print(f"\n📂 处理文件: {json_filename}")
            
            # 加载JSON数据
            geojson_data = self.load_geojson(json_path)
            if not geojson_data:
                continue
            
            # 处理数据
            processed_data = processor_func(geojson_data)
            
            # 插入数据库
            table_name = self.json_to_table_mapping.get(json_filename, '')
            if table_name and processed_data:
                self.insert_to_database(table_name, processed_data)
        
        print("\n🎉 所有JSON文件处理完成！")

def main():
    """主函数 - 示例用法"""
    
    # 数据库配置（使用MyRid项目的配置格式）
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'pw': '123456',
        'dbname': 'traffic_decision_db'
    }
    
    # 创建处理器
    processor = TrafficFeatureProcessor(db_config)
    
    # JSON文件目录路径
    json_directory = "./交通要素JSON文件"
    
    # 处理所有文件
    processor.process_all_json_files(json_directory)

if __name__ == "__main__":
    main() 