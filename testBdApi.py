import requests
import base64
import json

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

# headers2 = {
#     'Authorization': 'Bearer '+ base64_string # 如果需要认证，设置Authorization头
# }
# 创建请求的负载
payload = {
    'grant_type': 'client_credentials'  #,  # 授权类型
    # 'client_id': client_id,
    # 'client_secret': client_secret,
    # 'scope': scopes
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
    # #1.查询路口列表
    resp1 = requests.get(base_url+'road-api/intersections', headers=headers2, data=payload)
    if resp1.status_code == 200:
        print("路口列表",resp1.json().get("data"))
        intersections=[]
        for item in resp1.json().get("data"):
            intersections.append(item['intsid'])
            #2.路口渠化信息
            # resp2 = requests.get(base_url + 'road-api/cross/desc/' + item['intsid'], headers=headers2,
            #                       json=payload)
            # if resp2.status_code == 200:
            #     print("路口渠化信息",resp2.json().get("data"))
            #     crossDesc = []
            #     for item in resp2.json().get("data")['link_info']:
            #         # for link in item:
            #         crossDesc.append(item['id'])
            #3.路口流向指标数据标识1004 车均延误1005 停车次数1016 拥堵指数 （路口级别数据基于流向自己聚合）
        #     payload = {
        #                 'ids': [ str(cross) for cross in intersections ],  # 分⽀id  ，限制在100个以内，超过100个多次获取
        #                 'dates': ['2024-12-03'],  # 日期20241111-20241112
        #                 'times':[{
        #                  'startTime': '00:00:00',  # 开始时间 HH: mm:ss
        #                  'endTime': '23:59:59'     # 结束时间 HH: mm:ss
        #                 }],
        #                 'analysisObject':'TURN',
        #                 'aggGrain': 'P5'  # 时间粒度P5
        #     }
        #         # print(json.dumps(payload, ensure_ascii=False, indent=2))
        #     #     #1004 ⻋均延误1005 停⻋次数1016 拥堵指数
        #     for code in ['1004', '1005', '1016']:
        #         resp3 = requests.post(base_url + 'aitpm-statistic/aitpm/statistic/api/cross/groupAgg/time/' + code, headers=headers2,
        #                                       json=payload)
        #         if resp3.status_code == 200:
        #             print("路口流向指标"+code,resp3.json().get("data"))
        #         else:
        #             print("Error:", resp3.status_code, resp3.text)
        # else:
        #     print("Error:", resp2.status_code, resp2.text)

                #4.路口报警 数据标识1036 空放1037 失衡1038 遗留 路口拥堵根据路口流向拥堵指数自己计算+ item['intsid']
        # payload = {
        #         'ids': [ str(intersection) for intersection in intersections ],  # 路口id ，限制在100个以内，超过100个多次获取
        #         'dates': ['2024-12-03'],  # 日期20241111-20241112
        #         'times': [{
        #         'startTime': '00:00:00',  # 开始时间 HH: mm:ss
        #         'endTime': '23:59:59'     # 结束时间 HH: mm:ss
        #         }],
        #         'aggGrain': 'P5'  # 时间粒度P5
        # }
        # print(json.dumps(payload))
        # for code in ['1036', '1037', '1038']:
        #     resp4 = requests.post(base_url + 'aitpm-statistic/aitpm/statistic/api/crossing/time/get/batch/warn/'+code ,
        #                               headers=headers2,
        #                               json=payload)
        #     if resp4.status_code == 200:
        #         print("路口报警"+code,resp4.json().get("data"))
        #     else:
        #         print("Error:", resp4.status_code, resp4.text)
    else:
        print("Error:", resp1.status_code, resp1.text)

    #
    # 5 干线列表查询
    resp5 = requests.get(base_url + 'road-api/arteries' , headers=headers2,   json=payload)
    if resp5.status_code == 200:
        print("干线列表",json.dumps(resp5.json().get("data")))
        arteries=[]
        for item in resp5.json().get("data"):
            arteries.append(str(item['artery_id']))
        #6.干线指标 数据标识 3009 停车次数3012 车均行程时间3004 车均延误3013 车均速度
        payload = {
            'ids': [ str(arterie) for arterie in arteries],  # 干线id ，限制在100个以内，超过100个多次获取
            'dates': ['2024-12-04'],  # 日期20241111-20241112
            'times': [{'startTime': '00:00:00',  # 开始时间 HH: mm:ss
            'endTime': '23:59:59'}],  # 结束时间 HH: mm:ss
            'aggGrain': 'P5'  # 时间粒度P5
        }

         #3009 停⻋次数3012 ⻋均⾏程时间3004 ⻋均延误3013 ⻋均速度,'3012','3004','3013'
        for code in ['3009']:
            resp6 = requests.post(
                    base_url + 'aitpm-statistic/aitpm/statistic/api/artery/groupAgg/time/'+code,
                    headers=headers2,
                    json=payload)
            if resp6.status_code == 200:
                print("干线指标"+code+"->",json.dumps(resp6.json().get("data")))
            else:
                print("Error:", resp6.status_code, resp6.text)
    else:
        print("Error:", resp5.status_code, resp5.text)

    # 7.查询区域列表
    # resp7 = requests.get(base_url+'road-api/bdmap/regions?type=1', headers=headers2)
    # if resp7.status_code == 200:
    #     print("区域列表",resp7.json().get("data"))
    #     data=resp7.json().get("data")
    #     #print('data->'+data)
    #     regions=[]
    #     for item in resp7.json().get("data"):
    #         for children in item['children']:
    #             regions.append(children['region_id'])
    #     #print(regions)
    #     #8.查询区域指标
    #     payload = {
    #         'ids': [ str(region) for region in regions ],   # 区域id ，限制在100个以内，超过100个多次获取
    #         'dates': ['2024-12-05'], #日期20241111-20241112
    #         'startTime': '00:00:00',  #开始时间 HH: mm:ss
    #         'endTime': '23:59:59',  # 结束时间 HH: mm:ss
    #         'aggGrain': 'P5' #时间粒度P5
    #     }
    #     #print(payload)
    #     #数据标识5003 车均速度 5006 拥堵指数
    #     resp85003 = requests.post(base_url + 'aitpm-statistic/aitpm/statistic/api/region/all/batch/5003', headers=headers2, json=payload)
    #     if resp85003.status_code == 200:
    #         print("车均速度",json.dumps(resp85003.json().get("data")))
    #     else:
    #         print("Error:", resp85003.status_code, resp85003.text)
    #
    #     resp85006 = requests.post(base_url + 'aitpm-statistic/aitpm/statistic/api/region/all/batch/5006' , headers=headers2, json=payload)
    #     if resp85006.status_code == 200:
    #         print("拥堵指数",json.dumps(resp85006.json().get("data")))
    #     else:
    #         print("Error:", resp85006.status_code, resp85006.text)
    # else:
    #     print("Error:", resp7.status_code, resp7.text)

else:
    print("Error:", response.status_code, response.text)
