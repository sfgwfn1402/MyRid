import json
from Geocoding import Geocoding
import geopandas as gpd
from sqlalchemy import create_engine


# 示例线段的坐标列表
def convert_to_2d_array(data, n):
    # 使用列表推导式将一维数组转换为二维数组
    return [data[i:i + n] for i in range(0, len(data), n)]


def import_geojson_data(geojson_file):
    # 读取 GeoJSON 文件
    gdf = gpd.read_file(geojson_file, encoding='gbk')

    # 创建数据库连接，替换以下信息
    # 格式: postgis://username:password@hostname:port/database
    db_url = 'postgresql://postgres:Wanji300552@106.120.201.126:14727/gisc_jinan_1101'
    engine = create_engine(db_url)
    # 将数据写入 PostGIS 数据表
    # 如果表不存在则会创建表
    gdf.to_postgis(name='gaode_link', con=engine, if_exists='replace', index=True,index_label="gid")

    print("数据成功导入到 PostGIS 数据表！")


# 读取 JSON 文件
with open('D:\\Wanji\\济南绿波城项目\\百度数据接入\\arteries.json', 'r', encoding='utf8') as file:
    data = json.load(file)
features=[]
# 遍历 JSON 数组并打印每个元素
for item in data:
    arteryId = item['artery_id']
    arteryName= item['name']
    coordinates = item['artery_points']
    passData= item['pass']
    startIntsid= item['start_intsid']
    endIntsid= item['end_intsid']
    forwardId= item['forward_id']
    backwardId= item['backward_id']
    forwardDirect= item['forward_direct']
    backwardDirect= item['backward_direct']
    backwardArteryPoints= item['backward_artery_points']
    #print(coordinates)
    #print(f"linkId: {linkId},roadName: {roadName},length: {length},formway: {formway} ,roadclass: {roadclass}, coordList: {coordinates}")
    #
    features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [ Geocoding().BD09_to_WGS84(coord['longitude'], coord['latitude']) for coord in coordinates]
                },
                "properties": {
                    "arteryId": arteryId,
                    "arteryName": arteryName,
                    "passData": passData,
                    "startIntsid": startIntsid,
                    "endIntsid": endIntsid,
                    "forwardId": forwardId,
                    "backwardId": backwardId,
                    "forwardDirect": forwardDirect,
                    "backwardDirect": backwardDirect,
                    "backwardArteryPoints": backwardArteryPoints
                }
            })

# 构建 GeoJSON 数据
geojson = {
        "type": "FeatureCollection",
        "features":features
    }

# 打印 GeoJSON 输出
#geojson_str = json.dumps(geojson, ensure_ascii=False, indent=2)
print(geojson)
# 将数据写入 JSON 文件
with open('D:\\Wanji\\济南绿波城项目\\百度数据接入\\arteries_data.geojson', 'w') as json_file:
    json.dump(geojson, json_file, ensure_ascii=False, indent=4)

# import_geojson_data('D:\\Wanji\\济南绿波城项目\\高德数据接入\gaode_link_new.json')

