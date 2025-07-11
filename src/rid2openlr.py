import os,json,time,math

from qgis._core import QgsProject
from collections import OrderedDict
from ..lib.dbconn import cursor,db_conn_dict
from ..lib.common import parseConfig
from ..lib.openlr_r_w import Get_Info2Openlr, Points_Info

SRID = 4326

def initDb(conn, schema, tab_openlr_link, tab_openlr_node):
    sql_create = """drop table if exists {4}.{0};
       create table {4}.{0} (gid serial4 PRIMARY KEY, node_id int);
       select AddGeometryColumn('{4}', '{0}', '{3}', {2}, 'POINT', 2, True);

       drop table if exists {4}.{1};
       CREATE TABLE {4}.{1} (gid serial4 PRIMARY KEY, name_chn varchar(128),
       startnode INT, endnode INT, frc INT2 DEFAULT 5, fow INT2,line_id int8,
       forwardroadid64 varchar(30), road_class int, direction int2,
       form_way int2, s_angle decimal(6,3), e_angle decimal(6,3), len1 decimal(10, 2));
       select AddGeometryColumn('{4}', '{1}', '{3}', {2}, 'LINESTRING', 2, True);
       """.format(tab_openlr_node, tab_openlr_link, SRID, 'geom', schema)
    print(sql_create)
    cursor(conn, sql_create, commit=True)

def createIndex(conn, schema, tab_openlr_link, tab_openlr_node):

    sql_index = """
    create index if not exists idx_{3}_{0}_geom on {3}.{0} using gist({2});
    create index if not exists idx_{3}_{0}_line_id on {3}.{0} using btree(line_id);
    create index if not exists idx_{3}_{0}_startnode on {3}.{0} using btree(startnode);
    create index if not exists idx_{3}_{0}_endnode on {3}.{0} using btree(endnode);
    create index if not exists idx_{3}_{1}_geom on {3}.{1} using gist({2});
    create index if not exists idx_{3}_{1}_node_id on {3}.{1} using btree(node_id);
    """.format(tab_openlr_link, tab_openlr_node, 'geom', schema)
    print(sql_index)
    cursor(conn, sql_index, commit=True)

def createNode(conn, schema, tab_openlr_link, tab_openlr_node):
    sql_delete = "delete from {1}.{0};".format(tab_openlr_node, schema)
    cursor(conn, sql_delete, commit=True)

    sql_node = """insert into {2}.{0} (geom)
    select t1.geom from (
    select st_startpoint(geom) as geom from {2}.{1}
    union
    select st_endpoint(geom) as geom from {2}.{1}
    ) t1;""".format(tab_openlr_node, tab_openlr_link, schema)
    print(sql_node)
    cursor(conn, sql_node, commit=True)

    sql_update = 'update {1}.{0} set node_id = gid;'.format(tab_openlr_node, schema)
    cursor(conn, sql_update, commit=True)

def convertLine(conn, schema, tab_road, tab_openlr_link):
    # sql_delete = "delete from {};".format((tab_openlr_link))
    # cursor(conn, sql_delete, commit=True)

    # direction = 2
    sql_road = """insert into {7}.{1}(name_chn, fow, frc, geom, road_class,
    direction, form_way, forwardroadid64)
    select t1.name_chn,

    case
    when (t1.form_way=1 and t1.road_class=0) then 1
    when (t1.form_way=1 and t1.road_class!=0) then 2
    when (t1.form_way=15) then 3
    when (t1.form_way=4) then 4
    when (t1.form_way in (5,53,56,58)) then 5
    when (t1.form_way in (3,6,7,8,9,10,17)) then 6
    when (t1.form_way in (11,12,13,14,16)) then 7
    else 0
    end as fow,t1.road_class  frc, t1.geom, t1.road_class,1 AS direction, t1.form_way,t1.forwardroadid64
    from {7}.{0} t1
    ;""".format(tab_road, tab_openlr_link, "", "", "", "", SRID, schema)
    print(sql_road)
    cursor(conn, sql_road, commit=True)

    sql_update = """update {2}.{0} set line_id=gid,len1=st_length({1},True),
    s_angle = degrees(ST_azimuth(st_startpoint({1}), st_pointn({1}, 2))),
    e_angle = degrees(ST_azimuth(st_endpoint({1}),st_pointn({1}, ST_NumPoints({1})-1)));
    update {2}.{0} set frc=5 where frc is null;
    """.format(tab_openlr_link, 'geom', schema)
    print(sql_update)
    cursor(conn, sql_update, commit=True)

def updateftNode(conn, schema, tab_openlr_link, tab_openlr_node):
    # print('1', time.strftime('%H:%M:%S', time.localtime(time.time())))
    sql_update_fnode = """update {3}.{0} set startnode=t1.node_id from {3}.{1} t1
    where st_dwithin({0}.geom, t1.geom, {2}) and ST_LineLocatePoint({0}.geom, t1.geom) < {2};
    update {3}.{0} set endnode=t1.node_id from {3}.{1} t1
    where st_dwithin({0}.geom, t1.geom, {2}) and ST_LineLocatePoint({0}.geom, t1.geom) > 1-{2};
    """.format(tab_openlr_link, tab_openlr_node, 0.000001, schema)
    print(sql_update_fnode)
    cursor(conn, sql_update_fnode, commit=True)

def link2openlr(task):
    try:
        parDict = parseConfig()
        schema = parDict.get('schema')
        tab_link=parDict.get('tab_link')
        tab_nodes = parDict.get('tab_openlr_nodes')
        tab_lines = parDict.get('tab_openlr_lines')
        tab_rid = parDict.get('tab_rid')
        conn = parseConfig().get('conn')
        project = QgsProject.instance()
        initDb(conn,schema,tab_lines,tab_nodes)
        convertLine(conn,schema,tab_link,tab_lines)
        createNode(conn,schema,tab_lines,tab_nodes)
        createIndex(conn,schema,tab_lines,tab_nodes)
        updateftNode(conn,schema,tab_lines,tab_nodes)

    except Exception as e:
        print('Exception in rid to openlr ', e)
        conn.rollback()

def rid2openlr(task,single_rid):
    try:
        parDict = parseConfig()
        schema = parDict.get('schema')
        tab_rid = parDict.get('tab_rid')
        conn = parseConfig().get('conn')
        project = QgsProject.instance()

        # # convert single rid 2 openlr, input rid code
        dct_rid_openlrs=convertSingle(conn,schema,single_rid)
        saveOpenLr(conn,schema,single_rid,dct_rid_openlrs)

    except Exception as e:
        print('Exception in rid to openlr ', e)
        conn.rollback()

def saveOpenLr(conn,schema,rid:str, dct_rid_openlrs):
    sql_update_openlr="""
        update {3}.{0} set openlr_base64='{2}' where rid='{1}';
    """.format(parseConfig().get('tab_rid'),rid, dct_rid_openlrs[rid],  schema)
    print(sql_update_openlr)
    cursor(conn, sql_update_openlr)
    conn.commit()
    print('save openLr.....')

def convertSingle(conn,schema, rid: str) -> None:
    "convert single rid"
    sql_base_info = """select {6},
      st_x(st_startpoint({1})) as s_x, st_y(st_startpoint({1})) as s_y,
      case
        when ({2}='41000') then 0
        when ({2}='43000') then 1
        when ({2} in ('42000', '44000')) then 2
        when ({2}='51000') then 3
        when ({2} in ('45000', '52000')) then 4
        when ({2} in ('47000', '53000')) then 5
        else 6
        end as s_frc,
        case
        when ({3}='1' and {2}='41000') then 1
        when ({3}='1' and {2}!='41000') then 2
        when ({3}='15') then 3
        when ({3}='4') then 4
        when ({3} in ('5', '53','56','58')) then 5
        when ({3} in ('3','6','7','8','9','10','17')) then 6
        when ({3} in ('11','12','13','14','16')) then 7
        else 0
        end as s_fow,

        degrees(ST_azimuth( st_pointn({1}, 1), st_pointn({1}, 2))) as s_bear,
        st_length({1}, True) as dnp,
        st_x(st_endpoint({1})) as e_x, st_y(st_endpoint({1})) as e_y,

        case
        when ({4}='41000') then 0
        when ({4}='43000') then 1
        when ({4} in ('42000', '44000')) then 2
        when ({4}='51000') then 3
        when ({4} in ('45000', '52000')) then 4
        when ({4} in ('47000', '53000')) then 5
        else 6
        end as e_frc,
        case
        when ({5}='1' and {4}='41000') then 1
        when ({5}='1' and {4}!='41000') then 2
        when ({5}='15') then 3
        when ({5}='4') then 4
        when ({5} in ('5','53','56','58')) then 5
        when ({5} in ('3','6','7','8','9','10','17')) then 6
        when ({5} in ('11','12','13','14','16')) then 7
        else 0
        end as e_fow,

        degrees(ST_azimuth( st_pointn({1}, ST_NPOInTS({1})), st_pointn({1}, ST_NPOInTS({1})-1))) as e_bear
        from {10}.{0}
        where rid = '{7}'
        and st_length({1}, True) <= {9};
    """.format(parseConfig().get('tab_rid'), "geom", "roadclass", "from_way", "roadclass",
               "from_way", "rid", rid.strip(" "), "location_points", 15000, schema)
    print(sql_base_info)
    dct_rid_openlrs = _points_2_encode_info(conn,sql_base_info)
    print(dct_rid_openlrs)
    return dct_rid_openlrs



def _points_2_encode_info(conn, sql_base_info) -> None:
    "read rid and then write openlr"
    print(sql_base_info)
    rows_base_info = cursor(conn, sql_base_info, ret=True)

    dct_temp_rid_openlr = {}
    for row_base_info in rows_base_info:
        rid, s_x, s_y, s_rc, s_fow, s_bear, dnp, e_x, e_y, \
        e_rc, e_fow, e_bear = row_base_info
        s_bear = s_bear if s_bear != 0.0 else 0.01
        e_bear = e_bear if e_bear != 0.0 else 0.01

        start_point = Points_Info()
        start_point.properties["lon"] = s_x
        start_point.properties["lat"] = s_y
        start_point.properties["frc"] = s_rc
        start_point.properties["fow"] = s_fow
        start_point.properties["lfnp"] = s_rc + 3 if s_rc <= 4 else 7
        start_point.properties["bear"] = s_bear if s_bear != 0 else 0.01
        start_point.properties["dnp"] = dnp
        start_point.properties["seq"] = 1

        end_point = Points_Info()
        end_point.properties["lon"] = e_x
        end_point.properties["lat"] = e_y
        end_point.properties["frc"] = e_rc
        end_point.properties["fow"] = e_fow
        end_point.properties["lfnp"] = 7
        end_point.properties["bear"] = e_bear if e_bear != 0 else 0.01
        end_point.properties["dnp"] = 0
        end_point.properties["seq"] = 2

        dct_openlr_info = OrderedDict({"location_type": 1,
                                           "version": 3,
                                           "points": [start_point.properties, end_point.properties],
                                           "poff_bs": 0,
                                           "noff_bs": 0,
                                           "poff": 0,
                                           "noff": 0
                                           })
        #if is_out_info:
        print(dct_openlr_info)
        #is_out_info = 0

        obj_openlr = Get_Info2Openlr(dct_openlr_info)
        openlr_code = obj_openlr.openlr_info()
        print('openlr_code:',openlr_code)
        dct_temp_rid_openlr[rid] = openlr_code

    return dct_temp_rid_openlr

