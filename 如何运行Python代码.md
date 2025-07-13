# 如何在 Cursor 中运行 Python 代码

## 🚀 快速开始

### 1. 选择 Python 解释器（重要！）

**第一步：设置正确的 Python 解释器**

1. 打开任意`.py`文件
2. 按 `Cmd+Shift+P` 打开命令面板
3. 输入 `Python: Select Interpreter`
4. 选择：`/Users/duwei/anaconda3/envs/myrid-env/bin/python`

### 2. 运行 Python 代码的 4 种方法

#### 方法 1：右键运行（最简单）

1. 右键点击 Python 文件
2. 选择 `Run Python File in Terminal`

#### 方法 2：快捷键运行

- 按 `Ctrl+F5` 直接运行当前文件
- 或按 `F5` 进入调试模式

#### 方法 3：命令面板运行

1. `Cmd+Shift+P`
2. 输入 `Python: Run Python File in Terminal`

#### 方法 4：终端手动运行

```bash
/Users/duwei/anaconda3/envs/myrid-env/bin/python your_file.py
```

## 📝 实际运行示例

我已经创建了 `test_env.py` 测试文件，演示如何运行：

```python
# 运行结果展示：
🚀 MyRid Python环境测试
==================================================
📍 Python版本: 3.9.23
📁 Python路径: /Users/duwei/anaconda3/envs/myrid-env/bin/python
📂 当前工作目录: /Users/duwei/workspace/wanji/myrid

📦 核心依赖包测试:
  ✅ numpy: 2.0.2
  ✅ pandas: 2.3.1
  ✅ shapely: 2.0.7
  ✅ pyproj: 3.6.1
  ✅ networkx: 3.2.1
  ✅ psycopg2: 2.9.10
  ✅ requests: 2.32.4
  ✅ geographiclib: 2.0

🗺️  几何计算演示:
  📍 点1: POINT (110.3293 20.0311)
  📍 点2: POINT (110.35 20.04)
  📏 线段长度: 0.050816度
  📏 点间距离: 0.022532度
```

## ❗ 红线错误解释

### 为什么会有红线？

项目中的红线主要来自**QGIS 相关导入**：

```python
# 这些会显示红线，但是正常的！
from qgis.PyQt.QtCore import QSettings, QTranslator  # ❌ 红线
from qgis.core import QgsApplication, QgsTask         # ❌ 红线
from qgis._gui import QgsRubberBand                   # ❌ 红线
```

### 为什么是正常的？

1. **QGIS 模块只在 QGIS 环境中存在**

   - 我们的 conda 环境没有安装 QGIS
   - 只有在 QGIS 中运行插件时才能导入这些模块

2. **开发环境 vs 运行环境**
   - **开发环境（Cursor）**: 代码编辑、智能提示、格式化
   - **运行环境（QGIS）**: 插件实际运行

## 🎯 可以正常运行的代码

### 数据处理代码

```python
import numpy as np
import pandas as pd
from shapely.geometry import Point, LineString

# 海口市坐标数据处理
data = {
    'name': ['海口', '三亚', '儋州'],
    'lon': [110.3293, 109.5115, 109.5765],
    'lat': [20.0311, 18.2527, 19.5175]
}

df = pd.DataFrame(data)
points = [Point(row.lon, row.lat) for _, row in df.iterrows()]
print("✅ 数据处理成功！")
```

### 几何计算代码

```python
from shapely.geometry import Point, LineString
import geographiclib.geodesic as geo

# 海口两点间距离计算
p1 = Point(110.3293, 20.0311)
p2 = Point(110.3500, 20.0400)

# 计算真实地理距离
geod = geo.Geodesic.WGS84
distance = geod.Inverse(p1.y, p1.x, p2.y, p2.x)['s12']
print(f"两点距离: {distance:.2f}米")
```

### 数据库连接代码（需要配置）

```python
import psycopg2
import json

# 读取配置
with open('./config/config.json', 'r') as f:
    config = json.load(f)

# 连接数据库（如果数据库已启动）
try:
    conn = psycopg2.connect(
        host=config['dbinfo']['host'],
        database=config['dbinfo']['dbname'],
        user=config['dbinfo']['user'],
        password=config['dbinfo']['pw']
    )
    print("✅ 数据库连接成功!")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
```

## 🔧 处理红线的策略

### 1. 忽略 QGIS 相关红线

- 这些在 QGIS 中运行时是正常的
- 专注于业务逻辑代码的开发

### 2. 分离可测试代码

```python
# good: 可以在开发环境测试
def calculate_distance(point1, point2):
    from geographiclib.geodesic import Geodesic
    geod = Geodesic.WGS84
    return geod.Inverse(point1[1], point1[0], point2[1], point2[0])['s12']

# bad: 依赖QGIS，无法在开发环境测试
def add_layer_to_qgis(layer_data):
    from qgis.core import QgsVectorLayer  # 红线
    # ...
```

### 3. 使用条件导入

```python
try:
    from qgis.core import QgsApplication
    QGIS_AVAILABLE = True
except ImportError:
    QGIS_AVAILABLE = False
    print("QGIS环境不可用，仅开发模式")
```

## 💡 最佳实践

### 开发流程

1. **编写业务逻辑** → 在 Cursor 中开发和测试
2. **集成 QGIS 功能** → 忽略红线，在 QGIS 中测试
3. **完整功能验证** → 在 QGIS 中加载插件测试

### 推荐的开发顺序

1. 先开发**纯 Python 算法**（无红线）
2. 再添加**QGIS 集成**（有红线但正常）
3. 最后在**QGIS 中测试**完整功能

## 🎉 现在试试！

1. 打开 `test_env.py`
2. 按 `Ctrl+F5` 运行
3. 看到成功输出说明环境配置正确！

**记住：红线不代表错误，只是开发环境和运行环境的差异！**
