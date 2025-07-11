import requests
import pandas as pd
from shapely.geometry import LineString
from pyproj import Transformer
from coord_convert.transform import gcj2wgs
import mysql.connector

import osmnx as ox
import geopandas as gpd
from shapely.geometry import LineString
import pandas as pd

# 多AK轮换策略
# AK_DICT = {1: 'ak1', 2: 'ak2', ...}  # 替换为实际AK
ak_index = 1
count = 0

def get_traffic_data(rectangle):
    url = "https://restapi.amap.com/v3/traffic/status/circle"
    params = {
        "key": "7d5c2cd1146d629e7437a6375cf42ef5",
        "location": rectangle,  # 格式："左下经,左下纬;右上经,右上纬"
        "extensions": "all",  # 返回全部路况细节
        "radius": "5000",
        "output": "json"
    }
    response=requests.get(url, params)
    # print(response.json())
    return response.json()

def parse_data(data_list):
    roads = []

    for item in data_list:
        # coords = [list(gcj2wgs(float( p.split(',')[0]),float( p.split(',')[1]))) for p in item['polyline'].split(';')]
        coords = [str(gcj2wgs(float( p.split(',')[0]),float( p.split(',')[1]))[0])+','+str(gcj2wgs(float( p.split(',')[0]),float( p.split(',')[1]))[1]) for p in item['polyline'].split(';')]
        # print(coords)
        strCoords=';'.join(coords)
        roads.append({
            "name": item['name'],
            "status": item['status'],
            "geometry": strCoords  # 转换为几何线段
        })
    return roads

def import_json_data(table_name,data_list):

    # 将 JSON 数据解析为 Python 字典
    # conn = db_conn("192.168.208.42", "5432","postgres",
    #                "Wanji300552", "wanji_supervise")
    # cursor = conn.cursor()
    # 连接到 MySQL 数据库
    conn = mysql.connector.connect(
        host='192.168.208.42',
        port=53306,
        user='root',
        password='Wanji300552',
        database='holo_roadnet_wh'
    )
    cursor = conn.cursor()

    # 执行批量插入操作
    for data in data_list:
        # 插入数据的 SQL 语句
        # insert_query = """
        # # INSERT INTO {0}.{1} (name, status, geom) VALUES ('{2}', '{3}', {4} ));
        # # """.format("public", table_name,data['name'],data['status'],"(select ST_GeomFromGeoJSON('{\"type\":\"LineString\",\"coordinates\": "+str(data['geometry'])+"}')")

        insert_query = """
         INSERT INTO {0} (name, status, wkt) VALUES ('{1}', '{2}', '{3}' );
         """.format( table_name,data['name'],data['status'],data['geometry'])
        print(insert_query)
        try:
            cursor.execute(insert_query)
        except Exception as e:
            print(e)
            # 提交事务
        conn.commit()
    # 关闭游标和连接
    cursor.close()
    conn.close()
    print("数据已成功插入到 数据库中。")

if __name__ == '__main__':
    # 示例：爬取武汉市矩形区域（步长0.01°≈1km）
    rect = "114.0866409747826, 30.453506578293883"
    data_list = []
    traffic_data = []

    # for i in range(1):  # 纬度方向
    #     for j in range(1):  # 经度方向
    #         rect = f"{base_lat+i*0.01},{base_lng+j*0.01};{base_lat+(i+1)*0.01},{base_lng+(j+1)*0.01}"
    data = get_traffic_data(rect)
    traffic_data.extend(data["trafficinfo"]["roads"])

            # if 'road_traffic' in data:
            #     print(data['road_traffic'])
            #     data_list.extend(data['road_traffic'])  # 存储道路数据
            # 路况（1绿,2黄,3红）0：未知;1：畅通;2：缓行;3：拥堵

    # print(traffic_data)
    roads=parse_data(traffic_data)
    import_json_data("t_traffic_data",roads)
    # print(roads)