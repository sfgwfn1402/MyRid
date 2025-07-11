import uuid,os
from datetime import datetime, timedelta

# 生成一个随机的UUID
random_uuid = uuid.uuid4()
print("生成的UUID:", random_uuid)

# 如果你需要生成基于命名空间的UUID（例如，基于一个字符串）
namespace_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, 'example.com')
print("基于命名空间生成的UUID:", namespace_uuid)

folder_name = datetime.fromtimestamp(1741708800).hour
folder_path = os.path.join('ht=', str(folder_name).zfill(2))
print(folder_path)

folder_time =(datetime.fromtimestamp(1741708800).minute// 10) * 10

folder_path2 = os.path.join('mt=', str(folder_time).zfill(2))
print(folder_name)
print(folder_path2)




