-- 创建路口转向基础信息表
CREATE TABLE IF NOT EXISTS t_base_cross_turn_info (
    id CHAR(15) NOT NULL COMMENT '转向ID（路口ID_驶入方向_转向类型）',
    turn_type CHAR(1) NOT NULL COMMENT '转向类型：u掉头；l左转；s直行；r右转',
    in_dir INT(11) NOT NULL DEFAULT 0 COMMENT '驶入方向：1北；2东北；3东；4东南；5南；6西南；7西；8西北',
    out_dir INT(11) NOT NULL DEFAULT 0 COMMENT '驶出方向：1北；2东北；3东；4东南；5南；6西南；7西；8西北',
    cross_id CHAR(11) NOT NULL COMMENT '路口ID',
    gmt_create DATETIME NOT NULL COMMENT '创建时间',
    gmt_modified DATETIME NOT NULL COMMENT '修改时间',
    PRIMARY KEY (id),
    KEY idx_cross_id (cross_id),
    KEY idx_turn_type (turn_type),
    KEY idx_in_dir (in_dir),
    KEY idx_out_dir (out_dir)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='路口转向基础信息表'; 