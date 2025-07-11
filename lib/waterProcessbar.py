import sys
from PyQt5.QtWidgets import QWidget,QApplication
from PyQt5.QtCore import QThread, pyqtSignal
from .WaterRippleProgressBar import WaterRippleProgressBar
from qgis.PyQt import QtCore
from ..src.road2rid import road2rid
from PyQt5.QtWidgets import QMessageBox
from .common import parseConfig


class ConvertTimer(QWidget):
    def __init__(self, conn,project):
        super(ConvertTimer, self).__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowSystemMenuHint)
        self.progressbar = WaterRippleProgressBar(self)
        self.progressbar.setMinimumSize(200, 100)
        self.progressbar.setMaximumSize(200, 100)
        # self.progressbar.setStyleType(0)
        self.step = 0
        self.progressbar_init()
        # self.crawl_thread = CrawlThread()
        self.crawl_thread = CrawlThread(conn,project)
        self.crawl_thread.start()
        self.crawl_init()

    def progressbar_init(self):
        self.progressbar.setRange(0, 100)
        self.progressbar.setValue(0)

    def set_probar_slot(self,val):
        self.step += val
        if self.step >= 100:
            self.step = 100
        self.progressbar.setValue(int(self.step))
        if self.progressbar.value() == 100:
            # print('finished')
            self.crawl_thread.terminate()
            print(QMessageBox.warning(self, '提示', '任务完成！'))
            self.close()

    def crawl_init(self):
        self.crawl_thread.result_signal.connect(self.set_probar_slot)



class CrawlThread(QThread):
    result_signal = pyqtSignal(float)

    def __init__(self,conn,project):
        super(CrawlThread, self).__init__()
        self.conn = conn
        self.project=project

    def run(self):
        try:
            parDict = parseConfig()
            schema = parDict.get('schema')
            tab_nodes = parDict.get('tab_nodes')
            tab_segment = parDict.get('tab_segment')
            tab_rid = parDict.get('tab_rid')
            tab_cross = parDict.get('tab_cross')
            tab_lane = parDict.get('tab_lane')
            tab_axf = parDict.get('tab_axf')
            road2rid(self.conn,self.project, schema, tab_nodes, tab_segment, tab_rid, tab_cross,tab_lane,tab_axf, self.result_signal)
        except Exception as e:
            # self.log_signal.emit(str(e))
            pass

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ConvertTimer()
    window.show()
    sys.exit(app.exec_())

