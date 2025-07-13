#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql
import math
from datetime import datetime
import sys
import os

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from road_network.config.database_config import get_database_connection

class AreaCrossProcessor:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.stats = {
            'total_areas': 0,
            'total_crosses': 0,
            'relationships_created': 0,
            'errors': 0
        }
    
    def connect_database(self):
        try:
            self.connection = get_database_connection()
            self.cursor = self.connection.cursor()
            print("数据库连接成功")
        except Exception as e:
            print("数据库连接失败: {}".format(e))
            return False
        return True
    
    def parse_location(self, location_str):
        try:
            if not location_str:
                return None, None
            
            if ',' in location_str:
                parts = location_str.split(',')
                if len(parts) >= 2:
                    try:
                        lon = float(parts[0].strip())
                        lat = float(parts[1].strip())
                        return lon, lat
                    except ValueError:
                        pass
            
            if ':' in location_str and ',' in location_str:
                try:
                    parts = location_str.split(',')
                    if len(parts) >= 2:
                        lon_part = parts[0].strip()
                        if ':' in lon_part:
                            lon = float(lon_part.split(':')[1].strip())
                        else:
                            lon = float(lon_part)
                        
                        lat_part = parts[1].strip()
                        if ':' in lat_part:
                            lat = float(lat_part.split(':')[1].strip())
                        else:
                            lat = float(lat_part)
                        
                        return lon, lat
                except ValueError:
                    pass
            
            return None, None
                
        except Exception as e:
            return None, None
    
    def calculate_distance(self, lon1, lat1, lon2, lat2):
        try:
            R = 6371000
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)
            
            a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
                 math.cos(lat1_rad) * math.cos(lat2_rad) *
                 math.sin(delta_lon/2) * math.sin(delta_lon/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            distance = R * c
            return distance
            
        except Exception as e:
            return float('inf')
    
    def get_area_data(self):
        try:
            query = """
            SELECT id, name, type, location, code
            FROM t_base_area_info
            WHERE location IS NOT NULL AND location != ''
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            areas = []
            for row in results:
                area_id, name, area_type, location, code = row
                lon, lat = self.parse_location(location)
                
                if lon is not None and lat is not None:
                    areas.append({
                        'id': area_id,
                        'name': name,
                        'type': area_type,
                        'code': code,
                        'lon': lon,
                        'lat': lat
                    })
            
            self.stats['total_areas'] = len(areas)
            print("获取区域数据: {} 条".format(len(areas)))
            return areas
            
        except Exception as e:
            print("获取区域数据失败: {}".format(e))
            return []
    
    def get_cross_data(self):
        try:
            query = """
            SELECT id, name, type, location, area_code
            FROM t_base_cross_info
            WHERE location IS NOT NULL AND location != ''
            """
            self.cursor.execute(query)
            results = self.cursor.fetchall()
            
            crosses = []
            for row in results:
                cross_id, name, cross_type, location, area_code = row
                lon, lat = self.parse_location(location)
                
                if lon is not None and lat is not None:
                    crosses.append({
                        'id': cross_id,
                        'name': name,
                        'type': cross_type,
                        'area_code': area_code,
                        'lon': lon,
                        'lat': lat
                    })
            
            self.stats['total_crosses'] = len(crosses)
            print("获取路口数据: {} 条".format(len(crosses)))
            return crosses
            
        except Exception as e:
            print("获取路口数据失败: {}".format(e))
            return []
    
    def create_area_cross_relationship(self, area_id, cross_id):
        try:
            now = datetime.now()
            insert_query = """
            INSERT INTO t_base_area_cross (area_id, cross_id, gmt_create, gmt_modified)
            VALUES (%s, %s, %s, %s)
            """
            
            self.cursor.execute(insert_query, (area_id, cross_id, now, now))
            return True
            
        except pymysql.IntegrityError as e:
            if "Duplicate entry" in str(e):
                return False
            else:
                self.stats['errors'] += 1
                return False
        except Exception as e:
            self.stats['errors'] += 1
            return False
    
    def process_relationships(self):
        areas = self.get_area_data()
        crosses = self.get_cross_data()
        
        if not areas or not crosses:
            print("没有足够的数据进行处理")
            return
        
        print("开始处理区域路口关系...")
        
        relationships_created = 0
        
        for cross in crosses:
            min_distance = float('inf')
            closest_area = None
            
            for area in areas:
                distance = self.calculate_distance(
                    cross['lon'], cross['lat'],
                    area['lon'], area['lat']
                )
                
                if distance < min_distance:
                    min_distance = distance
                    closest_area = area
            
            if closest_area and min_distance <= 5000:
                if self.create_area_cross_relationship(closest_area['id'], cross['id']):
                    relationships_created += 1
                    print("创建关系: area_id={} -> cross_id={} 距离:{:.2f}m".format(
                        closest_area['id'],
                        cross['id'],
                        min_distance
                    ))
            
            if cross['area_code'] and cross['area_code'] != 0:
                for area in areas:
                    if area['code'] == cross['area_code']:
                        if self.create_area_cross_relationship(area['id'], cross['id']):
                            relationships_created += 1
                            print("创建关系(区域代码匹配): area_id={} -> cross_id={}".format(
                                area['id'],
                                cross['id']
                            ))
                        break
        
        self.stats['relationships_created'] = relationships_created
        print("成功创建 {} 个区域路口关系".format(relationships_created))
    
    def print_statistics(self):
        print("\n=== 区域路口关系处理统计 ===")
        print("区域总数: {}".format(self.stats['total_areas']))
        print("路口总数: {}".format(self.stats['total_crosses']))
        print("成功创建关系: {}".format(self.stats['relationships_created']))
        print("处理错误: {}".format(self.stats['errors']))
        print("关系创建率: {:.2f}%".format(
            (self.stats['relationships_created'] / max(self.stats['total_crosses'], 1)) * 100
        ))
    
    def run(self):
        print("开始处理区域路口关系...")
        
        if not self.connect_database():
            return
        
        try:
            self.process_relationships()
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
    processor = AreaCrossProcessor()
    processor.run() 