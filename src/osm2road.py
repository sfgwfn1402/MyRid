import json
import os
import requests
from PyQt5.QtCore import QThread,pyqtSignal
from PyQt5.QtGui import QFont, QColor
from qgis._core import QgsVectorLayer, QgsVectorLayerExporter, QgsCoordinateReferenceSystem, QgsDataSourceUri, QgsTask, \
    QgsProject, QgsMarkerSymbol, QgsLineSymbol, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsPalLayerSettings, \
    QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling, Qgis
from osgeo import ogr

from shapely.geometry import Polygon
from ..lib.dbconn import cursor
from ..lib.common import parseConfig
from ..lib import osmnx as ox
from ..lib.common import parseConfig

from time import sleep

class OsmRoadThread( QThread ):
    osm_signal=pyqtSignal(str)
    def run(self ):
        self.osm_signal.emit("0")

def downloadOsm(task,ad_code,data_folder):
    try:
        print('行政区:' + ad_code)
        geojson = requests.get('https://geo.datav.aliyun.com/areas_v3/bound/geojson?code=' + ad_code)
        #print(geojson.text)
        content = json.loads(geojson.text)['features'][0]['geometry']
        coords = content['coordinates'][0][0]
        #print(coords)
        task.setProgress(10)

        polygon = Polygon(coords)
        G = ox.graph_from_polygon(polygon, network_type="drive")
        task.setProgress(60)
        #north, south, east, west = 40.0703, 40.0390, 116.3422, 116.2785
        #G = ox.graph_from_bbox(north, south, east, west, network_type="drive")
        #print('already graph from polygon....')
        #ox.plot_graph(G)
        G = ox.consolidate_intersections(ox.project_graph(G), 15, True, True)
        task.setProgress(80)
        print(data_folder+'osm_data.gpkg')
        ox.save_graph_geopackage(G, data_folder+'osm_data.gpkg', 'utf-8', True)
        task.setProgress(100)
    except Exception as e:
        print('Exception in download osm', e)

    return {'total': 100, 'iterations': 100,
            'task': 'download osm data'}

#
def roadData2Postgresql(task,data_folder):
    parDict = parseConfig()
    dbinfo = parDict.get('db_info')
    schema = parDict.get('schema')
    tab_segment = parDict.get('tab_segment')
    tab_nodes = parDict.get('tab_nodes')

    conn = parseConfig().get('conn')
    project = QgsProject.instance()

    if task.isCanceled():
        return None
    #TRUNCATE TABLE "{2}"."{0}";
    #TRUNCATE TABLE "{2}"."{1}";
    drop_sql = """
                    DROP TABLE IF EXISTS "{2}"."{0}" CASCADE;
                    DROP TABLE IF EXISTS "{2}"."{1}" CASCADE;
                    """.format(tab_nodes,tab_segment, schema)
    # print(drop_sql)
    try:
        cursor(conn, drop_sql)
        conn.commit()
    except Exception as e:
        print(str(e))

    path_to_gpkg = data_folder + 'osm_data.gpkg'
    for layer in ['edges', 'nodes']:
        gpkg_places_layer = path_to_gpkg + "|layername=" + layer
        # 例如：gpkg_places_layer = "/home/project/data/data.gpkg|layername=places"
        #print(gpkg_places_layer)
        try:
            my_layer = QgsVectorLayer(gpkg_places_layer, layer, "ogr")
            if not my_layer.isValid():
                ret = -1
                errMsg = str('图层加载失败！')
                return ret,errMsg
            else:
                # my_layer is some QgsVectorLayer
                con_string = """
                            dbname='{0}' host='{1}' port='{2}' user='{3}' password='{4}' key=gid type=LINESTRING table="{5}"."{6}" (geom)
                            """.format(dbinfo['dbname'], dbinfo['host'], dbinfo['port'], dbinfo['user'], dbinfo['pw'],
                                       schema, tab_segment)

                if layer == 'nodes':
                    con_string = """
                                dbname='{0}' host='{1}' port='{2}' user='{3}' password='{4}' key=gid type=POINT table="{5}"."{6}" (geom)
                                """.format(dbinfo['dbname'], dbinfo['host'], dbinfo['port'], dbinfo['user'],
                                           dbinfo['pw'], schema, tab_nodes)
            #print(con_string)
            ret, errMsg = QgsVectorLayerExporter.exportLayer(my_layer, con_string, 'postgres',
                                                             QgsCoordinateReferenceSystem(4326), False)

            task.setProgress(60)
        except Exception as e:
            #print('Exception->'+str(e))
            ret = -1
            errMsg = str(e)

    # print('load osm data..ret->'+str(ret))

    if ret==0:
        alter_sql = """
                        ALTER TABLE "{2}"."{0}"  DROP COLUMN "fid";
                        ALTER TABLE "{2}"."{1}"  DROP COLUMN "fid";
                        ALTER TABLE "{2}"."{0}" RENAME COLUMN "y" TO "y_coord";
                        ALTER TABLE "{2}"."{0}" RENAME COLUMN "x" TO "x_coord";
                        ALTER TABLE "{2}"."{0}" ADD COLUMN "signlight" int2;
                        ALTER TABLE "{2}"."{0}" ADD COLUMN "cross" int2 DEFAULT 1;
                        ALTER TABLE "{2}"."{0}" ADD COLUMN "data_mode" int2 DEFAULT 0;
                        COMMENT ON COLUMN "{2}"."{0}"."data_mode" IS '数据状态：0 未处理  1已处理';
                        ALTER TABLE "{2}"."{1}" RENAME COLUMN "u" TO "fnode";
                        ALTER TABLE "{2}"."{1}" RENAME COLUMN "v" TO "tnode";
                        ALTER TABLE "{2}"."{1}"  ADD COLUMN "road_class" int4;
                        ALTER TABLE "{2}"."{1}"  ADD COLUMN "direction" int2;
                        ALTER TABLE "{2}"."{1}"  ADD COLUMN "ad_code" varchar(6) COLLATE "pg_catalog"."default";
                        ALTER TABLE "{2}"."{1}"  ADD COLUMN "form_way" int2;
                        ALTER TABLE "{2}"."{1}"  ADD COLUMN "fow" int2;
                        ALTER TABLE "{2}"."{1}"  ADD COLUMN "link_type" int2;
                        ALTER TABLE "{2}"."{1}"  ADD COLUMN "fc" int2;
                        ALTER TABLE "{2}"."{1}"  ADD COLUMN "over_head" int2;
                        ALTER TABLE "{2}"."{1}"  ADD COLUMN "innerarc" int2;
                        ALTER TABLE "{2}"."{1}" ADD COLUMN "data_mode" int2 DEFAULT 0;
                        COMMENT ON COLUMN "{2}"."{1}"."data_mode" IS '数据状态：0 未处理  1已处理';
        """.format(tab_nodes,tab_segment,schema )
        update_sql = """
                        --更新坐标
                        UPDATE "{2}"."{0}" SET x_coord=st_x(geom),y_coord=st_y(geom);
                        --更新信控路口
                        UPDATE "{2}"."{0}" SET signlight=0;
                        UPDATE "{2}"."{0}" SET signlight=1 WHERE highway='traffic_signals';
                        --更新road_class
                        UPDATE "{2}"."{1}" SET road_class ='49' ;
                        UPDATE "{2}"."{1}" SET road_class ='41000' WHERE highway LIKE '%motorway%';
                        UPDATE "{2}"."{1}" SET road_class ='42000' WHERE highway LIKE '%trunk%';
                        UPDATE "{2}"."{1}" SET road_class ='46000' WHERE highway LIKE '%tertiary%';
                        UPDATE "{2}"."{1}" SET road_class ='45000' WHERE highway LIKE '%secondary%';
                        UPDATE "{2}"."{1}" SET road_class ='44000' WHERE highway LIKE '%primary%';
                        UPDATE "{2}"."{1}" SET road_class ='53000' WHERE LEFT(ref,1)= 'Y' AND highway LIKE '%tertiary%';
                        UPDATE "{2}"."{1}" SET road_class ='52000' WHERE LEFT(ref,1)= 'X' AND highway LIKE '%secondary%';
                        UPDATE "{2}"."{1}" SET road_class ='51000' WHERE LEFT(ref,1)= 'S' AND highway LIKE '%primary%';
                        -- 更新车道数量
                        UPDATE "{2}"."{1}" SET lanes='2' WHERE lanes ='' AND highway='tertiary';
                        UPDATE "{2}"."{1}" SET lanes='2' WHERE lanes ='' AND highway='secondary';
                        UPDATE "{2}"."{1}" SET lanes='3' WHERE lanes ='' AND highway='primary';
                        UPDATE "{2}"."{1}" SET lanes='3' WHERE lanes ='' AND highway='trunk';
                        UPDATE "{2}"."{1}" SET lanes='3' WHERE lanes ='' AND highway='motorway';
                        UPDATE "{2}"."{1}" SET lanes='1' WHERE lanes ='';
                        UPDATE "{2}"."{1}" SET lanes=(array_remove(regexp_split_to_array(lanes,E'\[[\\'\\\s?,\\\]]+',''),''))[1] WHERE lanes like '[%';
                        COMMIT;
                        -- 更新路段方向 direction
                        UPDATE "{2}"."{1}" s SET direction=( case when round(degrees(ST_Azimuth(st_startpoint(s.geom), st_endpoint(s.geom)))::NUMERIC,2)>315 OR  round(degrees(ST_Azimuth(st_startpoint(s.geom), st_endpoint(s.geom)))::NUMERIC,2)<= 45 THEN 1 
                         when round(degrees(ST_Azimuth(st_startpoint(s.geom), st_endpoint(s.geom)))::NUMERIC,2)>45 AND  round(degrees(ST_Azimuth(st_startpoint(s.geom), st_endpoint(s.geom)))::NUMERIC,2)<= 135 THEN 2 
                         when round(degrees(ST_Azimuth(st_startpoint(s.geom), st_endpoint(s.geom)))::NUMERIC,2)>135 AND  round(degrees(ST_Azimuth(st_startpoint(s.geom), st_endpoint(s.geom)))::NUMERIC,2)<= 225 THEN 3 
                         when round(degrees(ST_Azimuth(st_startpoint(s.geom), st_endpoint(s.geom)))::NUMERIC,2)>225 AND  round(degrees(ST_Azimuth(st_startpoint(s.geom), st_endpoint(s.geom)))::NUMERIC,2)<= 315 THEN 4 END );
                        COMMIT;
                        -- 更新速度
                        UPDATE "{2}"."{1}" set maxspeed=(array_remove(regexp_split_to_array(maxspeed,E'\[[\\'\\\s?,\\\]]+',''),''))[1] where maxspeed like '[%';
                        COMMIT;
                        -- 标记岔口
                        UPDATE osm_nodes SET "cross" = 0 where osmid in (
                        select fnode as gid from "{2}"."{1}" where ((name ='' and highway like '%_link%') or road_class ='49') 
                        union all
                        select tnode as gid from "{2}"."{1}" where ((name ='' and highway like '%_link%') or road_class ='49')
                        union all
                        select tnode as osmid from "{2}"."{1}" group by tnode HAVING count(tnode)=2 and tnode in(
                        select fnode as fnode from "{2}"."{1}" where name <>'' group by fnode HAVING count(fnode)=1 )
                        union all
                        select n.osmid from "{2}"."{0}" n left join "{2}"."{1}" f on n.osmid=f.fnode
                        left join "{2}"."{1}" t on n.osmid=t.tnode 
                        group by n.osmid having string_agg(f.name,'')='' and string_agg(t.name,'') ='')
                        and osmid not in (select fnode as osmid from "{2}"."{1}" group by fnode HAVING count(fnode)>3  union all select tnode as osmid  from "{2}"."{1}" group by tnode HAVING count(tnode)>3)
                        and osmid not in (select distinct(n.osmid)  from "{2}"."{0}" n left join "{2}"."{1}" f on n.osmid=f.fnode left join "{2}"."{1}" t on n.osmid=t.tnode where f.name||t.name ='' group by n.osmid);
                        COMMIT;
                        UPDATE "{2}"."{0}" SET "cross"=1 WHERE signlight=1;
        """.format(tab_nodes,tab_segment,schema )
        # print(update_sql)
        try:
            cursor(conn, alter_sql)
            conn.commit()
            task.setProgress(70)
            cursor(conn, update_sql)
            conn.commit()
            task.setProgress(90)
            if not QgsProject.instance().mapLayersByName(tab_nodes):
                #加载规整后osm数据库图层
                nodes_uri = QgsDataSourceUri()
                # 设置主机，端口，数据库名称，用户名和密码
                nodes_uri.setConnection(dbinfo['host'], str(dbinfo['port']), dbinfo['dbname'], dbinfo['user'], dbinfo['pw'])
                # 设置数据库架构，表名，几何列和可选项（WHERE 语句）
                nodes_uri.setDataSource(schema, tab_nodes, "geom", "", "gid")
                nlayer =QgsVectorLayer(nodes_uri.uri(False), tab_nodes, "postgres")
                nlayer.setRenderer(
                QgsCategorizedSymbolRenderer('cross', [
                    QgsRendererCategory('0', QgsMarkerSymbol.createSimple({ 'name':'dot','color': '#1f78b4'}), '岔口'),
                    QgsRendererCategory('1', QgsMarkerSymbol.createSimple({ 'name':'dot','color': '#2cff25'}), '路口')
                ]))
                project.addMapLayer(nlayer)
            if not QgsProject.instance().mapLayersByName(tab_segment):
                segment_uri = QgsDataSourceUri()
                # 设置主机，端口，数据库名称，用户名和密码
                segment_uri.setConnection(dbinfo['host'], str(dbinfo['port']), dbinfo['dbname'], dbinfo['user'], dbinfo['pw'])
                # 设置数据库架构，表名，几何列和可选项（WHERE 语句）
                segment_uri.setDataSource(schema, tab_segment, "geom", "", "gid")
                slayer=QgsVectorLayer(segment_uri.uri(False), tab_segment, "postgres")
                symbol = QgsLineSymbol.createSimple({ 'color': '#2cff25'})
                slayer.renderer().setSymbol(symbol)
                #标注路名
                layer_settings = QgsPalLayerSettings()
                text_format = QgsTextFormat()
                text_format.setFont(QFont("Arial", 10))
                text_format.setSize(10)
                buffer_settings = QgsTextBufferSettings()
                buffer_settings.setEnabled(True)
                buffer_settings.setSize(1)
                buffer_settings.setColor(QColor("white"))
                text_format.setBuffer(buffer_settings)
                layer_settings.setFormat(text_format)
                layer_settings.fieldName = "name"
                layer_settings.placement = Qgis.LabelPlacement(2)
                layer_settings.enabled = True
                layer_settings = QgsVectorLayerSimpleLabeling(layer_settings)
                slayer.setLabelsEnabled(True)
                slayer.setLabeling(layer_settings)
                # 显示更改
                slayer.triggerRepaint()
                project.addMapLayer(slayer)
            task.setProgress(100)
        except Exception as e:
            print('Exception in road data to postgresql', e)
            conn.rollback()

    return {'total': 100, 'iterations': 100,
            'task': 'road data to postgresql'}

def getRoadList(conn,condition):
    parDict = parseConfig()
    schema = parDict.get('schema')
    tab_segment = parDict.get('tab_segment')
    if condition !='':
        roads_sql = """
                select distinct(name) from {2}.{0} where name not like \'[%\' and name <>'' and name like '%{1}%'
                """.format(tab_segment,condition, schema)
    else:
        roads_sql = """
                        select distinct(name) from {1}.{0} where name not like \'[%\' and name <>''
                        """.format(tab_segment,  schema)
    print(roads_sql)
    lst_segment = cursor(conn, roads_sql, ret=True)
    print('获取道路数量：' + str(len(lst_segment)))
    return lst_segment


