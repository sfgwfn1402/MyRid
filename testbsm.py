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
import io

from logging.handlers import TimedRotatingFileHandler

from confluent_kafka import avro, Consumer, KafkaError
from confluent_kafka.avro import AvroProducer
from confluent_kafka.avro.cached_schema_registry_client import CachedSchemaRegistryClient
from confluent_kafka.avro.serializer.message_serializer import MessageSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer
import avro.schema
from avro.io import DatumReader, BinaryDecoder

KAFKA_ADDRESS = os.getenv("BOOTSTRAP_SERVERS", "ps-kafka-m1c2-paas.paas:29092")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://icosevent-schemaregistry-service-icos.icos.icos.city")
# 获取目标topic
TARGET_TOPIC_DATANG = os.getenv("TARGET_TOPIC_DATANG", "EVENT.datang.obu.telemetry")
TARGET_TOPIC_HUALI = os.getenv("TARGET_TOPIC_HUALI", "EVENT.huali.obu.telemetry")
TARGET_TOPIC_HUAWEI = os.getenv("TARGET_TOPIC_HUAWEI", "EVENT.huawei.obu.telemetry")
TARGET_TOPIC_BAIDU = os.getenv("TARGET_TOPIC_BAIDU", "EVENT.baidu.obu.telemetry")
DEBUG_FLAG = os.environ.get("NUCLIO_DEBUG_FLAG", "false").lower()

# --------全局访问对象----------------
g_producer_obj = None  # 生产者管理对象
g_serializer_obj = None  # schema管理对象
g_schema_r = None  # schema原始对象
g_schema_t = None  # schema目标对象
g_logger = None  # 日志管理对象


# ---------init接口-------------------
def init_producer():
    """
    创建topic生产者管理对象
    """
    global g_producer_obj
    g_producer_obj = AvroProducer({
        'bootstrap.servers': KAFKA_ADDRESS,
        'schema.registry.url': SCHEMA_REGISTRY_URL,
        'queue.buffering.max.ms': 5,
    }, default_value_schema=g_schema_t)


def init_avro():
    """
    创建序列化对象
    """
    global g_schema_r, g_schema_t
    avro_r = """
        {
        "namespace": "com.icos.sense.message",
        "type": "record",
        "name": "SenseMessage",
        "fields": [
            {
                "name": "messageId",
                "type": "string"
            },
            {
                "name": "tenantId",
                "type": ["null", "string"],
                "default": null
            },
            {
                "name": "deviceId",
                "type": ["null", "string"],
                "default": null
            },
            {
                "name": "deviceType",
                "type": ["null", "string"],
                "default": null
            },
            {
                "name": "gatewayId",
                "type": ["null", "string"],
                "default": null
            },
            {
                "name": "creationTime",
                "type": ["null", "long"],
                "default": null
            },
            {
                "name": "commandType",
                "type": ["null", "string"],
                "default": null
            },
            {
                "name": "commandReply",
                "type": ["null", "string"],
                "default": null
            },
            {
                "name": "commandName",
                "type": ["null", "string"],
                "default": null
            },
            {
                "name": "payload",
                "type": "string"
            }
        ]
    }
    """

    avro_t = """
        {
        "namespace": "com.icosobu.telemetry.message",
        "type": "record",
        "name": "ObuHuaLiBSMMessage",
        "fields": [
        {
            "name": "tenantId",
            "type":  ["null","string"],
            "default": null
        },
        {
            "name": "deviceId",
            "type":  ["null","string"],
            "default": null
        },
        {
            "name": "gatewayId",
            "type":  ["null","string"],
            "default": null
        },
        {
            "name": "creationTime",
            "type": [ "null" , "long" ],
            "default": null
        },
        {
            "name": "tag",
            "type": "int"
        },
        {
            "name": "msgCnt",
            "type": "long"
        },
        {
            "name": "id",
            "type": "string"
        },
        {
            "name": "secMark",
            "type": "long"
        },
        {
            "name": "timeConfidence",
            "type": ["null", "double"],"default":null
        },
        {
            "name": "pos",
            "type": ["null",{
                "name": "pos",
                "type": "record",
                "fields": [{
                    "name": "lat",
                    "type": "string"
                },
                    {
                        "name": "long",
                        "type": "string"
                    },
                    {
                        "name": "elevation",
                        "type": ["null", "string"]
                    }
                ]
            }
            ],"default":null
        },
        {
            "name": "posAccuracy",
            "type": ["null",{
                "name": "posAccuracy",
                "type": "record",
                "fields": [{
                        "name": "semiMajor",
                        "type": ["null", "double"]
                    },
                    {
                        "name": "semiMinor",
                        "type": ["null", "double"]
                    },
                    {
                        "name": "orientation",
                        "type": ["null", "double"]
                    }
                ]
            }
            ],"default":null
        },
        {
            "name": "posConfidence",
            "type": ["null",{
                "name": "posConfidence",
                "type": "record",
                "fields": [{
                    "name": "pos",
                    "type": ["null", "double"]
                },
                    {
                        "name": "elevation",
                        "type": ["null", "double"]
                    }
                ]
            }],"default":null
        },
        {
            "name": "transmission",
            "type": "int"
        },
        {
            "name": "speed",
            "type": "double"
        },
        {
            "name": "heading",
            "type": "double"
        },
        {
            "name": "angle",
            "type": ["null", "double"],"default":null
        },
        {
            "name": "motionCfd",
            "type": ["null",{
                "name": "motionCfd",
                "type": "record",
                "fields": [{
                    "name": "speedCfd",
                    "type": ["null", "int"]
                },
                    {
                        "name": "headingCfd",
                        "type": ["null", "int"]
                    },
                    {
                        "name": "steerCfd",
                        "type": ["null", "int"]
                    }
                ]
            }],"default":null
        },
        {
            "name": "accelSet",
            "type": ["null",{
                "name": "accelSet",
                "type": "record",
                "fields": [{
                    "name": "long",
                    "type": ["null", "double"]
                },
                    {
                        "name": "lat",
                        "type": ["null", "double"]
                    },
                    {
                        "name": "vert",
                        "type": ["null", "double"]
                    },
                    {
                        "name": "yaw",
                        "type": ["null", "double"]
                    }
                ]
            }],"default":null
        },
        {
            "name": "brakes",
            "type": ["null",{
                "name": "brakes",
                "type": "record",
                "fields": [
                    {
                        "name": "wheelBrakes",
                        "type": ["null",{
                            "name": "wheelBrakes",
                            "type": "record",
                            "fields": [
                                {
                                    "name": "leftFront",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "rightFront",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "leftRear",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "rightRear",
                                    "type": ["null", "boolean"]
                                }
                            ]
                        }],"default":null
                    },
                    {
                        "name": "brakePadel",
                        "type": ["null", "int"]
                    },
                    {
                        "name": "traction",
                        "type": ["null", "int"]
                    },
                    {
                        "name": "abs",
                        "type": ["null", "int"]
                    },
                    {
                        "name": "scs",
                        "type": ["null", "int"]
                    },
                    {
                        "name": "brakeBoost",
                        "type": ["null", "int"]
                    },
                    {
                        "name": "auxBrakes",
                        "type": ["null", "int"]
                    }
                ]
            }],"default":null
        },
        {
            "name": "size",
            "type": ["null",{
                "name": "size",
                "type": "record",
                "fields": [{
                    "name": "width",
                    "type": ["null", "double"]
                },
                    {
                        "name": "length",
                        "type": ["null", "double"]
                    },
                    {
                        "name": "height",
                        "type": ["null", "double"]
                    }
                ]
            }],"default":null
        },
        {
            "name": "vehicleClass",
            "type": ["null",{
                "name": "vehicleClass",
                "type": "record",
                "fields": [{
                    "name": "classification",
                    "type": ["null", "int"]
                },
                    {
                        "name": "fuelType",
                        "type": ["null", "int"]
                    }
                ]
            }],"default":null
        },
        {
            "name": "safetyExt",
            "type": ["null",{
                "name": "safetyExt",
                "type": "record",
                "fields": [
                    {
                        "name": "events",
                        "type": ["null",{
                            "name": "events",
                            "type": "record",
                            "fields": [
                                {
                                    "name": "eventReserved1",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventLightsChanged",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventStabilityControlactivated",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventHazardousMaterials",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventWipersChanged",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventHazardLights",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventTractionControlLoss",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventABSactivated",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventAirBagDeployment",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventFlatTire",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventDisabledVehicle",
                                    "type": ["null", "boolean"]
                                }  ,
                                {
                                    "name": "eventHardBraking",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "eventStopLineViolation",
                                    "type": ["null", "boolean"]
                                }
                            ]
                        }],"default":null
                    },
                    {
                        "name": "pathHistory",
                        "type": {
                            "name": "pathHistory",
                            "type": "record",
                            "fields": [
                                {
                                    "name": "initialPosition",
                                    "type": ["null",{
                                        "name": "initialPosition",
                                        "type": "record",
                                        "fields": [
                                            {
                                                "name": "initPos",
                                                "type": ["null",{
                                                    "name": "initPos",
                                                    "type": "record",
                                                    "fields": [
                                                        {
                                                            "name": "lat",
                                                            "type": ["null", "double"]
                                                        },
                                                        {
                                                            "name": "long",
                                                            "type": ["null", "double"]
                                                        },
                                                        {
                                                            "name": "elevation",
                                                            "type": ["null", "double"]
                                                        }
                                                    ]
                                                }],"default":null
                                            },
                                            {
                                                "name": "utcTime",
                                                "type": ["null",{
                                                    "name": "utcTime",
                                                    "type": "record",
                                                    "fields": [
                                                        {
                                                            "name": "hour",
                                                            "type": ["null", "long"]
                                                        },
                                                        {
                                                            "name": "month",
                                                            "type": ["null", "long"]
                                                        },
                                                        {
                                                            "name": "year",
                                                            "type": ["null", "long"]
                                                        },
                                                        {
                                                            "name": "day",
                                                            "type": ["null", "long"]
                                                        },
                                                        {
                                                            "name": "minute",
                                                            "type": ["null", "long"]
                                                        },
                                                        {
                                                            "name": "second",
                                                            "type": ["null", "long"]
                                                        }
                                                    ]
                                                }],"default":null
                                            }
                                        ]
                                    }],"default":null
                                },
                                {
                                    "name": "currGNSSstatus",
                                    "type": ["null",{
                                        "name": "currGNSSstatus",
                                        "type": "record",
                                        "fields": [
                                            {
                                                "name": "GNSSstatus_unavailable",
                                                "type": ["null", "boolean"]
                                            },
                                            {
                                                "name": "isHealthy",
                                                "type": ["null", "boolean"]
                                            },
                                            {
                                                "name": "isMonitored",
                                                "type": ["null", "boolean"]
                                            },
                                            {
                                                "name": "baseStationType",
                                                "type": ["null", "boolean"]
                                            },
                                            {
                                                "name": "aPDOPofUnder5",
                                                "type": ["null", "boolean"]
                                            },
                                            {
                                                "name": "inViewOfUnder5",
                                                "type": ["null", "boolean"]
                                            },
                                            {

                                                "name": "localCorrectionsPresent",
                                                "type": ["null", "boolean"]
                                            },
                                            {
                                                "name": "networkCorrectionsPresent",
                                                "type": ["null", "boolean"]
                                            }
                                        ]
                                    }],"default":null
                                },
                                {
                                    "name": "crumbData",
                                    "type": {
                                        "type": "array",
                                        "items": {
                                            "type": "record",
                                            "name": "crumbData",
                                            "fields": [
                                                {
                                                    "name": "heading",
                                                    "type": ["null", "long"]
                                                },
                                                {
                                                    "name": "timeOffset",
                                                    "type": ["null", "long"]
                                                },
                                                {
                                                    "name": "speed",
                                                    "type": ["null", "double"]
                                                },
                                                {
                                                    "name": "posAccuracy",
                                                    "type": ["null", "long"]
                                                },
                                                {
                                                    "name": "llvOffset",
                                                    "type": ["null",{
                                                        "name": "llvOffset",
                                                        "type": "record",
                                                        "fields": [
                                                            {
                                                                "name": "offsetLL",
                                                                "type": ["null",{
                                                                    "name": "offsetLL",
                                                                    "type": "record",
                                                                    "fields": [
                                                                        {
                                                                            "name": "choiceID",
                                                                            "type": ["null", "long"]
                                                                        },
                                                                        {
                                                                            "name": "position_LatLon",
                                                                            "type": ["null",{
                                                                                "name": "position_LatLon",
                                                                                "type": "record",
                                                                                "fields": [
                                                                                    {
                                                                                        "name": "long",
                                                                                        "type": ["null", "double"]
                                                                                    },
                                                                                    {
                                                                                        "name": "lat",
                                                                                        "type": ["null", "double"]
                                                                                    }
                                                                                ]
                                                                            }],"default":null
                                                                        }
                                                                    ]
                                                                }],"default":null
                                                            } ,
                                                            {
                                                                "name": "offsetV",
                                                                "type": ["null",{
                                                                    "name": "offsetV",
                                                                    "type": "record",
                                                                    "fields": [
                                                                        {
                                                                            "name": "choiceID",
                                                                            "type": ["null", "long"]
                                                                        },
                                                                        {
                                                                            "name": "elevation",
                                                                            "type": ["null", "long"]
                                                                        }
                                                                    ]
                                                                }],"default":null
                                                            }
                                                        ]
                                                    }],"default":null
                                                }
                                            ]
                                        }
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "name": "pathPrediction",
                        "type": {
                            "name": "pathPrediction",
                            "type": "record",
                            "fields": [
                                {
                                    "name": "radiusOfCurve",
                                    "type": ["null", "double"]
                                },
                                {
                                    "name": "confidence",
                                    "type": ["null", "double"]
                                }
                            ]
                        }
                    },
                    {
                        "name": "lights",
                        "type": ["null",{
                            "name": "lights",
                            "type": "record",
                            "fields": [
                                {
                                    "name": "daytimeRunningLightsOn",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "automaticLightControlOn",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "parkingLightsOn",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "rightTurnSignalOn",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "hazardSignalOn",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "lowBeamHeadlightsOn",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "highBeamHeadlightsOn",
                                    "type": ["null", "boolean"]
                                }  ,
                                {
                                    "name": "leftTurnSignalOn",
                                    "type": ["null", "boolean"]
                                },
                                {
                                    "name": "fogLightOn",
                                    "type": ["null", "boolean"]
                                }
                            ]
                        }],"default":null
                    }
                ]
            }],"default":null
        },

        {
            "name": "emergencyExt",
            "type": ["null",{
                "name": "emergencyExt",
                "type": "record",
                "fields": [{
                    "name": "responseType",
                    "type": ["null", "long"]
                },
                    {
                        "name": "sirenUse",
                        "type": ["null", "long"]
                    },
                    {
                        "name": "lightsUse",
                        "type": ["null", "long"]
                    }
                ]
            }],"default":null
        },
        {
            "name": "additional",
            "type": ["null",{
                "name": "additional",
                "type": "record",
                "fields": [{
                    "name": "vip_status",
                    "type": ["null", "int"]
                },
                    {
                        "name": "vehicle_num",
                        "type": ["null", "string"]
                    },
                    {
                        "name": "drive_status",
                        "type": ["null", "int"]
                    },
                    {
                        "name": "modem_status",
                        "type": ["null", "string"]
                    },
                    {
                        "name": "temperature",
                        "type": ["null", "int"]
                    },
                    {
                        "name": "gnss_status",
                        "type": ["null", "string"]
                    },
                    {
                        "name": "mileage",
                        "type": ["null", "double"]
                    },
                    {
                        "name": "timestamp",
                        "type": ["null", "string"]
                    }
                ]
            }],"default":null
        }
    ]
    }
    """

    g_schema_r = avro.loads(avro_r)
    g_schema_t = avro.loads(avro_t)


def init_schema():
    """
    创建schema管理对象
    """
    global g_serializer_obj
    schema_registry_obj = CachedSchemaRegistryClient(SCHEMA_REGISTRY_URL)
    g_serializer_obj = MessageSerializer(schema_registry_obj)


def init_log():
    """
    初始化日志对象
    """
    global g_logger
    g_logger = logging.getLogger('telemetry')
    g_logger.setLevel(logging.INFO)
    # 创建TimedRotatingFileHandler对象,每天生成一个文件
    log_file_handler = TimedRotatingFileHandler(filename='bsm_{}.log'.format(os.getpid()), when="D", interval=1,
                                                backupCount=3)
    # 设置日志打印格式
    formatter = logging.Formatter("[%(asctime)s]: %(message)s")
    log_file_handler.setFormatter(formatter)
    g_logger.addHandler(log_file_handler)


def log_info(msg):
    """
    封装的日志记录接口
    params: msg 日志内容
    return: None
    """
    global g_logger
    if DEBUG_FLAG == "true":
        print(msg)
    # g_logger.info(msg)


def init_context(context):
    """
    初始化接口
    """
    global g_logger

    if not context.trigger.kind.startswith("kafka"):
        return

    init_log()  # 日志初始化必须放step 1

    init_avro()

    init_producer()

    init_schema()

    log_info("init all info success")


start_time_dict = {}


def handler(context, event):
    global start_time_dict
    head_dict = json.loads(event.get_header("X-Qloud-Data").decode("utf-8"))
    key = head_dict["deviceId"]
    creationtime = head_dict["creationTime"]
    if key in start_time_dict:
        if creationtime - start_time_dict[key] < 1000:
            return
        else:
            start_time_dict[key] = creationtime
    else:
        start_time_dict[key] = creationtime
    global g_schema_r, g_schema_t, g_producer_obj, g_serializer_obj

    resouce_dict = g_serializer_obj.decode_message(event.body)

    # 处理bsm转化
    target_dict = process(resouce_dict)

    # 选择目标topic
    target_topic = ""
    if event.path == "EVENT.datang.obubsm.generic.telemetry":
        target_topic = TARGET_TOPIC_DATANG
    elif event.path == 'EVENT.huali.obubsm.generic.telemetry':
        target_topic = TARGET_TOPIC_HUALI
    elif event.path == 'EVENT.huawei.obubsm.generic.telemetry':
        target_topic = TARGET_TOPIC_HUAWEI
    elif event.path == 'EVENT.baidu.obubsm.generic.telemetry':
        target_topic = TARGET_TOPIC_BAIDU
    else:
        log_info('未知topic：{}'.format(event.path))
        return context.Response(body='未知topic：{}'.format(event.path),
                                headers={},
                                content_type='text/plain',
                                status_code=200)
    # value = g_serializer_obj.encode_record_with_schema(target_topic, g_schema_t, target_dict)

    # print("目标topic{} data： {}".format(target_topic, target_dict))
    g_producer_obj.produce(topic=target_topic, value=target_dict, key=key, headers=event.headers)
    g_producer_obj.poll(0)
    log_info("send topic success by deviceid {}".format(key))
    return context.Response(body='Hello, from nuclio :]',
                            headers={},
                            content_type='text/plain',
                            status_code=200)


# avro组装
def process(resource_dict):
    target_dict = {}
    # 基础属性
    target_dict["tenantId"] = resource_dict.get("tenantId", None)
    target_dict["deviceId"] = resource_dict.get("deviceId", None)
    target_dict["gatewayId"] = resource_dict.get("gatewayId", None)
    target_dict["creationTime"] = resource_dict.get("creationTime", None)

    payload = json.loads(resource_dict["payload"])
    target_dict["tag"] = payload["tag"]
    target_dict["msgCnt"] = payload["msgCnt"]
    target_dict["id"] = payload["id"]
    target_dict["secMark"] = payload["secMark"]
    target_dict["timeConfidence"] = payload.get("timeConfidence", None)

    # pos
    pos = payload.get("pos", None)
    if pos is not None:
        target_pos = {}
        target_pos["lat"] = str(pos["lat"])
        target_pos["long"] = str(pos["long"])
        target_pos["elevation"] = str(pos.get("elevation", None))
        target_dict["pos"] = target_pos

    # posAccuracy
    posAccuracy = payload.get("posAccuracy", None)
    if posAccuracy is not None:
        target_posAccuracy = {}
        target_posAccuracy["semiMajor"] = posAccuracy.get("semiMajor", None)
        target_posAccuracy["semiMinor"] = posAccuracy.get("semiMinor", None)
        target_posAccuracy["orientation"] = posAccuracy.get("orientation", None)
        target_dict["posAccuracy"] = target_posAccuracy

    # posConfidence
    posConfidence = payload.get("posConfidence", None)
    if posConfidence is not None:
        target_posConfidence = {}
        target_posConfidence["pos"] = posConfidence.get("pos", None)
        target_posConfidence["elevation"] = posConfidence.get("elevation", None)
        target_dict["posConfidence"] = target_posConfidence

    target_dict["transmission"] = payload["transmission"]
    target_dict["speed"] = payload["speed"]
    target_dict["heading"] = payload["heading"]
    target_dict["angle"] = payload.get("angle", None)

    # motionCfd
    motionCfd = payload.get("motionCfd", None)
    if motionCfd is not None:
        target_motionCfd = {}
        target_motionCfd["speedCfd"] = motionCfd.get("speedCfd", None)
        target_motionCfd["headingCfd"] = motionCfd.get("headingCfd", None)
        target_motionCfd["steerCfd"] = motionCfd.get("steerCfd", None)
        target_dict["motionCfd"] = target_motionCfd

    # accelSet
    accelSet = payload.get("accelSet", None)
    if accelSet is not None:
        target_accelSet = {}
        target_accelSet["long"] = accelSet.get("long", None)
        target_accelSet["lat"] = accelSet.get("lat", None)
        target_accelSet["vert"] = accelSet.get("vert", None)
        target_accelSet["yaw"] = accelSet.get("yaw", None)
        target_dict["accelSet"] = target_accelSet

    # brakes
    brakes = payload.get("brakes", None)
    if brakes is not None:
        target_brakes = {}

        # wheelBrakes
        wheelBrakes = brakes.get("wheelBrakes", None)
        if wheelBrakes is not None:
            target_wheelBrakes = {}
            target_wheelBrakes["leftFront"] = wheelBrakes.get("leftFront", None)
            target_wheelBrakes["rightFront"] = wheelBrakes.get("rightFront", None)
            target_wheelBrakes["leftRear"] = wheelBrakes.get("leftRear", None)
            target_wheelBrakes["rightRear"] = wheelBrakes.get("rightRear", None)
            target_brakes["wheelBrakes"] = target_wheelBrakes

        target_brakes["brakePadel"] = brakes.get("brakePadel", None)
        target_brakes["traction"] = brakes.get("traction", None)
        target_brakes["abs"] = brakes.get("abs", None)
        target_brakes["scs"] = brakes.get("scs", None)
        target_brakes["brakeBoost"] = brakes.get("brakeBoost", None)
        target_brakes["auxBrakes"] = brakes.get("auxBrakes", None)
        target_dict["brakes"] = target_brakes

    # size
    size = payload.get("size", None)
    if size is not None:
        target_size = {}
        target_size["width"] = size.get("width", None)
        target_size["length"] = size.get("length", None)
        target_size["height"] = size.get("height", None)
        target_dict["size"] = target_size

        # vehicleClass
    vehicleClass = payload.get("vehicleClass", None)
    if size is not None:
        target_vehicleClass = {}
        target_vehicleClass["classification"] = vehicleClass.get("classification", None)
        target_vehicleClass["fuelType"] = vehicleClass.get("fuelType", None)
        target_dict["vehicleClass"] = target_vehicleClass

        # safetyExt
    safetyExt = payload.get("safetyExt", None)
    # safetyExt = None
    if safetyExt is not None:
        target_safetyExt = {}

        # events
        events = safetyExt.get("events", None)
        # events = None
        if events is not None:
            target_events = {}
            target_events["eventReserved1"] = events.get("eventReserved1", None)
            target_events["eventLightsChanged"] = events.get("eventLightsChanged", None)
            target_events["eventStabilityControlactivated"] = events.get("eventStabilityControlactivated", None)
            target_events["eventHazardousMaterials"] = events.get("eventHazardousMaterials", None)
            target_events["eventWipersChanged"] = events.get("eventWipersChanged", None)
            target_events["eventHazardLights"] = events.get("eventHazardLights", None)
            target_events["eventTractionControlLoss"] = events.get("eventTractionControlLoss", None)
            target_events["eventABSactivated"] = events.get("eventABSactivated", None)
            target_events["eventAirBagDeployment"] = events.get("eventAirBagDeployment", None)
            target_events["eventFlatTire"] = events.get("eventFlatTire", None)
            target_events["eventDisabledVehicle"] = events.get("eventDisabledVehicle", None)
            target_events["eventHardBraking"] = events.get("eventHardBraking", None)
            target_events["eventStopLineViolation"] = events.get("eventStopLineViolation", None)
            target_safetyExt["events"] = target_events

        # pathHistory
        pathHistory = safetyExt.get("pathHistory", None)
        if pathHistory is not None:
            target_pathHistory = {}

            # initialPosition
            initialPosition = pathHistory.get("initialPosition", None)
            if initialPosition is not None:
                target_initialPosition = {}

                # initPos
                initPos = initialPosition.get("initPos", None)
                if initPos is not None:
                    target_initPos = {}
                    target_initPos["lat"] = initPos.get("lat", None)
                    target_initPos["long"] = initPos.get("long", None)
                    target_initPos["elevation"] = initPos.get("elevation", None)
                    target_initialPosition["initPos"] = target_initPos
                initPos = initialPosition.get("pos", None)
                if initPos is not None:
                    target_initPos = {}
                    target_initPos["lat"] = initPos.get("lat", None)
                    target_initPos["long"] = initPos.get("long", None)
                    target_initPos["elevation"] = initPos.get("elevation", None)
                    target_initialPosition["initPos"] = target_initPos

                # utcTime
                utcTime = initialPosition.get("utcTime", None)
                if utcTime is not None:
                    target_utcTime = {}
                    target_utcTime["hour"] = utcTime.get("hour", None)
                    target_utcTime["month"] = utcTime.get("month", None)
                    target_utcTime["year"] = utcTime.get("year", None)
                    target_utcTime["day"] = utcTime.get("day", None)
                    target_utcTime["minute"] = utcTime.get("minute", None)
                    target_utcTime["second"] = utcTime.get("second", None)
                    target_initialPosition["utcTime"] = target_utcTime

                target_pathHistory["initialPosition"] = target_initialPosition

            # currGNSSstatus
            currGNSSstatus = pathHistory.get("currGNSSstatus", None)
            if currGNSSstatus is not None:
                target_currGNSSstatus = {}
                target_currGNSSstatus["GNSSstatus_unavailable"] = currGNSSstatus.get("GNSSstatus_unavailable", None)
                target_currGNSSstatus["isHealthy"] = currGNSSstatus.get("isHealthy", None)
                target_currGNSSstatus["isMonitored"] = currGNSSstatus.get("isMonitored", None)
                target_currGNSSstatus["baseStationType"] = currGNSSstatus.get("baseStationType", None)
                target_currGNSSstatus["aPDOPofUnder5"] = currGNSSstatus.get("aPDOPofUnder5", None)
                target_currGNSSstatus["inViewOfUnder5"] = currGNSSstatus.get("inViewOfUnder5", None)
                target_currGNSSstatus["localCorrectionsPresent"] = currGNSSstatus.get("localCorrectionsPresent", None)
                target_currGNSSstatus["networkCorrectionsPresent"] = currGNSSstatus.get("networkCorrectionsPresent",
                                                                                        None)
                target_pathHistory["currGNSSstatus"] = target_currGNSSstatus

            # crumbData
            crumbData = pathHistory.get("crumbData", None)
            if crumbData is not None:
                target_crumbData = []
                for crumbDatum in crumbData:
                    target_crumbDatum = {}
                    target_crumbDatum["heading"] = crumbDatum.get("heading", None)
                    target_crumbDatum["timeOffset"] = crumbDatum.get("timeOffset", None)
                    target_crumbDatum["speed"] = crumbDatum.get("speed", None)
                    target_crumbDatum["posAccuracy"] = crumbDatum.get("posAccuracy", None)

                    # llvOffset
                    llvOffset = crumbDatum.get("llvOffset", None)
                    if llvOffset is not None:
                        target_llvOffset = {}

                        # offsetLL
                        offsetLL = llvOffset.get("offsetLL", None)
                        if offsetLL is not None:
                            target_offsetLL = {}
                            target_offsetLL["choiceID"] = offsetLL.get("choiceID", None)

                            # position_LatLon
                            position_LatLon = offsetLL.get("position_LatLon", None)
                            if position_LatLon is not None:
                                target_position_LatLon = {}
                                target_position_LatLon["long"] = position_LatLon.get("long", None)
                                target_position_LatLon["lat"] = position_LatLon.get("lat", None)
                                target_offsetLL["position_LatLon"] = target_position_LatLon

                            target_llvOffset["offsetLL"] = target_offsetLL

                        # offsetV
                        offsetV = llvOffset.get("offsetV", None)
                        if offsetV is not None:
                            target_offsetV = {}
                            target_offsetV["choiceID"] = offsetV.get("choiceID", None)
                            target_offsetV["elevation"] = offsetV.get("elevation", None)
                            target_llvOffset["offsetV"] = target_offsetV

                        target_crumbDatum["llvOffset"] = target_llvOffset
                        target_crumbData.append(target_crumbDatum)

                target_pathHistory["crumbData"] = target_crumbData

            target_safetyExt["pathHistory"] = target_pathHistory
        else:
            crumbDataDefault = []
            crumbDataDefault.append(
                {"llvOffset": {"offsetLL": None, "offsetV": None}, "timeOffset": None, "speed": None,
                 "posAccuracy": None, "heading": None})
            target_safetyExt["pathHistory"] = {"initialPosition": None,
                                               "currGNSSstatus": None,
                                               "crumbData": crumbDataDefault}

        # pathPrediction
        pathPrediction = safetyExt.get("pathPrediction", None)
        if pathPrediction is not None:
            target_pathPrediction = {}
            target_pathPrediction["radiusOfCurve"] = pathPrediction.get("radiusOfCurve", None)
            target_pathPrediction["confidence"] = pathPrediction.get("confidence", None)
            target_safetyExt["pathPrediction"] = target_pathPrediction
        else:
            target_safetyExt["pathPrediction"] = {"radiusOfCurve": 0.0, "confidence": 0.0}

        # lights
        lights = safetyExt.get("lights", None)
        if lights is not None:
            target_lights = {}
            target_lights["daytimeRunningLightsOn"] = lights.get("daytimeRunningLightsOn", None)
            target_lights["automaticLightControlOn"] = lights.get("automaticLightControlOn", None)
            target_lights["parkingLightsOn"] = lights.get("parkingLightsOn", None)
            target_lights["rightTurnSignalOn"] = lights.get("rightTurnSignalOn", None)
            target_lights["hazardSignalOn"] = lights.get("hazardSignalOn", None)
            target_lights["lowBeamHeadlightsOn"] = lights.get("lowBeamHeadlightsOn", None)
            target_lights["highBeamHeadlightsOn"] = lights.get("highBeamHeadlightsOn", None)
            target_lights["leftTurnSignalOn"] = lights.get("leftTurnSignalOn", None)
            target_lights["fogLightOn"] = lights.get("fogLightOn", None)
            target_safetyExt["lights"] = target_lights

        target_dict["safetyExt"] = target_safetyExt

    # emergencyExt
    emergencyExt = payload.get("emergencyExt", None)
    if emergencyExt is not None:
        target_emergencyExt = {}
        target_emergencyExt["responseType"] = emergencyExt.get("responseType", None)
        target_emergencyExt["sirenUse"] = emergencyExt.get("sirenUse", None)
        target_emergencyExt["lightsUse"] = emergencyExt.get("lightsUse", None)
        target_dict["emergencyExt"] = target_emergencyExt

        # additional
    additional = payload.get("additional", None)
    if additional is not None:
        target_additional = {}
        target_additional["vip_status"] = additional.get("vip_status", None)
        target_additional["vehicle_num"] = additional.get("vehicle_num", None)
        target_additional["drive_status"] = additional.get("drive_status", None)
        target_additional["modem_status"] = additional.get("modem_status", None)
        target_additional["temperature"] = additional.get("temperature", None)
        target_additional["gnss_status"] = additional.get("gnss_status", None)
        target_additional["mileage"] = additional.get("mileage", None)
        target_additional["timestamp"] = additional.get("timestamp", None)
        target_dict["additional"] = target_additional

    return target_dict


if __name__ == '__main__':
    # 加载 Avro Schema
    schema_path = "E:/ObuHuaLiBSMMessage.avsc"
    schema = avro.schema.parse(open(schema_path, "rb").read())
    # 创建 DatumReader
    datum_reader = DatumReader(schema)
    # Kafka 配置
    kafka_conf = {
        'bootstrap.servers': 'kafka-0.icos.city:29094',  # Kafka 地址
        'group.id': 'my-group8',  # 消费者组 ID
        'auto.offset.reset': 'earliest'  # 从最早的消息开始消费
    }
    # Schema Registry 配置
    # schema_registry_conf = {'url': 'http://kafka-0.icos.city:29094'}  # Schema Registry 地址
    # schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    # 创建 Avro 反序列化器
    # avro_deserializer = AvroDeserializer(schema_registry_client)
    # 创建 Kafka 消费者
    consumer = Consumer(kafka_conf)
    # 订阅 Topic
    consumer.subscribe(['TEL.baidu.xbox.bsm'])

    # 消费消息
    try:
        while True:
            msg = consumer.poll(1.0)  # 拉取消息
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print("Reached end of partition")
                else:
                    print("Error: ", msg.error())
            else:
                with open('E:\\file.avro', 'rb') as input_file:
                    #将二进制内容写入文件
                    content = input_file.read()
                    bytes_reader = io.BytesIO(content)
                    decoder = BinaryDecoder(bytes_reader)
                    user = datum_reader.read(decoder)
                    print("File message: ", user)

                with open('E:\\file'+str(msg.timestamp())+'.avro', 'wb') as output_file:
                    buffer = io.BytesIO(msg.value())
                    output_file.write(buffer.getvalue())
                    output_file.flush()  # 确保数据写入磁盘
                buffer.close()
                # 解析 Avro 消息
                bytes_reader = io.BytesIO(msg.value())
                decoder = BinaryDecoder(bytes_reader)
                user = datum_reader.read(decoder)
                print("Received message: ", user)

    except KeyboardInterrupt:
        pass
    finally:
        # 关闭消费者
        consumer.close()