import json
import mysql.connector
from datetime import datetime, timedelta
import requests
import base64

def import_json_data(area_name,table_name,data_list):

    # 将 JSON 数据解析为 Python 字典
    # 连接到 MySQL 数据库
    connection = mysql.connector.connect(
        host='37.12.182.29',
        user='root',
        password='Wanji300552',
        database='wjdit_ecosystem_db_v1.0.0'
    )
    cursor = connection.cursor()
    # 插入数据的 SQL 语句
    insert_query = """
    INSERT INTO {0} (start, end, value) VALUES (%s, %s, %s);
    """.format(table_name)
    #print(data_list)
    # 准备要插入的数据
    # data_to_insert = [(datetime.utcfromtimestamp(data['start']/ 1000),datetime.utcfromtimestamp(data['end']/1000), float(data['value'])) for data in data_list['24160100012']]
    #print(data_to_insert)
    # 执行批量插入操作
    for data in data_list[area_name]:
        data_to_insert=(datetime.fromtimestamp(data['start']/ 1000),datetime.fromtimestamp(data['end']/1000), float(data['value']))
        try:
            cursor.execute(insert_query, data_to_insert)
        except Exception as e:
            print(e)
            # 提交事务
    connection.commit()
    # 关闭游标和连接
    cursor.close()
    connection.close()
    print("数据已成功插入到 MySQL 数据库中。")


base_url="http://172.54.0.29:8880/"
# 定义参数
token_url = "oauth/token"  # OAuth2令牌请求的URL
# client_id = "your_client_id"
# client_secret = "your_client_secret"
# scopes = "your_scopes"  # 可选，具体根据API要求
ak="wanji"
sk="dhso_y6mh"
original_string=ak+":"+sk
bytes_string = original_string.encode("utf-8")
# 进行Base64编码
base64_encoded = base64.b64encode(bytes_string)
base64_string = base64_encoded.decode("utf-8")

print(base64_string)
# 自定义请求头
headers = {
    'Authorization': 'Basic '+ base64_string # 如果需要认证，设置Authorization头
}
# 创建请求的负载
payload = {
    'grant_type': 'client_credentials'  #,  # 授权类型
}
# 发送请求
response = requests.post(base_url+token_url,headers=headers, data=payload)
# 检查响应
if response.status_code == 200:
    # 解析JSON响应
    token_info = response.json()
    #print("token_info:", token_info)
    access_token = token_info.get("access_token")
    print("Access Token:", access_token)
    headers2 = {
        'Authorization': 'Bearer ' + access_token  # 如果需要认证，设置Authorization头
    }
    print(headers2)
    # 7.查询区域列表
    resp7 = requests.get(base_url+'road-api/bdmap/regions?type=2', headers=headers2)
    if resp7.status_code == 200:
        print("区域列表",resp7.json().get("data"))
        data=resp7.json().get("data")
        #print('data->'+data)
        regions=[]
        for item in resp7.json().get("data"):
            for children in item['children']:
                regions.append(children['region_id'])
        #print(regions)
        #8.查询区域指标
        payload = {
            'ids': [ str(region) for region in regions ],   # 区域id ，限制在100个以内，超过100个多次获取
            # 'dates': [datetime.now().strftime('%Y-%m-%d')], #日期20241111-20241112
            'dates': ['2024-12-11'],
            # 'startTime': (datetime.now()-timedelta(hours=1)).strftime('%H:%M:%S'),  #开始时间 HH: mm:ss
            'startTime': '00:00:00',  # 开始时间 HH: mm:ss
            'endTime': '23:59:59',  # 结束时间 HH: mm:ss
            'aggGrain': 'P5' #时间粒度P5
        }
        print(payload)
        #数据标识5003 车均速度 5006 拥堵指数
        resp85003 = requests.post(base_url + 'aitpm-statistic/aitpm/statistic/api/region/all/batch/5003', headers=headers2, json=payload)
        if resp85003.status_code == 200:
            print("车均速度",json.dumps(resp85003.json().get("data")))
            import_json_data(str(regions[0]),'bd_vehicle_speed_test', resp85003.json().get("data"))
        else:
            print("Error:", resp85003.status_code, resp85003.text)

        resp85006 = requests.post(base_url + 'aitpm-statistic/aitpm/statistic/api/region/all/batch/5006' , headers=headers2, json=payload)
        if resp85006.status_code == 200:
            print("拥堵指数",json.dumps(resp85006.json().get("data")))
            import_json_data(str(regions[0]),'bd_vehicle_yd_test', resp85006.json().get("data"))
        else:
            print("Error:", resp85006.status_code, resp85006.text)
    else:
        print("Error:", resp7.status_code, resp7.text)

else:
    print("Error:", response.status_code, response.text)
# # 将数据写入 JSON 文件
# with open('D:\\Wanji\\济南绿波城项目\\百度数据接入\\车均速度.json', 'r', encoding='utf8') as file:
#     data_list = json.load(file)
