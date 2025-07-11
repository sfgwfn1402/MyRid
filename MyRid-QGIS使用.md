# MyRid-QGIS操作使用指南

## 📋 概述

本文档详细介绍MyRid插件在QGIS中的实际操作流程，包括插件功能使用方法、数据处理步骤和数据库表的输入输出关系。

## 🔧 环境准备

### 必要软件
- **QGIS**: 3.16+ (推荐3.28 LTR)
- **PostgreSQL**: 12+ with PostGIS 3.0+
- **Python**: 3.7+ (QGIS内置)

### 数据库配置
```json
{
  "dbinfo": {
    "host": "localhost",
    "port": 5432,
    "dbname": "gisc_haikou",
    "user": "postgres", 
    "pw": "123456"
  }
}
```

## 🚀 MyRid插件功能详解

### 插件界面布局

插件加载后，QGIS工具栏会出现MyRid工具集，包含以下主要功能：

```
MyRid工具栏:
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 获取OSM数据  │ 道路数据入库  │ RID数据初始化 │ RID数据生成  │
└─────────────┴─────────────┴─────────────┴─────────────┘
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 道路列表     │ Rid匹配OpenLr│ 位置匹配验证  │ 图层加载    │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

## 📊 完整操作流程

### 第一步：获取OSM数据

#### 操作方法
1. 点击工具栏 **"获取OSM数据"** 按钮
2. 系统自动下载指定区域的OpenStreetMap道路数据
3. 等待下载完成（显示进度条）

#### 数据输出
- **文件**: `data/osm_data.gpkg` (约24MB)
- **内容**: 海口市道路网络数据
  - `nodes` 图层：2690个路网节点
  - `edges` 图层：6079条道路段

#### 技术细节
```python
# 下载范围：海口市 (行政区代码: 460100)
# 坐标范围：经度 110.68-110.69°, 纬度 19.80-19.82°
# 网络类型：drive (机动车道路)
```

### 第二步：道路数据入库

#### 操作方法
1. 点击 **"道路数据入库"** 按钮
2. 系统将OSM数据导入PostgreSQL数据库
3. 自动创建空间索引

#### 数据库表创建

**输入**: `data/osm_data.gpkg`

**输出表**:

| 表名 | 记录数 | 描述 | 关键字段 |
|------|--------|------|----------|
| `osm_nodes` | 2690 | 道路节点表 | osmid, x, y, geom |
| `osm_segment` | 6079 | 道路路段表 | osmid, fnode, tnode, name, geom |

```sql
-- osm_nodes 表结构
CREATE TABLE osm_nodes (
    osmid BIGINT PRIMARY KEY,           -- OSM节点ID
    x DOUBLE PRECISION,                 -- 经度
    y DOUBLE PRECISION,                 -- 纬度  
    geom GEOMETRY(POINT, 4326),         -- 点几何
    cross INTEGER DEFAULT 0            -- 路口标识
);

-- osm_segment 表结构  
CREATE TABLE osm_segment (
    osmid BIGINT,                       -- OSM路段ID
    fnode BIGINT,                       -- 起始节点
    tnode BIGINT,                       -- 终止节点
    name VARCHAR(200),                  -- 道路名称
    highway VARCHAR(50),                -- 道路类型
    length DOUBLE PRECISION,            -- 长度(米)
    geom GEOMETRY(LINESTRING, 4326),    -- 线几何
    maxspeed VARCHAR(20),               -- 限速
    oneway VARCHAR(10)                  -- 单行道
);
```

### 第三步：RID数据初始化

#### 操作方法
1. 点击 **"RID数据初始化"** 按钮
2. 系统创建RID相关的数据库表结构
3. 执行初始化SQL脚本

#### 创建的数据表

| 表名 | 功能 | 主要字段 |
|------|------|----------|
| `rid_rid` | 道路标识主表 | rid, name, geom, openlr_base64 |
| `rid_cross` | 路口信息表 | crossid, crossname, geom |
| `rid_lane_obj` | 车道对象表 | laneid, rid, lane_info |
| `rid_axf_three` | 三级分类表 | id, rid, classification |
| `gaode_link` | 链路映射表 | link_id, rid, geom |

```sql
-- rid_rid 核心表结构
CREATE TABLE rid_rid (
    rid VARCHAR(23) PRIMARY KEY,        -- 道路唯一标识
    name VARCHAR(200),                  -- 道路名称  
    roadclass VARCHAR(5),               -- 道路等级
    length INTEGER,                     -- 长度
    startcrossid VARCHAR(11),           -- 起点路口ID
    endcrossid VARCHAR(11),             -- 终点路口ID
    geom GEOMETRY(LINESTRING, 4326),    -- 道路几何
    openlr_base64 VARCHAR(100),         -- OpenLR编码
    from_way VARCHAR(8),                -- 道路类型
    fow INTEGER,                        -- Form of Way
    roadclass INTEGER                   -- 功能等级
);

-- rid_cross 路口表结构
CREATE TABLE rid_cross (
    crossid VARCHAR(11) PRIMARY KEY,   -- 路口唯一标识
    crossname VARCHAR(200),            -- 路口名称
    cross_type INTEGER,                -- 路口类型
    geom GEOMETRY(POINT, 4326),        -- 路口位置
    connect_road_count INTEGER         -- 连接道路数
);
```

### 第四步：RID数据生成

#### 操作方法
1. 点击 **"RID数据生成"** 按钮
2. 系统分析道路连通性，生成标准化道路标识
3. 处理时间较长，建议耐心等待

#### 数据处理逻辑

**输入表**: `osm_nodes`, `osm_segment`

**处理算法**:
1. **道路名称分组**: 按name字段聚合相同道路
2. **连通性分析**: 计算同名道路的连通分量  
3. **RID生成**: 为每个连通分量生成唯一标识符
4. **路口识别**: 标识道路起终点的重要路口

**输出结果**:
- `rid_rid`: 11条道路记录
- `rid_cross`: 11个路口记录  
- `gaode_link`: 200条链路记录

#### 示例数据
```sql
-- RID数据示例
SELECT rid, name, length, startcrossid, endcrossid 
FROM rid_rid LIMIT 3;

-- 结果示例:
-- RID2024001001 | 椰海大道 | 1520 | CROSS_001 | CROSS_002
-- RID2024001002 | 美好路   | 890  | CROSS_003 | CROSS_004  
-- RID2024001003 | 海府路   | 2340 | CROSS_005 | CROSS_006
```

### 第五步：查看道路列表

#### 操作方法
1. 点击 **"道路列表"** 按钮
2. 弹出道路选择对话框
3. 列表显示所有可用的RID道路

#### 道路列表界面
```
┌─────────────────────────────────────────┐
│              道路列表选择                  │
├─────────────────────────────────────────┤
│ □ 椰海大道辅路:美好路@椰海大道路段          │
│ □ 海府路:人民大道@海府路路段               │
│ □ 龙昆北路:海府路@龙昆北路路段             │
│ □ 美好路:椰海大道@美好路路段               │
│ ...                                     │
├─────────────────────────────────────────┤
│           [确定]  [取消]                  │
└─────────────────────────────────────────┘
```

### 第六步：OpenLR编码生成

#### 操作方法
1. 在道路列表中选择特定道路（如：椰海大道辅路）
2. 点击 **"Rid匹配OpenLr"** 按钮  
3. 系统执行OpenLR位置编码算法
4. 生成Base64格式的编码结果

#### OpenLR编码过程

**输入**: 选中的RID几何数据

**算法步骤**:
1. **路网图构建**: 基于osm_segment构建拓扑图
2. **路径匹配**: 将RID几何匹配到路网图
3. **LRP选择**: 选择关键的位置参考点
4. **编码压缩**: 生成二进制编码并转Base64

**输出表**: `data_openlr`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 自增ID |
| rid | VARCHAR(23) | 关联的道路ID |
| openlr_base64 | TEXT | OpenLR编码字符串 |
| lrp_count | INTEGER | 位置参考点数量 |
| total_length | DOUBLE | 总长度 |
| encode_time | TIMESTAMP | 编码时间 |

#### 编码结果示例
```sql
-- OpenLR编码结果
SELECT rid, openlr_base64, lrp_count, total_length 
FROM data_openlr LIMIT 2;

-- 结果示例:
-- RID2024001001 | CwRbACIA/gH4AQ== | 3 | 1520.5
-- RID2024001002 | CwRcBCIA/gH5AQ== | 2 | 890.2
```

### 第七步：位置匹配验证

#### 操作方法
1. 选择已编码的道路
2. 点击 **"位置匹配验证"** 按钮
3. 系统执行反向解码验证
4. 计算匹配精度

#### 验证过程

**输入**: OpenLR编码字符串

**验证算法**:
1. **编码解码**: 将Base64编码解析为位置参考点
2. **候选搜索**: 在路网中搜索候选路径
3. **匹配评分**: 计算几何相似度、方位角等得分
4. **精度计算**: 对比原始几何与匹配结果

**输出表**: `data_openlr_match`

| 字段 | 说明 |
|------|------|
| rid | 原始道路ID |
| matched_geometry | 匹配得到的几何 |
| match_score | 匹配得分 (0-1) |
| match_accuracy | 匹配精度 (%) |

### 第八步：图层加载与可视化

#### 操作方法
1. 点击 **"图层加载"** 按钮
2. 系统自动加载相关数据库图层到QGIS
3. 在地图画布中查看处理结果

#### 加载的图层

| 图层名称 | 数据源 | 样式 | 用途 |
|----------|--------|------|------|
| OSM节点 | osm_nodes | 红色圆点 | 显示路网节点 |
| OSM路段 | osm_segment | 蓝色线条 | 显示原始道路 |
| RID道路 | rid_rid | 绿色粗线 | 显示标准化道路 |
| 路口 | rid_cross | 黄色方块 | 显示重要路口 |
| 链路 | gaode_link | 紫色虚线 | 显示映射关系 |

#### 图层配置示例
```python
# 图层样式配置
layer_styles = {
    'osm_nodes': {
        'color': 'red',
        'size': 2,
        'symbol': 'circle'
    },
    'rid_rid': {
        'color': 'green', 
        'width': 3,
        'style': 'solid'
    },
    'rid_cross': {
        'color': 'yellow',
        'size': 5,
        'symbol': 'square'
    }
}
```

## 📊 数据流转总览

### 数据处理链路图

```
OSM原始数据 (外部)
    ↓ [获取OSM数据]
osm_data.gpkg (24MB文件)
    ↓ [道路数据入库]
osm_nodes (2690条) + osm_segment (6079条)
    ↓ [RID数据初始化]
rid_rid + rid_cross + rid_lane_obj + rid_axf_three + gaode_link (表结构)
    ↓ [RID数据生成] 
rid_rid (11条) + rid_cross (11条) + gaode_link (200条)
    ↓ [Rid匹配OpenLr]
data_openlr (编码结果)
    ↓ [位置匹配验证]
data_openlr_match (验证结果)
    ↓ [图层加载]
QGIS地图显示
```

### 核心数据表关系

```sql
-- 表关系图
osm_segment (原始路段)
    ↓ (聚合分析)
rid_rid (标准道路)
    ↓ (一对一映射)
gaode_link (链路表)
    ↓ (编码处理)
data_openlr (OpenLR编码)
    ↓ (验证解码)
data_openlr_match (匹配结果)

-- 关联关系
rid_rid.startcrossid → rid_cross.crossid
rid_rid.endcrossid → rid_cross.crossid
gaode_link.rid → rid_rid.rid
data_openlr.rid → rid_rid.rid
```

## 🔍 实际操作示例

### 完整操作演示

假设处理海口市道路数据的完整流程：

#### 1. 启动插件
```
QGIS → 插件 → 管理和安装插件 → MyRid (勾选)
工具栏出现 MyRid Tools
```

#### 2. 数据获取
```
点击 [获取OSM数据] 
→ 下载进度: "正在下载海口市道路数据..."
→ 完成提示: "OSM数据下载完成！文件: data/osm_data.gpkg"
```

#### 3. 数据入库
```
点击 [道路数据入库]
→ 处理进度: "正在导入节点数据... 2690条"
→ 处理进度: "正在导入路段数据... 6079条" 
→ 完成提示: "道路数据入库完成！"
```

#### 4. 初始化表结构
```
点击 [RID数据初始化]
→ 处理进度: "正在创建表结构..."
→ 完成提示: "RID表结构初始化完成！"
```

#### 5. 生成RID
```
点击 [RID数据生成]
→ 处理进度: "正在分析道路连通性..."
→ 处理进度: "正在生成道路标识符..."
→ 完成提示: "RID数据生成完成！生成11条道路，11个路口"
```

#### 6. 选择道路进行编码
```
点击 [道路列表]
→ 选择: "椰海大道辅路:美好路@椰海大道路段"
→ 点击 [确定]

点击 [Rid匹配OpenLr]  
→ 处理进度: "正在执行OpenLR编码..."
→ 完成提示: "OpenLR编码完成！编码: CwRbACIA/gH4AQ=="
```

#### 7. 验证匹配
```
点击 [位置匹配验证]
→ 处理进度: "正在执行匹配验证..."
→ 完成提示: "匹配验证完成！精度: 98.5%"
```

#### 8. 查看结果
```
点击 [图层加载]
→ QGIS图层面板显示:
  ├── OSM节点 (2690 要素)
  ├── OSM路段 (6079 要素) 
  ├── RID道路 (11 要素)
  ├── 路口 (11 要素)
  └── 链路 (200 要素)
```

## ⚠️ 注意事项

### 操作顺序要求
1. **必须按顺序执行**: 获取数据 → 入库 → 初始化 → 生成RID → 编码
2. **数据依赖关系**: 后续步骤依赖前面步骤的输出数据
3. **表结构完整性**: 删除任何核心表都需要重新初始化

### 性能考虑
- **大数据集处理**: 城市级数据处理可能需要5-10分钟
- **内存需求**: 建议8GB以上内存，16GB更佳
- **数据库优化**: 确保PostgreSQL配置adequate shared_buffers

### 常见问题
1. **插件无法加载**: 检查Python依赖库安装
2. **数据库连接失败**: 验证config.json配置
3. **OSM数据下载失败**: 检查网络连接
4. **RID生成数量少**: 正常现象，只处理有名称的主要道路

## 📋 数据质量检查

### 验证SQL查询

```sql
-- 检查数据完整性
SELECT 
    'osm_nodes' as table_name, COUNT(*) as record_count 
FROM osm_nodes
UNION ALL
SELECT 'osm_segment', COUNT(*) FROM osm_segment
UNION ALL  
SELECT 'rid_rid', COUNT(*) FROM rid_rid
UNION ALL
SELECT 'rid_cross', COUNT(*) FROM rid_cross
UNION ALL
SELECT 'gaode_link', COUNT(*) FROM gaode_link;

-- 检查OpenLR编码结果
SELECT 
    rid, 
    LENGTH(openlr_base64) as code_length,
    lrp_count,
    total_length
FROM data_openlr 
ORDER BY encode_time DESC;

-- 检查匹配验证结果
SELECT 
    rid,
    match_score,
    match_accuracy,
    CASE 
        WHEN match_accuracy >= 95 THEN '优秀'
        WHEN match_accuracy >= 85 THEN '良好' 
        WHEN match_accuracy >= 70 THEN '一般'
        ELSE '待优化'
    END as quality_level
FROM data_openlr_match
ORDER BY match_accuracy DESC;
```

---

## 📞 技术支持

如遇到操作问题，请检查：
1. **日志文件**: `logs/myrid_YYYYMMDD.log`
2. **配置文件**: `config/config.json`
3. **数据库状态**: PostgreSQL服务运行状态
4. **QGIS版本**: 确保版本兼容性

---

*本操作指南基于MyRid v0.1版本，适用于QGIS 3.28 LTR环境。*
