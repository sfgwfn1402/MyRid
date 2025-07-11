import json

with open('D:\mapdata\mengzi_geojson\hd_202_cdm.geojson','r') as fjson:
    cneter_line_data={'type': 'FeatureCollection','name': '车道中心线','crs': { 'type': 'name', 'properties': { 'name': 'urn:ogc:def:crs:OGC:1.3:CRS84' } },'features':[]}
    data=fjson.read()
    geojson_data=json.loads(data)
    new_features = []
    features=geojson_data['features']
    for feature in features:
        cdzxx_data=feature['properties']
        # print(cdzxx_data['centerLine'])
        cdzxx_geom=json.loads(str(cdzxx_data['centerLine']).replace('\'','\"'))
        #print(cdzxx_geom)
        cdzxx_geom['type']='Feature'
        cdzxx_geom['properties']={'cdid':cdzxx_data['cdid'],'ldid':cdzxx_data['ldid'],'qhdid':cdzxx_data['qhdid'],'cdsxh':cdzxx_data['cdsxh'],'cdlb':cdzxx_data['cdlb'],'cdgn':cdzxx_data['cdgn'],'cdfx':cdzxx_data['cdfx'],'cdgs':cdzxx_data['cdgs'],'cdcd':cdzxx_data['cdcd'],'cdkd':cdzxx_data['cdkd'],'sycdlb':cdzxx_data['sycdlb']}
        coordinates=[]
        for geom in cdzxx_geom['geometry']:
            coordinates.append([geom['lng'],geom['lat'],geom['alt']])
            #print(geom)
        # { "type": "Polygon", "coordinates": [ [ [ 103.377246223390102, 23.369768221846698, 1268.12890625 ], [ 103.377290144562721, 23.369747139501968, 1268.1796875 ], [ 103.377288468182087, 23.36974360012989, 1268.21875 ], [ 103.377244547009468, 23.369764528589478, 1268.12890625 ], [ 103.377246223390102, 23.369768221846698, 1268.12890625 ] ] ] } }
        #print(coordinates)
        cdzxx_geom['geometry']={'type': 'LineString', 'coordinates':coordinates}
        new_features.append(cdzxx_geom)

    cneter_line_data['features']=new_features
    with open('D:\mapdata\mengzi_geojson\hd_201_cdzxx.geojson', 'w') as wjson:
        wjson.write(json.dumps(cneter_line_data))
