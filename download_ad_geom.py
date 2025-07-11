import pymysql
import os,datetime,json,requests

dct_dbinfo = {
    'user': 'root',
    'pw': 'Wanji300552',
    'host': '10.102.1.182',
    'port': '3306',
    'db': 'wjdp_dev_db_v1.1.0'
}

def data_folder():
    return os.path.dirname(os.path.abspath(__file__)) + "\\data\\"

def download_geojson():

    conn = pymysql.connect(host=dct_dbinfo['host'],
                             user=dct_dbinfo['user'],
                             password=dct_dbinfo['pw'],
                             database=dct_dbinfo['db'],
                             cursorclass=pymysql.cursors.DictCursor)

    query_sql = """
            SELECT * FROM {0};
    """.format("gis_bd_adcode")

    with conn.cursor() as cursor:
        cursor.execute(query_sql)
        rows =cursor.fetchall()
        print('query numbers: '+str(len(rows)))
        for r in rows:
            print(str(r['S_AD_CODE'])+' '+str(r['S_AD_NAME']))
            try:
                geojson=requests.get('https://geo.datav.aliyun.com/areas_v3/bound/geojson?code='+str(r['S_AD_CODE']))
                print(geojson.text)
                f=open(data_folder()+str(r['S_AD_CODE'])+".json","w")
                f.write(json.dumps(json.loads(geojson.text)['features'][0]['geometry']))
                f.close()
            except Exception as e:
                print('Exception in requests geojson', e)

def restore_geojson():
    conn = pymysql.connect(host=dct_dbinfo['host'],
                           user=dct_dbinfo['user'],
                           password=dct_dbinfo['pw'],
                           database=dct_dbinfo['db'],
                           cursorclass=pymysql.cursors.DictCursor)

    lst_json=os.listdir(data_folder())
    with conn.cursor() as cursor:
        for j in lst_json:
            print(j)
            f = open(data_folder() + j, "r")
            geojson=f.read()
            if len(geojson)>0:
                print(json.loads(geojson))
                try:
                    update_sql = """
                            UPDATE {0} SET S_GEOM='{1}' where S_AD_CODE='{2}';
                      """.format("gis_bd_adcode",json.dumps(json.loads(geojson)),j.replace('.json',''))
                    cursor.execute(update_sql)
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    print('Exception in restore geojson', e)

    conn.close()


if __name__ == '__main__':
    restore_geojson()