long_distance_bus_tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_long_distance_bus_info",
            "description": "分页查询丽江市长途客车的全量信息，返回长途客车的全量信息、客车总数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "页码，分页查询。",
                        "default": 1
                    }
                },
                "required": ["page"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_long_distance_bus_operation_status",
            "description": "查询指定车牌号的长途客车的详细信息，运营状态。",
            "parameters": {
                "type": "object",
                "properties": {
                    "veh_plate": {
                        "type": "string",
                        "description": "车牌号"
                    }
                },
                "required": ["veh_plate"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_long_distance_bus_alarm_data",
            "description": "查询指定车牌号的长途客车的报警详细数据，包括报警类型，报警时间等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "veh_plate": {
                        "type": "string",
                        "description": "车牌号"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "报警数据的开始时间，格式为YYYY-MM-DD hh:mm:ss"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "报警数据的结束时间，格式为YYYY-MM-DD hh:mm:ss"
                    }
                },
                "required": ["veh_plate", "start_time", "end_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_all_long_distance_bus_alarm_data",
            "description": "查询全量长途客车的报警详细数据，包括报警类型，报警时间等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "报警数据的开始时间，格式为YYYY-MM-DD hh:mm:ss"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "报警数据的结束时间，格式为YYYY-MM-DD hh:mm:ss"
                    },
                    "page": {
                        "type": "integer",
                        "description": "页码，分页查询。",
                        "default": 1
                    }
                },
                "required": ["start_time", "end_time", "page"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_all_long_distance_bus_driver_info",
            "description": "获取丽江市长途客车驾驶员全量信息，返回驾驶员详细信息、总人数、分页信息等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "页码，分页查询。",
                        "default": 1
                    }
                },
                "required": ["page"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_long_distance_bus_driver_cert_status",
            "description": "查询长途客车司机从业资格证状态，有效期等详细信息。",
            "parameters": {
                "type": "object",
                "properties": {
                    "driver_name": {
                        "type": "string",
                        "description": "司机姓名"
                    }
                },
                "required": ["driver_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_all_long_distance_transport_companies",
            "description": "获取丽江长途客运公司全量信息。",
            "parameters": {}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_long_distance_transport_company_by_name",
            "description": "获取指定名称的长途客运公司的经营状态等详细数据。",
            "parameters": {
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "长途客运公司名称"
                    }
                },
                "required": ["company_name"]
            }
        }
    }
]