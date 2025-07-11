import json

# 读取 JSON 文件
with open(r'd:\Downloads\市中区.json', 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# 获取坐标
coordinates = geojson_data['features'][0]['geometry']['coordinates']

# 定义递归函数以处理多维坐标
def format_coordinates(coords):
    if isinstance(coords[0][0], list):  # 检查是否为多边形
        return ';'.join(format_coordinates(polygon) for polygon in coords)
    else:
        return ';'.join(f"{lon},{lat}" for lon, lat in coords)

# 格式化坐标
formatted_coordinates = format_coordinates(coordinates)

# 输出结果
print(formatted_coordinates)
