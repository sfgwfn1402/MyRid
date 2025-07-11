import os
import sys
import json
from collections import OrderedDict
from typing import List
from openlr_r_w import Get_Info2Openlr, Points_Info
from dbconn import db_conn_dict, cursor, batch_insert


class Rid2Openlr():

    def __init__(self, conn, input_info,schema) -> None:
        self.t_rid = input_info.get("openlr", "rid")
        print(self.t_rid)
        self.t_point = input_info.get("tab_point", "location_points")
        self.f_rid = input_info.get("field_rid", "rid")
        self.f_openlr = input_info.get("field_openlr", "openlr")
        self.f_geom = input_info.get("field_geom", "geom")
        self.f_s_rc = input_info.get("field_line_first_rc", "roadclass")
        self.f_s_fow = input_info.get("field_line_first_fow", "form_way")
        self.f_e_rc = input_info.get("field_line_end_rc", "roadclass")
        self.f_e_fow = input_info.get("field_line_end_fow", "form_way")
        self.f_p_rc = input_info.get("field_line_end_rc", "roadclass")
        self.f_p_fow = input_info.get("field_line_end_fow", "form_way")
        self.max_len = input_info.get("max_len", 15000)
        self.other_sql = input_info.get("other_sql", "")
        self.frc_fow_sql = input_info.get("frc_fow_sql", "")
        self.schema = schema
        self.is_out_info = 0
        self.conn = conn


    def convert_multi(self) -> None:
        "convert all rid"
        sql_base_info = """select {6},
        st_x(st_startpoint({1})) as s_x, st_y(st_startpoint({1})) as s_y,

        case
        when ({2}=41000) then 0
        when ({2}=43000) then 1
        when ({2} in (42000, 44000)) then 2
        when ({2}=51000) then 3
        when ({2} in (45000, 52000)) then 4
        when ({2} in (47000, 53000)) then 5
        else 6
        end as s_frc,
        case
        when ({3}=1 and {2}=41000) then 1
        when ({3}=1 and {2}!=41000) then 2
        when ({3}=15) then 3
        when ({3}=4) then 4
        when ({3} in (5,53,56,58)) then 5
        when ({3} in (3,6,7,8,9,10,17)) then 6
        when ({3} in (11,12,13,14,16)) then 7
        else 0
        end as s_fow,

        degrees(ST_azimuth( st_pointn({1}, 1), st_pointn({1}, 2))) as s_bear,
        st_length({1}, True) as dnp,
        st_x(st_endpoint({1})) as e_x, st_y(st_endpoint({1})) as e_y,

        case
        when ({4}=41000) then 0
        when ({4}=43000) then 1
        when ({4} in (42000, 44000)) then 2
        when ({4}=51000) then 3
        when ({4} in (45000, 52000)) then 4
        when ({4} in (47000, 53000)) then 5
        else 6
        end as e_frc,
        case
        when ({5}=1 and {4}=41000) then 1
        when ({5}=1 and {4}!=41000) then 2
        when ({5}=15) then 3
        when ({5}=4) then 4
        when ({5} in (5,53,56,58)) then 5
        when ({5} in (3,6,7,8,9,10,17)) then 6
        when ({5} in (11,12,13,14,16)) then 7
        else 0
        end as e_fow,

        degrees(ST_azimuth( st_pointn({1}, ST_NPOInTS({1})), st_pointn({1}, ST_NPOInTS({1})-1))) as e_bear
        from {10}.{0}
        where st_length({1}, True) <= {7}
        and {6} not in (select {6} from {10}.{9} group by {6})
        {8}
        ;
        """.format(self.t_rid, self.f_geom, self.f_s_rc, self.f_s_fow, self.f_e_rc,
                   self.f_e_fow, self.f_rid, self.max_len, self.other_sql, self.t_point, self.schema)
        # print(sql_base_info)
        dct_rid_openlrs = self._points_2_encode_info(sql_base_info)

        # more rela points
        sql_more_rela_rid = """select {2}
        from {6}.{0} 
        where st_length({1}, True) <= {3}
        and {2} in (select {2} from {6}.{5} group by {2})
        {4}
        ;
        """.format(self.t_rid, self.f_geom, self.f_rid, self.max_len, self.other_sql, self.t_point, self.schema)
        # print(sql_more_rela_rid)
        rows_more_rela = cursor(self.conn, sql_more_rela_rid, ret=True)
        for row_more_rela in rows_more_rela:
            rid = row_more_rela[self.f_rid]
            dct_rid_openlrs[rid] = self._points_more_encode_info(rid)
        return dct_rid_openlrs

    def convert_single(self, rid: str, is_print=False) -> None:
        "convert single rid"
        if is_print:
            self.is_out_info = 1

        sql_base_info = """select {6},
        st_x(st_startpoint({1})) as s_x, st_y(st_startpoint({1})) as s_y,

        case
        when ({2}=41000) then 0
        when ({2}=43000) then 1
        when ({2} in (42000, 44000)) then 2
        when ({2}=51000) then 3
        when ({2} in (45000, 52000)) then 4
        when ({2} in (47000, 53000)) then 5
        else 6
        end as s_frc,
        case
        when ({3}=1 and {2}=41000) then 1
        when ({3}=1 and {2}!=41000) then 2
        when ({3}=15) then 3
        when ({3}=4) then 4
        when ({3} in (5, 53,56,58)) then 5
        when ({3} in (3,6,7,8,9,10,17)) then 6
        when ({3} in (11,12,13,14,16)) then 7
        else 0
        end as s_fow,

        degrees(ST_azimuth( st_pointn({1}, 1), st_pointn({1}, 2))) as s_bear,
        st_length({1}, True) as dnp,
        st_x(st_endpoint({1})) as e_x, st_y(st_endpoint({1})) as e_y,

        case
        when ({4}=41000) then 0
        when ({4}=43000) then 1
        when ({4} in (42000, 44000)) then 2
        when ({4}=51000) then 3
        when ({4} in (45000, 52000)) then 4
        when ({4} in (47000, 53000)) then 5
        else 6
        end as e_frc,
        case
        when ({5}=1 and {4}=41000) then 1
        when ({5}=1 and {4}!=41000) then 2
        when ({5}=15) then 3
        when ({5}=4) then 4
        when ({5} in (5,53,56,58)) then 5
        when ({5} in (3,6,7,8,9,10,17)) then 6
        when ({5} in (11,12,13,14,16)) then 7
        else 0
        end as e_fow,

        degrees(ST_azimuth( st_pointn({1}, ST_NPOInTS({1})), st_pointn({1}, ST_NPOInTS({1})-1))) as e_bear
        from {10}.{0}
        where {6} = '{7}'
        and st_length({1}, True) <= {9}
        and {6} not in (select {6} from {10}.{8} group by {6})
        ;
        """.format(self.t_rid, self.f_geom, self.f_s_rc, self.f_s_fow, self.f_e_rc,
                   self.f_e_fow, self.f_rid, rid.strip(" "), self.t_point, self.max_len, self.schema)
        # print(sql_base_info)
        dct_rid_openlrs = self._points_2_encode_info(sql_base_info)
        # print(dct_rid_openlrs)
        sql_check_rela_point = """select count(1) as js from {3}.{0}
        where {1} = '{2}'
        ;""".format(self.t_point, self.f_rid, rid, self.schema)
        num_points = cursor(self.conn, sql_check_rela_point, ret=True)[0]['js']
        if num_points:
            dct_rid_openlrs[rid] = self._points_more_encode_info(rid)
        return dct_rid_openlrs

    def _points_more_encode_info(self, rid) -> None:

        sql_points = """select t3.*
        from (
        select 

        case
        when (t2.{9}=41000) then 0
        when (t2.{9}=43000) then 1
        when (t2.{9} in (42000, 44000)) then 2
        when (t2.{9}=51000) then 3
        when (t2.{9} in (45000, 52000)) then 4
        when (t2.{9} in (47000, 53000)) then 5
        else 6
        end as point_frc,
        case
        when (t2.{10}=1 and t2.{9}=41000) then 1
        when (t2.{10}=1 and t2.{9}!=41000) then 2
        when (t2.{10}=15) then 3
        when (t2.{10}=4) then 4
        when (t2.{10} in (5,53,56,58)) then 5
        when (t2.{10} in (3,6,7,8,9,10,17)) then 6
        when (t2.{10} in (11,12,13,14,16)) then 7
        else 0
        end as point_fow,

        ST_Line_Locate_Point(t1.{2}, t2.{2}) as offset,
        t1.{3} as rid, st_length(t1.geom, true) as line_len,

        st_x(st_startpoint(t1.{2})) as line_s_x, st_y(st_startpoint(t1.{2})) as line_s_y,

        case
        when (t1.{5}=41000) then 0
        when (t1.{5}=43000) then 1
        when (t1.{5} in (42000, 44000)) then 2
        when (t1.{5}=51000) then 3
        when (t1.{5} in (45000, 52000)) then 4
        when (t1.{5} in (47000, 53000)) then 5
        else 6
        end as line_s_frc,
        case
        when (t1.{6}=1 and t1.{5}=41000) then 1
        when (t1.{6}=1 and t1.{5}!=41000) then 2
        when (t1.{6}=15) then 3
        when (t1.{6}=4) then 4
        when (t1.{6} in (5, 53,56,58)) then 5
        when (t1.{6} in (3,6,7,8,9,10,17)) then 6
        when (t1.{6} in (11,12,13,14,16)) then 7
        else 0
        end as line_s_fow,

        degrees(ST_azimuth( st_startpoint(t1.{2}), st_pointn(t1.{2}, 2))) as line_s_bear,
        st_x(st_endpoint(t1.{2})) as line_e_x, st_y(st_endpoint(t1.{2})) as line_e_y,

        case
        when (t1.{7}=41000) then 0
        when (t1.{7}=43000) then 1
        when (t1.{7} in (42000, 44000)) then 2
        when (t1.{7}=51000) then 3
        when (t1.{7} in (45000, 52000)) then 4
        when (t1.{7} in (47000, 53000)) then 5
        else 6
        end as line_e_frc,
        case
        when (t1.{8}=1 and t1.{7}=41000) then 1
        when (t1.{8}=1 and t1.{7}!=41000) then 2
        when (t1.{8}=15) then 3
        when (t1.{8}=4) then 4
        when (t1.{8} in (5,53,56,58)) then 5
        when (t1.{8} in (3,6,7,8,9,10,17)) then 6
        when (t1.{8} in (11,12,13,14,16)) then 7
        else 0
        end as line_e_fow,

        degrees(ST_azimuth(st_endpoint(t1.{2}), st_pointn(t1.{2}, ST_NPOInTS(t1.{2})-1))) as line_e_bear

        from {11}.{0} t1, {11}.{1} t2
        where t1.{3} = '{4}' and t2.{3} = '{4}'
        ) t3 order by t3.offset
        ;""".format(self.t_rid, self.t_point, self.f_geom, self.f_rid, rid,
                    self.f_s_rc, self.f_s_fow, self.f_e_rc, self.f_e_fow, self.f_p_rc, self.f_p_fow, self.schema)
        # print(sql_points)

        row_points = cursor(self.conn, sql_points, ret=True)
        start_bs = 0
        end_bs = 0
        lst_points = []
        self.last_offset = 0
        for ii, row_point in enumerate(row_points):
            # print(row_point)
            p_frc, p_fow, p_offset, l_rid, l_len, \
            l_lon_s, l_lat_s, l_frc_s, l_fow_s, l_bear_s, l_lon_e, \
            l_lat_e, l_frc_e, l_fow_e, l_bear_e = row_point

            if start_bs == 0:
                point = Points_Info()
                point.properties["lon"] = l_lon_s
                point.properties["lat"] = l_lat_s
                point.properties["frc"] = l_frc_s
                point.properties["fow"] = l_fow_s
                point.properties["lfnp"] = l_frc_s + 3 if l_frc_s <= 4 else 7
                point.properties["bear"] = l_bear_s if l_bear_s != 0 else 0.01
                point.properties["dnp"] = p_offset * l_len
                point.properties["seq"] = ii + 1
                lst_points.append(point.properties)
                start_bs = 1

            if start_bs == 0 or end_bs == 0:
                # rela points
                sql_sub_point = """select st_x(st_pointn(t1.geom, st_npoints(t1.geom)-1)),
                st_y(st_pointn(t1.geom, st_npoints(t1.geom)-1)),
                degrees(ST_azimuth(st_pointn(t1.geom, st_npoints(t1.geom)-1), st_endpoint(t1.geom))) as p_bear
                from (
                select st_line_substring({1}, 0, {2}) as geom
                from {5}.{0} where {3}='{4}') t1
                """.format(self.t_rid, self.f_geom, p_offset, self.f_rid, l_rid, self.schema)
                # print(sql_sub_point)
                p_lon, p_lat, p_bear = cursor(self.conn, sql_sub_point, ret=True)[0]
                if ii + 1 <= len(row_points) - 1:
                    p_next_offset = row_points[ii + 1]["offset"]
                else:
                    p_next_offset = 1

                point = Points_Info()
                point.properties["lon"] = p_lon
                point.properties["lat"] = p_lat
                point.properties["frc"] = p_frc
                point.properties["fow"] = p_fow
                point.properties["lfnp"] = p_frc + 3 if p_frc <= 4 else 7
                point.properties["bear"] = p_bear if p_bear != 0 else 0.01
                point.properties["dnp"] = (p_next_offset - p_offset) * l_len
                point.properties["seq"] = ii + 1 + 1
                lst_points.append(point.properties)

            if ii == len(row_points) - 1 and end_bs == 0:
                # start end point
                point = Points_Info()
                point.properties["lon"] = l_lon_e
                point.properties["lat"] = l_lat_e
                point.properties["frc"] = l_frc_e
                point.properties["fow"] = l_fow_e
                point.properties["lfnp"] = 7
                point.properties["bear"] = l_bear_e if l_bear_e != 0 else 0.01
                point.properties["dnp"] = 0
                point.properties["seq"] = ii + 2 + 1
                lst_points.append(point.properties)
                end_bs = 1

        # print(lst_points)
        dct_openlr_info = OrderedDict({"location_type": 1,
                                       "version": 3,
                                       "points": lst_points,
                                       "poff_bs": 0,
                                       "noff_bs": 0,
                                       "poff": 0,
                                       "noff": 0
                                       })
        if self.is_out_info:
            print(dct_openlr_info)
        self.is_out_info = 0

        obj_openlr = Get_Info2Openlr(dct_openlr_info)
        openlr_code = obj_openlr.openlr_info()

        return openlr_code

    def _points_2_encode_info(self, sql_base_info) -> None:
        "read rid and then write openlr"
        print(sql_base_info)
        rows_base_info = cursor(self.conn, sql_base_info, ret=True)

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
            if self.is_out_info:
                print(dct_openlr_info)
            self.is_out_info = 0

            obj_openlr = Get_Info2Openlr(dct_openlr_info)
            openlr_code = obj_openlr.openlr_info()
            # print('openlr_code:',openlr_code)
            dct_temp_rid_openlr[rid] = openlr_code

        return dct_temp_rid_openlr

def ridSingle(f_json, single_rid,schema):
    read_json = open(f_json, 'r', encoding='utf8')
    json_info = json.loads(read_json.read())
    read_json.close()
    db_info, input_info = json_info['dbinfo'], json_info['input_rid_tab']

    conn = db_conn_dict(db_info)
    rid_info = Rid2Openlr(conn, input_info,schema)
    # # convert single rid 2 openlr, input rid code
    return rid_info.convert_single(single_rid, is_print=False)


def main():
    f_json = './config.json'

    single_rid = "13H3Q0C5QA013H4G0C5QA00"
    schema = 'public'
    dct_temp_rid_openlr = ridSingle(f_json, single_rid,schema)
    if len(dct_temp_rid_openlr) > 0:
        print(dct_temp_rid_openlr)
    else:
        print('匹配过程中,rid无转化成openlr,考虑是否rid长度过长,尝试在location_points增加途径点,再进行匹配')
    print('Over')


if __name__ == "__main__":
    main()
