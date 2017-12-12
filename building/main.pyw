# -*- coding: utf-8 -*-
import os
import smtplib
import urllib.request
import images
import re
from datetime import datetime
from PyQt4 import QtGui, QtCore
from subprocess import call


class LogFileDialog(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowIcon(QtGui.QIcon(':/images/log.png'))
        self.resize(500, 500)
        self.setWindowTitle('Просмотр LOG файла')
        self.show()


class MyThread(QtCore.QThread):

    def __init__(self, parent=None):
        QtCore.QThread.__init__(self, parent)

    def run(self):
        self.etrust_check1(main.urletrust)
        self.crl_check1(main.cdp1)
        self.crl_check1(main.cdp2)
        self.crl_check1(main.cdp3)
        self.crl_check1(main.cdp4)
        self.ocsp_check1(main.ocsp_ra)
        self.ocsp_check1(main.ocsp_ra2)
        self.tsp_check1(main.tsp)


    def crl_check1(self, cdp):
        crl_filename = 'crls/' + cdp.rpartition('/')[2]
        text_to_log = 'Начинаю проверку СОС. CDP = ' + cdp + '\n'
        self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)
        try:
            crl = urllib.request.urlopen(cdp)
            crl = crl.read()
            if crl != 0:
                crl_out = open(crl_filename, 'wb')
                crl_out.write(crl)
                crl_out.close()
                self.emit(QtCore.SIGNAL("setCRLgreen(QString)"), cdp)
                text_to_log = 'Качнул не битый СОС с адреса: '+ cdp +' Размер файла: ' + os.path.getsize(crl_out) + '\n'
                self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)
            else:
                self.emit(QtCore.SIGNAL("setCRLred(QString)"), cdp)
                self.emit(QtCore.SIGNAL('error(QString, QString)'), main.error_notfound, cdp)
                text_to_log = 'СОС с адреса: ' + cdp + ' нулевой длины.\n'
                self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)
        except:
            self.emit(QtCore.SIGNAL("setCRLred(QString)"), cdp)

        #os.system('c:\windows\system32\certutil.exe ' + crl_filename + ' > ' + crl_filename + '.txt')
        cmd = 'c:\windows\system32\certutil.exe ' + crl_filename + ' > ' + crl_filename + '.txt'
        s = call(cmd, shell=True)
        with open(crl_filename + '.txt') as f:
            for line in f:
                if (line.partition('NextUpdate: ')[1]) != '':
                    next_crl_update = (line.partition('NextUpdate: ')[2])[:-1]
                    self.emit(QtCore.SIGNAL('setDATAcrl(QString, QString)'), next_crl_update, cdp)

        delta = datetime.strptime(next_crl_update, "%d.%m.%Y %H:%M") - datetime.now()

        if delta.days > 0:
            self.emit(QtCore.SIGNAL("setCRLgreen(QString)"), cdp)
            text_to_log = 'СОС с адреса: ' + cdp + ' действующий.\n'
            self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)
        elif delta.days < 0:
            self.emit(QtCore.SIGNAL("setCRLred(QString)"), cdp)
            self.emit(QtCore.SIGNAL('error(QString, QString)'), main.error_hasexpired, cdp)
            text_to_log = 'СОС с адреса: ' + cdp + ' НЕ ДЕЙСТВУЮЩИЙ.\n'
            self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)
        elif delta.days == 0 and 0 < delta.seconds < 86400:
            text_to_log = 'СОС с адреса: ' + cdp + ' скоро заканчивается.\n'
            self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)
            self.emit(QtCore.SIGNAL("setCRLyellow(QString)"), cdp)

    def ocsp_check1(self, ocsp):
        text_to_log = 'Начинаю проверку OCSP расположенного по адресу: ' + ocsp +'\n'
        self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)
        s = call("ocsputil.exe sendreq --url=" + ocsp + " ra.orq ra.ors", shell=True)
        if s == 0:
            self.emit(QtCore.SIGNAL("setOCSPgreen(QString)"), ocsp)
            text_to_log = 'OCSP расположенная по адресу: ' + ocsp + ' отвечает на запросы.\n'
            self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)
        else:
            self.emit(QtCore.SIGNAL("setOCSPred(QString)"), ocsp)
            self.emit(QtCore.SIGNAL('error(QString, QString)'), main.error_ocspoffline, ocsp)
            text_to_log = 'OCSP расположенная по адресу: ' + ocsp + ' не доступна. Возможно служба отключена.\n'
            self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)

    def tsp_check1(self, tsp):
        text_to_log = 'Начинаю проверку TSP расположенного по адресу: ' + tsp + '\n'
        self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)
        s = call("tsputil.exe sendreq --url="+tsp+" request.tsq stamp.tsr", shell=True)
        if s == 0:
            self.emit(QtCore.SIGNAL("setTSPgreen()"))
            text_to_log = 'TSP расположенная по адресу: ' + tsp + ' отвечает на запросы. \n'
            self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)
        else:
            self.emit(QtCore.SIGNAL("setTSPred()"))
            self.emit(QtCore.SIGNAL('error(QString, QString)'), main.error_tspoffline, tsp)
            text_to_log = 'TSP расположенная по адресу: ' + tsp + ' не доступна. Возможно служба отключена.\n'
            self.emit(QtCore.SIGNAL('writeTOlog(QString)'), text_to_log)

    def etrust_check1(self, url):
        html = urllib.request.urlopen(url)
        text = html.read().decode('utf-8')
        p = re.compile('<td>[0-9]{1,3}%<\/td>')
        finddata = re.findall(p, text)
        for i in range(3):
            finddata[i] = finddata[i].replace('<td>', '')
            finddata[i] = finddata[i].replace('</td>', '')
        text = 'Сутки: '+finddata[0]+' Неделя: '+finddata[1]+' Месяц: '+finddata[2]
        self.emit(QtCore.SIGNAL('etrust(QString)'), text)
        self.emit(QtCore.SIGNAL('writeTOlog(QString)'), 'Доступность СОС по данным e-trust. '+text+'\n')

class MainWindow(QtGui.QMainWindow):

    def __init__(self):
        self.urletrust = 'https://goo.gl/zijbr3'
        self.cdp1 = "http://uc.e-portal.ru/certenroll/e-portal_2016.crl"
        self.cdp2 = "http://uc2.e-portal.ru/certenroll/e-portal_2016.crl"
        self.cdp3 = "http://uc.e-portal.ru/certenroll/e-portal_2017.crl"
        self.cdp4 = "http://uc2.e-portal.ru/certenroll/e-portal_2017.crl"
        self.ocsp_ra = "http://ra.e-portal.ru/ocsp/ocsp.srf"
        self.ocsp_ra2 = "http://ra2.e-portal.ru/ocsp/ocsp.srf"
        self.tsp = "http://tsp.e-portal.ru/tsp/tsp.srf"
        self.l1 = 'Дата последней проверки: '
        self.l2 = 'CDP1 Дата истечения CRL: '
        self.l3 = 'CDP1 Дата истечения CRL: '
        self.timer_value = 10

        self.error_notfound = '0x000404'
        self.error_hasexpired = '0x000001'
        self.error_ocspoffline = '0x000002'
        self.error_tspoffline = '0x000003'

        QtGui.QMainWindow.__init__(self)

        self.setWindowIcon(QtGui.QIcon(':/images/icon.png'))
        self.resize(600, 300)
        self.setWindowTitle('CA Control by XOMRKOB')

        self.exit = QtGui.QAction(QtGui.QIcon(':/images/exit.png'), 'Выход', self)
        self.exit.setShortcut('F10')
        self.exit.setStatusTip('Закрыть приложение')
        self.connect(self.exit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))

        self.check = QtGui.QAction(QtGui.QIcon(':/images/check.png'), 'Проверить', self)
        self.check.setShortcut('F5')
        self.check.setStatusTip('Проверить')
        self.connect(self.check, QtCore.SIGNAL('triggered()'), self.on_auto)

        self.auto = QtGui.QAction(QtGui.QIcon(':/images/start.png'), 'Включить таймер', self)
        self.auto.setShortcut('F6')
        self.auto.setStatusTip('Включить проверку по таймеру')
        self.connect(self.auto, QtCore.SIGNAL('triggered()'), self.timer_on)

        self.stop = QtGui.QAction(QtGui.QIcon(':/images/stop.png'), 'Выключить таймер', self)
        self.stop.setShortcut('F7')
        self.stop.setStatusTip('Выключить проверку по таймеру')
        self.stop.setDisabled(True)
        self.connect(self.stop, QtCore.SIGNAL('triggered()'), self.timer_off)

        self.settings = QtGui.QAction(QtGui.QIcon(':/images/settings.png'), 'Настройки таймера', self)
        self.settings.setShortcut('F8')
        self.settings.setStatusTip('Настройки таймера')
        self.connect(self.settings, QtCore.SIGNAL('triggered()'), self.open_settings)

        self.about_me = QtGui.QAction(QtGui.QIcon(':/images/icon.png'), 'О программе', self)
        self.about_me.setShortcut('F11')
        self.about_me.setStatusTip('О программе')
        self.connect(self.about_me, QtCore.SIGNAL('triggered()'), self.open_about_me)

        self.about_qt = QtGui.QAction(QtGui.QIcon(':/images/qt.png'), 'О Qt', self)
        self.about_qt.setShortcut('F12')
        self.about_qt.setStatusTip('О Qt')
        self.connect(self.about_qt, QtCore.SIGNAL('triggered()'), self.open_about_qt)

        self.open_logfile = QtGui.QAction(QtGui.QIcon(':/images/log.png'), 'Открыть log файл', self)
        self.open_logfile.setShortcut('F2')
        self.open_logfile.setStatusTip('Открыть log файл')
        self.connect(self.open_logfile, QtCore.SIGNAL('triggered()'), self.open_log)

        self.label_etrust = QtGui.QLabel('...')
        self.label_etrust_header = QtGui.QLabel('Доступность по данным e-trust')

        self.statusBar().showMessage('Готов к труду и обороне')

        self.menubar = self.menuBar()
        self.file = self.menubar.addMenu('&Файл')
        self.file.addAction(self.exit)

        self.func = self.menubar.addMenu('&Действия')
        self.func.addAction(self.check)
        self.func.addAction(self.auto)
        self.func.addAction(self.stop)

        self.set = self.menubar.addMenu('&Настройки')
        self.set.addAction(self.settings)

        self.help = self.menubar.addMenu('&Помощь')
        self.help.addAction(self.open_logfile)
        self.help.addAction(self.about_me)
        self.help.addAction(self.about_qt)


        self.toolbar = self.addToolBar('Основная панель')
        self.toolbar.addAction(self.exit)
        self.toolbar.addAction(self.check)
        self.toolbar.addAction(self.auto)
        self.toolbar.addAction(self.stop)
        self.toolbar.addAction(self.settings)
        self.toolbar.addAction(self.open_logfile)

        self.widget = QtGui.QWidget()
        self.setCentralWidget(self.widget)

        hbox = QtGui.QHBoxLayout()              # Основная горизонтальная сетка
        vbox1 = QtGui.QVBoxLayout()             # Вертикалка
        vbox2 = QtGui.QVBoxLayout()
        hbox1 = QtGui.QHBoxLayout()
        hbox2 = QtGui.QHBoxLayout()

        self.led_red = QtGui.QPixmap()
        self.led_red.load(':/images/red.png')

        self.led_green = QtGui.QPixmap()
        self.led_green.load(':/images/green.png')

        self.led_yellow = QtGui.QPixmap()
        self.led_yellow.load(':/images/yellow.png')

        self.box1 = QtGui.QGroupBox('ПАК УЦ Е-Портал Квалифицированный')

        self.label1_cdp1 = QtGui.QLabel('CDP1: <a href=%s>%s</a>' % (self.cdp1, self.cdp1))
        self.label1_cdp1.setAlignment(QtCore.Qt.AlignTop)
        self.label1_cdp1.setOpenExternalLinks(True)

        self.label1_cdp2 = QtGui.QLabel('CDP2: <a href=%s>%s</a>' % (self.cdp2, self.cdp2))
        self.label1_cdp2.setAlignment(QtCore.Qt.AlignTop)
        self.label1_cdp2.setOpenExternalLinks(True)

        self.label1_ocsp = QtGui.QLabel('OCSP: <a href=%s>%s</a>' % (self.ocsp_ra, self.ocsp_ra))
        self.label1_ocsp.setAlignment(QtCore.Qt.AlignTop)
        self.label1_ocsp.setOpenExternalLinks(True)

        self.label1_tsp = QtGui.QLabel('TSP : <a href=%s>%s</a>' % (self.tsp, self.tsp))
        self.label1_tsp.setAlignment(QtCore.Qt.AlignTop)
        self.label1_tsp.setOpenExternalLinks(True)


        self.label1_crl_cdp1_nextupdate = QtGui.QLabel(self.l2)
        self.label1_crl_cdp1_nextupdate.setAlignment(QtCore.Qt.AlignTop)

        self.label1_crl_cdp2_nextupdate = QtGui.QLabel(self.l3)
        self.label1_crl_cdp2_nextupdate.setAlignment(QtCore.Qt.AlignTop)

        self.label1_crl_data_check = QtGui.QLabel(self.l1)
        self.label1_crl_data_check.setAlignment(QtCore.Qt.AlignTop)

        self.label1_cdp1_led = QtGui.QLabel()
        self.label1_cdp1_led.setToolTip('e-portal_2016.crl CDP1')
        self.label1_cdp1_led.setPixmap(self.led_red)

        self.label1_cdp2_led = QtGui.QLabel()
        self.label1_cdp2_led.setToolTip('e-portal_2016.crl CDP2')
        self.label1_cdp2_led.setPixmap(self.led_red)

        self.label1_ocsp_led = QtGui.QLabel()
        self.label1_ocsp_led.setToolTip('ra.e-portal.ru/ocsp')
        self.label1_ocsp_led.setPixmap(self.led_red)

        self.label1_tsp_led = QtGui.QLabel()
        self.label1_tsp_led.setToolTip('tsp.e-portal.ru')
        self.label1_tsp_led.setPixmap(self.led_red)

        vbox1.addWidget(self.label1_cdp1)
        vbox1.addWidget(self.label1_cdp2)
        vbox1.addWidget(self.label1_ocsp)
        vbox1.addWidget(self.label1_tsp)
        vbox1.addWidget(self.label1_crl_cdp1_nextupdate)
        vbox1.addWidget(self.label1_crl_cdp2_nextupdate)
        vbox1.addWidget(self.label_etrust_header)
        vbox1.addWidget(self.label_etrust)
        vbox1.addStretch()
        vbox1.addWidget(self.label1_crl_data_check)


        self.box2 = QtGui.QGroupBox('ПАК УЦ Е-Портал Не квалифицированный')

        self.label2_cdp1 = QtGui.QLabel('CDP1: <a href=%s>%s</a>' % (self.cdp3, self.cdp3))
        self.label2_cdp1.setAlignment(QtCore.Qt.AlignTop)
        self.label2_cdp1.setOpenExternalLinks(True)

        self.label2_cdp2 = QtGui.QLabel('CDP2: <a href=%s>%s</a>' % (self.cdp4, self.cdp4))
        self.label2_cdp2.setAlignment(QtCore.Qt.AlignTop)
        self.label2_cdp2.setOpenExternalLinks(True)

        self.label2_ocsp = QtGui.QLabel('OCSP: <a href=%s>%s</a>' % (self.ocsp_ra2, self.ocsp_ra2))
        self.label2_ocsp.setAlignment(QtCore.Qt.AlignTop)
        self.label2_ocsp.setOpenExternalLinks(True)

        self.label2_crl_cdp1_nextupdate = QtGui.QLabel(self.l2)
        self.label2_crl_cdp1_nextupdate.setAlignment(QtCore.Qt.AlignTop)

        self.label2_crl_cdp2_nextupdate = QtGui.QLabel(self.l3)
        self.label2_crl_cdp2_nextupdate.setAlignment(QtCore.Qt.AlignTop)

        self.label2_crl_data_check = QtGui.QLabel(self.l1)
        self.label2_crl_data_check.setAlignment(QtCore.Qt.AlignTop)

        self.label2_cdp1_led = QtGui.QLabel()
        self.label2_cdp1_led.setToolTip('e-portal_2017.crl CDP1')
        self.label2_cdp1_led.setPixmap(self.led_red)

        self.label2_cdp2_led = QtGui.QLabel()
        self.label2_cdp2_led.setToolTip('e-portal_2017.crl CDP2')
        self.label2_cdp2_led.setPixmap(self.led_red)

        self.label2_ocsp_led = QtGui.QLabel()
        self.label2_ocsp_led.setToolTip('ra2.e-portal.ru/ocsp')
        self.label2_ocsp_led.setPixmap(self.led_red)

        vbox2.addWidget(self.label2_cdp1)
        vbox2.addWidget(self.label2_cdp2)
        vbox2.addWidget(self.label2_ocsp)
        vbox2.addWidget(self.label2_crl_cdp1_nextupdate)
        vbox2.addWidget(self.label2_crl_cdp2_nextupdate)
        vbox2.addStretch()
        vbox2.addWidget(self.label2_crl_data_check)

        self.widget1 = QtGui.QWidget()
        self.box1.setLayout(vbox1)

        self.widget2 = QtGui.QWidget()
        self.box2.setLayout(vbox2)

        hbox.addWidget(self.box1)
        hbox.addWidget(self.box2)

        self.toolbar_indicator = QtGui.QToolBar('Индикаторы')
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar_indicator)
        self.toolbar_indicator.addWidget(self.label1_cdp1_led)
        self.toolbar_indicator.addWidget(self.label1_cdp2_led)
        self.toolbar_indicator.addWidget(self.label2_cdp1_led)
        self.toolbar_indicator.addWidget(self.label2_cdp2_led)
        self.toolbar_indicator.addWidget(self.label1_ocsp_led)
        self.toolbar_indicator.addWidget(self.label2_ocsp_led)
        self.toolbar_indicator.addWidget(self.label1_tsp_led)

        self.mythread = MyThread()

        self.connect(self.check, QtCore.SIGNAL('triggered()'), self.on_auto)
        self.connect(self.mythread, QtCore.SIGNAL('started()'), self.on_started)
        self.connect(self.mythread, QtCore.SIGNAL('finished()'), self.on_finished)
        self.connect(self.mythread, QtCore.SIGNAL('setCRLgreen(QString)'), self.set_crl_green, QtCore.Qt.QueuedConnection)
        self.connect(self.mythread, QtCore.SIGNAL('setCRLyellow(QString)'), self.set_crl_yellow, QtCore.Qt.QueuedConnection)
        self.connect(self.mythread, QtCore.SIGNAL('setCRLred(QString)'), self.set_crl_red, QtCore.Qt.QueuedConnection)
        self.connect(self.mythread, QtCore.SIGNAL('setOCSPgreen(QString)'), self.set_ocsp_green, QtCore.Qt.QueuedConnection)
        self.connect(self.mythread, QtCore.SIGNAL('setOCSPred(QString)'), self.set_ocsp_red, QtCore.Qt.QueuedConnection)
        self.connect(self.mythread, QtCore.SIGNAL('setTSPred()'), self.set_tsp_red, QtCore.Qt.QueuedConnection)
        self.connect(self.mythread, QtCore.SIGNAL('setTSPgreen()'), self.set_tsp_green, QtCore.Qt.QueuedConnection)
        self.connect(self.mythread, QtCore.SIGNAL('setDATAcrl(QString, QString)'), self.set_data_crl, QtCore.Qt.QueuedConnection)
        self.connect(self.mythread, QtCore.SIGNAL('error(QString, QString)'), self.send_to_email, QtCore.Qt.QueuedConnection)
        self.connect(self.mythread, QtCore.SIGNAL('writeTOlog(QString)'), self.write_to_log, QtCore.Qt.QueuedConnection)
        self.connect(self.mythread, QtCore.SIGNAL('etrust(QString)'), self.etrust_label_update, QtCore.Qt.QueuedConnection)
        self.widget.setLayout(hbox)

    def etrust_label_update(self, text):
        self.label_etrust.setText(text)

    def set_data_crl(self, next_crl_update, cdp):
        if cdp == self.cdp1: self.label1_crl_cdp1_nextupdate.setText(self.l2 + next_crl_update)
        elif cdp == self.cdp2: self.label1_crl_cdp2_nextupdate.setText(self.l3 + next_crl_update)
        elif cdp == self.cdp3: self.label2_crl_cdp1_nextupdate.setText(self.l2 + next_crl_update)
        elif cdp == self.cdp4: self.label2_crl_cdp2_nextupdate.setText(self.l3 + next_crl_update)

    def set_tsp_red(self):
        self.label1_tsp_led.setPixmap(self.led_red)

    def set_tsp_green(self):
        self.label1_tsp_led.setPixmap(self.led_green)

    def set_ocsp_red(self, ocsp):
        if ocsp == self.ocsp_ra: self.label1_ocsp_led.setPixmap(self.led_red)
        elif ocsp == self.ocsp_ra2:self.label2_ocsp_led.setPixmap(self.led_red)

    def set_ocsp_green(self, ocsp):
        if ocsp == self.ocsp_ra: self.label1_ocsp_led.setPixmap(self.led_green)
        elif ocsp == self.ocsp_ra2:self.label2_ocsp_led.setPixmap(self.led_green)

    def set_crl_green(self, cdp):
        if cdp == self.cdp1: self.label1_cdp1_led.setPixmap(self.led_green)
        elif cdp == self.cdp2: self.label1_cdp2_led.setPixmap(self.led_green)
        elif cdp == self.cdp3: self.label2_cdp1_led.setPixmap(self.led_green)
        elif cdp == self.cdp4: self.label2_cdp2_led.setPixmap(self.led_green)

    def set_crl_yellow(self, cdp):
        if cdp == self.cdp1: self.label1_cdp1_led.setPixmap(self.led_yellow)
        elif cdp == self.cdp2: self.label1_cdp2_led.setPixmap(self.led_yellow)
        elif cdp == self.cdp3: self.label2_cdp1_led.setPixmap(self.led_yellow)
        elif cdp == self.cdp4: self.label2_cdp2_led.setPixmap(self.led_yellow)


    def set_crl_red(self, cdp):
        if cdp == self.cdp1: self.label1_cdp1_led.setPixmap(self.led_red)
        elif cdp == self.cdp2: self.label1_cdp2_led.setPixmap(self.led_red)
        elif cdp == self.cdp3: self.label2_cdp1_led.setPixmap(self.led_red)
        elif cdp == self.cdp4: self.label2_cdp2_led.setPixmap(self.led_red)

    def on_finished(self):
        self.check.setDisabled(False)
        self.statusBar().showMessage('Готов')
        run_time = str(datetime.now().strftime("%d.%m.%Y %H:%M"))
        self.label1_crl_data_check.setText(self.l1 + run_time)
        self.label2_crl_data_check.setText(self.l1 + run_time)

    def on_auto(self):
        self.mythread.start()
        self.check.setDisabled(True)

    def on_started(self):
        self.statusBar().showMessage('...')

    def timer_on(self):
        self.timer_id = self.startTimer(60000*self.timer_value)
        self.statusBar().showMessage('Таймер включён')
        self.auto.setDisabled(True)
        self.stop.setDisabled(False)
        self.on_auto()

    def timer_off(self):
        if self.timer_id:
            self.killTimer(self.timer_id)
            self.timer_id = 0
            self.statusBar().showMessage('Таймер выключен')
            self.auto.setDisabled(False)
            self.stop.setDisabled(True)
            self.check.setDisabled(False)

    def timerEvent(self, event):
        self.on_auto()

    def open_about_me(self):
        about_me = QtGui.QMessageBox.about(main, 'О программе ca_control', 'Программа для контроля работоспособности сервисов удостоверяющего центра Е-Портал.\nПри написании использовались:\n\tPython 3.5\n\tPyQt4\nАвтор: @XOMRKOB')

    def open_about_qt(self):
        about_qt = QtGui.QMessageBox.aboutQt(main)

    def open_log(self):
        modalWindow = QtGui.QWidget(self, QtCore.Qt.Window)
        modalWindow.setWindowTitle('Просмотр LOG файла')
        modalWindow.setWindowIcon(QtGui.QIcon(':/images/log.png'))
        modalWindow.resize(700, 800)
        modalWindow.setWindowModality(QtCore.Qt.WindowModal)
        modalWindow.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        vbox = QtGui.QVBoxLayout()
        text_edit = QtGui.QTextEdit()
        vbox.addWidget(text_edit)
        modalWindow.setLayout(vbox)
        panel = QtGui.QToolBar()

        file = open('ca_control.log', 'rt')
        line = file.readline().replace('\n', '')
        while line:
            text_edit.append(line)
            line = file.readline().replace('\n', '')
        file.close()
        text_edit.setReadOnly(True)
        modalWindow.show()

    def open_settings(self):
        dialog = QtGui.QInputDialog(main)
        dialog.setLabelText('Введите интервал проверки в минутах')
        dialog.setOkButtonText('&Сохранить')
        dialog.setCancelButtonText('&Закрыть')
        dialog.setInputMode(1)
        dialog.setIntValue(self.timer_value)
        dialog.setIntRange(1, 60)
        result = dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            self.timer_value = dialog.intValue()

    def send_to_email(self, error_code, cdp):
        login = 'ca.eportal@gmail.com'
        passwd = 'v9CXRj5T5jzR'
        server = 'smtp.gmail.com'
        port = 587
        to_addrs = 'mr.humster@gmail.com'

        if error_code == self.error_notfound:
            txt = 'Список отзыв сертификатов, находящийся по адресу:\n'+cdp+'\nне доступен.'
        elif error_code == self.error_hasexpired:
            txt = 'Список отзыв сертификатов, находящийся по адресу:\n' + cdp + '\nистёк.'
        elif error_code == self.error_ocspoffline:
            txt = 'Служба OCSP, расположенная по адресу:\n'+cdp+'\nотключена.'
        elif error_code == self.error_tspoffline:
            txt = 'Служба TSP, расположенная по адресу:\n' + cdp + '\nотключена.'

        template = open('message.html', 'rt').read()
        message = template %(txt)
        smtpObj = smtplib.SMTP(server, port)                            # Открываем портал в SMTP
        smtpObj.starttls()                                              # Включаем TLS
        smtpObj.login(login, passwd)                                    # Авторизуемся
        smtpObj.sendmail(login, to_addrs, message.encode('utf-8'))
        smtpObj.quit()                                                  # Закрываем портал в SMTP

    def write_to_log(self, text):
        log_file = open('ca_control.log', 'a')
        log_file.write(str(datetime.now())+'   ' + text)
        log_file.close()


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    main = MainWindow()
    main.show()
    main.on_auto()
    sys.exit(app.exec_())