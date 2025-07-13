#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
路段基础信息处理器
从luwangJson/路段面.json文件中提取数据并导入到MySQL数据库的路段基础表中
"""

import json
import pymysql
from datetime import datetime
import logging
import sys
from imp import reload
import re
import math
reload(sys)
sys.setdefaultencoding('utf-8')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RidInfoProcessor:
    """路段基础信息处理器"""
    
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
        创建路段基础信息表
        
        Returns:
            bool: 表创建是否成功
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS t_base_rid_info (
            id CHAR(23) PRIMARY KEY COMMENT '路段编号',
            name VARCHAR(50) DEFAULT NULL COMMENT '路段名称',
            road_id CHAR(23) DEFAULT NULL COMMENT '道路编号',
            road_name VARCHAR(50) DEFAULT NULL COMMENT '道路名称',
            road_dir_id CHAR(23) DEFAULT NULL COMMENT '道路方向编号',
            start_cross_id CHAR(11) DEFAULT NULL COMMENT '开始路口编号',
            end_cross_id CHAR(11) DEFAULT NULL COMMENT '结束路口编号',
            out_dir INT(11) DEFAULT NULL COMMENT '驶出方向：1北；2东北；3东；4东南；5南；6西南；7西；8西北',
            in_dir INT(11) DEFAULT NULL COMMENT '驶入方向：1北；2东北；3东；4东南；5南；6西南；7西；8西北',
            start_angle DOUBLE DEFAULT NULL COMMENT '驶出角度，正北顺时针0-359',
            end_angle DOUBLE DEFAULT NULL COMMENT '驶入角度，正北顺时针0-359',
            direction INT(11) DEFAULT NULL COMMENT '行驶方向：0上行；1下行',
            sort INT(11) DEFAULT NULL COMMENT '顺序号：路段在道路方向的顺序号',
            trend INT(11) DEFAULT NULL COMMENT '路段走向：1南向北；2西向东；3北向南；4东向西；5内环；6外环；99其他',
            level INT(11) DEFAULT NULL COMMENT '道路等级：41000高速公路；42000国道；43000城市快速路；44000城市主干道；45000城市次干道；47000城市普通道路；51000省道；52000县道；53000乡道；54000县乡村内部道路；49小路',
            area_code VARCHAR(50) DEFAULT NULL COMMENT '行政区划代码',
            length DOUBLE DEFAULT NULL COMMENT '路段长度（米）',
            width DOUBLE DEFAULT NULL COMMENT '路段宽度（米）',
            is_oneway INT(11) DEFAULT NULL COMMENT '是否单行线：0否；1是；99其他',
            type INT(11) DEFAULT NULL COMMENT '路段类型：1路段；3匝道；4隧道；5桥梁；6高架；99其他',
            main_flag INT(11) DEFAULT NULL COMMENT '主辅标志：1主路；2辅路；99其他',
            wkt VARCHAR(200) DEFAULT NULL COMMENT '空间对象',
            sc_id CHAR(23) DEFAULT NULL COMMENT '信控路段编号',
            sc_name VARCHAR(50) DEFAULT NULL COMMENT '信控路段名称',
            sc_sort INT(11) DEFAULT NULL COMMENT '信控路段序号',
            gmt_create DATETIME DEFAULT NULL COMMENT '创建时间',
            gmt_modified DATETIME DEFAULT NULL COMMENT '修改时间'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='路段基础信息表';
        """
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_table_sql)
                self.connection.commit()
                logger.info("路段基础信息表创建成功")
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
            List[Dict]: 路段数据列表
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
    
    def extract_cross_ids_from_name(self, name):
        """
        从路段名称中提取路口信息
        
        Args:
            name: 路段名称，如"全力二路-全力南路-朱山湖大道"
            
        Returns:
            tuple: (start_cross_name, end_cross_name)
        """
        if not name:
            return None, None
        
        # 分割路段名称
        parts = name.split('-')
        if len(parts) >= 3:
            start_cross_name = parts[0] + "与" + parts[1] + "交叉口"
            end_cross_name = parts[1] + "与" + parts[2] + "交叉口"
        elif len(parts) == 2:
            start_cross_name = parts[0] + "与" + parts[1] + "交叉口"
            end_cross_name = parts[1] + "交叉口"
        else:
            start_cross_name = name
            end_cross_name = name
        
        return start_cross_name, end_cross_name
    
    def infer_road_level(self, name):
        """
        根据路段名称推断道路等级
        
        Args:
            name: 路段名称
            
        Returns:
            int: 道路等级代码
        """
        if not name:
            return 47000  # 默认城市普通道路
        
        name_unicode = unicode(name, 'utf-8') if isinstance(name, str) else name
        
        # 道路等级推断规则
        if u"高速" in name_unicode:
            return 41000  # 高速公路
        elif u"国道" in name_unicode:
            return 42000  # 国道
        elif u"快速" in name_unicode:
            return 43000  # 城市快速路
        elif u"主干道" in name_unicode or u"大道" in name_unicode:
            return 44000  # 城市主干道
        elif u"次干道" in name_unicode:
            return 45000  # 城市次干道
        elif u"省道" in name_unicode:
            return 51000  # 省道
        elif u"县道" in name_unicode:
            return 52000  # 县道
        elif u"乡道" in name_unicode:
            return 53000  # 乡道
        elif u"小路" in name_unicode or u"巷" in name_unicode:
            return 49  # 小路
        else:
            return 47000  # 城市普通道路
    
    def infer_road_type(self, name):
        """
        根据路段名称推断路段类型
        
        Args:
            name: 路段名称
            
        Returns:
            int: 路段类型代码
        """
        if not name:
            return 1  # 默认路段
        
        name_unicode = unicode(name, 'utf-8') if isinstance(name, str) else name
        
        if u"匝道" in name_unicode:
            return 3  # 匝道
        elif u"隧道" in name_unicode:
            return 4  # 隧道
        elif u"桥" in name_unicode:
            return 5  # 桥梁
        elif u"高架" in name_unicode:
            return 6  # 高架
        else:
            return 1  # 路段
    
    def calculate_length_from_geometry(self, geometry):
        """
        根据几何坐标计算路段长度
        
        Args:
            geometry: 几何对象
            
        Returns:
            float: 长度（米）
        """
        if not geometry or geometry.get('type') != 'Polygon':
            return 0.0
        
        coordinates = geometry.get('coordinates', [])
        if not coordinates:
            return 0.0
        
        # 取第一个环的坐标
        ring = coordinates[0]
        if len(ring) < 2:
            return 0.0
        
        # 计算周长的一半作为长度估算
        total_length = 0.0
        for i in range(len(ring) - 1):
            lon1, lat1 = ring[i][:2]
            lon2, lat2 = ring[i + 1][:2]
            
            # 使用简单的距离公式计算
            distance = math.sqrt((lon2 - lon1)**2 + (lat2 - lat1)**2) * 111000  # 粗略转换为米
            total_length += distance
        
        return total_length / 2  # 返回周长的一半作为长度估算
    
    def calculate_trend_from_geometry(self, geometry):
        """
        根据几何坐标计算路段走向
        
        Args:
            geometry: 几何对象
            
        Returns:
            int: 走向代码
        """
        if not geometry or geometry.get('type') != 'Polygon':
            return 99  # 其他
        
        coordinates = geometry.get('coordinates', [])
        if not coordinates:
            return 99
        
        ring = coordinates[0]
        if len(ring) < 2:
            return 99
        
        # 计算起点和终点的方向
        start_point = ring[0]
        end_point = ring[len(ring)//2]  # 取中间点作为终点
        
        lon_diff = end_point[0] - start_point[0]
        lat_diff = end_point[1] - start_point[1]
        
        # 根据坐标差异判断走向
        if abs(lat_diff) > abs(lon_diff):
            if lat_diff > 0:
                return 1  # 南向北
            else:
                return 3  # 北向南
        else:
            if lon_diff > 0:
                return 2  # 西向东
            else:
                return 4  # 东向西
    
    def polygon_to_wkt(self, geometry):
        """
        将多边形几何转换为WKT格式
        
        Args:
            geometry: 几何对象
            
        Returns:
            str: WKT字符串
        """
        if not geometry or geometry.get('type') != 'Polygon':
            return None
        
        coordinates = geometry.get('coordinates', [])
        if not coordinates:
            return None
        
        # 只取第一个环
        ring = coordinates[0]
        if len(ring) < 3:
            return None
        
        # 构建WKT字符串
        points = []
        for coord in ring:
            points.append("{} {}".format(coord[0], coord[1]))
        
        wkt = "POLYGON(({})".format(", ".join(points))
        
        # 截断到200字符
        if len(wkt) > 200:
            wkt = wkt[:197] + "..."
        
        return wkt
    
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
        
        current_time = datetime.now()
        
        # 提取基本信息
        ldid = properties.get('ldid', '')
        ldmc = properties.get('ldmc', '')
        fcxx = properties.get('fcxx', '200')
        
        # 从名称中提取路口信息
        start_cross_name, end_cross_name = self.extract_cross_ids_from_name(ldmc)
        
        # 计算几何相关信息
        length = self.calculate_length_from_geometry(geometry)
        trend = self.calculate_trend_from_geometry(geometry)
        wkt = self.polygon_to_wkt(geometry)
        
        # 构建数据库记录
        record = {
            'id': ldid,
            'name': ldmc,
            'road_id': ldid[:11] if ldid else '',  # 取前11位作为道路编号
            'road_name': ldmc.split('-')[0] if ldmc else '',  # 取第一个道路名称
            'road_dir_id': ldid,
            'start_cross_id': None,  # 需要与路口表关联
            'end_cross_id': None,    # 需要与路口表关联
            'out_dir': 1,  # 默认北向
            'in_dir': 1,   # 默认北向
            'start_angle': 0.0,
            'end_angle': 0.0,
            'direction': 0,  # 默认上行
            'sort': 1,       # 默认序号
            'trend': trend,
            'level': self.infer_road_level(ldmc),
            'area_code': '420100',  # 武汉市市辖区
            'length': length,
            'width': float(fcxx) if fcxx and fcxx.isdigit() else 20.0,
            'is_oneway': 0,  # 默认非单行线
            'type': self.infer_road_type(ldmc),
            'main_flag': 1,  # 默认主路
            'wkt': wkt,
            'sc_id': ldid,
            'sc_name': ldmc,
            'sc_sort': 1,
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
        INSERT INTO t_base_rid_info 
        (id, name, road_id, road_name, road_dir_id, start_cross_id, end_cross_id, 
         out_dir, in_dir, start_angle, end_angle, direction, sort, trend, level, 
         area_code, length, width, is_oneway, type, main_flag, wkt, sc_id, sc_name, 
         sc_sort, gmt_create, gmt_modified)
        VALUES (%(id)s, %(name)s, %(road_id)s, %(road_name)s, %(road_dir_id)s, 
                %(start_cross_id)s, %(end_cross_id)s, %(out_dir)s, %(in_dir)s, 
                %(start_angle)s, %(end_angle)s, %(direction)s, %(sort)s, %(trend)s, 
                %(level)s, %(area_code)s, %(length)s, %(width)s, %(is_oneway)s, 
                %(type)s, %(main_flag)s, %(wkt)s, %(sc_id)s, %(sc_name)s, 
                %(sc_sort)s, %(gmt_create)s, %(gmt_modified)s)
        ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        road_name = VALUES(road_name),
        length = VALUES(length),
        width = VALUES(width),
        wkt = VALUES(wkt),
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
        logger.info("开始处理路段基础信息数据...")
        
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
                cursor.execute("SELECT COUNT(*) as total FROM t_base_rid_info")
                total = cursor.fetchone()['total']
                
                # 按道路等级统计
                cursor.execute("""
                    SELECT level, COUNT(*) as count 
                    FROM t_base_rid_info 
                    GROUP BY level 
                    ORDER BY count DESC
                """)
                level_stats = cursor.fetchall()
                
                # 按路段类型统计
                cursor.execute("""
                    SELECT type, COUNT(*) as count 
                    FROM t_base_rid_info 
                    GROUP BY type 
                    ORDER BY type
                """)
                type_stats = cursor.fetchall()
                
                # 按走向统计
                cursor.execute("""
                    SELECT trend, COUNT(*) as count 
                    FROM t_base_rid_info 
                    GROUP BY trend 
                    ORDER BY trend
                """)
                trend_stats = cursor.fetchall()
                
                return {
                    'total': total,
                    'level_stats': level_stats,
                    'type_stats': type_stats,
                    'trend_stats': trend_stats
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
    json_file_path = 'luwangJson/路段面.json'
    
    # 创建处理器
    processor = RidInfoProcessor(db_config)
    
    # 处理数据
    if processor.process_all(json_file_path):
        logger.info("数据处理完成！")
        
        # 查询统计信息
        stats = processor.query_statistics()
        if stats:
            print("\n=== 导入统计信息 ===")
            print("总记录数: {}".format(stats['total']))
            
            print("\n道路等级统计:")
            level_names = {
                41000: "高速公路", 42000: "国道", 43000: "城市快速路",
                44000: "城市主干道", 45000: "城市次干道", 47000: "城市普通道路",
                51000: "省道", 52000: "县道", 53000: "乡道", 
                54000: "县乡村内部道路", 49: "小路"
            }
            for stat in stats['level_stats']:
                level_name = level_names.get(stat['level'], "等级{}".format(stat['level']))
                print("  {}: {}条".format(level_name, stat['count']))
            
            print("\n路段类型统计:")
            type_names = {1: "路段", 3: "匝道", 4: "隧道", 5: "桥梁", 6: "高架", 99: "其他"}
            for stat in stats['type_stats']:
                type_name = type_names.get(stat['type'], "类型{}".format(stat['type']))
                print("  {}: {}条".format(type_name, stat['count']))
            
            print("\n走向统计:")
            trend_names = {
                1: "南向北", 2: "西向东", 3: "北向南", 4: "东向西",
                5: "内环", 6: "外环", 99: "其他"
            }
            for stat in stats['trend_stats']:
                trend_name = trend_names.get(stat['trend'], "走向{}".format(stat['trend']))
                print("  {}: {}条".format(trend_name, stat['count']))
    else:
        logger.error("数据处理失败！")

if __name__ == "__main__":
    main() 