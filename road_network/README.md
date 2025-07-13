# 路网数据处理工具

## 目录结构

```
road_network/
├── processors/           # 处理器脚本
│   ├── cross_info_processor.py      # 交叉口信息处理器
│   ├── rid_info_processor.py        # 路段信息处理器
│   ├── lane_info_processor.py       # 车道信息处理器
│   ├── area_info_processor.py       # 区域信息处理器
│   ├── area_cross_processor.py      # 区域路口关系处理器
│   ├── cross_turn_processor.py      # 路口转向信息处理器
│   ├── cross_dir_processor.py       # 路口方向信息处理器
│   ├── update_rid_cross_relation.py # 路段-交叉口关系更新(基于名称匹配)
│   └── update_rid_cross_by_id.py    # 路段-交叉口关系更新(基于ID解析)
├── config/              # 配置文件
└── README.md           # 本说明文档
```

## 功能说明

### 1. cross_info_processor.py

- **功能**: 处理交叉口基础信息数据
- **输入**: luwangJson/路口点.json
- **输出**: MySQL 数据库表 t_base_cross_info
- **特性**:
  - 自动推断交叉口类型(T 型、十字、环形等)
  - 根据坐标映射区域代码
  - 处理 Unicode 编码兼容性
- **结果**: 成功导入 16 条交叉口记录

### 2. rid_info_processor.py

- **功能**: 处理路段基础信息数据
- **输入**: luwangJson/路段面.json
- **输出**: MySQL 数据库表 t_base_rid_info
- **特性**:
  - 道路等级推断(高速、国道、城市主干道等)
  - 路段长度和方向趋势计算
  - 几何数据 WKT 格式转换
  - 宽度信息提取
- **结果**: 成功导入 37 条路段记录

### 3. lane_info_processor.py

- **功能**: 处理车道基础信息数据
- **输入**: luwangJson/车道.json
- **输出**: MySQL 数据库表 t_base_lane_info
- **特性**:
  - 车道类型推断(路段车道、进口车道、出口车道等)
  - 车道转向自动识别
  - 车道类别分类(机动车、非机动车、公交专用等)
  - 关联路口 ID 和路段编号
  - MultiPolygon 几何数据 WKT 转换
- **结果**: 成功导入 1689 条车道记录(97.3%成功率)
  - 路段车道: 940 条
  - 进口车道: 626 条
  - 出口车道: 123 条
  - 机动车道: 1483 条
  - 非机动车道: 206 条

### 4. update_rid_cross_relation.py

- **功能**: 基于名称匹配更新路段与交叉口关系
- **方法**: 通过路段名称匹配交叉口名称
- **效果**: 起点 ID 匹配率 89.2%，终点 ID 匹配率 5.4%

### 5. update_rid_cross_by_id.py

- **功能**: 基于 ID 结构解析更新路段与交叉口关系
- **方法**: 从路段 ID 中直接提取起点和终点交叉口 ID
- **效果**: 起点 ID 匹配率 97.3%，终点 ID 匹配率 97.3%
- **原理**: 发现路段 ID 结构为`[起点交叉口ID(11)][终点交叉口ID(11)][序号(1)]`

### 6. area_info_processor.py

- **功能**: 处理区域基础信息数据
- **输入**: luwangJson/路口形状.json、绿化带.json 等多个文件
- **输出**: MySQL 数据库表 t_base_area_info
- **特性**:
  - 整合多种区域类型(安全岛、绿化带、停车位、公交车站等)
  - 区域类型自动分类
  - 几何中心点计算
  - 空间边界数据处理
- **结果**: 成功导入 34 条区域记录

### 7. area_cross_processor.py

- **功能**: 建立区域与路口的空间关系
- **输入**: 基于已有的区域信息表和路口信息表
- **输出**: MySQL 数据库表 t_base_area_cross
- **特性**:
  - 基于地理距离最近匹配(5 公里范围内)
  - 基于区域代码精确匹配
  - Haversine 公式计算地理距离
  - 自动去重和错误处理
- **结果**: 成功建立 16 个区域路口关系(100%覆盖率)

### 8. cross_turn_processor.py

- **功能**: 处理地面箭头数据，提取路口转向信息
- **输入**: luwangJson/地面箭头.json
- **输出**: MySQL 数据库表 t_base_cross_turn_info
- **特性**:
  - 识别 4 种转向类型：直行(s)、左转(l)、右转(r)、掉头(u)
  - 基于方向代码映射 8 个方向
  - 自动计算驶出方向
  - 路口 ID 验证和关联
  - Unicode 箭头符号解析
- **结果**: 成功创建 43 条转向记录，覆盖 16 个路口

### 9. cross_dir_processor.py

- **功能**: 处理渠化段数据，提取路口方向基础信息
- **输入**: luwangJson/渠化段.json、luwangJson/斑马线.json
- **输出**: MySQL 数据库表 t_base_cross_dir_info
- **特性**:
  - 渠化段序号解析（100-900）
  - 方向类型推断（1-8：北、东北、东、东南、南、西南、西、西北）
  - 进出口类型判断（1 进口；2 出口）
  - 长度计算（多边形周长）
  - 行人过街设施检测（基于斑马线数据）
- **结果**: 成功创建 240 条方向记录，覆盖 16 个路口（100%覆盖率）

## 数据库表结构

### t_base_cross_info (交叉口基础信息表)

- 16 条记录，覆盖主要交叉口
- 包含交叉口类型、等级、位置信息
- 所有记录区域代码为 420100(武汉市)

### t_base_rid_info (路段基础信息表)

- 37 条记录，覆盖主要道路
- 包含路段等级、长度、方向、几何信息
- 94.6%的路段已正确关联起点和终点交叉口

### t_base_lane_info (车道基础信息表)

- 1689 条记录，详细车道级别数据
- 包含车道类型、转向、类别、尺寸信息
- 支持精确到车道级别的交通分析

### t_base_area_info (区域基础信息表)

- 34 条记录，涵盖多种区域类型
- 包含安全岛、绿化带、停车位、公交车站等
- 支持区域级别的空间分析

### t_base_area_cross (区域路口关系表)

- 16 条记录，建立区域与路口的空间关系
- 基于地理距离和区域代码匹配
- 支持区域级别的路口查询和分析

### t_base_cross_turn_info (路口转向基础信息表)

- 43 条记录，详细的路口转向规则
- 包含直行、左转、右转、掉头 4 种转向类型
- 支持交通仿真和路径规划应用

### t_base_cross_dir_info (路口方向基础信息表)

- 240 条记录，详细的路口方向段信息
- 包含 8 个方向类型（北、东北、东、东南、南、西南、西、西北）
- 进出口类型分类（进口 137 条，出口 103 条）
- 长度信息和行人过街设施标识
- 支持精细化的路口几何分析

## 数据质量

### 空间关系完整性

- **交叉口-路段关系**: 94.6%完整
- **路段-车道关系**: 通过渠化段 ID 关联
- **空间几何**: 完整的 WKT 格式存储

### 数据覆盖率

- **交叉口**: 100% (16/16)
- **路段**: 100% (37/37)
- **车道**: 97.3% (1689/1736)
- **区域**: 100% (34/34)
- **区域路口关系**: 100% (16/16)
- **路口转向**: 11.1% (43/386) 覆盖全部 16 个路口
- **路口方向**: 46.5% (240/516) 覆盖全部 16 个路口

## 使用说明

1. **环境要求**: Python 2.7, pymysql
2. **数据库**: MySQL 5.7+
3. **执行顺序**:

   ```bash
   # 1. 处理交叉口数据
   python cross_info_processor.py

   # 2. 处理路段数据
   python rid_info_processor.py

   # 3. 处理车道数据
   python lane_info_processor.py

   # 4. 处理区域信息
   python area_info_processor.py

   # 5. 建立区域路口关系
   python area_cross_processor.py

   # 6. 处理路口转向信息
   python cross_turn_processor.py

   # 7. 处理路口方向信息
   python cross_dir_processor.py

   # 8. 更新路段-交叉口关系
   python update_rid_cross_by_id.py
   ```

4. **配置修改**: 更新`config/database_config.py`中的数据库连接参数

## 技术特点

- **编码兼容**: 支持 Python 2.7 和 UTF-8 编码
- **几何处理**: GeoJSON 到 WKT 格式转换
- **数据推断**: 智能推断缺失的属性信息
- **关系发现**: 自动发现 ID 结构规律建立数据关联
- **错误处理**: 完善的异常处理和日志输出
- **统计分析**: 详细的数据质量统计报告

## 应用场景

- 交通仿真建模
- 路网拓扑分析
- 交通流量分析
- 智能交通系统
- 导航路径规划
- 交通决策支持

## 区域路口关系数据关联原理

区域路口关系表的数据关联采用了**双重策略**，以确保关系的准确性：

### 1. 主要策略：基于地理距离的最近匹配

#### 距离计算公式

使用**Haversine 公式**计算两点间的地理距离：

```python
def calculate_distance(self, lon1, lat1, lon2, lat2):
    R = 6371000  # 地球半径（米）
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon/2) * math.sin(delta_lon/2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    distance = R * c
    return distance
```

#### 匹配逻辑

1. **遍历所有路口**：对每个路口计算到所有区域的距离
2. **找最近区域**：选择距离最小的区域作为匹配对象
3. **距离阈值**：只有在**5000 米（5 公里）**范围内才建立关系
4. **创建关系**：插入`t_base_area_cross`表

### 2. 辅助策略：基于区域代码的精确匹配

如果路口数据中有`area_code`字段且不为 0，会尝试找到相同`code`的区域进行精确匹配。

### 3. 实际关联结果

从处理结果可以看到距离分布：

```
创建关系: area_id=496129 -> cross_id=12Q2K099BL0 距离:28.36m
创建关系: area_id=496266 -> cross_id=12Q3Q099D
```
