import json,os
from collections import OrderedDict
from .dbconn import db_conn

def parseConfig():
    # f_json = (os.path.join(os.path.abspath(os.path.join(os.getcwd(), "..")),'config/config.json'))
    f_json = os.path.dirname(os.path.dirname(__file__)) +  '/config/config.json'
    fr = open(f_json, 'r', encoding='utf-8')
    json_info = json.loads(fr.read(),
                                object_pairs_hook=OrderedDict)

    db_info= json_info['dbinfo']
    par_info = json_info['my_config']

    dct_dbinfo = {
        'user': db_info['user'],
        'pw': db_info['pw'],
        'host': db_info['host'],
        'port': int(db_info['port']),
        'dbname': db_info['dbname']
    }
    conn = db_conn(dct_dbinfo['host'], dct_dbinfo['port'], dct_dbinfo['user'],
                   dct_dbinfo['pw'], dct_dbinfo['dbname'])

    dct_par={
        'min_score': float(par_info['min_score']),
        'search_radius': int(par_info['search_radius']),
        'max_dnp_deviation': float(par_info['max_dnp_deviation']),
        'max_bear_deviation': int(par_info['max_bear_deviation']),
        'fow_weight': float(par_info['fow_weight']),
        'frc_weight': float(par_info['frc_weight']),
        'geo_weight': float(par_info['geo_weight']),
        'bear_weight': float(par_info['bear_weight']),
        'bear_dist': int(par_info['bear_dist']),
        'tolerated_dnp_dev': int(par_info['tolerated_dnp_dev'])
    }
    schema = json_info['schema']
    tab_nodes = json_info['tab_nodes']
    tab_segment = json_info['tab_segment']
    tab_link=json_info['tab_link']
    tab_rid = json_info['tab_rid']
    tab_cross = json_info['tab_cross']
    tab_lane = json_info['tab_lane']
    tab_axf = json_info['tab_axf']

    tab_openlr_nodes= json_info['tab_openlr_nodes']
    tab_openlr_lines= json_info['tab_openlr_lines']
    tab_output= json_info['tab_output']
    tab_match= json_info['tab_match']
    ad_code = json_info['ad_code']
    fr.close()
    return {
            'schema': schema,
            'tab_nodes': tab_nodes,
            'tab_segment': tab_segment,
            'tab_link':tab_link,
            'tab_rid': tab_rid,
            'tab_cross': tab_cross,
            'tab_lane': tab_lane,
            'tab_axf': tab_axf,
            'tab_openlr_lines': tab_openlr_lines,
            'tab_openlr_nodes': tab_openlr_nodes,
            'tab_output': tab_output,
            'tab_match':tab_match,
            'par':dct_par,
            'ad_code':ad_code,
            'db_info':dct_dbinfo,
            'conn':conn
            }

def getCrossFieldsInfo():
    # f_json = (os.path.join(os.path.abspath(os.path.join(os.getcwd(), "..")),'config/config.json'))
    f_json = os.path.dirname(os.path.dirname(__file__)) +  '/config/config_cross.json'
    fr = open(f_json, 'r', encoding='utf-8')
    json_info = json.loads(fr.read(),
                                object_pairs_hook=OrderedDict)

    cross_fields_info= json_info['tab_cross']['fields']
    # field_lst = []
    # for field_name, attr_value in cross_fields_info.items():
    #     field_lst.append(field_name)
    #
    # interleveltype = cross_fields_info.get('interleveltype').get('value')
    # field_all_values = list(interleveltype.keys())
    #
    # print(field_all_values)
    fr.close()
    return cross_fields_info

def getRidFieldsInfo():
    # f_json = (os.path.join(os.path.abspath(os.path.join(os.getcwd(), "..")),'config/config.json'))
    f_json = os.path.dirname(os.path.dirname(__file__)) +  '/config/config_rid.json'
    fr = open(f_json, 'r', encoding='utf-8')
    json_info = json.loads(fr.read(),
                                object_pairs_hook=OrderedDict)
    # print(f_json)
    ld_fields_info= json_info['tab_rid']['fields']

    fr.close()
    return ld_fields_info



if __name__ == '__main__':
    getCrossFieldsInfo()

