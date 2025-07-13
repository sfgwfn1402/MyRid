#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
几何计算演示
这个文件展示如何在开发环境中运行Python代码（无红线）
"""

from shapely.geometry import Point, LineString, Polygon
import geographiclib.geodesic as geo
import numpy as np
import pandas as pd

def haikou_road_demo():
    """海口市道路几何计算演示"""
    print("🗺️  海口市道路几何计算演示")
    print("=" * 40)
    
    # 海口市一些关键点坐标
    locations = {
        '海口站': (110.3293, 20.0311),
        '美兰机场': (110.4588, 20.0206), 
        '海南大学': (110.3176, 20.0614),
        '万绿园': (110.3085, 20.0375),
        '五公祠': (110.3426, 20.0498)
    }
    
    print("📍 关键地点坐标:")
    for name, (lon, lat) in locations.items():
        print(f"  {name}: ({lon:.4f}, {lat:.4f})")
    
    return locations

def calculate_distances(locations):
    """计算地点间的距离"""
    print("\n📏 地点间距离计算:")
    
    # 使用geographiclib计算真实地理距离
    geod = geo.Geodesic.WGS84
    
    # 计算海口站到各地的距离
    base_point = locations['海口站']
    
    for name, point in locations.items():
        if name != '海口站':
            result = geod.Inverse(
                base_point[1], base_point[0],  # 纬度，经度
                point[1], point[0]
            )
            distance_m = result['s12']  # 距离（米）
            bearing = result['azi1']    # 方位角（度）
            
            print(f"  海口站 → {name}:")
            print(f"    距离: {distance_m:.0f}米 ({distance_m/1000:.2f}公里)")
            print(f"    方位角: {bearing:.1f}°")

def create_route_analysis():
    """创建路线分析"""
    print("\n🛣️  路线分析:")
    
    # 模拟一条从海口站到美兰机场的路线
    route_points = [
        (110.3293, 20.0311),  # 海口站
        (110.3500, 20.0280),  # 中间点1
        (110.3800, 20.0250),  # 中间点2  
        (110.4200, 20.0220),  # 中间点3
        (110.4588, 20.0206),  # 美兰机场
    ]
    
    # 创建线段
    route_line = LineString(route_points)
    
    print(f"  路线总长度: {route_line.length:.6f}度")
    print(f"  路线边界: {route_line.bounds}")
    
    # 计算实际距离
    total_distance = 0
    geod = geo.Geodesic.WGS84
    
    for i in range(len(route_points) - 1):
        p1 = route_points[i]
        p2 = route_points[i + 1]
        
        segment_dist = geod.Inverse(p1[1], p1[0], p2[1], p2[0])['s12']
        total_distance += segment_dist
        print(f"  段{i+1}: {segment_dist:.0f}米")
    
    print(f"  总实际距离: {total_distance:.0f}米 ({total_distance/1000:.2f}公里)")

def shapely_operations_demo():
    """Shapely几何操作演示"""
    print("\n📐 Shapely几何操作演示:")
    
    # 创建一些点
    points = [
        Point(110.30, 20.03),
        Point(110.35, 20.04), 
        Point(110.32, 20.06),
        Point(110.31, 20.05)
    ]
    
    # 创建多边形（海口某个区域）
    polygon_coords = [
        (110.30, 20.03),
        (110.35, 20.03),
        (110.35, 20.06),
        (110.30, 20.06),
        (110.30, 20.03)  # 闭合
    ]
    polygon = Polygon(polygon_coords)
    
    print(f"  区域面积: {polygon.area:.8f}平方度")
    print(f"  区域周长: {polygon.length:.6f}度")
    
    # 检查点是否在区域内
    for i, point in enumerate(points):
        inside = polygon.contains(point)
        status = "✅ 在区域内" if inside else "❌ 在区域外"
        print(f"  点{i+1} {point}: {status}")

def data_processing_demo():
    """数据处理演示"""
    print("\n📊 数据处理演示:")
    
    # 创建模拟的路段数据
    road_data = {
        'road_id': ['R001', 'R002', 'R003', 'R004'],
        'start_lon': [110.30, 110.32, 110.34, 110.36],
        'start_lat': [20.02, 20.03, 20.04, 20.05],
        'end_lon': [110.32, 110.34, 110.36, 110.38],
        'end_lat': [20.03, 20.04, 20.05, 20.06],
        'road_type': ['主干道', '次干道', '支路', '主干道']
    }
    
    df = pd.DataFrame(road_data)
    
    print("  路段数据预览:")
    print(df.to_string(index=False))
    
    # 计算每条路段的长度
    distances = []
    geod = geo.Geodesic.WGS84
    
    for _, row in df.iterrows():
        dist = geod.Inverse(
            row['start_lat'], row['start_lon'],
            row['end_lat'], row['end_lon']
        )['s12']
        distances.append(dist)
    
    df['length_m'] = distances
    
    print(f"\n  路段统计:")
    print(f"    总路段数: {len(df)}")
    print(f"    总长度: {sum(distances):.0f}米")
    print(f"    平均长度: {np.mean(distances):.0f}米")
    
    # 按道路类型分组
    type_stats = df.groupby('road_type')['length_m'].agg(['count', 'sum', 'mean'])
    print(f"\n  按道路类型统计:")
    print(type_stats)

def main():
    """主函数"""
    print("🎯 MyRid几何计算演示")
    print("这个演示展示了可以在开发环境中运行的Python代码\n")
    
    # 运行各个演示
    locations = haikou_road_demo()
    calculate_distances(locations)
    create_route_analysis()
    shapely_operations_demo()
    data_processing_demo()
    
    print("\n" + "=" * 50)
    print("🎉 演示完成！")
    print("💡 这些代码都可以在Cursor中正常运行，没有红线错误")
    print("🚀 试试修改坐标或添加新的计算功能！")

if __name__ == "__main__":
    main() 