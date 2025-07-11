import os,json,time,math

from PyQt5.QtGui import QColor
from qgis._core import QgsDataSourceUri, QgsVectorLayer, QgsApplication, QgsProject, QgsMarkerSymbol, QgsLineSymbol, \
    QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer, QgsRuleBasedRenderer, QgsSimpleLineSymbolLayer
from shapely import LineString, MultiLineString
from shapely.geometry import mapping,shape
from shapely.ops import linemerge
import numpy as np

from ..lib.dbconn import cursor
from ..lib.common import parseConfig
from ..lib.geohash import geo_encode

def roadInit(conn):

    return

def createCross(conn, interId,x_coord,y_coord,osmid,highway):
    parDict = parseConfig()
    schema = parDict.get('schema')
    tab_segment = parDict.get('tab_segment')
    tab_cross = parDict.get('tab_cross')
    adcode=parDict.get("ad_code")
    # calate cross infos
    current_time = time.strftime("%Y%m%d%H%M", time.localtime())
    data_version=time.strftime("%Y%m%d", time.localtime())
    #inter_name 获取当前路口内所有的RID数据。根据高等级RID数据进行排序按西北东南方向进行命名
    inter_nameLst = []
    interleveltypeLst = []

    is_signlight = 1
    crss_road_sql="""
                SELECT DISTINCT(regexp_split_to_table(name,E'\[[\\'\\\s?\\',\\\]]+','')),road_class from {2}.{0} where fnode={1} or tnode={1} order by road_class asc
    """.format(tab_segment,osmid,schema)

    roads = cursor(conn, crss_road_sql, ret=True)
    print(str(osmid) + "关联路段数量：" + str(len(roads)))
    for road in roads:
        if road[0]!='':
            inter_nameLst.append(road[0])
            interleveltypeLst.append(str(road[1]))
        if len(inter_nameLst) == 2:
            break
    if len(inter_nameLst) <2:
        inter_nameLst.append("无名道路")
        is_signlight = 0
    inter_name = '与'.join(inter_nameLst) + '交叉口'
    #intertype 十字形路口
    #定义：两条相互垂直道路的平面交叉口
    #规则：计算时可取角度75-105
    #路口：交叉口中心点
    #T形路口
    #注：无信号灯，且T型路口只是简单出入口时（进入路段与主路另一方向完全隔离），不算为路口。
    #其他都认定为路口。
    #环形交叉口
    #整个环形路口，认定为一个路口点，路口坐标为环形中心点坐标。
    #错位T形路口
    #50米以后的错位T型，需要合并为一个路口。路口坐标点取中点。
    #斜交路口（X型路口）
    #规则：计算时两条路交叉出现75角以下时，可认定为X型路口
    intertype=1

    #is_entity 1 标准路口 有正反相数据的相交路口
    #3 行人过街路口 高精反馈信息
    #4 掉头路口 计算有掉头线数据。线数据里fromway = 2 and uline = 2
    #5 虚拟路口 高精反馈信息
    #6 末端路口（真）如果真是末端的路口数据确实很少
    #8 末端路口（假）填写
    #99 岔口 计算-不用计算(岔口数据中只要RID对应数据的起点或终点)
    is_entity=1

    #if highway=='traffic_signals':
    #    is_signlight=1
    #interleveltype 路口等级类型，41000 高速公路  高
    #43000 城市快速路  快
    #44000 城市主干道  主路
    #45000 城市次干道  次
    #42000 国道  国
    #51000 省道  省
    #52000 县道  县
    #53000 乡道  乡
    #47000 城市普通道路  支
    #54000 县乡村内部道路 其它
    #49 小路  其它参见路口等级类型字典
    # 排列组合新的数据字典(将路口数据所有的道路数据（有主路与辅路的时候要去除辅路）按名称进行去重，取最两个高等级的道路数据进行命名)
    interleveltype=interleveltypeLst[0]
    #flowtowardtype 路口流量类型，1 交叉口（多进多出）一般多于3叉
    #2 合流路口 两个RID数据进到一个RID中
    #3 分流路口 一个RID数据分开成两个RID数据
    #4  悬挂 只有一个RID数据，不是起点即是终点
    #5 一进一出 在两个路段上的路口数据。
    #99 其它（参见路口流向类型字典）
    flowtowardtype=99
    #crossarea 有高精取路口面的面积，无为空
    #markcross 有完整的路口形态，有停止线、斑马线等，0 否 1 是  99 其它
    markcross=99
    #is_cross 路口数据的类型：cross ,fork
    is_cross='cross'

    create_sql = """
        INSERT INTO {28}.{0} ("inter_id", "inter_name", "intertype", "is_entity", "is_signlight", "interleveltype", "geom",
         "flowtowardtype", "data_source", "great_date", "modify_date", "author", "data_vesion", "pre_data_version",
         "data_mode", "relation", "change", "geom_change", "crossarea", "markcross", "adcode", "allotropiccross", "openlr_base64", "p_modify","is_cross","is_hd" )
        VALUES
        ('{1}','{2}','{3}','{4}', {5}, '{6}', st_geomfromtext('POINT({7} {8})',4326), '{9}','{10}',{11},'{12}','{13}','{14}','{15}','{16}','{17}','{18}','{19}','{20}','{21}','{22}',{23},'{24}',{25},'{26}',{27})
         ON CONFLICT ("inter_id") DO NOTHING;
       """.format(tab_cross,interId,inter_name,intertype,is_entity,is_signlight,intertype,x_coord,y_coord,flowtowardtype,"06",current_time,current_time,"py",data_version,"","2","","","","",markcross,adcode,"1","","0",is_cross,"0", schema)
    #print(create_sql)
    try:
        cursor(conn, create_sql)
        conn.commit()
    except Exception as e:
        print('Exception in createCross', e)

def createRid(conn, road,start_cross,end_cross):
    parDict = parseConfig()
    schema = parDict.get('schema')
    tab_segment = parDict.get('tab_segment')
    tab_rid = parDict.get('tab_rid')
    tab_cross = parDict.get('tab_cross')
    tab_lane = parDict.get('tab_lane')
    tab_axf = parDict.get('tab_axf')
    adcode=parDict.get("ad_code")

    current_time = time.strftime("%Y%m%d%H%M", time.localtime())
    data_version = time.strftime("%Y%m%d", time.localtime())
    #rid 起点路口id+终点路口id+顺序号（起终点路口间存在多个路段时，通过一位标示位进行标识，取值0~9，A~U）。固定长度23位。
    max_id=0
    rid_exist_sql = """
                  SELECT MAX(RIGHT("rid",1)) FROM {3}.{0} WHERE rid LIKE '{1}{2}_'
            """.format(tab_rid, start_cross,end_cross, schema)

    #print(rid_exist_sql)
    rids = cursor(conn, rid_exist_sql, ret=True)
    #print( "路段最大序号：" + str(rids[0][0]))
    if rids[0][0] is not None:
        max_id=int(rids[0][0])+1
        #print('max new id： '+str(max_id))
    rid=start_cross+end_cross+str(max_id)
    print('RID:'+rid)
    #name 当前道路名称：起点路口相交道路-终点路口相交道路，相交道路以左右直的顺序进行排序
    if  "[" in road[12] or "]" in road[12]:
        road[12]='无名道路'
    rid_nameLst = []
    start_road_sql = """
                    SELECT DISTINCT(regexp_split_to_table(name,E'\[[\\'\\\s?\\',\\\]]+','')),road_class from {2}.{0} where (fnode={1} or tnode={1})  order by road_class asc
        """.format(tab_segment, road[6], schema)
    # print(start_road_sql)
    start_roads = cursor(conn, start_road_sql, ret=True)
    if len(start_roads)>1:
        for sr in start_roads:
            if sr[0]!='' and sr[0]!=road[12] and len(rid_nameLst)==0:
                rid_nameLst.append(sr[0])
    if len(rid_nameLst)==0:
        rid_nameLst.append("无名道路")
    end_road_sql = """
                   SELECT DISTINCT(regexp_split_to_table(name,E'\[[\\'\\\s?\\',\\\]]+','')),road_class from {2}.{0} where (fnode={1} or tnode={1})  order by road_class asc
            """.format(tab_segment, road[7], schema)
    end_roads = cursor(conn, end_road_sql, ret=True)
    if len(end_roads)>1:
        for er in end_roads:
            if er[0]!='' and er[0]!=road[12] and len(rid_nameLst)==1:
                rid_nameLst.append(er[0])
    if len(rid_nameLst) == 1:
        rid_nameLst.append("无名道路")

    name = road[12]+":"+'@'.join(rid_nameLst) + '路段'
    #roadclass 取当前RID数据中最长一段数据选择roadclass字段属性填写
    roadclass=road[13]
    #length当前RID数据的实际长度取决于RID数据自身几何长度。
    length=shape(json.loads(road[9])).length* 1852 * 60
    #startangle 相对于入口的绝对角度
    startangle=getAngle(road[2],road[3],road[4],road[5])
    #endangle相对于出口的绝对角度
    endangle=getAngle(road[4],road[5],road[2],road[3])
    #startangle_p相对于入口的绝对角度
    startangle_p=getAngle(road[2],road[3],road[4],road[5])
    #endangle_p相对于出口的绝对角度
    endangle_p=getAngle(road[4],road[5],road[2],road[3])
    #trend 路段走向:1 南向北2 西向东3 北向南4 东向西5 内环6 外环99 其他（参见路段走向字典）
    trend=road[8]
    #isoneway 是否单行线：0 否  1 是  99 其他
    isoneway = 0
    if road[15]=='True':
        isoneway=1
    #roadsegtype 1路段 3匝道 4隧道 5桥梁6高架 99其他
    roadsegtype=1
    if road[16]=='yes':
        roadsegtype = 5
    if road[18]=='yes':
        roadsegtype = 4
    #mainflag 1主路 2辅路 99其他
    mainflag=1

    maxspeed='NULL'
    if road[19]!='':
        maxspeed= str(road[19])

    create_sql = """
                INSERT INTO {41}.{0} ("rid", "name", "roadclass", "width", "startcrossid", "endcrossid", "startangle", "endangle",
                             "startlocation", "endlocation", "adminlevel", "techlevel", "geom", "loadcapacity", "trend", "curvature", "slope",
                             "minspeed", "maxspeed", "isoneway", "roadsegtype", "designflow", "mainflag", "data_source", "great_date",
                             "modify_date", "author", "data_vesion", "pre_data_version", "data_mode", "relation", "change", "geom_change",
                             "adcode", "length", "startangle_p" ,"endangle_p", "openlr_base64","p_modify","is_hd")
        VALUES ('{1}','{2}','{3}',{4},'{5}','{6}',{7},{8},'{9}','{10}','{11}','{12}', ST_SetSRID(st_geomfromgeojson('{13}'),4326), {14}, '{15}', {16}, {17}, {18}, {19}, '{20}', '{21}', '{22}', '{23}', '{24}', '{25}', '{26}', '{27}','{28}','{29}','{30}','{31}','{32}','{33}','{34}',{35},'{36}','{37}','{38}','{39}',{40})
        ON CONFLICT ("rid") DO NOTHING;
               """.format(tab_rid,rid,name,roadclass,"0",start_cross,end_cross,startangle,endangle,"","","","",road[9],"NULL",trend,"NULL","NULL","NULL",maxspeed,isoneway,roadsegtype,"",mainflag,"06",current_time,current_time,"py",data_version,"","2","","","",adcode,length,startangle_p,endangle_p,"","0","0", schema)
    # print(create_sql)
    try:
        cursor(conn, create_sql)
        conn.commit()
    except Exception as e:
        print('Exception in createRid', e)

    #创建路段所归属车道
    for sectionid in ['900','200','100']:
        i=0
        while(i<int(road[20])):
            turntype='2'
            lanecatagory=1
            if roadclass!='41000' and sectionid=='900':
                if i==0:
                    turntype = '1,2'
                if i==int(road[20])-1:
                    turntype='3'
            if roadclass!='41000' and sectionid=='900' and int(road[20])==1:
                turntype='1,4,2,3'
            if sectionid == '900':
                lanecatagory = 2
            elif sectionid == '100':
                lanecatagory = 3
            createLane(conn,rid,sectionid,str(i+11),turntype,lanecatagory)
            i = i + 1

def createLane(conn, rid,sectionid,lane_no,turntype,lanecatagory):
    parDict = parseConfig()
    schema = parDict.get('schema')
    tab_nodes = parDict.get('tab_nodes')
    tab_segment = parDict.get('tab_segment')
    tab_lane = parDict.get('tab_lane')
    adcode = parDict.get("ad_code")

    current_time = time.strftime("%Y%m%d%H%M", time.localtime())
    data_version = time.strftime("%Y%m%d", time.localtime())
    # sectionid 以当前数据的渠化代码，进口900，出口100，中间车道200

    # laneid 编码长度固定28个字符串。路段+渠化顺序号+车道顺序号
    # （1）路段RID：当前车道所属路段RID，为长度23位字符串；
    # （2）渠化面序号：当前车道所属渠化面序号，长度3位字符串100；
    # （3）车道序号：当前车道序号，长度2位字符串。
    laneid=rid+sectionid+lane_no
    sectionid=rid+sectionid
    #lane_no 从最左侧车道开始编号“11,12……”
    #mainflag 1	主路车道2	辅路车道6	匝道0	未知99	其他
    mainflag=1
    #lanefunction 1	常规车道2	非机动车3	机非混合0	未知99	其他
    lanefunction=1
    #lanespecifictype 4	公交专用车道5	公交港湾车道6	BRT车道7	多乘员专用车道8	潮汐车道9	可变车道10	应急车道11	应急停车车道12	避险车道13	ETC车道14	小型车专用车道15	大型车专用车道0	未知99	其他
    lanespecifictype=99
    #Lanelocation 1	独立左转2	独立右转3	提前掉头4	混合右转99	其他0	未知
    lanelocation=0

    create_sql = """
                INSERT INTO {29}.{0} ("laneid", "rid", "sectionid", "lane_no", "length", "width",
                              "turntype", "waitinglaneid",
                              "lanecatagory",  "lanefunction",
                              "category_no", "lanespecifictype", "adcode",
                              "data_source", "great_date", "modify_date",
                              "author", "data_vesion", "pre_data_version",
                              "data_mode", "relation", "change",
                              "geom_change", "mainflag", "lanelocation", "openlr_base64","p_modify","is_hd")
                VALUES ('{1}','{2}','{3}',{4}, {5},{6},'{7}','{8}','{9}',{10},{11},'{12}','{13}','{14}','{15}','{16}','{17}','{18}','{19}','{20}','{21}','{22}',{23},{24},{25},'{26}',{27},{28})
                ON CONFLICT ("laneid") DO NOTHING;
               """.format(tab_lane,laneid,rid,sectionid,lane_no,"NULL","NULL",turntype,"",lanecatagory,lanefunction,"NULL",lanespecifictype,adcode,"06",current_time,current_time,"py",data_version,"","2","","","NULL",mainflag,lanelocation,"","0","0", schema)
    # print(create_sql)
    try:
        cursor(conn, create_sql)
        conn.commit()
    except Exception as e:
        print('Exception in createLane', e)

def createAxf(conn, segmentId):
    parDict = parseConfig()
    schema = parDict.get('schema')
    tab_nodes = parDict.get('tab_nodes')
    tab_segment = parDict.get('tab_segment')
    tab_axf = parDict.get('tab_axf')

    create_sql = """
                INSERT INTO {0}.{1} (rid, forwardroa, seq_no, dir, adcode, geom)
                VALUES ({1},{2},{2},{2}, st_geomfromtext(#{geom,jdbcType=VARCHAR},4326), {2},{2},{2},{2})
               """.format("", schema)
    print(create_sql)
    try:
        cursor(conn, create_sql)
        conn.commit()
    except Exception as e:
        print('Exception in createAxf', e)

def road2rid_signal(task, road_name):
    try:
        parDict = parseConfig()
        schema = parDict.get('schema')
        tab_nodes = parDict.get('tab_nodes')
        tab_segment = parDict.get('tab_segment')
        tab_rid = parDict.get('tab_rid')

        conn = parseConfig().get('conn')
        project = QgsProject.instance()
        # 获取所有的路段名称列表
        roadnames_sql = """
        select distinct(name) from {2}.{0} where name not like \'[%\' and name <>'' and name IN ('{1}')
        """.format(tab_segment,road_name, schema)
        rows_segment = cursor(conn, roadnames_sql, ret=True)
        print('获取道路数量：' + str(len(rows_segment)))

        if len(rows_segment) > 0:
            rid_delete_sql="""
            delete from {2}.{0} where starts_with(name,'{1}')
            """.format(tab_rid,road_name, schema)
            try:
                cursor(conn, rid_delete_sql)
                conn.commit()
            except Exception as e:
                print('Exception in rid delete', e)
            iterations = 0
            for name in rows_segment:
                road_sql = """
                select m.cross,n.cross,m.x_coord,m.y_coord,n.x_coord,n.y_coord,s.fnode,s.tnode,s.direction,st_asgeojson(s.geom),s.highway,s.highway,s.name,s.road_class,s.length,s.oneway,s.bridge,s.ref,s.tunnel,s.maxspeed,s.lanes  from {3}.{0} s 
                      left join {3}.{1} m on m.osmid=s.fnode
                      left join {3}.{1} n on n.osmid=s.tnode
                      where ( '{2}' in (select regexp_split_to_table(s.name,E'\[[\\'\\\s?\\',\\\]]+','')) and s.highway not like '%_link') and s.fnode<>s.tnode order by m.cross desc ,case
                               when road_class='43000' then 1
                               when road_class='44000' then 2
                               when road_class='45000' then 3
                               when road_class='47000' then 4
                               when road_class='41000' then 1
                               when road_class='42000' then 2
                               when road_class='51000' then 2
                               when road_class='52000' then 3
                               when road_class='53000' then 4
                               when road_class='54000' then 5
                               when road_class='49000' then 5
                               end;
                """.format(tab_segment, tab_nodes, name[0], schema)
                lst_road = cursor(conn, road_sql, ret=True)
                print(name[0] + "包含路段数量：" + str(len(lst_road)))
                for road in lst_road:
                    iterations += 1
                    task.setProgress(100*(iterations/len(lst_road)))
                    #print(road)
                    start_cross_id = ''
                    end_cross_id = ''
                    print('process road:' + str(road[6]) + "," + str(road[7]))
                    if road[0] == 1:
                        # if fcross=1 then process generate startcrossid and save rid_cross and mark osm_nodes
                        start_cross_id = geo_encode(road[2], road[3])
                        print('startCrossId:' + start_cross_id)
                        createCross(conn,start_cross_id,road[2],road[3],road[6],road[10])
                        if road[1] == 1:
                            # if tcross=1 then process generate endcrossid and save rid_cross and mark osm_nodes
                            end_cross_id = geo_encode(road[4], road[5])
                            print('endCrossId:' + end_cross_id)
                            createCross(conn, end_cross_id,road[4],road[5],road[7],road[11])
                            #lst_road.remove(road)
                            createRid(conn,road,start_cross_id,end_cross_id)
                            #createAxf(conn,"")
                        # else find tcross=fcross and direction equals  merge segement recursion;
                        else:
                            #lst_road.remove(road)
                            end_cross_id,road=generateRid(conn,road, lst_road)
                            print('end_cross_id returnd:'+end_cross_id)
                            #  save rid_rid and mark osm_segment
                            createRid(conn, road,start_cross_id,end_cross_id)
                            #  generate rid_axf_three
                            #createAxf(conn, "")
        dbinfo = parseConfig().get('db_info')
        if not QgsProject.instance().mapLayersByName(parseConfig().get('tab_rid')):
            nodes_uri = QgsDataSourceUri()
         # 设置主机，端口，数据库名称，用户名和密码
            nodes_uri.setConnection(dbinfo['host'], str(dbinfo['port']), dbinfo['dbname'], dbinfo['user'], dbinfo['pw'])
         # 设置数据库架构，表名，几何列和可选项（WHERE 语句）
            nodes_uri.setDataSource(parseConfig().get('schema'), parseConfig().get('tab_rid'), "geom", "", "gid")
            vlayer = QgsVectorLayer(nodes_uri.uri(False), parseConfig().get('tab_rid'), "postgres")
            #symbol = QgsLineSymbol.createSimple({ 'color': 'red'})
            #simpleMarkerSymbolLayer = QgsSimpleMarkerSymbolLayer()
            #simpleMarkerSymbolLayer.setColor(QColor('#ff0000'))
            #simpleMarkerSymbolLayer.setShape(QgsSimpleMarkerSymbolLayer.ArrowHead)
            #markerSymbol = QgsMarkerSymbol([simpleMarkerSymbolLayer])
            #markerSymbol.setAngle(90.0) # Commented as we already set dynamically angle from an expression
            markerSymbol = QgsMarkerSymbol.createSimple({'name':'arrowhead','color':'red'})
            markerLineSymbolLayer = QgsMarkerLineSymbolLayer()
            markerLineSymbolLayer.setColor(QColor('#ff0000'))
            markerLineSymbolLayer.setSubSymbol(markerSymbol)

            simpleLineSymbolLayer=QgsSimpleLineSymbolLayer()
            simpleLineSymbolLayer.setColor(QColor('#ff0000'))
            lineSymbol=QgsLineSymbol([markerLineSymbolLayer,simpleLineSymbolLayer])
            lineSymbol.setColor(QColor('#ff0000'))
            vlayer.renderer().setSymbol(lineSymbol)
            newRenderer = QgsRuleBasedRenderer.convertFromRenderer(vlayer.renderer())
            vlayer.setRenderer(newRenderer)


            # props = []
            # props['align_dash_pattern'] = '0'
        # props['capstyle'] = 'round'
        # props['customdash'] = '5;2'
        # props['customdash_map_unit_scale'] = '3x:0,0,0,0,0,0'
        # props['customdash_unit'] = 'MM'
        # props['dash_pattern_offset'] = '0'
        # props['dash_pattern_offset_map_unit_scale'] = '3x:0,0,0,0,0,0'
        # props['dash_pattern_offset_unit'] = 'MM'
        # props['draw_inside_polygon'] = '0'
        # props['joinstyle'] = 'round'
        # props['line_color'] = '227,26,28, 255'
        # props['line_style'] = 'solid'
        # props['line_width'] = '0.4'
        # props['line_width_unit'] = 'MM'
        # props['offset'] = '0'
        # props['offset_map_unit_scale'] = '3x:0,0,0,0,0,0'
        # props['offset_unit'] = 'MM'
        # props['ring_filter'] = '0'
        # props['trim_distance_end'] = '0'
        # props['trim_distance_end_map_unit_scale'] = '3x:0,0,0,0,0,0'
        # props['trim_distance_end_unit'] = 'MM'
        # props['trim_distance_start'] = '0'
        # props['trim_distance_start_map_unit_scale'] = '3x:0,0,0,0,0,0'
        # props['trim_distance_start_unit'] = 'MM'
        # props['tweak_dash_pattern_on_corners'] = '0'
        # props['use_custom_dash'] = '0'
        # props['width_map_unit_scale'] = '3x:0,0,0,0,0,0'
        # vlayer.renderer().setSymbol(QgsLineSymbol.createSimple(props))

        # props2=[]
        # props2['average_angle_length'] = '4'
        # props2['average_angle_map_unit_scale'] = '3x:0,0,0,0,0,0'
        # props2['average_angle_unit'] = 'MM'
        # props2['interval'] = '3'
        # props2['interval_map_unit_scale'] = '3x:0,0,0,0,0,0'
        # props2['interval_unit'] = 'MM'
        # props2['offset'] = '0'
        # props2['offset_along_line'] = '0'
        # props2['offset_along_line_map_unit_scale'] = '3x:0,0,0,0,0,0'
        # props2['offset_along_line_unit'] = 'MM'
        # props2['place_on_every_part'] = True
        # props2['placements'] = 'Interval'
        # props2['ring_filter'] = '0'
        # props2['rotate'] = '1'
        #
        # vlayer.renderer().symbol().appendSymbolLayer(QgsMarkerSymbol.createSimple(props2))
        # 显示更改v
            vlayer.triggerRepaint()
            project.addMapLayer(vlayer)
        if not QgsProject.instance().mapLayersByName(parseConfig().get('tab_cross')):
            segment_uri = QgsDataSourceUri()
            # 设置主机，端口，数据库名称，用户名和密码
            segment_uri.setConnection(dbinfo['host'], str(dbinfo['port']), dbinfo['dbname'], dbinfo['user'],
                                  dbinfo['pw'])
            # 设置数据库架构，表名，几何列和可选项（WHERE 语句）
            segment_uri.setDataSource(parseConfig().get('schema'), parseConfig().get('tab_cross'), "geom", "", "gid")
            slayer=QgsVectorLayer(segment_uri.uri(False), parseConfig().get('tab_cross'), "postgres")
            symbol = QgsMarkerSymbol.createSimple({'name': 'diamond', 'color': 'red','size':'3.6'})
            slayer.renderer().setSymbol(symbol)
            # 显示更改
            slayer.triggerRepaint()
            project.addMapLayer(slayer)

    except Exception as e:
        print('Exception in rid generate', e)
        conn.rollback()
    return {'total': len(lst_road), 'iterations': iterations,
            'task': 'rid generate'}

def road2rid(task):
    try:
        parDict = parseConfig()
        schema = parDict.get('schema')
        tab_nodes = parDict.get('tab_nodes')
        tab_segment = parDict.get('tab_segment')
        tab_rid = parDict.get('tab_rid')
        conn = parseConfig().get('conn')
        project = QgsProject.instance()
        iterations=0
        # 获取所有的路段名称列表and name IN ('旅游路','回龙山路','霞景路','洪山路','转山西路','福地街','福佑街')
        roadnames_sql = """
        select distinct(name) from {1}.{0} where name not like \'[%\' and name <>'' 
        """.format(tab_segment, schema)
        rows_segment = cursor(conn, roadnames_sql, ret=True)
        print('获取道路数量：' + str(len(rows_segment)))
        if len(rows_segment) > 0:
            for name in rows_segment:
                iterations += 1
                task.setProgress(100 * (iterations / len(rows_segment)))
                road_sql = """
                select m.cross,n.cross,m.x_coord,m.y_coord,n.x_coord,n.y_coord,s.fnode,s.tnode,s.direction,st_asgeojson(s.geom),s.highway,s.highway,s.name,s.road_class,s.length,s.oneway,s.bridge,s.ref,s.tunnel,s.maxspeed,s.lanes  from {3}.{0} s 
                      left join {3}.{1} m on m.osmid=s.fnode
                      left join {3}.{1} n on n.osmid=s.tnode
                      where ( '{2}' in (select regexp_split_to_table(s.name,E'\[[\\'\\\s?\\',\\\]]+','')) and s.highway not like '%_link') and s.fnode<>s.tnode order by m.cross desc ,case
                               when road_class='43000' then 1
                               when road_class='44000' then 2
                               when road_class='45000' then 3
                               when road_class='47000' then 4
                               when road_class='41000' then 1
                               when road_class='42000' then 2
                               when road_class='51000' then 2
                               when road_class='52000' then 3
                               when road_class='53000' then 4
                               when road_class='54000' then 5
                               when road_class='49000' then 5
                               end;
                """.format(tab_segment, tab_nodes, name[0], schema)
                lst_road = cursor(conn, road_sql, ret=True)
                print(name[0] + "包含路段数量：" + str(len(lst_road)))
                for road in lst_road:
                    #print(road)
                    start_cross_id = ''
                    end_cross_id = ''
                    print('process road:' + str(road[6]) + "," + str(road[7]))
                    if road[0] == 1:
                        # if fcross=1 then process generate startcrossid and save rid_cross and mark osm_nodes
                        start_cross_id = geo_encode(road[2], road[3])
                        print('startCrossId:' + start_cross_id)
                        createCross(conn,start_cross_id,road[2],road[3],road[6],road[10])
                        if road[1] == 1:
                            # if tcross=1 then process generate endcrossid and save rid_cross and mark osm_nodes
                            end_cross_id = geo_encode(road[4], road[5])
                            print('endCrossId:' + end_cross_id)
                            createCross(conn, end_cross_id,road[4],road[5],road[7],road[11])
                            #lst_road.remove(road)
                            createRid(conn,road,start_cross_id,end_cross_id)
                            #createAxf(conn,"")
                        # else find tcross=fcross and direction equals  merge segement recursion;
                        else:
                            #lst_road.remove(road)
                            end_cross_id,road=generateRid(conn,road, lst_road)
                            print('end_cross_id returnd:'+end_cross_id)
                            #  save rid_rid and mark osm_segment
                            createRid(conn, road,start_cross_id,end_cross_id)
                            #  generate rid_axf_three
                            #createAxf(conn, "")
        dbinfo = parseConfig().get('db_info')
        if not QgsProject.instance().mapLayersByName( parseConfig().get('tab_rid')):
            nodes_uri = QgsDataSourceUri()
             # 设置主机，端口，数据库名称，用户名和密码
            nodes_uri.setConnection(dbinfo['host'], str(dbinfo['port']), dbinfo['dbname'], dbinfo['user'], dbinfo['pw'])
             # 设置数据库架构，表名，几何列和可选项（WHERE 语句）
            nodes_uri.setDataSource(parseConfig().get('schema'), parseConfig().get('tab_rid'), "geom", "", "gid")
            vlayer=QgsVectorLayer(nodes_uri.uri(False), parseConfig().get('tab_rid'), "postgres")

            markerSymbol = QgsMarkerSymbol.createSimple({'name': 'arrowhead', 'color': 'red'})
            markerLineSymbolLayer = QgsMarkerLineSymbolLayer()
            markerLineSymbolLayer.setColor(QColor('#ff0000'))
            markerLineSymbolLayer.setSubSymbol(markerSymbol)

            simpleLineSymbolLayer = QgsSimpleLineSymbolLayer()
            simpleLineSymbolLayer.setColor(QColor('#ff0000'))
            lineSymbol = QgsLineSymbol([markerLineSymbolLayer, simpleLineSymbolLayer])
            lineSymbol.setColor(QColor('#ff0000'))
            vlayer.renderer().setSymbol(lineSymbol)
            newRenderer = QgsRuleBasedRenderer.convertFromRenderer(vlayer.renderer())
            vlayer.setRenderer(newRenderer)
            project.addMapLayer(vlayer )
        if not QgsProject.instance().mapLayersByName( parseConfig().get('tab_cross')):
            segment_uri = QgsDataSourceUri()
            # 设置主机，端口，数据库名称，用户名和密码
            segment_uri.setConnection(dbinfo['host'], str(dbinfo['port']), dbinfo['dbname'], dbinfo['user'],
                                      dbinfo['pw'])
            # 设置数据库架构，表名，几何列和可选项（WHERE 语句）
            segment_uri.setDataSource(parseConfig().get('schema'), parseConfig().get('tab_cross'), "geom", "", "gid")

            slayer = QgsVectorLayer(segment_uri.uri(False), parseConfig().get('tab_cross'), "postgres")
            symbol = QgsMarkerSymbol.createSimple({'name': 'diamond', 'color': 'red', 'size': '3.6'})
            slayer.renderer().setSymbol(symbol)
            # 显示更改
            slayer.triggerRepaint()
            project.addMapLayer(slayer)

    except Exception as e:
        print('Exception in rid generate', e)
        conn.rollback()

# find tcross==fcross and direction equals  merge segement recursion
def generateRid(conn, first_road, lst_road):
    print('first_road:' + str(first_road[6]) + "," + str(first_road[7]))
    #and x[8] == first_road[8]
    next_roads = list(filter(lambda x: (x[6] == first_road[7] and x[7]!=first_road[6] and x[10] == first_road[10]), lst_road))
    #if len(next_roads) > 1:
    #    next_roads = list(filter(lambda x: (x[10] == first_road[10] ), next_roads))
    #next_roads=[x for x in lst_road if x[6] == first_road[7] and x[7]!=first_road[6]]
    #print(next_roads)
    print('segement recursion:' + str(len(next_roads)))
    if len(next_roads) == 0:
        # return segment
        #print(first_road)
        end_cross_id = geo_encode(first_road[4], first_road[5])
        print('endCrossId:' + end_cross_id)
        return end_cross_id,first_road
    else:
        next_road = next_roads[0]
        #print(next_road)
        #lst_road.remove(first_road)
        #lst_road.remove(next_road)
        # return segment
        # reset field value
        first_road[4] = next_road[4]
        first_road[5] = next_road[5]
        first_road[7] = next_road[7]
        #print(first_road)
        #print(next_road)
        new_line=linemerge([shape(json.loads(first_road[9])), shape(json.loads(next_road[9]))])
        #print(new_line)
        if type(new_line) is MultiLineString:
            outcoords = [list(i.coords) for i in np.array(new_line.geoms)]
            #print(outcoords)
            new_line = LineString([i for sublist in outcoords for i in sublist])
        first_road[9] = json.dumps(mapping(new_line))
        #print(first_road)
        if next_road[1] == 1:
            # if tcross=1 then process generate endcrossid and save rid_cross and makrk osm_nodes
            end_cross_id = geo_encode(next_road[4], next_road[5])
            print('endCrossId:' + end_cross_id)
            createCross(conn, end_cross_id, next_road[4], next_road[5], next_road[7], next_road[11])
            return end_cross_id,first_road
        # else find tcross=fcross and direction equals  merge segement recursion;
        else:
            return generateRid(conn, first_road, lst_road)

def roadInit(conn,schema,tab_cross,tab_rid,tab_lane,tab_axf):
    create_cross_table = """
                    DROP SEQUENCE IF EXISTS {0}_gid_seq CASCADE;
                    CREATE SEQUENCE {0}_gid_seq increment by 1 minvalue 1 start with 1;
                    DROP TABLE IF EXISTS "{1}"."{0}";
                    CREATE TABLE "{1}"."{0}" (
                      "inter_id" varchar(11) COLLATE "pg_catalog"."default" NOT NULL,
                      "inter_name" varchar(200) COLLATE "pg_catalog"."default",
                      "intertype" varchar(10) COLLATE "pg_catalog"."default",
                      "is_entity" varchar(6) COLLATE "pg_catalog"."default",
                      "is_signlight" int2,
                      "interleveltype" varchar(6) COLLATE "pg_catalog"."default",
                      "geom" "public"."geometry",
                      "flowtowardtype" text COLLATE "pg_catalog"."default",
                      "adcode" varchar(6) COLLATE "pg_catalog"."default",
                      "allotropiccross" int2,
                      "data_source" varchar(10) COLLATE "pg_catalog"."default",
                      "great_date" varchar(12) COLLATE "pg_catalog"."default",
                      "modify_date" varchar(12) COLLATE "pg_catalog"."default",
                      "author" varchar(50) COLLATE "pg_catalog"."default",
                      "data_vesion" varchar(17) COLLATE "pg_catalog"."default",
                      "pre_data_version" varchar(17) COLLATE "pg_catalog"."default",
                      "data_mode" varchar(6) COLLATE "pg_catalog"."default",
                      "relation" varchar(500) COLLATE "pg_catalog"."default",
                      "change" varchar(6) COLLATE "pg_catalog"."default",
                      "geom_change" varchar(6) COLLATE "pg_catalog"."default",
                      "crossarea" varchar(20) COLLATE "pg_catalog"."default",
                      "markcross" varchar(10) COLLATE "pg_catalog"."default",
                      "openlr_base64" varchar(150) COLLATE "pg_catalog"."default",
                      "is_hd" int2,
                      "p_modify" int2,
                      "newnodetype" varchar(255) COLLATE "pg_catalog"."default",
                      "realcross" int2,
                      "light_source" int2,
                      "is_cross" varchar(6) COLLATE "pg_catalog"."default",
                      "gid" int4 NOT NULL DEFAULT nextval('rid_cross_gid_seq'::regclass),
                      "geomarea" "public"."geometry",
                      "polygon_geom" "public"."geometry");
                      ALTER TABLE "{1}"."{0}" ADD CONSTRAINT "{0}_unique" UNIQUE ("inter_id");
                      ALTER TABLE "{1}"."{0}" ADD CONSTRAINT "{0}_pkey" PRIMARY KEY ("gid");
                   """.format(tab_cross, schema)
    #print(create_cross_table)
    try:
        cursor(conn, create_cross_table)
        conn.commit()
    except Exception as e:
        print('Exception in create cross', e)
        conn.rollback()

    create_rid_table = """
                    DROP SEQUENCE IF EXISTS {0}_gid_seq CASCADE;
                    CREATE SEQUENCE {0}_gid_seq increment by 1 minvalue 1 start with 1;
                    DROP TABLE IF EXISTS "{1}"."{0}";
                    CREATE TABLE "{1}"."{0}" (
                        "rid" varchar(23) COLLATE "pg_catalog"."default",
                        "name" varchar(200) COLLATE "pg_catalog"."default",
                        "roadclass" varchar(5) COLLATE "pg_catalog"."default",
                        "length" int4,
                        "width" int2,
                        "startcrossid" varchar(11) COLLATE "pg_catalog"."default",
                        "endcrossid" varchar(11) COLLATE "pg_catalog"."default",
                        "startangle" int2,
                        "endangle" int2,
                        "startangle_p" int2,
                        "endangle_p" int2,
                        "startlocation" varchar(200) COLLATE "pg_catalog"."default",
                        "endlocation" varchar(200) COLLATE "pg_catalog"."default",
                        "adminlevel" varchar(6) COLLATE "pg_catalog"."default",
                        "techlevel" varchar(6) COLLATE "pg_catalog"."default",
                        "geom" "public"."geometry",
                        "loadcapacity" int2,
                        "trend" varchar(10) COLLATE "pg_catalog"."default",
                        "curvature" int2,
                        "slope" int2,
                        "minspeed" int2,
                        "maxspeed" int2,
                        "isoneway" varchar(6) COLLATE "pg_catalog"."default",
                        "roadsegtype" varchar(10) COLLATE "pg_catalog"."default",
                        "designflow" varchar(6) COLLATE "pg_catalog"."default",
                        "mainflag" text COLLATE "pg_catalog"."default",
                        "adcode" varchar(50) COLLATE "pg_catalog"."default",
                        "link_change" int2,
                        "data_source" varchar(10) COLLATE "pg_catalog"."default",
                        "great_date" varchar(20) COLLATE "pg_catalog"."default",
                        "modify_date" varchar(20) COLLATE "pg_catalog"."default",
                        "author" varchar(50) COLLATE "pg_catalog"."default",
                        "data_vesion" varchar(17) COLLATE "pg_catalog"."default",
                        "pre_data_version" varchar(17) COLLATE "pg_catalog"."default",
                        "data_mode" varchar(6) COLLATE "pg_catalog"."default",
                        "relation" varchar(500) COLLATE "pg_catalog"."default",
                        "change" varchar(6) COLLATE "pg_catalog"."default",
                        "geom_change" text COLLATE "pg_catalog"."default",
                        "openlr_base64" varchar(100) COLLATE "pg_catalog"."default",
                        "openlrfow" varchar(16) COLLATE "pg_catalog"."default",
                        "openlrfrc" varchar(16) COLLATE "pg_catalog"."default",
                        "pairsrid" varchar(23) COLLATE "pg_catalog"."default",
                        "ndsid" int8,
                        "is_hd" numeric(16),
                        "p_modify" int2,
                        "cxjk" numeric(16),
                        "line_geom" "public"."geometry",
                        "polygon_geom" "public"."geometry",
                        "from_way" varchar(8) COLLATE "pg_catalog"."default",
                        "fow" int2,
                        "fcxx" int2,
                        "info_wkt" varchar(50) COLLATE "pg_catalog"."default",
                        "is_modify" int2,
                        "gid" int4 NOT NULL DEFAULT nextval('{0}_gid_seq'::regclass),
                        "fullname" varchar(255) COLLATE "pg_catalog"."default");
                      ALTER TABLE "{1}"."{0}" ADD CONSTRAINT "{0}_unique" UNIQUE ("rid");
                      ALTER TABLE "{1}"."{0}" ADD CONSTRAINT "{0}_pkey" PRIMARY KEY ("gid");
     """.format(tab_rid, schema)
    #print(create_rid_table)
    try:
        cursor(conn, create_rid_table)
        conn.commit()
    except Exception as e:
        print('Exception in create rid', e)
        conn.rollback()

    create_lane_table = """
                    DROP SEQUENCE IF EXISTS {0}_gid_seq CASCADE;
                    CREATE SEQUENCE {0}_gid_seq increment by 1 minvalue 1 start with 1;
                    DROP TABLE IF EXISTS "{1}"."{0}";
                    CREATE TABLE "{1}"."{0}" (
                      "rid" varchar(23) COLLATE "pg_catalog"."default",
                      "sectionid" varchar(26) COLLATE "pg_catalog"."default",
                      "laneid" varchar(28) COLLATE "pg_catalog"."default",
                      "lane_no" varchar(2) COLLATE "pg_catalog"."default",
                      "length" numeric(24),
                      "turntype" varchar(20) COLLATE "pg_catalog"."default",
                      "waitinglaneid" varchar(30) COLLATE "pg_catalog"."default",
                      "lanecatagory" varchar(10) COLLATE "pg_catalog"."default",
                      "line_geom" "public"."geometry",
                      "mainflag" varchar(6) COLLATE "pg_catalog"."default",
                      "lanefunction" varchar(10) COLLATE "pg_catalog"."default",
                      "category_no" int2,
                      "lanespecifictype" text COLLATE "pg_catalog"."default",
                      "lanelocation" int2,
                      "adcode" varchar(150) COLLATE "pg_catalog"."default",
                      "data_source" text COLLATE "pg_catalog"."default",
                      "great_date" varchar(12) COLLATE "pg_catalog"."default",
                      "modify_date" varchar(12) COLLATE "pg_catalog"."default",
                      "author" varchar(50) COLLATE "pg_catalog"."default",
                      "data_vesion" varchar(17) COLLATE "pg_catalog"."default",
                      "pre_data_version" varchar(17) COLLATE "pg_catalog"."default",
                      "data_mode" varchar(6) COLLATE "pg_catalog"."default",
                      "relation" varchar(500) COLLATE "pg_catalog"."default",
                      "change" varchar(6) COLLATE "pg_catalog"."default",
                      "geom_change" varchar(6) COLLATE "pg_catalog"."default",
                      "polygon_geom" "public"."geometry",
                      "width" numeric(5),
                      "openlr_base64" varchar(100) COLLATE "pg_catalog"."default",
                      "is_hd" int2,
                      "tzxid" varchar(50) COLLATE "pg_catalog"."default",
                      "cdfx" varchar(17) COLLATE "pg_catalog"."default",
                      "cdmj" float8,
                      "turntype1" varchar(20) COLLATE "pg_catalog"."default",
                      "p_modify" int2,
                      "reallane" varchar(50) COLLATE "pg_catalog"."default",
                      "geom" "public"."geometry");
                      ALTER TABLE "{1}"."{0}" ADD CONSTRAINT "{0}_pkey" PRIMARY KEY ("laneid");
     """.format(tab_lane, schema)
    #print(create_lane_table)
    try:
        cursor(conn, create_lane_table)
        conn.commit()
    except Exception as e:
        print('Exception in create lane', e)
        conn.rollback()

    create_axf_table = """
                        DROP SEQUENCE IF EXISTS {0}_gid_seq CASCADE;
                        CREATE SEQUENCE {0}_gid_seq increment by 1 minvalue 1 start with 1;
                        DROP TABLE IF EXISTS "{1}"."{0}";
                        CREATE TABLE "{1}"."{0}" (
                        "rid" varchar(23) COLLATE "pg_catalog"."default",
                        "forwardroa" varchar(19) COLLATE "pg_catalog"."default",
                        "seq_no" varchar(8) COLLATE "pg_catalog"."default",
                        "dir" int2,
                        "adcode" varchar(20) COLLATE "pg_catalog"."default",
                        "road_class" int4,
                        "p_modify" int2,
                        "geom" "public"."geometry");
    """.format(tab_axf, schema)
    #print(create_axf_table)
    try:
        cursor(conn, create_axf_table)
        conn.commit()
    except Exception as e:
        print('Exception in create axf', e)
        conn.rollback()

def getRidList(conn,condition):
    parDict = parseConfig()
    schema = parDict.get('schema')
    tab_rid = parDict.get('tab_rid')
    tab_cross = parDict.get('tab_cross')
    if condition != '':
        rids_sql = """
                    select distinct(name),rid from {2}.{0} where name <>'' and name like '{1}%'
                    """.format(tab_rid, condition, schema)
    else:
        rids_sql = """
                    select distinct(name),rid from {1}.{0} where name <>'' 
                    """.format(tab_rid, schema)

    lst_rids = cursor(conn, rids_sql, ret=True)
    print('获取路段数量：' + str(len(lst_rids)))
    crosss_sql = """
                    select distinct(inter_name),inter_id from {1}.{0} where inter_name <>'' 
                 """.format(tab_cross, schema)
    lst_crosss = cursor(conn, crosss_sql, ret=True)
    print('获取路口数量：' + str(len(lst_crosss)))
    return lst_rids,lst_crosss

def getLinkList(conn,selectedRid):
    parDict = parseConfig()
    schema = parDict.get('schema')
    tab_axf = parDict.get('tab_axf')

    rids_sql = """
                    select distinct(forwardroa),seq_no from {1}.{0} where rid ='{2}' order by seq_no asc;
                    """.format(tab_axf, schema,selectedRid)
    lst_links = cursor(conn, rids_sql, ret=True)
    print('获取Link数量：' + str(len(lst_links)))
    return lst_links


def getAngle(sx, sy, ex, ey):
    Rc = 6378137
    Rj = 6356725
    rAngle = 0

    Ec = Rj + (Rc - Rj) * (90.0 - sy) / 90.0
    Ed = Ec * math.cos(sy * math.pi / 180.0)

    dx = ((ex * math.pi / 180.0) - (sx * math.pi / 180.0)) * Ed
    dy = ((ey * math.pi / 180.0) - (sy * math.pi / 180.0)) * Ec
    if dy==0:
        return rAngle
    angle = math.atan(math.fabs(dx / dy)) * 180.0 / math.pi
    dLo = ex - sx
    dLa = ey - sy
    if dLo > 0 and dLa <= 0 :
        angle = (90.0 - angle) + 90
    elif dLo <= 0 and dLa < 0:
        angle = angle + 180.0
    elif dLo < 0 and dLa >= 0 :
        angle = (90.0 - angle) + 270

    rAngle = int(angle)
    return rAngle
