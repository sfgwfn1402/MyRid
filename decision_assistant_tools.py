decision_assistant_tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_area_index_analysis_realtime",
            "description": "查询区域实时指标信息，区域实时交通状态。",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": "string"
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_cross_flow_list",
            "description": "查询路口交通流量分析信息，路口交通流量。（时间间隔15分钟，默认展示最近1.5小时流量）",
            "parameters": {
                "type": "object",
                "properties": {
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_rid_flow_list",
            "description": "查询路段交通流量分析信息，路段交通流量。时间间隔15分钟，默认展示最近1.5小时流量。",
            "parameters": {
                "type": "object",
                "properties": {
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_analysis_cross_run_state",
            "description": "查询所有路口运行状态详细数据，包括拥堵指数，溢出指数，失衡指数等。",
            "parameters": {
                "type": "object",
                "properties": {
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_analysis_cross_indicators_query",
            "description": "查询路口交通指标。",
            "parameters": {
                "type": "object",
                "properties": {
                    "crossId": "string"
                },
                "required": ["crossId"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_analysis_cross_indicators_top",
            "description": "查询路口效率排名。",
            "parameters": {
                "type": "object",
                "properties": {
                    "timeGranularity": {
                        "type": "string",
                        "description": "时间粒度 5m:五分钟 15m:15分钟 30m:30分钟 1h:一小时"
                    },
                    "count": "integer",
                    "startTime": {
                        "type": "string",
                        "description": "开始时间，格式为YYYY-MM-DD hh:mm:ss"
                    },
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_analysis_event_trend_list",
            "description": "交通事件趋势分析。",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "时间类型 1：当日 2：周(近7天) 3：月（近30天）"
                    }
                },
                "required": ["type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_event_info_list",
            "description": "按时间查询事件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "crossId": "string",
                    "dayType": {
                        "type": "string",
                        "description": "时间类型 1：当日 2：周(近7天) 3：月（近30天）"
                    }
                },
                "required": ["crossId","dayType"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_event_info_alarm",
            "description": "查询事件告警。",
            "parameters": {
                "type": "object",
                "properties": {
                    "eventType": {
                        "type": "string",
                        "description": "事件类型：1 机动车违停2	非机动车逆行3	机动车逆行4	占用专用车道5	行人在机动车道逗留6	机动车超速7	非机动车超速8	机动车慢行9	机动车压线10	非机动车横穿马路11	行人横穿马路12	机动车横穿马路13	机动车闯红灯14	行人闯红灯15	机动车占用公交车道16	机动车实线违规变道17	遗洒物（车道范围内有明显抛洒物）18	交通事故（碰撞/追尾/撞壁）19	占用应急车道23	非机动车越线停车24	非机动车占用机动车道25	非机动车闯红灯26	非机动车违规载人27	机动车不按规定车道行驶（例：直行车道遇路口左转）28	机动车占用非机动车道29	机动车越线停车30	施工31	机动车未礼让行人32	机动车限号出行33	急加速34	急减速35	急转弯36	s型驾驶401	疑似事故501	畅通502	轻微拥堵503	中度拥堵504	重度拥堵701	相位空放702	路口失衡703	路口溢出704	路口死锁 "
                    }
                },
                "required": ["eventType"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_base_cross_info_list",
            "description": "查询路口基础信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "crossName": {
                        "type": "string",
                        "description": "路口名模糊匹配"
                    }
                },
                "required": ["crossName"]
            }
        }
    }

]