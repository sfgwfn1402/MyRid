-- 路口方向基础信息表
CREATE TABLE IF NOT EXISTS `t_base_cross_dir_info` (
  `id` char(17) NOT NULL COMMENT '路口方向ID（路口ID_方向_进出口_主辅路序号）',
  `dir_type` int(11) NOT NULL COMMENT '路口方向类型：1北；2东北；3东；4东南；5南；6西南；7西；8西北',
  `in_out_type` int(10) NOT NULL COMMENT '进出口类型：1进口；2出口',
  `cross_id` char(11) NOT NULL COMMENT '路口ID',
  `length` double NOT NULL COMMENT '路段长度',
  `is_pedestrian` int(11) NOT NULL DEFAULT '0' COMMENT '是否有行人过街：0否；1是',
  `gmt_create` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `gmt_modified` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',
  PRIMARY KEY (`id`),
  KEY `idx_cross_id` (`cross_id`),
  KEY `idx_dir_type` (`dir_type`),
  KEY `idx_in_out_type` (`in_out_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='路口方向基础信息表'; 