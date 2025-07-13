#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试演示文件
演示如何在Cursor中使用Python调试功能
"""

from shapely.geometry import Point, LineString
import numpy as np
import pandas as pd

def calculate_road_distance(start_point, end_point):
    """
    计算两点间距离（演示调试功能）
    可以在这里设置断点调试
    """
    # 断点1：设置在这里，查看输入参数
    print(f"开始计算距离: {start_point} -> {end_point}")
    
    # 创建Shapely点对象
    p1 = Point(start_point[0], start_point[1])
    p2 = Point(end_point[0], end_point[1])
    
    # 断点2：设置在这里，查看点对象
    distance = p1.distance(p2)
    
    # 断点3：设置在这里，查看计算结果
    print(f"计算完成，距离: {distance}")
    
    return distance

def process_road_data():
    """
    处理路段数据（演示复杂调试场景）
    """
    # 模拟海口市路段数据
    roads = [
        {"id": "R001", "start": (110.30, 20.02), "end": (110.32, 20.03), "type": "主干道"},
        {"id": "R002", "start": (110.32, 20.03), "end": (110.34, 20.04), "type": "次干道"},
        {"id": "R003", "start": (110.34, 20.04), "end": (110.36, 20.05), "type": "支路"},
        {"id": "R004", "start": (110.36, 20.05), "end": (110.38, 20.06), "type": "主干道"},
    ]
    
    results = []
    
    # 断点4：设置在循环开始处
    for i, road in enumerate(roads):
        print(f"处理路段 {i+1}/{len(roads)}: {road['id']}")
        
        # 断点5：设置在这里，查看当前路段数据
        start_point = road["start"]
        end_point = road["end"]
        road_type = road["type"]
        
        # 计算距离
        distance = calculate_road_distance(start_point, end_point)
        
        # 创建结果字典
        result = {
            "road_id": road["id"],
            "distance": distance,
            "type": road_type,
            "length_category": "长" if distance > 0.02 else "短"
        }
        
        # 断点6：设置在这里，查看结果
        results.append(result)
    
    return results

def analyze_results(results):
    """
    分析结果数据
    """
    # 断点7：设置在这里，查看所有结果
    df = pd.DataFrame(results)
    
    print("📊 路段分析结果:")
    print(df)
    
    # 统计分析
    total_roads = len(df)
    avg_distance = df['distance'].mean()
    max_distance = df['distance'].max()
    min_distance = df['distance'].min()
    
    # 断点8：设置在这里，查看统计数据
    stats = {
        "total_roads": total_roads,
        "avg_distance": avg_distance,
        "max_distance": max_distance, 
        "min_distance": min_distance
    }
    
    print(f"\n📈 统计信息:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return stats

def debug_with_error():
    """
    故意包含错误的函数，用于演示错误调试
    """
    try:
        # 这里会产生除零错误
        numbers = [1, 2, 3, 0, 5]
        results = []
        
        for i, num in enumerate(numbers):
            # 断点9：设置在这里，观察错误发生
            result = 10 / num  # 当num=0时会出错
            results.append(result)
            
        return results
        
    except ZeroDivisionError as e:
        # 断点10：设置在异常处理处
        print(f"❌ 捕获到除零错误: {e}")
        print(f"错误发生在索引: {i}, 值: {num}")
        return None

def main():
    """
    主函数 - 调试入口点
    """
    print("🐛 MyRid调试演示")
    print("=" * 40)
    
    # 断点11：设置在程序开始处
    print("1. 开始处理路段数据...")
    results = process_road_data()
    
    print("\n2. 分析结果...")
    stats = analyze_results(results)
    
    print("\n3. 测试错误处理...")
    error_result = debug_with_error()
    
    # 断点12：设置在程序结束处
    print("\n🎉 调试演示完成!")
    return results, stats

if __name__ == "__main__":
    main() 