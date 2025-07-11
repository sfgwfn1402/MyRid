from kafka import KafkaProducer
import json
import sched
import time
from datetime import datetime

scheduler = sched.scheduler(time.time, time.sleep)

def job():
    print("任务执行...")
    # 在这里添加下次执行的时间
    scheduler.enter(10, 1, job)  # 60秒后再次执行
    # 创建 Kafka producer
    #producer = KafkaProducer(bootstrap_servers='192.168.208.42:9092')
    # producer = KafkaProducer(bootstrap_servers='kafka-0.icos.city:29094')
    producer = KafkaProducer(bootstrap_servers='192.168.204.99:32099')
    # 发送消息
    # topic = 'TEL.baidu.platform_http.order'
    # data = {"type":"place","payload":"{\"depLatitude\":30.417289448535335,\"depLongitude\":114.1551502024515,\"destLatitude\":30.417348864309986,\"destLongitude\":114.15497662622965,\"orderTime\":1728552456706,\"orderld\":\"A001\"}"}  # 消息必须是字节类型
    # # 将字典转换为 JSON 字符串
    # message = json.dumps(data)
    # producer.send(topic, value=message.encode('utf-8'))
    # data2 = {"type":"start","payload":"{\"depLatitude\":30.417289448535335,\"depLongitude\":114.1551502024515,\"depTime\":1728552456706,\"orderld\":\"A001\",\"vin\":\"车架号\",\"waitMile\":600}"}  # 消息必须是字节类型
    # message2 = json.dumps(data2)
    # producer.send(topic, value=message2.encode('utf-8'))

    # # 发送消息：车辆信息
    # topic = 'TEL.baidu.platform_http.vehicleInfo'
    # data = {"type":"add","payload":"{\"brand\":\"occaecat dolor fugiat est\",\"certifyDateA\":\"2025-08-27\",\"engineDisplace\":\"officia in\",\"engineld\":\"ad laboris dolore labore nulla\",\"fuelType\":0,\"genType\":\"anim voluptate\",\"hardwareType\":\"eu labore incididunt ea\",\"model\":\"aute nisi\",\"plateColor\":0,\"seats\":68,\"vehicleNo\":\"轿车\",\"vin\":\"laborum ut occaecat dolore minim\"}"}  # 消息必须是字节类型
    # # 将字典转换为 JSON 字符串
    # message = json.dumps(data)
    # producer.send(topic, value=message.encode('utf-8'))

    # data2 = {"type":"modify","payload":"{\"brand\":\"est dolor\",\"certifyDateA\":\"2024-09-05\",\"engineDisplace\":\"ut aliquip veniam dolor\",\"engineld\":\"ex velit commodo\",\"fuelType\":2,\"genType\":\"ex ut nulla reprehenderit\",\"hardwareType\":\"est labore\",\"model\":\"magna ullamco velit\",\"plateCoIor\":3,\"seats\":4,\"vehicleNo\":\"旅行车\",\"vin\":\"sunt enim in elit\"}"}  # 消息必须是字节类型
    # message2 = json.dumps(data2)
    # producer.send(topic, value=message2.encode('utf-8'))

    # 发送消息：车辆保险
    # topic = 'TEL.baidu.platform_http.insurance'
    # data = {"type":"add","payload":"{\"insurances\":[{\"insurCom\":\"et\",\"insurCount\":2.0,\"insurEff\":\"sint\",\"insurExp\":\"cupidatat\",\"insurNum\":\"91\",\"insurType\":0}],\"vin\":\"nostrud deserunt\"}"}  # 消息必须是字节类型
    # # 将字典转换为 JSON 字符串
    # message = json.dumps(data)
    # producer.send(topic, value=message.encode('utf-8'))
    #
    # data2 = {"type":"modify","payload":"{\"insurances\":[{\"insurCom\":\"do labore laborum exercitation amet\",\"insurCount\":18.0,\"insurEff\":\"est commodo velit\",\"insurExp\":\"laboris ipsum Ut magna\",\"insurNum\":\"68\",\"insurType\":2},{\"insurCom\":\"eu et ex anim\",\"insurCount\":37.0,\"insurEff\":\"dolore minim ut do\",\"insurExp\":\"voluptate nulla officia veniam\",\"insurNum\":\"7\",\"insurType\":0},{\"insurCom\":\"eu nostrud\",\"insurCount\":43.0,\"insurEff\":\"ad Lorem Duis commodo\",\"insurExp\":\"non officia\",\"insurNum\":\"45\",\"insurType\":1}],\"vin\":\"aliquip velit non laborum id\"}"}  # 消息必须是字节类型
    # message2 = json.dumps(data2)
    # producer.send(topic, value=message2.encode('utf-8'))

    # 发送消息：车辆轨迹
    # topic = 'TEL.baidu.xbox.bsm'
    # with open('E:\\file.avro', 'rb') as input_file:
    #     # 将二进制内容写入文件
    #     data = input_file.read()
    # producer.send(topic, value=data)

    # 发送消息：RsuBsmData
    topic = 'RsuBsmData'
    data = {"message":{"abs":3,"auxBrakes":3,"brakeBoost":3,"brakePadel":2,"eleConfidence":15,"elevation":100.5,"esp":3,"event":"0","fuelType":10,"gpstime":1633072800,"headConfidence":7,"heading":90.1234,"height":127,"latAccel":2001,"latitude":31.230416,"length":4095,"lightbarInUse":7,"lights":511,"lonAccel":2001,"longitude":121.473701,"msgCnt":127,"msgType":"bsm","obuId":"87654321","orientation":65535,"plateNo":"ABC1234","posConfidence":15,"responseType":6,"rsuId":"12345678","semiMajor":255,"semiMinor":255,"sirenInUse":3,"spdConfidence":7,"speed":30.5,"steeringAngle":127,"strConfidence":3,"traction":3,"transmission":2,"vehicleClass":0,"vertAccel":127,"wheelBrakes":31,"width":1023,"yawRate":32767},"rsuId":"7154"}  # 消息必须是字节类型
    # 将字典转换为 JSON 字符串
    # 获取当前时间
    # 格式化输出
    formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    key='R-7154-'+str(formatted_time)
    message = json.dumps(data)
    producer.send(topic, value=message.encode('utf-8'),key=key.encode('utf-8'))

    # 等待所有消息都被发送
    producer.flush()
    # 关闭 producer
    producer.close()

# 安排第一次执行
scheduler.enter(1, 1, job)
scheduler.run()