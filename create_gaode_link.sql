-- 创建简化的高德LINK表
DROP TABLE IF EXISTS gaode_link;

CREATE TABLE gaode_link AS 
SELECT 
    fid as gid,
    u as start_node,
    v as end_node,
    highway as road_class,
    oneway,
    length,
    name as road_name,
    u as forwardroadid64,
    geom
FROM osm_segments 
WHERE name IS NOT NULL 
LIMIT 200;

-- 查看创建结果
SELECT count(*) as total_records FROM gaode_link;
SELECT * FROM gaode_link LIMIT 3; 