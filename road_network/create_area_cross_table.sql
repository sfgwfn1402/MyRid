-- 创建区域路口关系表
CREATE TABLE IF NOT EXISTS t_base_area_cross (
    id INT(11) NOT NULL AUTO_INCREMENT COMMENT '主键',
    area_id INT(11) NOT NULL COMMENT '区域ID',
    cross_id CHAR(11) NOT NULL COMMENT '路口编号',
    gmt_create DATETIME NOT NULL COMMENT '创建时间',
    gmt_modified DATETIME NOT NULL COMMENT '修改时间',
    PRIMARY KEY (id),
    KEY idx_area_id (area_id),
    KEY idx_cross_id (cross_id),
    UNIQUE KEY uk_area_cross (area_id, cross_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='区域路口关系表'; 