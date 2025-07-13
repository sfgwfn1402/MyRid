#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import codecs
import pymysql
from datetime import datetime
import sys
import os
import re

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from road_network.config.database_config import get_database_connection

class CrossTurnProcessor:
    """路口转向基础信息处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.connection = None
        self.cursor = None
        self.stats = {
            'total_processed': 0,
            'success_count': 0,
            'error_count': 0,
            'by_turn_type': {},
            'by_cross': {}
        }
        
        # 转向类型映射
        self.turn_type_map = {
            u'Paint ↑': 's',    # 直行
            u'Paint ↰': 'l',    # 左转
            u'Paint ↱': 'r',    # 右转
            u'Paint U': 'u'     # 掉头
        }
        
        # 方向代码映射
        self.direction_map = {
            '1': 1,  # 北
            '2': 3,  # 东
            '3': 5,  # 南
            '4': 7   # 西
        }
        
        # 缓存有效的路口ID
        self.valid_cross_ids = set()
    
    def connect_database(self):
        """连接数据库"""
        try:
            self.connection = get_database_connection()
            self.cursor = self.connection.cursor()
            print("数据库连接成功")
            self.load_valid_cross_ids()
        except Exception as e:
            print("数据库连接失败: {}".format(e))
            return False
        return True
    
    def load_valid_cross_ids(self):
        """加载有效的路口ID"""
        try:
            query = "SELECT id FROM t_base_cross_info"
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            self.valid_cross_ids = set([row[0] for row in results])
            print("加载了 {} 个有效路口ID".format(len(self.valid_cross_ids)))
            
        except Exception as e:
            print("加载路口ID失败: {}".format(e))
    
    def load_arrow_data(self):
        """加载地面箭头数据"""
        try:
            file_path = '../../luwangJson/地面箭头.json'
            with codecs.open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            features = data.get('features', [])
            print("成功加载 {} 条地面箭头数据".format(len(features)))
            return features
            
        except Exception as e:
            print("加载地面箭头数据失败: {}".format(e))
            return []
    
    def extract_cross_id_from_ldid(self, ldid):
        """从ldid中提取路口ID"""
        try:
            if not ldid:
                return None
            
            # ldid格式通常为：起点路口ID(11) + 终点路口ID(11) + 序号
            if len(ldid) >= 22:
                # 提取前11位作为起点路口ID
                start_cross_id = ldid[:11]
                # 也可以提取终点路口ID：ldid[11:22]
                return start_cross_id
            elif len(ldid) >= 11:
                # 如果长度不够22，只取前11位
                start_cross_id = ldid[:11]
                return start_cross_id
            
            return None
            
        except Exception as e:
            return None
    
    def calculate_out_direction(self, in_dir, turn_type):
        """根据驶入方向和转向类型计算驶出方向"""
        try:
            if turn_type == 's':  # 直行，方向不变
                return in_dir
            elif turn_type == 'u':  # 掉头，相反方向
                return ((in_dir - 1 + 4) % 8) + 1
            elif turn_type == 'l':  # 左转，逆时针90度
                return ((in_dir - 1 + 6) % 8) + 1
            elif turn_type == 'r':  # 右转，顺时针90度
                return ((in_dir - 1 + 2) % 8) + 1
            else:
                return in_dir
                
        except Exception as e:
            return in_dir
    
    def generate_turn_id(self, cross_id, in_dir, turn_type):
        """生成转向ID"""
        try:
            if cross_id and len(cross_id) == 11:
                # 格式：路口ID(11) + 方向(1) + 转向(1) = 13位
                return "{}{}{}".format(cross_id, in_dir, turn_type)
            return None
        except Exception as e:
            return None
    
    def process_arrow_feature(self, feature):
        """处理单个箭头特征"""
        try:
            properties = feature.get('properties', {})
            
            # 提取转向类型
            feature_type = properties.get('featureType', '')
            turn_type = self.turn_type_map.get(feature_type)
            
            if not turn_type:
                print("未知转向类型，长度: {}".format(len(feature_type)))
                return None
            
            # 提取路口ID
            ldid = properties.get('ldid', '')
            cross_id = self.extract_cross_id_from_ldid(ldid)
            
            if not cross_id:
                print("无法提取路口ID: ldid={}".format(ldid))
                return None
            
            # 验证路口ID是否存在于数据库中
            if cross_id not in self.valid_cross_ids:
                print("路口ID不存在于数据库: {} (来源ldid: {})".format(cross_id, ldid))
                return None
            
            # 提取驶入方向
            dxfx = properties.get('dxfx', '')
            in_dir = self.direction_map.get(dxfx, 1)
            
            # 计算驶出方向
            out_dir = self.calculate_out_direction(in_dir, turn_type)
            
            # 生成转向ID
            turn_id = self.generate_turn_id(cross_id, in_dir, turn_type)
            
            if not turn_id:
                return None
            
            return {
                'id': turn_id,
                'turn_type': turn_type,
                'in_dir': in_dir,
                'out_dir': out_dir,
                'cross_id': cross_id,
                'feature_id': properties.get('featureId'),
                'ldid': ldid,
                'dxfx': dxfx
            }
            
        except Exception as e:
            print("处理箭头特征失败: {}".format(e))
            return None
    
    def insert_turn_info(self, turn_data):
        """插入转向信息到数据库"""
        try:
            now = datetime.now()
            
            insert_query = """
            INSERT INTO t_base_cross_turn_info 
            (id, turn_type, in_dir, out_dir, cross_id, gmt_create, gmt_modified)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            self.cursor.execute(insert_query, (
                turn_data['id'],
                turn_data['turn_type'],
                turn_data['in_dir'],
                turn_data['out_dir'],
                turn_data['cross_id'],
                now,
                now
            ))
            
            return True
            
        except pymysql.IntegrityError as e:
            # 主键冲突，跳过
            if "Duplicate entry" in str(e):
                return False
            else:
                print("插入转向信息失败: {}".format(e))
                self.stats['error_count'] += 1
                return False
        except Exception as e:
            print("插入转向信息失败: {}".format(e))
            self.stats['error_count'] += 1
            return False
    
    def process_all_arrows(self):
        """处理所有箭头数据"""
        arrow_features = self.load_arrow_data()
        
        if not arrow_features:
            print("没有箭头数据可处理")
            return
        
        print("开始处理箭头数据...")
        
        for feature in arrow_features:
            self.stats['total_processed'] += 1
            
            turn_data = self.process_arrow_feature(feature)
            
            if turn_data:
                if self.insert_turn_info(turn_data):
                    self.stats['success_count'] += 1
                    
                    # 统计转向类型
                    turn_type = turn_data['turn_type']
                    if turn_type not in self.stats['by_turn_type']:
                        self.stats['by_turn_type'][turn_type] = 0
                    self.stats['by_turn_type'][turn_type] += 1
                    
                    # 统计路口
                    cross_id = turn_data['cross_id']
                    if cross_id not in self.stats['by_cross']:
                        self.stats['by_cross'][cross_id] = 0
                    self.stats['by_cross'][cross_id] += 1
                    
                    print("创建转向: {} -> {} {} 方向{}->{}".format(
                        turn_data['cross_id'],
                        turn_data['id'],
                        turn_data['turn_type'],
                        turn_data['in_dir'],
                        turn_data['out_dir']
                    ))
            else:
                self.stats['error_count'] += 1
    
    def print_statistics(self):
        """打印统计信息"""
        print("\n=== 路口转向信息处理统计 ===")
        print("总处理数: {}".format(self.stats['total_processed']))
        print("成功创建: {}".format(self.stats['success_count']))
        print("处理错误: {}".format(self.stats['error_count']))
        print("成功率: {:.2f}%".format(
            (self.stats['success_count'] / max(self.stats['total_processed'], 1)) * 100
        ))
        
        print("\n转向类型分布:")
        turn_type_names = {'s': '直行', 'l': '左转', 'r': '右转', 'u': '掉头'}
        for turn_type, count in self.stats['by_turn_type'].items():
            name = turn_type_names.get(turn_type, turn_type)
            print("  {}: {} 条".format(name, count))
        
        print("\n路口转向数分布:")
        cross_count = len(self.stats['by_cross'])
        if cross_count > 0:
            avg_turns = sum(self.stats['by_cross'].values()) / cross_count
            print("  涉及路口数: {}".format(cross_count))
            print("  平均每路口转向数: {:.1f}".format(avg_turns))
            
            # 显示前5个路口的转向数
            sorted_crosses = sorted(self.stats['by_cross'].items(), 
                                  key=lambda x: x[1], reverse=True)
            print("  转向数最多的路口:")
            for i, (cross_id, count) in enumerate(sorted_crosses[:5]):
                print("    {}: {} 条转向".format(cross_id, count))
    
    def run(self):
        """运行处理器"""
        print("开始处理路口转向基础信息...")
        
        if not self.connect_database():
            return
        
        try:
            self.process_all_arrows()
            self.connection.commit()
            print("数据提交成功")
            
        except Exception as e:
            print("处理过程中发生错误: {}".format(e))
            self.connection.rollback()
            
        finally:
            self.print_statistics()
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()

if __name__ == "__main__":
    processor = CrossTurnProcessor()
    processor.run() 