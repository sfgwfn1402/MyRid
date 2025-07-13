#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于路段ID结构更新路口关联
路段ID格式：[起点路口ID(11位)][终点路口ID(11位)][序号(1位)]
"""

import pymysql
import logging
import sys
from imp import reload
reload(sys)
sys.setdefaultencoding('utf-8')

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RidCrossIdUpdater:
    """基于ID结构的路段路口关联更新器"""
    
    def __init__(self, db_config):
        """
        初始化更新器
        
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
    
    def extract_cross_ids_from_rid_id(self, rid_id):
        """
        从路段ID中提取起终点路口ID
        
        Args:
            rid_id: 路段ID（23位）
            
        Returns:
            tuple: (start_cross_id, end_cross_id)
        """
        if not rid_id or len(rid_id) != 23:
            return None, None
        
        # 路段ID格式：[起点路口ID(11位)][终点路口ID(11位)][序号(1位)]
        start_cross_id = rid_id[:11]  # 前11位
        end_cross_id = rid_id[11:22]  # 中间11位
        
        return start_cross_id, end_cross_id
    
    def validate_cross_exists(self, cross_id):
        """
        验证路口ID是否存在于路口表中
        
        Args:
            cross_id: 路口ID
            
        Returns:
            bool: 是否存在
        """
        if not cross_id:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1 FROM t_base_cross_info WHERE id = %s", (cross_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.warning("验证路口ID失败: {}".format(e))
            return False
    
    def update_rid_cross_ids(self):
        """基于路段ID结构更新路口关联"""
        try:
            with self.connection.cursor() as cursor:
                # 获取所有路段记录
                cursor.execute("SELECT id, name FROM t_base_rid_info")
                rids = cursor.fetchall()
                
                updated_count = 0
                success_count = 0
                
                for rid in rids:
                    rid_id = rid['id']
                    rid_name = rid['name']
                    
                    # 从路段ID中提取起终点路口ID
                    start_cross_id, end_cross_id = self.extract_cross_ids_from_rid_id(rid_id)
                    
                    if not start_cross_id or not end_cross_id:
                        logger.warning("路段ID格式不正确: {}".format(rid_id))
                        continue
                    
                    # 验证路口ID是否存在
                    start_exists = self.validate_cross_exists(start_cross_id)
                    end_exists = self.validate_cross_exists(end_cross_id)
                    
                    # 准备更新的值
                    update_start_id = start_cross_id if start_exists else None
                    update_end_id = end_cross_id if end_exists else None
                    
                    # 更新数据库记录
                    update_sql = """
                    UPDATE t_base_rid_info 
                    SET start_cross_id = %s,
                        end_cross_id = %s,
                        gmt_modified = NOW()
                    WHERE id = %s
                    """
                    
                    cursor.execute(update_sql, (update_start_id, update_end_id, rid_id))
                    
                    updated_count += 1
                    if start_exists and end_exists:
                        success_count += 1
                    
                    status = "✅" if (start_exists and end_exists) else "⚠️"
                    logger.info("{} 路段 {}: 起点{}={}, 终点{}={}".format(
                        status, rid_id[:15], 
                        "✓" if start_exists else "✗", start_cross_id,
                        "✓" if end_exists else "✗", end_cross_id
                    ))
                
                self.connection.commit()
                logger.info("更新完成！总计:{}, 成功:{}, 部分成功:{}".format(
                    updated_count, success_count, updated_count - success_count
                ))
                return True
                
        except Exception as e:
            logger.error("更新路段关联失败: {}".format(e))
            self.connection.rollback()
            return False
    
    def query_update_results(self):
        """查询更新结果统计"""
        try:
            with self.connection.cursor() as cursor:
                # 总体统计
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(start_cross_id) as has_start,
                        COUNT(end_cross_id) as has_end,
                        COUNT(CASE WHEN start_cross_id IS NOT NULL AND end_cross_id IS NOT NULL THEN 1 END) as both_exist
                    FROM t_base_rid_info
                """)
                stats = cursor.fetchone()
                
                # 查看具体的匹配情况
                cursor.execute("""
                    SELECT 
                        r.id,
                        r.name,
                        r.start_cross_id,
                        c1.name as start_cross_name,
                        r.end_cross_id,
                        c2.name as end_cross_name
                    FROM t_base_rid_info r
                    LEFT JOIN t_base_cross_info c1 ON r.start_cross_id = c1.id
                    LEFT JOIN t_base_cross_info c2 ON r.end_cross_id = c2.id
                    WHERE r.start_cross_id IS NOT NULL OR r.end_cross_id IS NOT NULL
                    ORDER BY 
                        CASE WHEN r.start_cross_id IS NOT NULL AND r.end_cross_id IS NOT NULL THEN 1 ELSE 2 END,
                        r.id
                    LIMIT 10
                """)
                samples = cursor.fetchall()
                
                return {
                    'stats': stats,
                    'samples': samples
                }
        except Exception as e:
            logger.error("查询更新结果失败: {}".format(e))
            return {}
    
    def process_all(self):
        """执行完整的更新流程"""
        logger.info("开始基于路段ID结构更新路口关联...")
        
        # 1. 连接数据库
        if not self.connect_database():
            return False
        
        # 2. 更新路段关联
        if not self.update_rid_cross_ids():
            return False
        
        # 3. 查询和显示结果
        results = self.query_update_results()
        if results:
            stats = results['stats']
            samples = results['samples']
            
            print("\n" + "="*60)
            print("📊 更新结果统计")
            print("="*60)
            print("总路段数: {}".format(stats['total']))
            print("有起点路口: {} ({:.1f}%)".format(
                stats['has_start'], 
                stats['has_start'] * 100.0 / stats['total']
            ))
            print("有终点路口: {} ({:.1f}%)".format(
                stats['has_end'], 
                stats['has_end'] * 100.0 / stats['total']
            ))
            print("起终点都有: {} ({:.1f}%)".format(
                stats['both_exist'], 
                stats['both_exist'] * 100.0 / stats['total']
            ))
            
            print("\n" + "="*60)
            print("📋 匹配示例（前10条）")
            print("="*60)
            for i, sample in enumerate(samples, 1):
                start_status = "✅" if sample['start_cross_id'] else "❌"
                end_status = "✅" if sample['end_cross_id'] else "❌"
                
                print("{}. 路段: {}".format(i, sample['name'][:30]))
                print("   起点 {}: {} - {}".format(
                    start_status, 
                    sample['start_cross_id'] or 'NULL',
                    sample['start_cross_name'] or '未找到'
                ))
                print("   终点 {}: {} - {}".format(
                    end_status,
                    sample['end_cross_id'] or 'NULL', 
                    sample['end_cross_name'] or '未找到'
                ))
                print()
        
        # 4. 关闭连接
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
    updater = RidCrossIdUpdater(db_config)
    
    # 执行更新
    if updater.process_all():
        logger.info("🎉 路口关联更新完成！")
    else:
        logger.error("❌ 路口关联更新失败！")

if __name__ == "__main__":
    main() 