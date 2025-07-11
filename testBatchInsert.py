import pymysql
import random
from datetime import datetime

# 连接数据库
conn = pymysql.connect(
    host='192.168.208.42',
    user='root',
    port=53306,
    password='Wanji300552',
    database='source_db'
)


# conn = pymysql.connect(
#     host='192.168.207.8',
#     user='source_dit',
#     port=3306,
#     password='BhC8X5AsLH6aekfJ',
#     database='source_dit'
# )
cursor = conn.cursor()

# 创建一条插入数据的SQL语句
insert_sql = "INSERT INTO `biz_order`(`order_no`, `start_point`, `end_point`, `order_time`, `boarding_time`, `vin`, `drop_location`, `drop_time`, `mileage`, `driving_time`, `status`, `response_time`, `cancel_order_time`, `dep_point`, `wait_mile`, `fact_price`, `price`, `pay_mode`, `pay_proof`, `modify_time`, `dest_time`, `update_time`) VALUES ( '%s', '114.1551502024515,30.417289448535335', '114.15497662622965,30.417348864309986', 1728552456706, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);"

# 生成百万条数据
data_to_insert = [(random.random()) for _ in range(10000)]

try:
    # 使用executemany批量插入
    for x in range(100):
        start =datetime.now()
        cursor.executemany(insert_sql, data_to_insert)
        conn.commit()  # 提交事务
        print("成功插入"+str(x+1)+"万条数据,时间：",datetime.now()-start)
    print("成功插入百万条数据")
except Exception as e:
    print(f"插入数据时发生错误: {e}")
    conn.rollback()  # 回滚事务
finally:
    cursor.close()
    conn.close()
