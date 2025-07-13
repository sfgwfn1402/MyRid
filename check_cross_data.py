#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pymysql

try:
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='123456',
        database='gisc_haikou',
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    # 查看路口数据
    cursor.execute('SELECT cross_id, ST_AsText(geom) FROM t_base_cross_info LIMIT 5')
    results = cursor.fetchall()
    print('现有路口数据:')
    for row in results:
        print('路口ID: {}, 几何: {}'.format(row[0], row[1]))
        
    cursor.close()
    conn.close()
    
except Exception as e:
    print('数据库连接失败: {}'.format(e)) 