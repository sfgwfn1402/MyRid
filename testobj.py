# Copyright 2017 The Nuclio Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
desc: bsm trans
date: 2021-6-22
author: wangyaocheng
"""
import json
import logging
import os
from datetime import datetime, timedelta
import uuid
from confluent_kafka import Consumer, TopicPartition,KafkaError

KAFKA_ADDRESS = os.getenv("BOOTSTRAP_SERVERS", "192.168.204.99:32100,192.168.204.100:32099,192.168.204.121:32121")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://icosevent-schemaregistry-service-icos.icos.icos.city")
# 获取目标topic
TARGET_TOPIC_DATANG = os.getenv("TARGET_TOPIC_DATANG", "EVENT.datang.obu.telemetry")
TARGET_TOPIC_HUALI = os.getenv("TARGET_TOPIC_HUALI", "EVENT.huali.obu.telemetry")
TARGET_TOPIC_HUAWEI = os.getenv("TARGET_TOPIC_HUAWEI", "EVENT.huawei.obu.telemetry")
TARGET_TOPIC_BAIDU = os.getenv("TARGET_TOPIC_BAIDU", "EVENT.baidu.obu.telemetry")
DEBUG_FLAG = os.environ.get("NUCLIO_DEBUG_FLAG", "false").lower()


def create_folder_by_hour(path ,timestamp):
    """根据日期创建文件夹"""
    folder_name = datetime.fromtimestamp(timestamp/1000).hour
    folder_path = 'ht='+ str(folder_name).zfill(2)
    if not os.path.exists(os.path.join(path,folder_path)):
        os.makedirs(os.path.join(path,folder_path))
    #print(folder_path)
    return folder_path

# 确保文件夹名称格式正确
def create_folder_by_time(path ,folder,timestamp):
    # 按每10分钟创建一个文件夹
    # folder_time = datetime.fromtimestamp(timestamp/1000) - timedelta(minutes=datetime.fromtimestamp(timestamp/1000).minute % 10)
    folder_time =(datetime.fromtimestamp(timestamp/1000).minute// 10) * 10
    folder_path = 'mt='+ str(folder_time).zfill(2)
    folder_id=''
    if not os.path.exists(os.path.join(path,folder,folder_path)):
        os.makedirs(os.path.join(path,folder,folder_path))
        folder_id=str(uuid.uuid4())
    #print(folder_path)
    return folder_path,folder_id

if __name__ == '__main__':
    # Kafka 配置
    kafka_conf = {
        'bootstrap.servers': '192.168.204.99:32100,192.168.204.100:32099,192.168.204.121:32121',  # Kafka 地址
        'group.id': 'my-test_group-999',  # 消费者组 ID
        'auto.offset.reset': 'earliest'  # 从最早的消息开始消费
        #'max_poll_records' : 500,  # 每次拉取批处理量
        #'enable_auto_commit' : False
    }
    # Schema Registry 配置
    # schema_registry_conf = {'url': 'http://kafka-0.icos.city:29094'}  # Schema Registry 地址
    # schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    # 创建 Avro 反序列化器
    # avro_deserializer = AvroDeserializer(schema_registry_client)
    # 创建 Kafka 消费者
    consumer = Consumer(kafka_conf)
    # 订阅 Topic
    # consumer.subscribe(['RCU2CLOUD_OBJS'])
    #partitions = [TopicPartition('RCU2CLOUD_OBJS', 0)]  # 这里假设只有一个分区
    # topic = 'RCU2CLOUD_OBJS'
    # topic = 'RCU2CLOUD_HEARTBEAT'
    # topic = 'RCU2CLOUD_EVENT_CANCEL'
    # topic = 'RCU2CLOUD_STATUS'
    # topic = 'RCU2CLOUD_EVENT'
    topic = 'RsuRsmData'
    # topic = 'RsuRsiData'



    # 获取所有分区
    partitions = consumer.list_topics(topic).topics[topic].partitions.keys()

    # 获取指定时间戳对应的 offset
    start_time = int(datetime(2025, 3, 12, 9, 0, 0).timestamp() * 1000)  # 开始时间戳，毫秒级
    end_time = int(datetime(2025, 3, 12, 10, 59, 59).timestamp() * 1000)  # 结束时间戳，毫秒级
    #print(start_time)
    # 查询 offset
    # 创建 TopicPartition 对象

    # 获取指定时间戳的消息偏移量
    offsets = consumer.offsets_for_times([TopicPartition(topic, p, start_time) for p in partitions ] )
    end_offset = consumer.offsets_for_times([TopicPartition(topic, p, end_time) for p in partitions])
    oid=''
    # 逐一分区消费
    for tp, end_offset in zip(offsets, end_offset):
        if not end_offset.offset:
            continue  # 跳过无数据的分区
        consumer.assign([tp])
        consumer.seek(tp)

        # 消费消息
        try:
            while True:
                msg = consumer.poll(timeout=1.0)  # 拉取消息
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        print("Reached end of partition")
                    else:
                        print("Error: ", msg.error())
                else:
                    # 检查消息的 offset 是否超过了 end_offset
                    if msg.offset() >= end_offset.offset:
                        break

                    base_path='D:\\DATA01\\'+topic+"\\"
                    # base_path = '/data/RCU2CLOUD/RCU2CLOUD_OBJS/'
                    dh=create_folder_by_hour(base_path,msg.timestamp()[1])
                    dm,uid=create_folder_by_time(base_path,dh,msg.timestamp()[1])
                    if uid != '':
                        oid=uid

                    with open(os.path.join(base_path,dh,dm,'compacted-part-'+oid+'-0-'+str(datetime.fromtimestamp(msg.timestamp()[1]/1000).minute//2 )), 'a') as json_file:
                        message_value = json.loads(msg.value().decode('utf-8'))
                        #print(message_value.get('rcuId'))
                        # if message_value.get('rcuId') != 'U-081509' :
                        #     continue
                        if message_value.get('rsuId') != 'R-081507' :
                            continue

                        # 将消息写入JSON文件
                        json.dump(message_value, json_file)
                        json_file.write('\n')  # 写入换行符以分隔不同的JSON对象
                        print(" message: ", message_value)
        finally:
            print('ok....')

        consumer.close()