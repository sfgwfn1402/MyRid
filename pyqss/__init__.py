# -*- coding: utf-8 -*-
# @Time    : 2019/3/22 9:53
# @Author  : llc
# @File    : __init__.py
import os,json
from collections import OrderedDict

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QEnterEvent
from PyQt5.QtWidgets import QFileDialog, \
    QShortcut, QMainWindow,QMessageBox

from .tr import init_language
from .widgets.find_replace import FRWidget
from .widgets.main import QssWindow


class Qss(QssWindow):
    def __init__(self, info,json_file,json_file_bak,custom_widget=None,language='zh'):
        super(Qss, self).__init__()
        self.custom_widget = custom_widget
        # 初始化语言
        self.tr = init_language(language)
        # 设置窗口大小
        self.resize(800, 800)
        self.title = self.tr("JSON_Editor")
        self.setWindowTitle(self.title)

        self.json_file = json_file
        self.json_file_bak = json_file_bak
        self.json_name = 'unknown'

        self.btn_open.setText(self.tr('open'))
        self.btn_save.setText(self.tr('save'))
        self.btn_format.setText(self.tr('format'))
        self.btn_default.setText(self.tr('default'))
        # 添加api
        self.editor.add_apis(self.custom_widget)

        # 获取焦点
        self.editor.setFocus()
        self.editor.installEventFilter(self)

        #获取配置
        self.editor.clear()
        self.editor.append(info)
        # 快捷键
        shortcut_save = QShortcut(QKeySequence.Save, self)
        shortcut_save.activated.connect(self.shortcut_save_activated)
        QShortcut(QKeySequence("Ctrl+F"), self, self.find_replace)
        QShortcut(QKeySequence("Ctrl+H"), self, self.btn_format_clicked)
        QShortcut(QKeySequence("Esc"), self, lambda: self.fr_widget.hide())

        # 信号和槽
        self.btn_open.clicked.connect(self.btn_open_clicked)
        self.btn_save.clicked.connect(self.btn_save_clicked)
        self.btn_format.clicked.connect(self.btn_format_clicked)
        self.btn_default.clicked.connect(self.btn_default_clicked)
        self.btn_attach.clicked.connect(self.btn_attach_clicked)
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_close.clicked.connect(self.close)

        if custom_widget is not None:
            self.editor.textChanged.connect(self.editor_text_changed)
        self.editor.opened.connect(self.open_json)

        # 加载样式
        with open(os.path.join(os.path.dirname(__file__), 'qss/default.qss'), 'r') as f:
            self.setStyleSheet(f.read())

        # 初始化查找替换
        self.fr_widget = None
        self.init_fr_widget()

    def init_fr_widget(self):
        self.fr_widget = FRWidget(parent=self)
        self.fr_widget.hide()
        self.fr_widget.setGeometry(50, 50, self.width() - 100, 40)
        self.fr_widget.le_find.textChanged.connect(self.le_find_text_changed)
        self.fr_widget.btn_pre.clicked.connect(lambda: self.find_text(forward=False))
        self.fr_widget.btn_next.clicked.connect(lambda: self.find_text(forward=True))
        self.fr_widget.btn_replace.clicked.connect(self.btn_replace_clicked)
        self.fr_widget.btn_replace_all.clicked.connect(self.btn_replace_all_clicked)
        self.resized.connect(self.resize_fr)

    def resize_fr(self):
        self.fr_widget.setGeometry(50, 50, self.width() - 100, 40)

    def find_replace(self):
        if self.fr_widget.isHidden():
            self.fr_widget.show()
            self.fr_widget.le_find.setFocus()
            self.le_find_text_changed(self.fr_widget.le_find.text())
        else:
            self.fr_widget.hide()
            self.editor.cancelFind()

    def editor_text_changed(self):
        text = self.editor.text()
        # self.setStyleSheet(text)
        self.label_title.setText(self.title + "-" + self.json_name + '*')
        # if hasattr(self.custom_widget, 'setStyleSheet'):
        #     self.custom_widget.setStyleSheet(text)
        if hasattr(self.custom_widget.textEdit,'setPlainText'):
            self.custom_widget.textEdit.setPlainText(text)

    def btn_open_clicked(self):
        # qss_file, ext = QFileDialog.getOpenFileName(self, '打开qss', '', '*.qss')
        json_file, ext = QFileDialog.getOpenFileName(self, '打开json', '', '*.json')
        if json_file:
            self.open_json(json_file)

    def open_json(self, json_file):
        with open(json_file,mode='r') as f:
            self.editor.clear()
            json_data = json.load(f,object_pairs_hook=OrderedDict)
            strText = json.dumps(json_data, indent=2, ensure_ascii=False)
            self.editor.append(strText)
        self.json_file = json_file
        self.json_name = str(os.path.basename(json_file).split('.')[0])
        print(self.json_name)
        self.label_title.setText(self.title + ':' + self.json_name)

    def btn_save_clicked(self):
        if self.json_file:
            self.shortcut_save_activated()
            return
        json_file, ext = QFileDialog.getSaveFileName(self, '保存json', self.json_name, '*.json')
        if json_file:
            with open(json_file, 'w', encoding='utf8') as f:
                f.write(self.editor.text())
            self.json_file = json_file
            self.json_name = str(os.path.basename(json_file).split('.')[0])
            self.label_title.setText(self.title + '-' + str(os.path.basename(json_file).split('.')[0]))
            return True
        return False

    def btn_format_clicked(self):
        try:
            text_dct = json.loads(self.editor.text())
            format_text= json.dumps(text_dct,indent=2,ensure_ascii=False)
            if format_text:
                self.editor.clear()
                self.editor.append(format_text)
        except Exception as e:
            # print(str(e))
            QMessageBox.information(self, '错误提示:', '不是标准json文本,不能被格式化!\n\t%s'%str(e))
            # raise e

    def btn_default_clicked(self):
        if self.json_file_bak:
            with open(self.json_file_bak,mode='r') as f:
                self.editor.clear()
                json_data = json.load(f,object_pairs_hook=OrderedDict)
                strText = json.dumps(json_data, indent=2, ensure_ascii=False)
                self.editor.append(strText)
            # self.json_file = self.json_file_bak
            self.json_name = str(os.path.basename(self.json_file).split('.')[0])
            # print(self.json_name)
            self.label_title.setText(self.title + ':' + self.json_name)
        else:
            QMessageBox.information(self, '错误提示:', '没有config_original.json')


    def shortcut_save_activated(self):
        if not self.json_file:
            if self.btn_save_clicked():
                self.label_title.setText(self.label_title.text().strip('*'))
        else:
            with open(self.json_file, 'w') as f:
                f.write(self.editor.text())
            self.label_title.setText(self.label_title.text().strip('*'))

    def le_find_text_changed(self, text):
        self.editor.findFirst(text, True, False, True, True)

    def find_text(self, forward):
        text_to_find = self.fr_widget.le_find.text()

        c_line, c_index = self.editor.getCursorPosition()
        line_from, index_from, line_to, index_to = self.editor.getSelection()

        if forward:
            line = line_to
            index = index_to
        else:
            if (line_from, index_from) == (-1, -1):
                line = c_line
                index = c_index
            else:
                line = line_from
                index = index_from

        return self.editor.findFirst(text_to_find, False, False, False, True, forward, line, index)

    def btn_replace_clicked(self):
        if self.editor.hasSelectedText():
            row1, line1, row2, line2 = self.editor.getSelection()
            self.editor.setCursorPosition(row1, line1)
        self.find_text(True)
        self.editor.replace(self.fr_widget.le_replace.text())
        return True

    def btn_replace_all_clicked(self):
        self.editor.beginUndoAction()
        text = self.editor.text()
        n = text.count(self.fr_widget.le_find.text(), False)
        for i in range(n):
            self.find_text(True)
            self.editor.replace(self.fr_widget.le_replace.text())
        self.editor.endUndoAction()

    def btn_attach_clicked(self, is_checked):
        if is_checked:
            self.move_custom_widget()

    def moveEvent(self, event):
        super(Qss, self).moveEvent(event)
        if self.btn_attach.isChecked():
            self.move_custom_widget()

    def move_custom_widget(self):
        if hasattr(self.custom_widget, "setGeometry"):
            if self.custom_widget.isMaximized() or self.custom_widget.isFullScreen():
                return
            self.custom_widget.setGeometry(self.x() - self.custom_widget.width() - 3,
                                           self.y(),
                                           self.custom_widget.width(),
                                           self.custom_widget.height())

    def eventFilter(self, obj, event):
        if obj.objectName() == 'editor' and isinstance(event, QEnterEvent):
            self.setCursor(Qt.ArrowCursor)

        return QMainWindow.eventFilter(self, obj, event)

    def closeEvent(self, event):
        if self.json_file:
            self.shortcut_save_activated()
        super(Qss, self).closeEvent(event)


# if __name__ == '__main__':
#     import sys
#     from PyQt5.QtWidgets import QApplication
#     from pyqss import Qss
#
#     QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
#     app = QApplication(sys.argv)
#     qss = Qss()
#     qss.editor.add_apis(qss)
#     qss.show()
#     app.exec_()
