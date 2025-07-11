import sys,os
import time
import json
import logging
from math import ceil
from collections import OrderedDict
from multiprocessing import Pool  # , cpu_count, Manager
from geographiclib.geodesic import Geodesic
try:
    from openlr import binary_decode, LineLocationReference, LocationReferencePoint, FOW, FRC
except ValueError as e:
    from openlr import binary_decode, LineLocation as LineLocationReference, LocationReferencePoint, FOW, FRC

from ..lib.openlr_dereferencer import decode
from ..lib.openlr_dereferencer import example_sqlite_map
from ..lib.openlr_dereferencer.decoding.configuration import Config
from ..lib.dbconn import db_conn, cursor, batch_insert
from itertools import tee
from ..src.QgsOpenlrLog import log

TAB_ROAD = 'data_lines_openlr'
#TAB_NODE = 'data_nodes_openlr'
OFFSET = False  # openlr poff and noff set 0; False 0, True origin 100

LST_FOW = [FOW.UNDEFINED, FOW.MOTORWAY, FOW.MULTIPLE_CARRIAGEWAY, FOW.SINGLE_CARRIAGEWAY,
               FOW.ROUNDABOUT, FOW.TRAFFICSQUARE, FOW.SLIPROAD, FOW.OTHER]
LST_FRC = [FRC.FRC0, FRC.FRC1, FRC.FRC2, FRC.FRC3, FRC.FRC4, FRC.FRC5, FRC.FRC6, FRC.FRC7]


def configParmeter(par):
    # my_config = Config(min_score=0.6, search_radius=40, max_dnp_deviation=0.15,
    #                max_bear_deviation=45, fow_weight=15/100, frc_weight=15/100,
    #                geo_weight=35/100, bear_weight=35/100)
    my_config = Config(min_score=par.get('min_score'), search_radius=par.get('search_radius'), max_dnp_deviation=par.get('max_dnp_deviation'),
                       max_bear_deviation=par.get('max_bear_deviation'), fow_weight=par.get('fow_weight'), frc_weight=par.get('frc_weight'),
                       geo_weight=par.get('geo_weight'), bear_weight=par.get('bear_weight'),bear_dist=par.get('bear_dist'), tolerated_dnp_dev=par.get('tolerated_dnp_dev'))
    return my_config

def parse(f_json):

    json_info = json.loads(open(f_json, 'r',encoding='utf8').read(),
                           object_pairs_hook=OrderedDict)
    return json_info


def get_forwardroad(conn, real_location, schema):
    lst_forwardroad = []
    lst_line_id = [line.line_id for line in real_location.lines]

    if len(lst_line_id):
        for line_id in lst_line_id:
            sql_forward = '''select {2} from {4}.{0} where {3}={1};
            '''.format(TAB_ROAD, line_id, 'forwardroadid64', 'line_id', schema)
            lst_forwardroad.append(cursor(conn, sql_forward, ret=True)[0][0])

    return lst_line_id, lst_forwardroad

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    first, second = tee(iterable)
    next(second, None)
    return zip(first, second)

def count_via(coord, lst_wkt, use_len):
    lst_distance = []
    inverse = Geodesic.WGS84.Inverse

    for (x, y) in lst_wkt:
        lst_distance.append(int(inverse(coord[1], coord[0], y, x, Geodesic.DISTANCE)["s12"]))

    bear = 0
    cur_len = 0
    index = (lst_distance.index(min(lst_distance)))
    if index < len(lst_wkt)-1:
        (x1, y1) = lst_wkt[index]
        (x2, y2) = lst_wkt[index+1]
        bear = inverse(float(y1), float(x1), float(y2), float(x2), Geodesic.AZIMUTH)["azi1"]

        ii = 0
        for (coord_a, coord_b) in pairwise(lst_wkt):
            if ii <= index:
                l = inverse(coord_a[1], coord_a[0], coord_b[1], coord_b[0], Geodesic.DISTANCE)
                cur_len += l["s12"]
                ii += 1

    return int(bear), int(cur_len)-use_len, int(cur_len)


# def rid2openlr(conn, tab_rid, rid, via_point=[], start_point=(), end_point=()):
#
#     rid = '12IR606S61012J8U06SA500'
#
#     # noinspection SqlResolve
#     sql_rid = """select st_x(st_startpoint({2})) as x1,st_y(st_startpoint({2})) as y1,
#     degrees(ST_azimuth(st_startpoint({2}), st_pointn({2}, 2))) as bear1,
#     3 as frc1, 2 as fow1,
#     st_length({2}, true) as len1,
#     st_x(st_endpoint({2})) as x2,st_y(st_endpoint({2})) as y2,
#     degrees(ST_azimuth(st_endpoint({2}),st_pointn({2}, ST_NumPoints({2})-1))) as bear2,
#     3 as frc2, 2 as fow2
#     from {0} where rid = '{1}';""".format(tab_rid, rid, 'geom')
#
#     rows = cursor(conn, sql_rid, ret=True)
#     if len(rows) == 1:
#         p1_x, p1_y, p1_bear, p1_frc, p1_fow, p1_len, p2_x, p2_y, p2_bear, p2_frc, p2_fow = rows[0]
#         # first point
#         if len(start_point):
#             (p1_x, p1_y) = start_point
#         # end point
#         if len(end_point):
#             (p2_x, p2_y) = end_point
#
#         if not len(via_point):
#             reference = LineLocationReference(points=[
#                 LocationReferencePoint(lon=p1_x, lat=p1_y, frc=LST_FRC[p1_frc],
#                                        fow=LST_FOW[p1_fow], bear=int(p1_bear),
#                                        lfrcnp=LST_FRC[7], dnp=int(p1_len)),
#                 LocationReferencePoint(lon=p2_x, lat=p2_y, frc=LST_FRC[p2_frc],
#                                        fow=LST_FOW[p2_fow], bear=int(p2_bear),
#                                        lfrcnp=LST_FRC[7], dnp=0)],
#                 poffs=0, noffs=0)
#         else:
#             lst_via = []
#             # noinspection SqlResolve
#             sql_points = """select array_to_string(array_agg(t3.coord order by t3.n), ',') as points
#                             from (
#                             select st_x(t2.geom) || ' ' || st_y(t2.geom) as coord, t2.n
#                             from (
#                             select
#                             st_pointn(
#                             t1.geom,
#                             generate_series(1, ST_NPoints(t1.geom))) as geom, generate_series(1, ST_NPoints(t1.geom)) as n
#                             from(
#                             select st_simplify(geom, 0.00000001) as geom
#                             FROM {0}
#                             where rid = '{1}'
#                             ) t1) t2) t3
#                             """.format(tab_rid, rid)
#             line_wkt = []
#             for coord in cursor(conn, sql_points, ret=True)[0]['points'].split(','):
#                 x, y = coord.split(' ')
#                 line_wkt.append((float(x), float(y)))
#
#             # check via_point order
#             sql_rate = """select string_agg(to_char(ST_LineLocatePoint(t1.geom, t2.geom), '0D999'), ',') as rate1
#             from {0} t1,
#             (select st_pointfromtext(unnest(string_to_array('{1}', ',')), 4326) as geom) t2
#             where t1.rid = '{2}';
#             """.format(tab_rid, ','.join(['POINT' + str(ii).replace(',', '') for ii in via_point]), rid)
#             rows_rate = cursor(conn, sql_rate, ret=True)[0]['rate1']
#
#             lst_rate = [float(ii) for ii in rows_rate.split(',')]
#
#             # check via point is not at the start/end point
#             if min(lst_rate)<=0 or max(lst_rate) >= 1:
#                 print('via point at the start/end point')
#                 # continue()
#                 reference = None
#             else:
#                 # update via_point order
#                 via_point = [point[1] for point in sorted(zip(lst_rate, via_point))]
#
#                 use_len = 0
#                 ii = 0
#                 for coord in via_point:
#                     bear1, dnp1, use_len = count_via(coord, line_wkt, use_len)
#                     lst_via.append((coord[0], coord[1], bear1, dnp1, use_len))
#
#                 # first point
#                 lst_points = [LocationReferencePoint(lon=p1_x, lat=p1_y, frc=LST_FRC[p1_frc],
#                                                      fow=LST_FOW[p1_fow], bear=int(p1_bear),
#                                                      lfrcnp=LST_FRC[7], dnp=lst_via[0][3])]
#
#                 # via points
#                 for i, lst in enumerate(lst_via):
#                     if i + 1 < len(lst_via):
#                         dnp = lst_via[i + 1][3]
#                     else:
#                         dnp = int(p1_len) - lst_via[i][4]
#
#                     lst_points.append(LocationReferencePoint(lon=lst[0], lat=lst[1], frc=LST_FRC[p1_frc],
#                                                              fow=LST_FOW[p1_fow], bear=lst[2],
#                                                              lfrcnp=LST_FRC[7], dnp=dnp))
#
#                 # end points
#                 lst_points.append(LocationReferencePoint(lon=p2_x, lat=p2_y, frc=LST_FRC[p2_frc],
#                                                          fow=LST_FOW[p2_fow], bear=int(p2_bear),
#                                                          lfrcnp=LST_FRC[7], dnp=0))
#
#                 reference = LineLocationReference(points=lst_points, poffs=0, noffs=0)
#
#         return reference
#     elif len(rows) > 1:
#         print('ERROR: there are more than one same rid code')
#         return None
#     else:
#         print('ERROR: input rid do not in the table')
#         return None


def singleDecode(dct_dbinfo,tab_openlr, tab_output,par,schema,single_rid):
    log.initLogging()
    print(dct_dbinfo)
    print(tab_openlr)
    print(tab_output)
    print(par)
    print(single_rid)

    conn = db_conn(dct_dbinfo['host'], dct_dbinfo['port'], dct_dbinfo['user'],
                   dct_dbinfo['pw'], dct_dbinfo['db'])
    # check database connection
    try:
        if conn.closed != 0:
            sys.exit()
    except IOError:
        print('error:database connect is error.')
        sys.exit()
    print(conn)
    #query rid
    sql_query_rid = "select openlr_base64 from {2}.{0} where rid = '{1}'".format(tab_openlr, single_rid, schema)
    print(sql_query_rid)
    openlr_code = cursor(conn, sql_query_rid, ret=True)[0][0]
    print('openlr_code exist:'+openlr_code)
    if not openlr_code:
        return
    # cursor(conn,
    #        'update {0} set {1} = 0 where {1}=1;'.format(TAB_ROAD, 'bz'),
    #        commit=True)
    mapreader = example_sqlite_map.ExampleMapReader(dct_dbinfo, schema)

    try:
        # if 1==1:
        reply = openlr_code
        #log.debug(reply)
        # reply = "C1CdPxADgAwoBACuAFIMEA=="
        reference = binary_decode(reply)
        # openlr poff and off set 0
        if not OFFSET:
            reference = LineLocationReference(reference.points,
                                              poffs=0, noffs=0)
        if reference is None:
            pass
        #log.debug(reference)
        print(configParmeter(par))
        # print(reference)
        # print('-'*40)
        real_location, scores = decode(reference, mapreader, config=configParmeter(par))
        # print(real_location)
        # print(scores)

        lines = None
        if real_location is not None:
            lst_line_id, lst_forwardroad = get_forwardroad(conn, real_location, schema)
            # print(lst_line_id)
            # print(scores)
            # lines = tuple(lst_line_id)
            lines = [str(l_id) for l_id in lst_line_id]
            first_scores = [str(score[1]) for score in scores if
                            str(score[0]) == lines[0]]
            tail_scores = [str(score[-1]) for score in scores if
                           str(score[-2]) == lines[-1]]
            if len(first_scores) > 0:
                first_score = round(float(first_scores[0]),2)
            if len(tail_scores) > 0:
                tail_score = round(float(tail_scores[0]),2)
            # print(first_score, tail_score)

            select_openlr = "select count(1) from {2}.{0} where openlr = '{1}'".format(tab_output, openlr_code, schema)
            print(select_openlr)
            existed_openlr = cursor(conn,select_openlr,ret=True)[0][0]
            # print(",".join(lines), ",".join(lst_forwardroad), real_location.p_off,
            #  real_location.n_off, first_score, tail_score)
            if single_rid != 0:
                openlr_code = single_rid

            if existed_openlr == 0:
                sql_insert = """insert into {8}.{0} (openlr, lines_id, lines, p_off, n_off, first_scores,tail_scores)
                                select '{1}','{2}','{3}','{4}','{5}',{6},{7};
                                """.format(tab_output, openlr_code,",".join(lines),",".join(lst_forwardroad),
                                           real_location.p_off,real_location.n_off,first_score,tail_score, schema)
                cursor(conn,sql_insert,commit=True)

            elif existed_openlr > 0:
                sql_update = """update {8}.{0} set lines_id = '{2}',lines = '{3}', p_off= '{4}', n_off= '{5}',first_scores = {6},tail_scores = {7}
                 where openlr = '{1}';
                 """.format(tab_output, openlr_code,",".join(lines),",".join(lst_forwardroad),real_location.p_off,
                            real_location.n_off,first_score,tail_score, schema)
                cursor(conn, sql_update, commit=True)

            # -----------------------------------------delete
            # openlr_join_sql = """
            #         update {0} set find = 1  where openlr = '{1}';
            #         """.format(tab_openlr, openlr_code)
            # cursor(conn, openlr_join_sql, commit=True)
            #
            # cursor(conn,
            #        'update {0} set {1} = 0 where {1}=1;update {2} set {1} = 0 where {1}=1;'.format(TAB_ROAD, 'bz',tab_openlr),
            #        commit=False)
            #
            # if len(lines) == 1:
            #     cursor(conn,
            #            "update {0} set {2} = 1 where {3} = {1};update {4} set {2} = 1 where openlr ='{5}';".format(
            #                TAB_ROAD, lines[0], 'bz', 'line_id',tab_openlr,openlr_code),
            #            commit=False)
            #
            #     status_code = '200'
            # elif len(lines) > 1:
            #     cursor(conn,
            #            "update {0} set {2} = 1 where {3} in {1};update {4} set {2} = 1 where openlr ='{5}';".format(
            #                TAB_ROAD, tuple(lines), 'bz', 'line_id',tab_openlr,openlr_code),
            #            commit=False)
            # -----------------------------------------delete
            if len(lines) >= 1:
                status_code = '200'
            else:
                print('no link')
                status_code = '400'

        else:
            print('no link')
            status_code = '400'
        conn.commit()

        print('-' * 50)
    finally:
        mapreader.connection.close()
        conn.close()
    return status_code,lines

def sub_jobs(dct_dbinfo, v1, tab_output,par,log_signal):

    # time.sleep(1)
    mapreader = example_sqlite_map.ExampleMapReader(dct_dbinfo)
    conn = db_conn(dct_dbinfo['host'], dct_dbinfo['port'], dct_dbinfo['user'],
                   dct_dbinfo['pw'], dct_dbinfo['db'])

    lst_sql = []
    dict_list = []
    sql_insert1 = """insert into {0} ({1}, {2}, {3}, {4}, {5})
            values (%({1})s, %({2})s, %({3})s, %({4})s, %({5})s);
            """.format(tab_output, 'openlr', 'lines_id', 'lines', 'p_off', 'n_off')
    try:
        for row_openlr in v1:
            openlr = row_openlr
            if len(openlr) < 24:
                continue
            print(openlr)
            log_signal.emit(openlr)
            reference = binary_decode(openlr)
            if not OFFSET:
                reference = LineLocationReference(reference.points,
                                                  poffs=0, noffs=0)
            real_location = decode(reference, mapreader, config=configParmeter(par))
            if real_location is not None:
                lst_line_id, lst_forwardroad = get_forwardroad(conn, real_location, schema)
                lines = [str(l_id) for l_id in lst_line_id]
                dict_list.append({'openlr':openlr, 'lines_id':",".join(lines),
                                  'lines':",".join(lst_forwardroad),
                                  'p_off':real_location.p_off,
                                  'n_off':real_location.n_off})

    finally:
        # if len(lst_sql):
        #     cursor(conn, ' '.join(lst_sql), commit=True)
        # print(sql_insert1)
        # print(dict_list)
        if len(dict_list):
            batch_insert(conn, sql_insert1, dict_list)
        # conn.commit()
        conn.close()
        mapreader.connection.close()
        del mapreader


def multi_decode(dct_dbinfo, tab_openlr, tab_output, debug,par,log_signal):

    process = 3
    conn = db_conn(dct_dbinfo['host'], dct_dbinfo['port'], dct_dbinfo['user'],
                   dct_dbinfo['pw'], dct_dbinfo['db'])
    try:
        sql_createtable = """drop table if exists {0};
        create table {0} (gid serial4 primary key, openlr varchar(30),
        lines_id varchar(2000), lines varchar(2000), p_off decimal(10,2),
        n_off decimal(10,2));
        """.format(tab_output)
        cursor(conn, sql_createtable, commit=True)

        for _ in range(3):
            sql_total = """select count(1) as js from {0} where {2} not in (select {2} from {1});
            """.format(tab_openlr, tab_output, 'openlr')
            total = cursor(conn, sql_total, ret=True)[0][0]

            if total >= 10000:
                step = 300
            elif total >= 2000:
                step = 50
                # todo: change to 50
            elif total >= 1000:
                step = 10
            elif total >= 500:
                step = 5
            elif total >= 200:
                step = 2
            else:
                step = 1

            jobs = {}
            for i in range(ceil(total / step)):
                sql_jobs = """select {4} from {0} where {4} not in
                (select {4} from {1}) order by {5} limit {2} offset {3};
                """.format(tab_openlr, tab_output, step, step * i, 'openlr', 'gid')
                # print(sql_jobs)
                rows_jobs = cursor(conn, sql_jobs, ret=True)
                lst_jobs = []
                for row_jobs in rows_jobs:
                    lst_jobs.append(row_jobs[0])
                jobs[str(i)] = lst_jobs

            if len(jobs.keys()) < process:
                process = len(jobs.keys()) if len(jobs.keys()) > 0 else 1

            pool = Pool(process)

            # debug = True
            for _, v1 in jobs.items():
                if debug:
                    sub_jobs(dct_dbinfo, v1, tab_output,par,log_signal)
                else:
                    pool.apply_async(func=sub_jobs,
                                     args=(dct_dbinfo, v1, tab_output,par))
            pool.close()
            pool.join()
            pool.terminate()
    finally:
        conn.close()
    conn.close()

if __name__ == '__main__':
    from ..lib.common import parseConfig
    parDict = parseConfig()
    dct_dbinfo = parDict.get('dct_dbinfo')
    TAB_ROAD = parDict.get('TAB_ROAD')
    TAB_NODE = parDict.get('TAB_NODE')
    tab_openlr = parDict.get('tab_openlr')
    schema = parDict.get('schema', 'public')

    tab_output = parDict.get('tab_output')
    par = parDict.get('par')
    example_sqlite_map.primitives.TAB_NODE = TAB_NODE  # nodes table
    example_sqlite_map.primitives.TAB_ROAD = TAB_ROAD  # lines table
    example_sqlite_map.primitives.SCHEMA = schema  # schema

    example_sqlite_map.TAB_NODE = TAB_NODE
    example_sqlite_map.TAB_ROAD = TAB_ROAD
    openlr_code = 'C1JWmRzOBDDm+TVP/d8BbsMJAtPxMBwAAA=='

    status_code = single_decode(dct_dbinfo, tab_openlr, tab_output, openlr_code, par)
