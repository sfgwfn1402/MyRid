import random

import pymysql
from datetime import datetime, timedelta
import time

# 连接到MySQL数据库
db_config = {
    'host': '124.225.163.92',
    'port':53306,
    'user': 'root',
    'password': 'wanji@413',
    'database': 'wjdit_ecosystem_db_v1.1.0'
}


# 固定日期，格式为 'YYYY-MM-DD'
fixed_date = '2025-04-01'


def fetch_and_update_data():
    # 建立数据库连接
    # conn = pymysql.connect(**db_config)
    conn = pymysql.connect(host=db_config['host'], port=db_config['port'],user=db_config['user'], password=db_config['password'], db=db_config['database'])

    cursor = conn.cursor()

    # 查询固定日期的数据
    query = """SELECT * FROM t_event_info WHERE start_time IS NOT NULL AND end_time IS NOT NULL AND DATE(start_time) = '{0}' AND DATE_FORMAT(start_time, '%H:%i')=DATE_FORMAT(CURTIME(), '%H:%i')""".format(fixed_date)
    cursor.execute(query)

    fixed_date_data = cursor.fetchall()

    # 获取当前日期和时间
    current_datetime = datetime.now()
    current_date = current_datetime.date()

    # 生成当前日期的数据
    current_date_data = []
    for row in fixed_date_data:
        # 假设row[1] 是日期时间列，你需要根据实际情况调整索引
        old_datetime_start = row[11]
        old_datetime_end = row[12]
        old_time_start = old_datetime_start.time()
        old_time_end = old_datetime_end.time()

        new_datetime_start = datetime.combine(current_date, old_time_start)
        new_datetime_end = datetime.combine(current_date, old_time_end)

        # 这里假设你想要更新的数据就在row[1]，其他列保持不变，调整为你的实际情况
        new_row = list(row)
        new_row[11] = (new_datetime_start- timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        new_row[12] = new_datetime_end.strftime('%Y-%m-%d %H:%M:%S')
        new_row[29] = new_datetime_start.strftime('%Y%m%d')
        new_row[32] = random.choice([0,1,2,3,4])

        current_date_data.append(tuple(new_row))



    # 打印生成的数据，你可以根据需要将这些数据插入到数据库中
    for data in current_date_data:
        insert_query = f"""
               INSERT INTO t_event_info (`oid`, `plate_no`, `object_type`, `confidence`, `detect_time`, `grade`, `place_desc`, `lng`, `lat`, `category`, `type`, `start_time`, `end_time`, `duration`, `source`, `ruksj`, `lane_id`, `rid`, `segment_id`, `cross_id`, `green_id`, `camera_oid`, `event_serial_number`, `data_status`, `global_id`, `station_id`, `event_id`, `remark`, `extend`, `dt`, `video_urls`, `target_type`, `alarm_status`, `opt_status`, `modify_time`, `dir`, `turn`, `unbalance_index`, `spillover_index`, `traffic_index`)
               VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               """
        print(data)
        try:
            cursor.execute(insert_query, data)
            conn.commit()
        except:
            print('data insert error...')

    # 关闭数据库连接
    cursor.close()
    conn.close()

def fetch_and_update_data2():
    if True:
    # if datetime.now().time().strftime('%H:%M')=='00:00':
        conn = pymysql.connect(host=db_config['host'], port=db_config['port'],user=db_config['user'], password=db_config['password'], db=db_config['database'])
        cursor = conn.cursor()
        insert_query = """
                       INSERT INTO `t_strategy_cross_result`(  `cross_id`, `cross_name`, `current_algo`, `request_time`, `issue_time`, `response_code`, `response_content`, `timing_plan`, `insert_time`, `rtn_type`, `extend_time`, `block_region`, `block_type`, `count_down`, `video_stamp`, `signal_machine_stamp`, `control_dir`, `data`, `duration`, `empty_turn`, `empty_dir`, `plan_contrast_info`, `dt`, `event_id`) VALUES ( '11K14063RO0', '环岛旅游公路交长滨四路路口', 1, '{0} 10:00:00', '{0} 10:00:00', -1, '空放优化', NULL, '{0} 10:33:30', 12, -1, NULL, NULL, -1, NULL, '1742399998748', NULL, NULL, NULL, '0', '0', NULL, 20250320, NULL);
                       """.format(datetime.now().date().strftime('%Y-%m-%d'))

        try:
            cursor.execute(insert_query)
            conn.commit()
        except:
            print('data insert error...')

def fetch_and_update_data3():
    # ========实时报警  1分钟刷新一次=============
    # 1.	实时报警的“警情状态”改为“持续时长”
    # 2.	空放报警
    # a)	报警时段 00:00~7:00  每【5到15取随机值】分钟，进行报警。注：但时间不要超过当前时间，如果超过当前时间按当前时间进行报警。
    # b)	持续时长：3~8分钟取随机值。注意：报警时间+持续时长，不要超过下次报警时间，也不要超过当前时间。如果超过，用下次报警时间或当前时间-报警时间作为持续时长。
    # c)	空放方向：在【1 北  2 东 3 南】取随机值
    # 3.	失衡报警
    # a)	报警时段 07:00~18:00  每【30~50取随机值】分钟，进行报警。注：但时间不要超过当前时间，如果超过当前时间按当前时间进行报警。
    # b)	持续时长：5~10分钟取随机值。注意：报警时间+持续时长，不要超过下次报警时间，也不要超过当前时间。如果超过，用下次报警时间或当前时间-报警时间作为持续时长。
    # c)	失衡方向：在{【1 北，2东】，【1北 3南】，【2东 3南】}中取随机值
    current_date = datetime.now().date()
    start = datetime(current_date.year, current_date.month, current_date.day, 0, 0, 0)
    end = datetime(current_date.year, current_date.month, current_date.day, 7, 0, 0)
    #endx = datetime(current_date.year, current_date.month, current_date.day, 18, 0, 0)
    endx = datetime(current_date.year, current_date.month, current_date.day, 23, 0, 0)


    current_time=( datetime.now() - timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
    dt =  datetime.now().strftime('%Y%m%d')

    conn = pymysql.connect(host=db_config['host'], port=db_config['port'], user=db_config['user'],
                           password=db_config['password'], db=db_config['database'])
    cursor = conn.cursor()
    insert_query = f"""
           INSERT INTO t_event_info (`oid`, `plate_no`, `object_type`, `confidence`, `detect_time`, `grade`, `place_desc`, `lng`, `lat`, `category`, `type`, `start_time`, `end_time`, `duration`, `source`, `ruksj`, `lane_id`, `rid`, `segment_id`, `cross_id`, `green_id`, `camera_oid`, `event_serial_number`, `data_status`, `global_id`, `station_id`, `event_id`, `remark`, `extend`, `dt`, `video_urls`, `target_type`, `alarm_status`, `opt_status`, `modify_time`, `dir`, `turn`, `unbalance_index`, `spillover_index`, `traffic_index`)
           VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
           """

    # try:
        # 2.	空放报警
    if start <= datetime.now() and datetime.now() < end:
        data = (None, None, None, None, None, None, '空放', None, None, '4', '701', str(current_time), str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), random.choice([3,4,5,6,7,8]), None, current_time, None, None, None, '11JNK063PC0', '9', None, '11JNK063PC0-1743501130125-空放', None, None, None, None, None, None, str(dt), None, None, random.choice([0, 1, 2, 3, 4]), 0, current_time, '['+str(random.choice([2,3]))+']', '['+str(random.choice([2,3]))+']', None, None, 1.0)
        # data[32] = random.choice([0, 1, 2, 3, 4])
        # data[11] = (new_datetime_start- timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        print(data)
        cursor.execute(insert_query, data)
        # 3.	失衡报警
    if end <= datetime.now() and  datetime.now() < endx:
        data = (None, None, None, None, None, None, '失衡', None, None, '4', '702', str(current_time), str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), random.choice([5,6,7,8,9,10]), None, current_time, None, None, None, '11JNK063PC0', '9', None, '11JNK063PC0-1743501130125-失衡', None, None, None, None, None, None, str(dt), None, None, random.choice([0, 1, 2, 3, 4]), 0, current_time, str(random.choice([[1,2],[1,3],[2,3]])), str(random.choice([[1,2],[1,3],[2,3]])), None, None, 1.0)
        # data[32] = random.choice([0,1,2,3,4])
        # data[11] = (new_datetime_start- timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
        print(data)
        cursor.execute(insert_query, data)
    conn.commit()
    # except:
    #     print('data insert error...')


# 无限循环，检查是否有任务需要执行
while True:
    fetch_and_update_data3()
    if datetime.now().time().strftime('%H:%M') == '00:00':
        fetch_and_update_data2()
    time.sleep(random.choice([5,6,7,8,9,10,11,12,13,14,15])*60)  # 每隔60秒检查一次
    # time.sleep(60)  # 每隔60秒检查