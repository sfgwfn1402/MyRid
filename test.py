from PyQt5.QtCore import PYQT_VERSION_STR, QDir, QFile
from qgis._core import QgsGeometry, QgsPoint, QgsPointXY
from shapely import MultiLineString,LineString
from shapely.ops import linemerge
import numpy as np
from shapely.geometry import mapping,shape
import json
from pyproj import Proj,transform
import os,time
from qgis.core import (QgsApplication, QgsMessageLog, QgsTask)


def worker(num):
    """线程执行的函数"""
    print('Worker: %s' % num)
    return

class MyTask(QgsTask):
    def __init__(self, description, flags):
        super().__init__(description, flags)

    def run(self):
        QgsMessageLog.logMessage('Started task {}'.format(self.description()))

        print('Worker: %s' % time.strftime("%Y%m%d%H%M", time.localtime()))
        return True

if __name__ == '__main__':
    #first_road='{"type":"LineString","coordinates":[[116.1150922,40.0661437],[116.1129144,40.0660424],[116.112936793,40.065951883]]}'
    #next_road='{"type":"LineString","coordinates":[[116.11765555,40.0664222],[116.1175819,40.0664188],[116.1155873,40.0663265]]}'
    #new_line=linemerge([shape(json.loads(first_road)), shape(json.loads(next_road))])
    #print(new_line)
    #if type(new_line) is MultiLineString:
    #   outcoords = [list(i.coords) for i in np.array(new_line.geoms)]
    #    print(outcoords)
    #    new_line = LineString([i for sublist in outcoords for i in sublist])
    #print(new_line)


    #geometry = QgsGeometry.fromWkt(

    #'LineString (116.68332170000000758 40.11661399999999844, 116.68342789999998388 40.11653979999999819, 116.68410170000001358 40.11606929999999238)')
    #split_line = [QgsPointXY(116.68339091418484088,40.11656123799151175), QgsPointXY(116.68339298152201877,40.11656419690268649)]

    #geometry = QgsGeometry.fromWkt(
    #       'LineString (2749546.2003820720128715 1262904.45356595050543547, 2749557.82053794478997588 1262920.05570670193992555)')
    #split_line = [QgsPointXY(2749544.19, 1262914.79), QgsPointXY(2749557.64, 1262897.30)]

    #result, new_geometries, point_xy = geometry.splitGeometry(split_line, True,False)
    #print(geometry.asWkt())
    #print(int(result))
    #print(new_geometries)

    task1 = QgsTask.fromFunction("dostuff", worker)
    QgsApplication.taskManager().addTask(task1)  # kills QGIS

