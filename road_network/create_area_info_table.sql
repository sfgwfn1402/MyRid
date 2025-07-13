-- 创建区域基础信息表
CREATE TABLE IF NOT EXISTS t_base_area_info (
    id INT(10) UNSIGNED NOT NULL COMMENT '主键',
    code INT(6) NOT NULL DEFAULT 0 COMMENT '行政区划代码',
    name VARCHAR(50) NOT NULL DEFAULT '' COMMENT '行政区划名称',
    road_name VARCHAR(50) NOT NULL DEFAULT '' COMMENT '道路名称',
    type INT(11) NOT NULL DEFAULT 0 COMMENT '区划类型：1 行政区划，2 交警辖区，3 商圈，4 交通小区，5 热点区域，6 道路',
    parent_code INT(6) NOT NULL DEFAULT 0 COMMENT '父节点',
    location VARCHAR(50) NOT NULL DEFAULT '' COMMENT '区域中心点',
    polylines TEXT NOT NULL COMMENT '区域边界',
    remark VARCHAR(255) NOT NULL DEFAULT '' COMMENT '备注',
    gmt_create DATETIME NOT NULL COMMENT '创建时间',
    gmt_modified DATETIME NOT NULL COMMENT '修改时间',
    PRIMARY KEY (id),
    KEY idx_code (code),
    KEY idx_type (type),
    KEY idx_parent_code (parent_code),
    KEY idx_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='区域基础信息表'; 