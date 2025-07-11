import json
import mysql.connector
from datetime import datetime, timedelta
import requests
import base64


base_url="https://37.8.219.231"
# 定义参数
token_url = "/api/bms/1.0/appKey/login"  # OAuth2令牌请求的URL
# client_id = "your_client_id"
# client_secret = "your_client_secret"
# scopes = "your_scopes"  # 可选，具体根据API要求
appKey="20dd1847e6a7410a9b5ee911be01cff2"
appSecret="89ce235a7a2fc756cc23c0b7dc810939"


# 创建请求的负载
payload = {
    "appKey": appKey,
    "appSecret": appSecret
}
print(payload)
# 发送请求
response = requests.post(base_url+token_url, data=json.dumps(payload),headers={'Content-Type':'application/json'},verify=False)
# 检查响应
if response.status_code == 200:
    # 解析JSON响应
    token_info = response.json()
    print("token_info:", token_info)
    access_token = token_info.get("data")
    print("Access Token:", access_token['token'])
    # 自定义请求头
    headers = {
        'Authorization':  access_token['token']  # 如果需要认证，设置Authorization头
    }
    # 7.查询区域列表
    resp7 = requests.get(base_url+'/api/bms/1.0/org/byPidAndSource?page=0&pid=0004&size=100', headers=headers,verify=False)
    if resp7.status_code == 200:
        print("区域列表",resp7.json().get("data"))
        data=resp7.json().get("data")
        #print('data->'+data)
        regions=[]
        for item in resp7.json().get("data")['content']:
            # regions.append(item['id'])

            #8.查询区域指标
            resp8 = requests.get(base_url + '/api/bms/1.0/device/byDeptAndSource/'+item['id'], headers=headers,
                                 verify=False)
            if resp8.status_code == 200:
                print("设备列表", resp8.json().get("data"))
                # deviceCodes=[]
                for item in resp8.json().get("data"):
                    #deviceCodes.append(item['deviceCode'])
                # print(deviceCodes)
                    # 8.查询区域指标
                    resp9 = requests.get(base_url + '/api/bms/1.0/channel/byDeviceCodeAndSource?deviceCode='+item['deviceCode'], headers=headers,
                                             verify=False)
                    if resp9.status_code == 200:
                        print("设备列表", resp9.json().get("data"))
                        for item in resp9.json().get("data"):
                            regions.append(item)
                    else:
                        print("Error:", resp9.status_code, resp9.text)
            else:
                print("Error:", resp8.status_code, resp8.text)

    print(regions)
else:
    print("Error:", response.status_code, response.text)
# # 将数据写入 JSON 文件
# with open('D:\\Wanji\\济南绿波城项目\\百度数据接入\\车均速度.json', 'r', encoding='utf8') as file:
#     data_list = json.load(file)
