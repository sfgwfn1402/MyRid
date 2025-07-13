#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import codecs
import pymysql
from datetime import datetime
import sys
import os
import math

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from road_network.config.database_config import get_database_connection

class CrossDirProcessor:
    """路口方向基础信息处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.connection = None
        self.cursor = None
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'by_dir_type': {},
            'by_in_out_type': {},
            'by_cross': {}
        }
        
        # 方向类型映射（基于序号推断）
        self.direction_mapping = {
            # 序号到方向类型的映射
            '100': {'dir_type': 1, 'in_out_type': 1},  # 北-进口
            '200': {'dir_type': 1, 'in_out_type': 2},  # 北-出口
            '210': {'dir_type': 2, 'in_out_type': 1},  # 东北-进口
            '220': {'dir_type': 2, 'in_out_type': 2},  # 东北-出口
            '230': {'dir_type': 3, 'in_out_type': 1},  # 东-进口
            '240': {'dir_type': 3, 'in_out_type': 2},  # 东-出口
            '250': {'dir_type': 4, 'in_out_type': 1},  # 东南-进口
            '260': {'dir_type': 4, 'in_out_type': 2},  # 东南-出口
            '270': {'dir_type': 5, 'in_out_type': 1},  # 南-进口
            '280': {'dir_type': 5, 'in_out_type': 2},  # 南-出口
            '290': {'dir_type': 6, 'in_out_type': 1},  # 西南-进口
            '300': {'dir_type': 6, 'in_out_type': 2},  # 西南-出口
            '310': {'dir_type': 7, 'in_out_type': 1},  # 西-进口
            '320': {'dir_type': 7, 'in_out_type': 2},  # 西-出口
            '330': {'dir_type': 8, 'in_out_type': 1},  # 西北-进口
            '340': {'dir_type': 8, 'in_out_type': 2},  # 西北-出口
            '900': {'dir_type': 1, 'in_out_type': 1}   # 通用/其他
        }
        
        # 缓存有效的路口ID
        self.valid_cross_ids = set()
        
        # 缓存斑马线信息
        self.crosswalk_crosses = set()
    
    def connect_database(self):
        """连接数据库"""
        try:
            self.connection = get_database_connection()
            self.cursor = self.connection.cursor()
            print("数据库连接成功")
        except Exception as e:
            print("数据库连接失败: {}".format(e))
            raise
    
    def load_valid_cross_ids(self):
        """加载有效的路口ID"""
        try:
            query = "SELECT id FROM t_base_cross_info"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            for row in results:
                self.valid_cross_ids.add(row[0])
            
            print("加载了 {} 个有效路口ID".format(len(self.valid_cross_ids)))
        except Exception as e:
            print("加载有效路口ID失败: {}".format(e))
    
    def load_crosswalk_data(self):
        """加载斑马线数据，判断路口是否有行人过街设施"""
        try:
            file_path = '../../luwangJson/斑马线.json'
            with codecs.open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            features = data.get('features', [])
            
            for feature in features:
                properties = feature.get('properties', {})
                lkid = properties.get('lkid')
                
                if lkid:
                    lkid = lkid.strip() if isinstance(lkid, (str, unicode)) else str(lkid)
                    if lkid:
                        self.crosswalk_crosses.add(lkid)
            
            print("加载了 {} 个路口的斑马线数据".format(len(self.crosswalk_crosses)))
            
        except Exception as e:
            print("加载斑马线数据失败: {}".format(e))
    
    def load_channel_data(self):
        """加载渠化段数据"""
        try:
            file_path = '../../luwangJson/渠化段.json'
            with codecs.open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            features = data.get('features', [])
            print("成功加载 {} 条渠化段数据".format(len(features)))
            return features
            
        except Exception as e:
            print("加载渠化段数据失败: {}".format(e))
            return []
    
    def extract_cross_id_from_ldid(self, ldid):
        """从ldid中提取路口ID"""
        try:
            if not ldid:
                return None
                
            # 尝试从ldid中提取路口ID
            # 假设ldid格式为 路口ID1路口ID2...
            parts = ldid.split('12Q')
            if len(parts) >= 2:
                # 取第一个路口ID
                cross_id = '12Q' + parts[1][:8]
                # 确保长度为11
                if len(cross_id) == 11:
                    return cross_id
            
            return None
            
        except Exception as e:
            print("提取路口ID失败: {}".format(e))
            return None
    
    def calculate_polygon_length(self, coordinates):
        """计算多边形周长作为路段长度"""
        try:
            if not coordinates or len(coordinates) < 1:
                return 0
            
            points = coordinates[0]  # 取第一个环
            if len(points) < 2:
                return 0
            
            total_length = 0
            for i in range(len(points) - 1):
                # 计算两点间距离
                lon1, lat1 = points[i][0], points[i][1]
                lon2, lat2 = points[i + 1][0], points[i + 1][1]
                
                # 使用简单的欧几里得距离（对于小范围可以近似）
                distance = math.sqrt((lon2 - lon1)**2 + (lat2 - lat1)**2) * 111000  # 转换为米
                total_length += distance
            
            return round(total_length, 2)
            
        except Exception as e:
            print("计算长度失败: {}".format(e))
            return 0
    
    def infer_direction_from_sequence(self, qhdsxh):
        """从序号推断方向类型和进出口类型"""
        try:
            # 直接查找映射
            if qhdsxh in self.direction_mapping:
                return self.direction_mapping[qhdsxh]
            
            # 如果没有直接映射，尝试分析序号
            if qhdsxh.startswith('1'):
                return {'dir_type': 1, 'in_out_type': 1}  # 北-进口
            elif qhdsxh.startswith('2'):
                return {'dir_type': 3, 'in_out_type': 1}  # 东-进口
            elif qhdsxh.startswith('9'):
                return {'dir_type': 1, 'in_out_type': 1}  # 默认为北-进口
            
            # 默认值
            return {'dir_type': 1, 'in_out_type': 1}
            
        except Exception as e:
            print("推断方向失败: {}".format(e))
            return {'dir_type': 1, 'in_out_type': 1}
    
    def generate_dir_id(self, cross_id, dir_type, in_out_type, sequence):
        """生成路口方向ID"""
        try:
            # 格式：路口ID_方向_进出口_序号
            dir_id = "{}_{}_{}_{:03d}".format(cross_id, dir_type, in_out_type, int(sequence[:3]))
            return dir_id[:17]  # 限制长度为17
        except Exception as e:
            print("生成路口方向ID失败: {}".format(e))
            return None
    
    def process_channel_feature(self, feature):
        """处理单个渠化段记录"""
        try:
            properties = feature.get('properties', {})
            geometry = feature.get('geometry', {})
            
            # 提取基本信息
            qhdsxh = properties.get('qhdsxh', '')
            ldid = properties.get('ldid', '')
            
            if not qhdsxh or not ldid:
                return None
            
            # 提取路口ID
            cross_id = self.extract_cross_id_from_ldid(ldid)
            if not cross_id or cross_id not in self.valid_cross_ids:
                return None
            
            # 推断方向类型和进出口类型
            direction_info = self.infer_direction_from_sequence(qhdsxh)
            dir_type = direction_info['dir_type']
            in_out_type = direction_info['in_out_type']
            
            # 计算长度
            coordinates = geometry.get('coordinates', [])
            length = self.calculate_polygon_length(coordinates)
            
            # 判断是否有行人过街
            is_pedestrian = 1 if cross_id in self.crosswalk_crosses else 0
            
            # 生成ID
            dir_id = self.generate_dir_id(cross_id, dir_type, in_out_type, qhdsxh)
            if not dir_id:
                return None
            
            # 返回处理结果
            return {
                'id': dir_id,
                'dir_type': dir_type,
                'in_out_type': in_out_type,
                'cross_id': cross_id,
                'length': length,
                'is_pedestrian': is_pedestrian,
                'original_sequence': qhdsxh
            }
            
        except Exception as e:
            print("处理渠化段记录失败: {}".format(e))
            return None
    
    def insert_dir_info(self, dir_data):
        """插入路口方向信息到数据库"""
        try:
            # 检查是否已存在
            check_query = "SELECT COUNT(*) FROM t_base_cross_dir_info WHERE id = %s"
            self.cursor.execute(check_query, (dir_data['id'],))
            
            if self.cursor.fetchone()[0] > 0:
                print("路口方向 {} 已存在，跳过".format(dir_data['id']))
                return False
            
            # 插入新记录
            insert_query = """
                INSERT INTO t_base_cross_dir_info 
                (id, dir_type, in_out_type, cross_id, length, is_pedestrian, gmt_create, gmt_modified)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            current_time = datetime.now()
            
            self.cursor.execute(insert_query, (
                dir_data['id'],
                dir_data['dir_type'],
                dir_data['in_out_type'],
                dir_data['cross_id'],
                dir_data['length'],
                dir_data['is_pedestrian'],
                current_time,
                current_time
            ))
            
            self.connection.commit()
            return True
            
        except Exception as e:
            print("插入路口方向信息失败: {}".format(e))
            self.connection.rollback()
            return False
    
    def process_all_channels(self):
        """处理所有渠化段数据"""
        try:
            # 加载数据
            features = self.load_channel_data()
            if not features:
                return
            
            print("开始处理渠化段数据...")
            
            for feature in features:
                self.stats['total_processed'] += 1
                
                # 处理单个记录
                dir_data = self.process_channel_feature(feature)
                
                if dir_data:
                    # 插入数据库
                    if self.insert_dir_info(dir_data):
                        self.stats['success_count'] += 1
                        
                        # 统计信息
                        cross_id = dir_data['cross_id']
                        dir_type = dir_data['dir_type']
                        in_out_type = dir_data['in_out_type']
                        
                        self.stats['by_cross'][cross_id] = self.stats['by_cross'].get(cross_id, 0) + 1
                        self.stats['by_dir_type'][dir_type] = self.stats['by_dir_type'].get(dir_type, 0) + 1
                        self.stats['by_in_out_type'][in_out_type] = self.stats['by_in_out_type'].get(in_out_type, 0) + 1
                        
                        print("成功处理路口方向: {} (路口: {}, 方向: {}, 类型: {})".format(
                            dir_data['id'], cross_id, dir_type, in_out_type))
                    else:
                        self.stats['error_count'] += 1
                else:
                    self.stats['error_count'] += 1
                
                # 每处理100条记录显示进度
                if self.stats['total_processed'] % 100 == 0:
                    print("已处理 {} 条记录...".format(self.stats['total_processed']))
            
        except Exception as e:
            print("处理渠化段数据失败: {}".format(e))
    
    def print_statistics(self):
        """打印统计信息"""
        print("\n=== 路口方向基础信息处理统计 ===")
        print("总处理记录数: {}".format(self.stats['total_processed']))
        print("成功处理: {}".format(self.stats['success_count']))
        print("失败记录: {}".format(self.stats['error_count']))
        success_rate = (self.stats['success_count'] / self.stats['total_processed']) * 100 if self.stats['total_processed'] > 0 else 0
        print("成功率: {:.2f}%".format(success_rate))
        
        print("\n按路口统计:")
        for cross_id, count in self.stats['by_cross'].items():
            print("  {}: {} 条方向记录".format(cross_id, count))
        
        print("\n按方向类型统计:")
        direction_names = {1: '北', 2: '东北', 3: '东', 4: '东南', 5: '南', 6: '西南', 7: '西', 8: '西北'}
        for dir_type, count in self.stats['by_dir_type'].items():
            print("  {}: {} 条".format(direction_names.get(dir_type, '未知'), count))
        
        print("\n按进出口类型统计:")
        io_names = {1: '进口', 2: '出口'}
        for in_out_type, count in self.stats['by_in_out_type'].items():
            print("  {}: {} 条".format(io_names.get(in_out_type, '未知'), count))
        
        print("\n路口覆盖率: {:.2f}% ({}/{})".format(
            (len(self.stats['by_cross']) / len(self.valid_cross_ids)) * 100 if len(self.valid_cross_ids) > 0 else 0,
            len(self.stats['by_cross']),
            len(self.valid_cross_ids)
        ))
    
    def close_connection(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("数据库连接已关闭")
    
    def run(self):
        """运行处理器"""
        try:
            print("开始处理路口方向基础信息...")
            
            # 连接数据库
            self.connect_database()
            
            # 加载有效路口ID
            self.load_valid_cross_ids()
            
            # 加载斑马线数据
            self.load_crosswalk_data()
            
            # 处理所有渠化段数据
            self.process_all_channels()
            
            # 打印统计信息
            self.print_statistics()
            
            print("\n路口方向基础信息处理完成！")
            
        except Exception as e:
            print("处理失败: {}".format(e))
        finally:
            self.close_connection()

if __name__ == "__main__":
    processor = CrossDirProcessor()
    processor.run() 