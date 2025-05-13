#!/usr/bin/python

"""
*************************************************************************
 *
 * Fracktal Works
 * __________________
 * Authors: Vijay Varada/Nishant Bilurkar
 * Created: May 2023
 *
 * Licence: AGPLv3
*************************************************************************
"""
Development = False   # set to True if running on any system other than RaspberryPi

import mainGUI
import keyboard
import dialog
import styles
import glob

from PyQt5 import QtCore, QtGui, QtWidgets
import time
import sys
import subprocess 
from octoprintAPI import octoprintAPI
from hurry.filesize.filesize import size
from datetime import datetime
import qrcode
import websocket
import json
import random
import uuid
import os
import io
import requests
import re
from collections import OrderedDict
import base64
import threading

from logger import setup_logger, delete_old_logs

# Setup logger
logger = setup_logger()

# Delete old logs
delete_old_logs()

# Now you can use logger to log messages
logger.info("TouchUI started")

# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++Global variables++++++++++++++++++++++++++++++++++++++
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

ip = '0.0.0.0:5000'
apiKey = 'B508534ED20348F090B4D0AD637D3660'

file_name = ''
filaments = [
                ("PLA", 190),
                ("ABS", 220),
                ("PETG", 220),
                ("PVA", 210),
                ("TPU", 230),
                ("Nylon", 220),
                ("PolyCarbonate", 240),
                ("HIPS", 220),
                ("WoodFill", 220),
                ("CopperFill", 200),
                ("Breakaway", 220)
]

filaments = OrderedDict(filaments)

filament_settings = {
    "PLA": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    },
    "ABS": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    },
    "PETG": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    },
    "PVA": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    },
    "TPU": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    },
    "Nylon": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    },
    "PolyCarbonate": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    },
    "HIPS": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    },
    "WoodFill": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    },
    "CopperFill": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    },
    "Breakaway": {
        "initialExtrudeLength": 10,
        "initialExtrudeSpeed": 100,
        "retractLength": 50,
        "retractSpeed": 500,
        "dwellTime": 2
    }
}

calibrationPosition = {'X1': 110, 'Y1': 67,
                       'X2': 410, 'Y2': 67,
                       'X3': 260, 'Y3': 350,
                       'X4': 260, 'Y4': 20
                       }

tool0PurgePosition = {'X': 15, 'Y': -43}

ptfeTubeLength = 1600

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


def run_async(func):
    """
    Function decorater to make methods run in a thread
    """
    from threading import Thread
    from functools import wraps

    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func


def getIP(interface):
    try:
        scan_result = \
            (subprocess.Popen("ifconfig | grep " + interface + " -A 1", stdout=subprocess.PIPE, shell=True).communicate()[0]).decode("utf-8")
        rInetAddr = r"inet\s*([\d.]+)"
        rInet6Addr = r"inet6"
        mt6Ip = re.search(rInet6Addr, scan_result)
        mtIp = re.search(rInetAddr, scan_result)
        if not mt6Ip and mtIp and len(mtIp.groups()) == 1:
            return str(mtIp.group(1))
    except Exception as e:
        logger.error("Error in getIP: {}".format(e))
        return None

def getMac(interface):
    logger.info("Getting MAC for interface: {}".format(interface))
    try:
        mac = subprocess.Popen(" cat /sys/class/net/" + interface + "/address",
                               stdout=subprocess.PIPE, shell=True).communicate()[0].rstrip()
        if not mac:
            return "Not found"
        return mac.upper()
    except Exception as e:
        logger.error("Error in getMac: {}".format(e))
        return "Error"


def getWifiAp():
    logger.info("Getting Wifi AP")
    try:
        ap = subprocess.Popen("iwgetid -r",
                              stdout=subprocess.PIPE, shell=True).communicate()[0].rstrip()
        if not ap:
            return "Not connected"
        return ap.decode("utf-8")
    except Exception as e:
        logger.error("Error in getWifiAp: {}".format(e))
        return "Error"


def getHostname():
    logger.info("Getting Hostname")
    try:
        hostname = subprocess.Popen("cat /etc/hostname", stdout=subprocess.PIPE, shell=True).communicate()[0].rstrip()
        if not hostname:
            return "Not connected"
        return hostname.decode("utf-8")  + ".local"
    except Exception as e:
        logger.error("Error in getHostname: {}".format(e))
        return "Error"

OriginalPushButton = QtWidgets.QPushButton
OriginalToolButton = QtWidgets.QToolButton

class QPushButtonFeedback(QtWidgets.QPushButton):
    def mousePressEvent(self, QMouseEvent):
        OriginalPushButton.mousePressEvent(self, QMouseEvent)


class QToolButtonFeedback(QtWidgets.QToolButton):
    def mousePressEvent(self, QMouseEvent):
        OriginalToolButton.mousePressEvent(self, QMouseEvent)


QtWidgets.QToolButton = QToolButtonFeedback
QtWidgets.QPushButton = QPushButtonFeedback


class Image(qrcode.image.base.BaseImage):
    def __init__(self, border, width, box_size):
        self.border = border
        self.width = width
        self.box_size = box_size
        _size = (width + border * 2) * box_size
        self._image = QtGui.QImage(
            _size, _size, QtGui.QImage.Format_RGB16)
        self._image.fill(QtCore.Qt.white)

    def pixmap(self):
        return QtGui.QPixmap.fromImage(self._image)

    def drawrect(self, row, col):
        painter = QtGui.QPainter(self._image)
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size, self.box_size,
            QtCore.Qt.black)

    def save(self, stream, kind=None):
        pass

class ClickableLineEdit(QtWidgets.QLineEdit):
    clicked_signal = QtCore.pyqtSignal()
    def __init__(self, parent):
        QtWidgets.QLineEdit.__init__(self, parent)
    def mousePressEvent(self, QMouseEvent):
        self.clicked_signal.emit()


class MainUiClass(QtWidgets.QMainWindow, mainGUI.Ui_MainWindow):
    """
    Main GUI Workhorse, all slots and events defined within
    The main implementation class that inherits methods, variables etc from mainGUI_pro_dual_abl.py and QMainWindow
    """
    def __init__(self):
        """
        This method gets called when an object of type MainUIClass is defined
        """
        super(MainUiClass, self).__init__()
        logger.info("MainUiClass.__init__ started")
        try:
            self.setupUi(self)
            self.stackedWidget.setCurrentWidget(self.loadingPage)
            self.setStep(10)
            self.keyboardWindow = None
            self.changeFilamentHeatingFlag = False
            self.setHomeOffsetBool = False
            self.currentImage = None
            self.currentFile = None
            self.sanityCheck = ThreadSanityCheck(virtual=False)
            self.sanityCheck.start()
            self.sanityCheck.loaded_signal.connect(self.proceed)
            self.sanityCheck.startup_error_signal.connect(self.handleStartupError)
            #self.setNewToolZOffsetFromCurrentZBool = False
            #self.setActiveExtruder(0)
            self.loadFlag = None
            self.dialogShown = False

            self.dialog_doorlock = None
            self.dialog_filamentsensor = None

            for spinbox in self.findChildren(QtWidgets.QSpinBox):
                lineEdit = spinbox.lineEdit()
                lineEdit.setReadOnly(True)
                lineEdit.setDisabled(True)


        except Exception as e:
            logger.error("Error in MainUiClass.__init__: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.__init__: {}".format(e), overlay=True)
    def setupUi(self, MainWindow):
        """
        This method sets up the UI, all the widgets, layouts etc are defined here
        """
        logger.info("MainUiClass.setupUi started")
        try:
            super(MainUiClass, self).setupUi(MainWindow)
            font = QtGui.QFont()
            font.setFamily(_fromUtf8("Gotham"))
            font.setPointSize(15)

            self.wifiPasswordLineEdit = ClickableLineEdit(self.wifiSettingsPage)
            self.wifiPasswordLineEdit.setGeometry(QtCore.QRect(300, 170, 400, 60))
            self.wifiPasswordLineEdit.setFont(font)
            self.wifiPasswordLineEdit.setStyleSheet(styles.textedit)
            self.wifiPasswordLineEdit.setObjectName(_fromUtf8("wifiPasswordLineEdit"))

            font.setPointSize(11)
            self.staticIPLineEdit = ClickableLineEdit(self.ethStaticSettings)
            self.staticIPLineEdit.setGeometry(QtCore.QRect(200, 15, 450, 40))
            self.staticIPLineEdit.setFont(font)
            self.staticIPLineEdit.setStyleSheet(styles.textedit)
            self.staticIPLineEdit.setObjectName(_fromUtf8("staticIPLineEdit"))

            self.staticIPGatewayLineEdit = ClickableLineEdit(self.ethStaticSettings)
            self.staticIPGatewayLineEdit.setGeometry(QtCore.QRect(200, 85, 450, 40))
            self.staticIPGatewayLineEdit.setFont(font)
            self.staticIPGatewayLineEdit.setStyleSheet(styles.textedit)
            self.staticIPGatewayLineEdit.setObjectName(_fromUtf8("staticIPGatewayLineEdit"))

            self.staticIPNameServerLineEdit = ClickableLineEdit(self.ethStaticSettings)
            self.staticIPNameServerLineEdit.setGeometry(QtCore.QRect(200, 155, 450, 40))
            self.staticIPNameServerLineEdit.setFont(font)
            self.staticIPNameServerLineEdit.setStyleSheet(styles.textedit)
            self.staticIPNameServerLineEdit.setObjectName(_fromUtf8("staticIPNameServerLineEdit"))

            self.menuCartButton.setDisabled(True)
            self.testPrintsButton.setDisabled(True)

            self.movie = QtGui.QMovie("templates/img/loading-90.gif")
            self.loadingGif.setMovie(self.movie)
            self.movie.start()
        except Exception as e:
            logger.error("Error in MainUiClass.setupUi: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.setupUi: {}".format(e), overlay=True)

    def safeProceed(self):
        """
        When Octoprint server cannot connect for whatever reason, still show the home screen to conduct diagnostics
        """
        logger.info("MainUiClass.safeProceed started")
        try:
            self.movie.stop()
            if not Development:
                self.stackedWidget.setCurrentWidget(self.homePage)
                self.setIPStatus()
            else:
                self.stackedWidget.setCurrentWidget(self.homePage)

            # Text Input events
            self.wifiPasswordLineEdit.clicked_signal.connect(lambda: self.startKeyboard(self.wifiPasswordLineEdit.setText))
            self.staticIPLineEdit.clicked_signal.connect(lambda: self.staticIPShowKeyboard(self.staticIPLineEdit))
            self.staticIPGatewayLineEdit.clicked_signal.connect(lambda: self.staticIPShowKeyboard(self.staticIPGatewayLineEdit))
            self.staticIPNameServerLineEdit.clicked_signal.connect(lambda: self.staticIPShowKeyboard(self.staticIPNameServerLineEdit))

            # Button Events:

            # Home Screen:
            self.stopButton.setDisabled(True)
            self.menuButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.MenuPage))
            self.controlButton.setDisabled(True)
            self.playPauseButton.setDisabled(True)

            # MenuScreen
            self.menuBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.homePage))
            self.menuControlButton.setDisabled(True)
            self.menuPrintButton.setDisabled(True)
            self.menuCalibrateButton.setDisabled(True)
            self.menuSettingsButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.settingsPage))


            # Settings Page
            self.networkSettingsButton.pressed.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.networkSettingsPage))
            self.displaySettingsButton.pressed.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.displaySettingsPage))
            self.settingsBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.MenuPage))
            self.pairPhoneButton.pressed.connect(self.pairPhoneApp)
            self.OTAButton.setDisabled(True)
            self.versionButton.setDisabled(True)

            self.restartButton.pressed.connect(self.askAndReboot)
            self.restoreFactoryDefaultsButton.pressed.connect(self.restoreFactoryDefaults)
            self.restorePrintSettingsButton.pressed.connect(self.restorePrintDefaults)

            # Network settings page
            self.networkInfoButton.pressed.connect(self.networkInfo)
            self.configureWifiButton.pressed.connect(self.wifiSettings)
            self.configureStaticIPButton.pressed.connect(self.staticIPSettings)
            self.networkSettingsBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.networkSettingsPage))

            # Network Info Page
            self.networkInfoBackButton.pressed.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.networkSettingsPage))

            # WifiSetings page
            self.wifiSettingsSSIDKeyboardButton.pressed.connect(
                lambda: self.startKeyboard(self.wifiSettingsComboBox.addItem))
            self.wifiSettingsCancelButton.pressed.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.networkSettingsPage))
            self.wifiSettingsDoneButton.pressed.connect(self.acceptWifiSettings)

            # Static IP settings page
            self.staticIPKeyboardButton.pressed.connect(lambda: self.staticIPShowKeyboard(self.staticIPLineEdit))
            self.staticIPGatewayKeyboardButton.pressed.connect(
                lambda: self.staticIPShowKeyboard(self.staticIPGatewayLineEdit))
            self.staticIPNameServerKeyboardButton.pressed.connect(
                lambda: self.staticIPShowKeyboard(self.staticIPNameServerLineEdit))
            self.staticIPSettingsDoneButton.pressed.connect(self.staticIPSaveStaticNetworkInfo)
            self.staticIPSettingsCancelButton.pressed.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.networkSettingsPage))
            self.deleteStaticIPSettingsButton.pressed.connect(self.deleteStaticIPSettings)

            # Display settings
            self.displaySettingsBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.settingsPage))

            # QR Code
            self.QRCodeBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.settingsPage))

            # SoftwareUpdatePage
            self.softwareUpdateBackButton.setDisabled(True)
            self.performUpdateButton.setDisabled(True)

            # Filament sensor toggle
            self.toggleFilamentSensorButton.setDisabled(True)
        except Exception as e:
            logger.error("Error in MainUiClass.safeProceed: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.safeProceed: {}".format(e), overlay=True)


    def handleStartupError(self):
        """
        Error Handler when Octoprint gives up
        """
        logger.info("MainUiClass.handleStartupError started")
        try:
            if dialog.WarningYesNo(self, "Server Error, Restore failsafe settings?", overlay=True):
                logger.info("Restoring Failsafe Settings")
                os.system('sudo rm -rf /home/pi/.octoprint/users.yaml')
                os.system('sudo rm -rf /home/pi/.octoprint/config.yaml')
                os.system('sudo cp -f config/users.yaml /home/pi/.octoprint/users.yaml')
                os.system('sudo cp -f config/config.yaml /home/pi/.octoprint/config.yaml')
                subprocess.call(["sudo", "systemctl", "restart", "octoprint"])
                self.sanityCheck.start()
            else:
                logger.info("User chose not to restore failsafe settings, going to safeProcees()")
                self.safeProceed()
        except Exception as e:
            logger.error("Error in MainUiClass.handleStartupError: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.handleStartupError: {}".format(e), overlay=True)


    def proceed(self):
        """
        Startes websocket, as well as initialises button actions and callbacks. THis is done in such a manner so that the callbacks that depend on websockets
        load only after the socket is available which in turn is dependent on the server being available which is checked in the sanity check thread
        """
        logger.info("MainUiClass.proceed started")
        try:
            self.QtSocket = QtWebsocket()
            self.QtSocket.start()
            self.setActions()
            self.movie.stop()
            if not Development:
                self.stackedWidget.setCurrentWidget(self.homePage)
                self.setIPStatus()
            else:
                self.stackedWidget.setCurrentWidget(self.homePage)
            self.isFilamentSensorInstalled()
            self.onServerConnected()
            self.checkKlipperPrinterCFG()
        except Exception as e:
            logger.error("Error in MainUiClass.proceed: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.proceed: {}".format(e), overlay=True)
    def setActions(self):

        """
        defines all the Slots and Button events.
        """
        logger.info("MainUiClass.setActions started")
        try:
            #self.QtSocket.set_z_tool_offset_signal.connect(self.setZToolOffset)
            self.QtSocket.z_probe_offset_signal.connect(self.updateEEPROMProbeOffset)
            self.QtSocket.temperatures_signal.connect(self.updateTemperature)
            self.QtSocket.status_signal.connect(self.updateStatus)
            self.QtSocket.print_status_signal.connect(self.updatePrintStatus)
            self.QtSocket.update_started_signal.connect(self.softwareUpdateProgress)
            self.QtSocket.update_log_signal.connect(self.softwareUpdateProgressLog)
            self.QtSocket.update_log_result_signal.connect(self.softwareUpdateResult)
            self.QtSocket.update_failed_signal.connect(self.updateFailed)
            self.QtSocket.connected_signal.connect(self.onServerConnected)
            self.QtSocket.filament_sensor_triggered_signal.connect(self.filamentSensorHandler)
            self.QtSocket.z_probing_failed_signal.connect(self.showProbingFailed)
            self.QtSocket.printer_error_signal.connect(self.showPrinterError)
    
            # Text Input events
            self.wifiPasswordLineEdit.clicked_signal.connect(lambda: self.startKeyboard(self.wifiPasswordLineEdit.setText))
            self.staticIPLineEdit.clicked_signal.connect(lambda: self.staticIPShowKeyboard(self.staticIPLineEdit))
            self.staticIPGatewayLineEdit.clicked_signal.connect(lambda: self.staticIPShowKeyboard(self.staticIPGatewayLineEdit))
            self.staticIPNameServerLineEdit.clicked_signal.connect(lambda: self.staticIPShowKeyboard(self.staticIPNameServerLineEdit))
    
            # Button Events:
    
            # Home Screen:
            self.stopButton.pressed.connect(self.stopActionMessageBox)
            self.menuButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.MenuPage))
            self.controlButton.pressed.connect(self.control)
            self.playPauseButton.clicked.connect(self.playPauseAction)
            self.doorLockButton.clicked.connect(self.doorLock)
    
            # MenuScreen
            self.menuBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.homePage))
            self.menuControlButton.pressed.connect(self.control)
            self.menuPrintButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.printLocationPage))
            self.menuCalibrateButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.calibratePage))
            self.menuSettingsButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.settingsPage))
    
            # Calibrate Page
            self.calibrateBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.MenuPage))
            self.nozzleOffsetButton.pressed.connect(self.requestEEPROMProbeOffset)
# the -ve sign is such that its converted to home offset and not just distance between nozzle and bed
            self.nozzleOffsetSetButton.pressed.connect(
                lambda: self.setZProbeOffset(self.nozzleOffsetDoubleSpinBox.value()))
            self.nozzleOffsetBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.calibratePage))
    
# --Dual Caliberation Addition--
            self.moveZMT1CaliberateButton.pressed.connect(lambda: octopiclient.jog(z=-0.025))
            self.moveZPT1CaliberateButton.pressed.connect(lambda: octopiclient.jog(z=0.025))
    
            self.calibrationWizardButton.clicked.connect(self.quickStep1)
            self.quickStep1NextButton.clicked.connect(self.quickStep2)
            self.quickStep2NextButton.clicked.connect(self.quickStep3)
            self.quickStep3NextButton.clicked.connect(self.quickStep4)
            self.quickStep4DoneButton.clicked.connect(self.cancelStep)
            #self.nozzleHeightStep1NextButton.clicked.connect(self.nozzleHeightStep1)
            self.quickStep1CancelButton.pressed.connect(self.cancelStep)
            self.quickStep2CancelButton.pressed.connect(self.cancelStep)
            self.quickStep3CancelButton.pressed.connect(self.cancelStep)
            self.quickStep4DoneButton.pressed.connect(self.cancelStep)
            #self.nozzleHeightStep1CancelButton.pressed.connect(self.cancelStep)
    
            self.testPrintsButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.testPrintsPage1_6))
            self.testPrintsNextButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.testPrintsPage2_6))
            self.testPrintsBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.calibratePage))
            self.testPrintsCancelButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.calibratePage))
            # self.dualCaliberationPrintButton.pressed.connect(
            #     lambda: self.testPrint(str(self.testPrintsTool0SizeComboBox.currentText()).replace('.', ''), 'dualCalibration'))
            self.bedLevelPrintButton.pressed.connect(
                lambda: self.testPrint(str(self.testPrintsTool0SizeComboBox.currentText()).replace('.', ''), 'bedLevel'))
            self.movementTestPrintButton.pressed.connect(
                lambda: self.testPrint(str(self.testPrintsTool0SizeComboBox.currentText()).replace('.', ''), 'movementTest'))
            self.singleNozzlePrintButton.pressed.connect(
                lambda: self.testPrint(str(self.testPrintsTool0SizeComboBox.currentText()).replace('.', ''), 'singleTest'))
    
            self.inputShaperCalibrateButton.pressed.connect(self.inputShaperCalibrate)

            # PrintLocationScreen
            self.printLocationScreenBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.MenuPage))
            self.fromLocalButton.pressed.connect(self.fileListLocal)
            self.fromUsbButton.pressed.connect(self.fileListUSB)
    
            # fileListLocalScreen
            self.localStorageBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.printLocationPage))
            self.localStorageScrollUp.pressed.connect(
                lambda: self.fileListWidget.setCurrentRow(self.fileListWidget.currentRow() - 1))
            self.localStorageScrollDown.pressed.connect(
                lambda: self.fileListWidget.setCurrentRow(self.fileListWidget.currentRow() + 1))
            self.localStorageSelectButton.pressed.connect(self.printSelectedLocal)
            self.localStorageDeleteButton.pressed.connect(self.deleteItem)
    
            # selectedFile Local Screen
            self.fileSelectedBackButton.pressed.connect(self.fileListLocal)
            self.fileSelectedPrintButton.pressed.connect(self.printFile)
    
            # filelistUSBPage
            self.USBStorageBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.printLocationPage))
            self.USBStorageScrollUp.pressed.connect(
                lambda: self.fileListWidgetUSB.setCurrentRow(self.fileListWidgetUSB.currentRow() - 1))
            self.USBStorageScrollDown.pressed.connect(
                lambda: self.fileListWidgetUSB.setCurrentRow(self.fileListWidgetUSB.currentRow() + 1))
            self.USBStorageSelectButton.pressed.connect(self.printSelectedUSB)
            self.USBStorageSaveButton.pressed.connect(lambda: self.transferToLocal(prnt=False))
    
            # selectedFile USB Screen
            self.fileSelectedUSBBackButton.pressed.connect(self.fileListUSB)
            self.fileSelectedUSBTransferButton.pressed.connect(lambda: self.transferToLocal(prnt=False))
            self.fileSelectedUSBPrintButton.pressed.connect(lambda: self.transferToLocal(prnt=True))
    
            # ControlScreen
            self.moveYPButton.pressed.connect(lambda: octopiclient.jog(y=self.step, speed=2000))
            self.moveYMButton.pressed.connect(lambda: octopiclient.jog(y=-self.step, speed=2000))
            self.moveXMButton.pressed.connect(lambda: octopiclient.jog(x=-self.step, speed=2000))
            self.moveXPButton.pressed.connect(lambda: octopiclient.jog(x=self.step, speed=2000))
            self.moveZPButton.pressed.connect(lambda: octopiclient.jog(z=self.step, speed=2000))
            self.moveZMButton.pressed.connect(lambda: octopiclient.jog(z=-self.step, speed=2000))
            self.extruderButton.pressed.connect(lambda: octopiclient.extrude(self.step))
            self.retractButton.pressed.connect(lambda: octopiclient.extrude(-self.step))
            self.motorOffButton.pressed.connect(lambda: octopiclient.gcode(command='M18'))
            self.fanOnButton.pressed.connect(lambda: octopiclient.gcode(command='M106 S255'))
            self.fanOffButton.pressed.connect(lambda: octopiclient.gcode(command='M107'))
            self.cooldownButton.pressed.connect(self.coolDownAction)
            self.step100Button.pressed.connect(lambda: self.setStep(100))
            self.step1Button.pressed.connect(lambda: self.setStep(1))
            self.step10Button.pressed.connect(lambda: self.setStep(10))
            self.homeXYButton.pressed.connect(lambda: octopiclient.home(['x', 'y']))
            self.homeZButton.pressed.connect(lambda: octopiclient.home(['z']))
            self.controlBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.homePage))
            self.setToolTempButton.pressed.connect(self.setToolTemp)
            self.tool180PreheatButton.pressed.connect(lambda: self.preheatToolTemp(180))
            self.tool250PreheatButton.pressed.connect(lambda: self.preheatToolTemp(250))
            self.setBedTempButton.pressed.connect(lambda: octopiclient.setBedTemperature(self.bedTempSpinBox.value()))
            self.bed60PreheatButton.pressed.connect(lambda: self.preheatBedTemp(60))
            self.bed100PreheatButton.pressed.connect(lambda: self.preheatBedTemp(100))
            self.setFlowRateButton.pressed.connect(lambda: octopiclient.flowrate(self.flowRateSpinBox.value()))
            self.setFeedRateButton.pressed.connect(lambda: octopiclient.feedrate(self.feedRateSpinBox.value()))
    
            self.moveZPBabyStep.pressed.connect(lambda: octopiclient.gcode(command='M290 Z0.025'))
            self.moveZMBabyStep.pressed.connect(lambda: octopiclient.gcode(command='M290 Z-0.025'))
    
            # ChangeFilament rutien
            self.changeFilamentButton.pressed.connect(self.changeFilament)
            self.changeFilamentBackButton.pressed.connect(self.control)
            self.changeFilamentBackButton2.pressed.connect(self.changeFilamentCancel)
            self.changeFilamentBackButton3.pressed.connect(self.changeFilamentCancel)
            self.changeFilamentUnloadButton.pressed.connect(self.unloadFilament)
            self.changeFilamentLoadButton.pressed.connect(self.loadFilament)
            self.loadedTillExtruderButton.pressed.connect(self.changeFilamentExtrudePageFunction)
            self.loadDoneButton.pressed.connect(self.control)
            self.unloadDoneButton.pressed.connect(self.changeFilament)
    
            # Settings Page
            self.settingsBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.MenuPage))
            self.networkSettingsButton.pressed.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.networkSettingsPage))
            self.displaySettingsButton.pressed.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.displaySettingsPage))
            self.pairPhoneButton.pressed.connect(self.pairPhoneApp)
            self.OTAButton.pressed.connect(self.softwareUpdate)
            self.versionButton.pressed.connect(self.displayVersionInfo)
            self.restartButton.pressed.connect(self.askAndReboot)
            self.restoreFactoryDefaultsButton.pressed.connect(self.restoreFactoryDefaults)
            self.restorePrintSettingsButton.pressed.connect(self.restorePrintDefaults)
    
            # Network settings page
            self.networkInfoButton.pressed.connect(self.networkInfo)
            self.configureWifiButton.pressed.connect(self.wifiSettings)
            self.configureStaticIPButton.pressed.connect(self.staticIPSettings)
            self.networkSettingsBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.settingsPage))
    
            # Network Info Page
            self.networkInfoBackButton.pressed.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.networkSettingsPage))
    
            # WifiSetings page
            self.wifiSettingsSSIDKeyboardButton.pressed.connect(
                lambda: self.startKeyboard(self.wifiSettingsComboBox.addItem))
            self.wifiSettingsCancelButton.pressed.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.networkSettingsPage))
            self.wifiSettingsDoneButton.pressed.connect(self.acceptWifiSettings)
    
            # Static IP settings page
            self.staticIPKeyboardButton.pressed.connect(lambda: self.staticIPShowKeyboard(self.staticIPLineEdit))                                                                            
            self.staticIPGatewayKeyboardButton.pressed.connect(lambda: self.staticIPShowKeyboard(self.staticIPGatewayLineEdit))
            self.staticIPNameServerKeyboardButton.pressed.connect(
                lambda: self.staticIPShowKeyboard(self.staticIPNameServerLineEdit))
            self.staticIPSettingsDoneButton.pressed.connect(self.staticIPSaveStaticNetworkInfo)
            self.staticIPSettingsCancelButton.pressed.connect(
                lambda: self.stackedWidget.setCurrentWidget(self.networkSettingsPage))
            self.deleteStaticIPSettingsButton.pressed.connect(self.deleteStaticIPSettings)
    
            self.displaySettingsBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.settingsPage))
    
            # QR Code
            self.QRCodeBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.settingsPage))
    
            # SoftwareUpdatePage
            self.softwareUpdateBackButton.pressed.connect(lambda: self.stackedWidget.setCurrentWidget(self.settingsPage))
            self.performUpdateButton.pressed.connect(lambda: octopiclient.performSoftwareUpdate())
    
            # Filament sensor toggle
            self.toggleFilamentSensorButton.clicked.connect(self.toggleFilamentSensor)
        except Exception as e:
            logger.error("Error in MainUiClass.setActions: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.setActions: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++Print Restore+++++++++++++++++++++++++++++++++++ '''

    def printRestoreMessageBox(self, file):
        """
        Displays a message box alerting the user of a filament error
        """
        logger.info("MainUiClass.printRestoreMessageBox started")
        try:
            if dialog.WarningYesNo(self, file + " Did not finish, would you like to restore?"):
                response = octopiclient.restore(restore=True)
                if response["status"] == "Successfully Restored":
                    dialog.WarningOk(self, response["status"])
                else:
                    dialog.WarningOk(self, response["status"])
        except Exception as e:
            logger.error("Error in MainUiClass.printRestoreMessageBox: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.printRestoreMessageBox: {}".format(e), overlay=True)


    def onServerConnected(self):
        """
        When the server is connected, check for filament sensor and previous print failure to complere
        """
        logger.info("MainUiClass.onServerConnected started")
        try:
            octopiclient.gcode(command='status')
            self.isFilamentSensorInstalled()
            try:
                response = octopiclient.isFailureDetected()
                if response["canRestore"] is True:
                    self.printRestoreMessageBox(response["file"])
                else:
                    pass
            except:
                pass
        except Exception as e:
            logger.error("Error in MainUiClass.onServerConnected: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.onServerConnected: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++Filament Sensor++++++++++++++++++++++++++++++++++++++ '''

    def isFilamentSensorInstalled(self):
        """
        Checks if the filament sensor is installed
        """
        logger.info("MainUiClass.isFilamentSensorInstalled started")
        try:
            success = False
            try:
                headers = {'X-Api-Key': apiKey}
                req = requests.get('http://{}/plugin/Julia2018FilamentSensor/status'.format(ip), headers=headers)
                success = req.status_code == requests.codes.ok
            except:
                pass
            return success
        except Exception as e:
            logger.error("Error in MainUiClass.isFilamentSensorInstalled: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.isFilamentSensorInstalled: {}".format(e), overlay=True)

    def toggleFilamentSensor(self):
        """
        Toggles the filament sensor
        """
        logger.info("MainUiClass.toggleFilamentSensor started")
        icon = 'filamentSensorOn' if self.toggleFilamentSensorButton.isChecked() else 'filamentSensorOff'
        self.toggleFilamentSensorButton.setIcon(QtGui.QIcon(_fromUtf8("templates/img/" + icon)))
        octopiclient.gcode(command="PRIMARY_SFS_ENABLE{}".format(int(self.toggleFilamentSensorButton.isChecked())))

    def filamentSensorHandler(self, data):
        """
        Handles the filament sensor
        """
        logger.info("MainUiClass.filamentSensorHandler started")
        try:
            print(data)

            icon = 'filamentSensorOn' if self.toggleFilamentSensorButton.isChecked() else 'filamentSensorOff'
            self.toggleFilamentSensorButton.setIcon(QtGui.QIcon(_fromUtf8("templates/img/" + icon)))

            if not self.toggleFilamentSensorButton.isChecked():  
                return

            triggered_extruder0 = False

            if '0' in data:
                triggered_extruder0 = True

            if 'disabled' in data:
                self.toggleFilamentSensorButton.setIcon(QtGui.QIcon(_fromUtf8("templates/img/filamentSensorOff")))

            if 'enabled' in data:
                self.toggleFilamentSensorButton.setIcon(QtGui.QIcon(_fromUtf8("templates/img/filamentSensorOn")))

            if triggered_extruder0 and self.stackedWidget.currentWidget() not in [self.changeFilamentPage, self.changeFilamentProgressPage,
                                    self.changeFilamentExtrudePage, self.changeFilamentRetractPage,self.changeFilamentLoadPage]:
                octopiclient.gcode(command='PAUSE')
                if dialog.WarningOk(self, "Filament outage or clog detected in Extruder 0. Please check the external motors. Print paused"):
                    pass
        except Exception as e:
            logger.error("Error in MainUiClass.filamentSensorHandler: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.filamentSensorHandler: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++++ Door Lock +++++++++++++++++++++++++++++++++++++ '''

    def doorLock(self):
        """
        function that toggles locking and unlocking the front door
        :return:
        """
        logger.info("MainUiClass.doorLock started")
        try:
            octopiclient.gcode(command='DoorToggle')
            octopiclient.overrideDoorLock()
        except Exception as e:
            logger.error("Error in MainUiClass.doorLock: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.doorLock: {}".format(e), overlay=True)

    def doorLockMsg(self, data):
        """
        Function that handles the door lock message
        """
        logger.info("MainUiClass.doorLockMsg started")
        try:
            if "msg" not in data:
                return

            msg = data["msg"]

            if self.dialog_doorlock:
                self.dialog_doorlock.close()
                self.dialog_doorlock = None

            if msg is not None:
                self.dialog_doorlock = dialog.dialog(self, msg, icon="exclamation-mark.png")
                if self.dialog_doorlock.exec_() == QtGui.QMessageBox.Ok:
                    self.dialog_doorlock = None
                    return
        except Exception as e:
            logger.error("Error in MainUiClass.doorLockMsg: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.doorLockMsg: {}".format(e), overlay=True)

    def doorLockHandler(self, data):
        """
        Function that handles the door lock status
        """
        logger.info("MainUiClass.doorLockHandler started")
        try:
            door_lock_disabled = False
            door_lock = False

            if 'door_lock' in data:
                door_lock_disabled = data["door_lock"] == "disabled"
                door_lock = data["door_lock"] == 1

            self.doorLockButton.setVisible(not door_lock_disabled)
            if not door_lock_disabled:
                self.doorLockButton.setText('Lock Door' if not door_lock else 'Unlock Door')

                icon = 'doorLock' if not door_lock else 'doorUnlock'
                self.doorLockButton.setIcon(QtGui.QIcon(_fromUtf8("templates/img/" + icon + ".png")))
            else:
                return
        except Exception as e:
            logger.error("Error in MainUiClass.doorLockHandler: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.doorLockHandler: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++++++++++OTA Update+++++++++++++++++++++++++++++++++++ '''

    def displayVersionInfo(self):
        """
        Displays the version information for octoprint plugins
        """
        logger.info("MainUiClass.displayVersionInfo started")
        try:
            self.updateListWidget.clear()
            updateAvailable = False
            self.performUpdateButton.setDisabled(True)

            data = octopiclient.getSoftwareUpdateInfo()
            if data:
                for item in data["information"]:
                    plugin = data["information"][item]
                    info = u'\u2713' if not plugin["updateAvailable"] else u"\u2717"
                    info += plugin["displayName"] + "  " + plugin["displayVersion"] + "\n"
                    info += "   Available: "
                    if "information" in plugin and "remote" in plugin["information"] and plugin["information"]["remote"]["value"] is not None:
                        info += plugin["information"]["remote"]["value"]
                    else:
                        info += "Unknown"
                    self.updateListWidget.addItem(info)

                    if plugin["updateAvailable"]:
                        updateAvailable = True

            if updateAvailable:
                self.performUpdateButton.setDisabled(False)
            self.stackedWidget.setCurrentWidget(self.OTAUpdatePage)
        except Exception as e:
            logger.error("Error in MainUiClass.displayVersionInfo: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.displayVersionInfo: {}".format(e), overlay=True)

    def softwareUpdateResult(self, data):
        logger.info("MainUiClass.softwareUpdateResult started")
        try:
            messageText = ""
            for item in data:
                messageText += item + ": " + data[item][0] + ".\n"
            messageText += "Restart required"
            self.askAndReboot(messageText)
        except Exception as e:
            logger.error("Error in MainUiClass.softwareUpdateResult: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.softwareUpdateResult: {}".format(e), overlay=True)

    def softwareUpdateProgress(self, data):
        logger.info("MainUiClass.softwareUpdateProgress started")
        try:
            self.stackedWidget.setCurrentWidget(self.softwareUpdateProgressPage)
            self.logTextEdit.setTextColor(QtCore.Qt.red)
            self.logTextEdit.append("---------------------------------------------------------------\n"
                                    "Updating " + data["name"] + " to " + data["version"] + "\n"
                                                                                            "---------------------------------------------------------------")
        except Exception as e:
            logger.error("Error in MainUiClass.softwareUpdateProgress: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.softwareUpdateProgress: {}".format(e), overlay=True)

    def softwareUpdateProgressLog(self, data):
        logger.info("MainUiClass.softwareUpdateProgressLog started")
        try:
            self.logTextEdit.setTextColor(QtCore.Qt.white)
            for line in data:
                self.logTextEdit.append(line["line"])
        except Exception as e:
            logger.error("Error in MainUiClass.softwareUpdateProgressLog: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.softwareUpdateProgressLog: {}".format(e), overlay=True)

    def updateFailed(self, data):
        logger.info("MainUiClass.updateFailed started")
        try:
            self.stackedWidget.setCurrentWidget(self.settingsPage)
            messageText = (data["name"] + " failed to update\n")
            if dialog.WarningOkCancel(self, messageText, overlay=True):
                pass
        except Exception as e:
            logger.error("Error in MainUiClass.updateFailed: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.updateFailed: {}".format(e), overlay=True)

    def softwareUpdate(self):
        logger.info("MainUiClass.softwareUpdate started")
        try:
            data = octopiclient.getSoftwareUpdateInfo()
            updateAvailable = False
            if data:
                for item in data["information"]:
                    if data["information"][item]["updateAvailable"]:
                        updateAvailable = True
            if updateAvailable:
                print('Update Available')
                if dialog.SuccessYesNo(self, "Update Available! Update Now?", overlay=True):
                    octopiclient.performSoftwareUpdate()

            else:
                if dialog.SuccessOk(self, "System is Up To Date!", overlay=True):
                    print('Update Unavailable')
        except Exception as e:
            logger.error("Error in MainUiClass.softwareUpdate: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.softwareUpdate: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++++++++++Wifi Config+++++++++++++++++++++++++++++++++++ '''

    def acceptWifiSettings(self):
        logger.info("MainUiClass.acceptWifiSettings started")
        try:
            wlan0_config_file = io.open("/etc/wpa_supplicant/wpa_supplicant.conf", "r+", encoding='utf8')
            wlan0_config_file.truncate()
            ascii_ssid = self.wifiSettingsComboBox.currentText()
            wlan0_config_file.write(u"country=IN\n")
            wlan0_config_file.write(u"ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
            wlan0_config_file.write(u"update_config=1\n")
            wlan0_config_file.write(u"network={\n")
            wlan0_config_file.write(u'ssid="' + str(ascii_ssid) + '"\n')
            if self.hiddenCheckBox.isChecked():
                wlan0_config_file.write(u'scan_ssid=1\n')
            if str(self.wifiPasswordLineEdit.text()) != "":
                wlan0_config_file.write(u'psk="' + str(self.wifiPasswordLineEdit.text()) + '"\n')
            wlan0_config_file.write(u'}')
            wlan0_config_file.close()
            self.restartWifiThreadObject = ThreadRestartNetworking(ThreadRestartNetworking.WLAN)
            self.restartWifiThreadObject.signal.connect(self.wifiReconnectResult)
            self.restartWifiThreadObject.start()
            self.wifiMessageBox = dialog.dialog(self,
                                                "Restarting networking, please wait...",
                                                icon="exclamation-mark.png",
                                                buttons=QtWidgets.QMessageBox.Cancel)
            if self.wifiMessageBox.exec_() in {QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel}:
                self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
        except Exception as e:
            logger.error("Error in MainUiClass.acceptWifiSettings: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.acceptWifiSettings: {}".format(e), overlay=True)

    def wifiReconnectResult(self, x):
        logger.info("MainUiClass.wifiReconnectResult started")
        try:
            self.wifiMessageBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            if x is not None:
                print("Ouput from signal " + x)
                self.wifiMessageBox.setLocalIcon('success.png')
                self.wifiMessageBox.setText('Connected, IP: ' + x)
                self.wifiMessageBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
                self.ipStatus.setText(x)

            else:
                self.wifiMessageBox.setText("Not able to connect to WiFi")
        except Exception as e:
            logger.error("Error in MainUiClass.wifiReconnectResult: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.wifiReconnectResult: {}".format(e), overlay=True)
    def networkInfo(self):
        logger.info("MainUiClass.networkInfo started")
        try:
            ipWifi = getIP(ThreadRestartNetworking.WLAN)
            ipEth = getIP(ThreadRestartNetworking.ETH)

            self.hostname.setText(getHostname())
            self.wifiAp.setText(getWifiAp())
            self.wifiIp.setText("Not connected" if not ipWifi else ipWifi)
            self.ipStatus.setText("Not connected" if not ipWifi else ipWifi)
            self.lanIp.setText("Not connected" if not ipEth else ipEth)
            self.wifiMac.setText(getMac(ThreadRestartNetworking.WLAN).decode('utf8'))
            self.lanMac.setText(getMac(ThreadRestartNetworking.ETH).decode('utf8'))
            self.stackedWidget.setCurrentWidget(self.networkInfoPage)
        except Exception as e:
            logger.error("Error in MainUiClass.networkInfo: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.networkInfo: {}".format(e), overlay=True)

    def wifiSettings(self):
        logger.info("MainUiClass.wifiSettings started")
        try:
            self.stackedWidget.setCurrentWidget(self.wifiSettingsPage)
            self.wifiSettingsComboBox.clear()
            self.wifiSettingsComboBox.addItems(self.scan_wifi())
        except Exception as e:
            logger.error("Error in MainUiClass.wifiSettings: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.wifiSettings: {}".format(e), overlay=True)

    def scan_wifi(self):
        """
        uses linux shell and WIFI interface to scan available networks
        :return: dictionary of the SSID and the signal strength
        """
        logger.info("MainUiClass.scan_wifi started")
        try:
            scan_result = \
                subprocess.Popen("iwlist wlan0 scan | grep 'ESSID'", stdout=subprocess.PIPE, shell=True).communicate()[0]
            scan_result = scan_result.decode('utf8').split('ESSID:')
            scan_result = [s.strip() for s in scan_result]
            scan_result = [s.strip('"') for s in scan_result]
            scan_result = filter(None, scan_result)
            return scan_result
        except Exception as e:
            logger.error("Error in MainUiClass.scan_wifi: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.scan_wifi: {}".format(e), overlay=True)
            return []

    @run_async
    def setIPStatus(self):
        """
        Function to update IP address of printer on the status bar. Refreshes at a particular interval.
        """
        try:
            while(True):
                try:
                    if getIP("eth0"):
                        self.ipStatus.setText(getIP("eth0"))
                    elif getIP("wlan0"):
                        self.ipStatus.setText(getIP("wlan0"))
                    else:
                        self.ipStatus.setText("Not connected")

                except:
                    self.ipStatus.setText("Not connected")
                time.sleep(60)
        except Exception as e:
            logger.error("Error in MainUiClass.setIPStatus: {}".format(e))



    ''' +++++++++++++++++++++++++++++++++Static IP Settings+++++++++++++++++++++++++++++ '''

    def staticIPSettings(self):
        logger.info("MainUiClass.staticIPSettings started")
        try:
            self.stackedWidget.setCurrentWidget(self.staticIPSettingsPage)
            self.staticIPComboBox.clear()
            self.staticIPComboBox.addItems(["eth0", "wlan0"])
        except Exception as e:
            logger.error("Error in MainUiClass.staticIPSettings: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.staticIPSettings: {}".format(e), overlay=True)
    def isIpErr(self, ip):
        return (re.search(r"^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})$", ip) is None)

    def showIpErr(self, var):
        return dialog.WarningOk(self, "Invalid input: {0}".format(var))

    def staticIPSaveStaticNetworkInfo(self):
        logger.info("MainUiClass.staticIPSaveStaticNetworkInfo started")
        try:
            txtStaticIPInterface = self.staticIPComboBox.currentText()
            txtStaticIPAddress = str(self.staticIPLineEdit.text())
            txtStaticIPGateway = str(self.staticIPGatewayLineEdit.text())
            txtStaticIPNameServer = str(self.staticIPNameServerLineEdit.text())
            if self.isIpErr(txtStaticIPAddress):
                return self.showIpErr("IP Address")
            if self.isIpErr(txtStaticIPGateway):
                return self.showIpErr("Gateway")
            if txtStaticIPNameServer is not "":
                if self.isIpErr(txtStaticIPNameServer):
                    return self.showIpErr("NameServer")
            Globaltxt = subprocess.Popen("cat /etc/dhcpcd.conf", stdout=subprocess.PIPE, shell=True).communicate()[0].decode('utf8')
            staticIPConfig = ""
            Globaltxt = re.sub(r"interface.*\n", "", Globaltxt)
            Globaltxt = re.sub(r"static.*\n", "", Globaltxt)
            Globaltxt = re.sub(r"^\s+", "", Globaltxt)
            staticIPConfig = "\ninterface {0}\nstatic ip_address={1}/24\nstatic routers={2}\nstatic domain_name_servers=8.8.8.8 8.8.4.4 {3}\n\n".format(
                txtStaticIPInterface, txtStaticIPAddress, txtStaticIPGateway, txtStaticIPNameServer)
            Globaltxt = staticIPConfig + Globaltxt
            with open("/etc/dhcpcd.conf", "w") as f:
                f.write(Globaltxt)

            if txtStaticIPInterface == 'eth0':
                print("Restarting networking for eth0")
                self.restartStaticIPThreadObject = ThreadRestartNetworking(ThreadRestartNetworking.ETH)
                self.restartStaticIPThreadObject.signal.connect(self.staticIPReconnectResult)
                self.restartStaticIPThreadObject.start()
                self.staticIPMessageBox = dialog.dialog(self,
                                                        "Restarting networking, please wait...",
                                                        icon="exclamation-mark.png",
                                                        buttons=QtWidgets.QMessageBox.Cancel)
                if self.staticIPMessageBox.exec_() in {QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel}:
                    self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
            elif txtStaticIPInterface == 'wlan0':
                print("Restarting networking for wlan0")
                self.restartWifiThreadObject = ThreadRestartNetworking(ThreadRestartNetworking.WLAN)
                self.restartWifiThreadObject.signal.connect(self.wifiReconnectResult)
                self.restartWifiThreadObject.start()
                self.wifiMessageBox = dialog.dialog(self,
                                                    "Restarting networking, please wait...",
                                                    icon="exclamation-mark.png",
                                                    buttons=QtWidgets.QMessageBox.Cancel)
                if self.wifiMessageBox.exec_() in {QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Cancel}:
                    self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
        except Exception as e:
            logger.error("Error in MainUiClass.staticIPSaveStaticNetworkInfo: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.staticIPSaveStaticNetworkInfo: {}".format(e), overlay=True)
    def deleteStaticIPSettings(self):
        logger.info("MainUiClass.deleteStaticIPSettings started")
        try:
            Globaltxt = subprocess.Popen("cat /etc/dhcpcd.conf", stdout=subprocess.PIPE, shell=True).communicate()[0].decode('utf8')
            Globaltxt = re.sub(r"interface.*\n", "", Globaltxt)
            Globaltxt = re.sub(r"static.*\n", "", Globaltxt)
            Globaltxt = re.sub(r"^\s+", "", Globaltxt)
            with open("/etc/dhcpcd.conf", "w") as f:
                f.write(Globaltxt)
            self.stackedWidget.setCurrentWidget(self.networkSettingsPage)
        except Exception as e:
            logger.error("Error in MainUiClass.deleteStaticIPSettings: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.deleteStaticIPSettings: {}".format(e), overlay=True)
                                                                                                  
    def staticIPReconnectResult(self, x):
        logger.info("MainUiClass.staticIPReconnectResult started")
        try:
            self.staticIPMessageBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            if x is not None:
                self.staticIPMessageBox.setLocalIcon('success.png')
                self.staticIPMessageBox.setText('Connected, IP: ' + x)
            else:

                self.staticIPMessageBox.setText("Not able to set Static IP")
        except Exception as e:
            logger.error("Error in MainUiClass.staticIPReconnectResult: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.staticIPReconnectResult: {}".format(e), overlay=True)

    def staticIPShowKeyboard(self, textbox):
        logger.info("MainUiClass.staticIPShowKeyboard started")
        try:
            self.startKeyboard(textbox.setText, onlyNumeric=True, noSpace=True, text=str(textbox.text()))
        except Exception as e:
            logger.error("Error in MainUiClass.staticIPShowKeyboard: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.staticIPShowKeyboard: {}".format(e), overlay=True)


    ''' ++++++++++++++++++++++++++++++++Display Settings+++++++++++++++++++++++++++++++ '''

    def touchCalibration(self):
        logger.info("MainUiClass.touchCalibration started")
        try:
            os.system('sudo su')
            os.system('export TSLIB_TSDEVICE=/dev/input/event0')
            os.system('export TSLIB_FBDEVICE=/dev/fb0')
            os.system('ts_calibrate')
        except Exception as e:
            logger.error("Error in MainUiClass.touchCalibration: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.touchCalibration: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++++++++++Change Filament+++++++++++++++++++++++++++++++ '''

    def calcExtrudeTime(self, length, speed):
        """
        Calculate the time it takes to extrude a certain length of filament at a certain speed
        :param length: length of filament to extrude
        :param speed: speed at which to extrude
        :return: time in seconds
        """
        return length / (speed/60)

    def unloadFilament(self):
        """
        Unloads filament from the single extruder (tool0).
        """
        logger.info("MainUiClass.unloadFilament started")
        try:
            # Disable SFS
            octopiclient.gcode(command="SFS_ENABLE0")
            
            # Move to the purge position for tool0
            if self.printerStatusText not in ["Printing", "Paused"]:
                octopiclient.jog(tool0PurgePosition['X'], tool0PurgePosition["Y"], absolute=True, speed=10000)

            if self.changeFilamentComboBox.findText("Loaded Filament") == -1:
                octopiclient.setToolTemperature({"tool0": filaments[str(self.changeFilamentComboBox.currentText())]})

            self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
            self.changeFilamentStatus.setText("Heating Tool 0, Please Wait...")
            self.changeFilamentNameOperation.setText("Unloading {}".format(str(self.changeFilamentComboBox.currentText())))

            self.changeFilamentHeatingFlag = True
            self.loadFlag = False
        except Exception as e:
            self.loadFlag = False
            self.changeFilamentHeatingFlag = False
            logger.error("Error in MainUiClass.unloadFilament: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.unloadFilament: {}".format(e), overlay=True)
        finally:
            # Re-enable SFS
            octopiclient.gcode(command="SFS_ENABLE1")

    def loadFilament(self):
        """
        Loads filament into the single extruder (tool0).
        """
        logger.info("MainUiClass.loadFilament started")
        try:
            # Disable SFS
            octopiclient.gcode(command="SFS_ENABLE0")
            
            # Move to the purge position for tool0
            if self.printerStatusText not in ["Printing", "Paused"]:
                octopiclient.jog(tool0PurgePosition['X'], tool0PurgePosition["Y"], absolute=True, speed=10000)

            if self.changeFilamentComboBox.findText("Loaded Filament") == -1:
                octopiclient.setToolTemperature({"tool0": filaments[str(self.changeFilamentComboBox.currentText())]})

            self.stackedWidget.setCurrentWidget(self.changeFilamentProgressPage)
            self.changeFilamentStatus.setText("Heating Tool 0, Please Wait...")
            self.changeFilamentNameOperation.setText("Loading {}".format(str(self.changeFilamentComboBox.currentText())))

            self.changeFilamentHeatingFlag = True
            self.loadFlag = True
        except Exception as e:
            self.loadFlag = False
            self.changeFilamentHeatingFlag = False
            logger.error("Error in MainUiClass.loadFilament: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.loadFilament: {}".format(e), overlay=True)
        finally:
            # Re-enable SFS
            octopiclient.gcode(command="SFS_ENABLE1")

    @run_async
    def changeFilamentLoadFunction(self):
        """
        This function is called once the heating is done, which slowly moves the extruder so that it starts pulling filament
        """
        logger.info("MainUiClass.changeFilamentLoadFunction started")
        try:
            self.stackedWidget.setCurrentWidget(self.changeFilamentLoadPage)
            while self.stackedWidget.currentWidget() == self.changeFilamentLoadPage:
                octopiclient.gcode("G91")
                octopiclient.gcode("G1 E5 F500")
                octopiclient.gcode("G90")
                time.sleep(self.calcExtrudeTime(5, 500))
        except Exception as e:
            logger.error("Error in MainUiClass.changeFilamentLoadFunction: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.changeFilamentLoadFunction: {}".format(e), overlay=True)

    @run_async
    def changeFilamentExtrudePageFunction(self):
        """
        once filament is loaded, this function is called to extrude filament till the toolhead
        """
        logger.info("MainUiClass.changeFilamentExtrudePageFunction started")
        try:
            self.stackedWidget.setCurrentWidget(self.changeFilamentExtrudePage)
            for i in range(int(ptfeTubeLength/150)):
                octopiclient.gcode("G91")
                octopiclient.gcode("G1 E150 F1500")
                octopiclient.gcode("G90")
                time.sleep(self.calcExtrudeTime(150, 1500))
                if self.stackedWidget.currentWidget() is not self.changeFilamentExtrudePage:
                    break

            while self.stackedWidget.currentWidget() == self.changeFilamentExtrudePage:
                if self.changeFilamentComboBox.currentText() == "TPU":
                    octopiclient.gcode("G91")
                    octopiclient.gcode("G1 E20 F300")
                    octopiclient.gcode("G90")
                    time.sleep(self.calcExtrudeTime(20, 300))
                else:
                    octopiclient.gcode("G91")
                    octopiclient.gcode("G1 E20 F600")
                    octopiclient.gcode("G90")
                    time.sleep(self.calcExtrudeTime(20, 600))
        except Exception as e:
            logger.error("Error in MainUiClass.changeFilamentExtrudePageFunction: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.changeFilamentExtrudePageFunction: {}".format(e), overlay=True)
    @run_async
    def changeFilamentRetractFunction(self):
        """
        Remove the filament from the toolhead
        """
        logger.info("MainUiClass.changeFilamentRetractFunction started")
        try:
            self.stackedWidget.setCurrentWidget(self.changeFilamentRetractPage)

            filament_type = self.changeFilamentComboBox.currentText()
            settings = filament_settings.get(filament_type, {})

            initialExtrudeLength = settings.get("initialExtrudeLength", 10)
            initialExtrudeSpeed = settings.get("initialExtrudeSpeed", 100)
            retractLength = settings.get("retractLength", 50)
            retractSpeed = settings.get("retractSpeed", 500)
            dwellTime = settings.get("dwellTime", 2)

            octopiclient.gcode("G91")
            octopiclient.gcode(f"G1 E{initialExtrudeLength} F{initialExtrudeSpeed}")
            time.sleep(self.calcExtrudeTime(initialExtrudeLength, initialExtrudeSpeed))
            time.sleep(dwellTime)
            octopiclient.gcode(f"G1 E-{retractLength} F{retractSpeed}")
            time.sleep(self.calcExtrudeTime(retractLength, retractSpeed))
            time.sleep(12)
            octopiclient.gcode("G90")

            for i in range(int(ptfeTubeLength/150)):
                octopiclient.gcode("G91")
                octopiclient.gcode("G1 E-150 F2000")
                octopiclient.gcode("G90")
                time.sleep(self.calcExtrudeTime(150, 2000))
                if self.stackedWidget.currentWidget() is not self.changeFilamentRetractPage:
                    break

            while self.stackedWidget.currentWidget() == self.changeFilamentRetractPage:
                octopiclient.gcode("G91")
                octopiclient.gcode("G1 E-5 F1200")
                octopiclient.gcode("G90")
                time.sleep(self.calcExtrudeTime(5, 1200))
        except Exception as e:
            logger.error("Error in MainUiClass.changeFilamentRetractFunction: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.changeFilamentRetractFunction: {}".format(e), overlay=True)

    def changeFilament(self):
        """
        This function is called when the user wants to change the filament. It sets the current page to the change filament page
        and preps the printer for filament change
        """
        logger.info("MainUiClass.changeFilament started")
        try:
            time.sleep(1)
            if self.printerStatusText not in ["Printing","Paused"]:
                octopiclient.gcode("G28")
            # self.selectToolChangeFilament()

            self.stackedWidget.setCurrentWidget(self.changeFilamentPage)
            self.changeFilamentComboBox.clear()
            self.changeFilamentComboBox.addItems(filaments.keys())
            print(self.tool0TargetTemperature)
            if self.tool0TargetTemperature  and self.printerStatusText in ["Printing","Paused"]:
                self.changeFilamentComboBox.addItem("Loaded Filament")
                index = self.changeFilamentComboBox.findText("Loaded Filament")
                if index >= 0 :
                    self.changeFilamentComboBox.setCurrentIndex(index)
        except Exception as e:
            logger.error("Error in MainUiClass.changeFilament: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.changeFilament: {}".format(e), overlay=True)
    def changeFilamentCancel(self):
        logger.info("MainUiClass.changeFilamentCancel started")
        try:
            self.changeFilamentHeatingFlag = False
            if self.printerStatusText not in ["Printing","Paused"]:
                self.coolDownAction()
            self.control()
            self.loadFlag = False
            self.changeFilamentHeatingFlag = False
        except Exception as e:
            logger.error("Error in MainUiClass.changeFilamentCancel: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.changeFilamentCancel: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++++++++++Job Operations+++++++++++++++++++++++++++++++ '''

    def stopActionMessageBox(self):
        """
        Displays a message box asking if the user is sure if he wants to turn off the print
        """
        logger.info("MainUiClass.stopActionMessageBox started")
        try:
            if dialog.WarningYesNo(self, "Are you sure you want to stop the print?"):
                octopiclient.cancelPrint()
        except Exception as e:
            logger.error("Error in MainUiClass.stopActionMessageBox: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.stopActionMessageBox: {}".format(e), overlay=True)

    def playPauseAction(self):
        """
        Toggles Play/Pause of a print depending on the status of the print
        """
        logger.info("MainUiClass.playPauseAction started")
        try:
            if self.printerStatusText == "Operational":
                if self.playPauseButton.isChecked:
                    self.checkKlipperPrinterCFG()
                    octopiclient.startPrint()
            elif self.printerStatusText == "Printing":
                octopiclient.pausePrint()
            elif self.printerStatusText == "Paused":
                octopiclient.pausePrint()
        except Exception as e:
            logger.error("Error in MainUiClass.playPauseAction: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.playPauseAction: {}".format(e), overlay=True)

    def fileListLocal(self):
        """
        Gets the file list from octoprint server, displays it on the list, as well as
        sets the stacked widget page to the file list page
        """
        logger.info("MainUiClass.fileListLocal started")
        try:
            self.stackedWidget.setCurrentWidget(self.fileListLocalPage)
            files = []
            for file in octopiclient.retrieveFileInformation()['files']:
                if file["type"] == "machinecode":
                    files.append(file)

            self.fileListWidget.clear()
            files.sort(key=lambda d: d['date'], reverse=True)
            self.fileListWidget.addItems([f['name'] for f in files])
            self.fileListWidget.setCurrentRow(0)
        except Exception as e:
            logger.error("Error in MainUiClass.fileListLocal: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.fileListLocal: {}".format(e), overlay=True)

    def fileListUSB(self):
        """
        Gets the file list from octoprint server, displays it on the list, as well as
        sets the stacked widget page to the file list page
        ToDO: Add deapth of folders recursively get all gcodes
        """
        logger.info("MainUiClass.fileListUSB started")
        try:
            self.stackedWidget.setCurrentWidget(self.fileListUSBPage)
            self.fileListWidgetUSB.clear()
            files = subprocess.Popen("ls /media/usb0 | grep gcode", stdout=subprocess.PIPE, shell=True).communicate()[0]
            files = files.decode('utf-8').split('\n')
            files = filter(None, files)
            self.fileListWidgetUSB.addItems(files)
            self.fileListWidgetUSB.setCurrentRow(0)
        except Exception as e:
            logger.error("Error in MainUiClass.fileListUSB: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.fileListUSB: {}".format(e), overlay=True)


    def printSelectedLocal(self):

        """
        gets information about the selected file from octoprint server,
        as well as sets the current page to the print selected page.
        This function also selects the file to print from octoprint
        """
        logger.info("MainUiClass.printSelectedLocal started")
        try:
            self.fileSelected.setText(self.fileListWidget.currentItem().text())
            self.stackedWidget.setCurrentWidget(self.printSelectedLocalPage)
            file = octopiclient.retrieveFileInformation(self.fileListWidget.currentItem().text())
            try:
                self.fileSizeSelected.setText(size(file['size']))
            except KeyError:
                self.fileSizeSelected.setText('-')
            try:
                self.fileDateSelected.setText(datetime.fromtimestamp(file['date']).strftime('%d/%m/%Y %H:%M:%S'))
            except KeyError:
                self.fileDateSelected.setText('-')
            try:
                m, s = divmod(file['gcodeAnalysis']['estimatedPrintTime'], 60)
                h, m = divmod(m, 60)
                d, h = divmod(h, 24)
                self.filePrintTimeSelected.setText("%dd:%dh:%02dm:%02ds" % (d, h, m, s))
            except KeyError:
                self.filePrintTimeSelected.setText('-')
            try:
                self.filamentVolumeSelected.setText(
                    ("%.2f cm" % file['gcodeAnalysis']['filament']['tool0']['volume']) + chr(179))
            except KeyError:
                self.filamentVolumeSelected.setText('-')

            try:
                self.filamentLengthFileSelected.setText(
                    "%.2f mm" % file['gcodeAnalysis']['filament']['tool0']['length'])
            except KeyError:
                self.filamentLengthFileSelected.setText('-')
            self.stackedWidget.setCurrentWidget(self.printSelectedLocalPage)

            self.displayThumbnail(self.printPreviewSelected, str(self.fileListWidget.currentItem().text()), usb=False)

        except Exception as e:
            logger.error("Error in MainUiClass.printSelectedLocal: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.printSelectedLocal: {}".format(e), overlay=True)


    def printSelectedUSB(self):
        """
        Sets the screen to the print selected screen for USB, on which you can transfer to local drive and view preview image.
        :return:
        """
        logger.info("MainUiClass.printSelectedUSB started")
        try:
            self.fileSelectedUSBName.setText(self.fileListWidgetUSB.currentItem().text())
            self.stackedWidget.setCurrentWidget(self.printSelectedUSBPage)
            self.displayThumbnail(self.printPreviewSelectedUSB, '/media/usb0/' + str(self.fileListWidgetUSB.currentItem().text()), usb=True)
        except Exception as e:
            logger.error("Error in MainUiClass.printSelectedUSB: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.printSelectedUSB: {}".format(e), overlay=True)

            # Set Image from USB

    def transferToLocal(self, prnt=False):
        """
        Transfers a file from USB mounted at /media/usb0 to octoprint's watched folder so that it gets automatically detected bu Octoprint.
        Warning: If the file is read-only, octoprint API for reading the file crashes.
        """
        logger.info("MainUiClass.transferToLocal started")
        try:
            file = '/media/usb0/' + str(self.fileListWidgetUSB.currentItem().text())

            self.uploadThread = ThreadFileUpload(file, prnt=prnt)
            self.uploadThread.start()
            if prnt:
                self.stackedWidget.setCurrentWidget(self.homePage)
        except Exception as e:
            logger.error("Error in MainUiClass.transferToLocal: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.transferToLocal: {}".format(e), overlay=True)

    def printFile(self):
        """
        Prints the file selected from printSelected()
        """
        logger.info("MainUiClass.printFile started")
        try:
            octopiclient.home(['x', 'y', 'z'])
            octopiclient.selectFile(self.fileListWidget.currentItem().text(), True)
            self.checkKlipperPrinterCFG()
            self.stackedWidget.setCurrentWidget(self.homePage)
        except Exception as e:
            logger.error("Error in MainUiClass.printFile: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.printFile: {}".format(e), overlay=True)


    def deleteItem(self):
        """
        Deletes a gcode file, and if associates, its image file from the memory
        """
        logger.info("MainUiClass.deleteItem started")
        try:
            octopiclient.deleteFile(self.fileListWidget.currentItem().text())
            octopiclient.deleteFile(self.fileListWidget.currentItem().text().replace(".gcode", ".png"))
            self.fileListLocal()
        except Exception as e:
            logger.error("Error in MainUiClass.deleteItem: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.deleteItem: {}".format(e), overlay=True)


    def getImageFromGcode(self,gcodeLocation):
        """
        Gets the image from the gcode text file
        """
        logger.info("MainUiClass.getImageFromGcode started")
        try:
            with open(gcodeLocation, 'rb') as f:
                content = f.readlines()[:500]
                content = b''.join(content)
            start = content.find(b'; thumbnail begin')
            end = content.find(b'; thumbnail end')
            if start != -1 and end != -1:
                thumbnail = content[start:end]
                thumbnail = base64.b64decode(thumbnail[thumbnail.find(b'\n') + 1:].replace(b'; ', b'').replace(b'\r\n', b''))
                return thumbnail
            else:
                return False
        except Exception as e:
            logger.error("Error in MainUiClass.getImageFromGcode: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.getImageFromGcode: {}".format(e), overlay=True)
            return False

    @run_async
    def displayThumbnail(self,labelObject,fileLocation, usb=False):
        """
        Displays the image on the label object
        :param labelObject: QLabel object to display the image
        :param fileLocation: location of the file
        :param usb: if the file is from
        """
        logger.info("MainUiClass.displayThumbnail started")
        try:
            pixmap = QtGui.QPixmap()
            if usb:
                img = self.getImageFromGcode(fileLocation)
            else:
                img = octopiclient.getImage(fileLocation)
            if img:
                pixmap.loadFromData(img)
                labelObject.setPixmap(pixmap)
            else:
                labelObject.setPixmap(QtGui.QPixmap(_fromUtf8("templates/img/thumbnail.png")))
        except Exception as e:
            labelObject.setPixmap(QtGui.QPixmap(_fromUtf8("templates/img/thumbnail.png")))
            logger.error("Error in MainUiClass.displayThumbnail: {}".format(e))

    ''' +++++++++++++++++++++++++++++++++Printer Status+++++++++++++++++++++++++++++++ '''

    def updateTemperature(self, temperature):
        """
        Slot that gets a signal originating from the thread that keeps polling for printer status
        runs at 1HZ, so do things that need to be constantly updated only. This also controls the cooling fan depending on the temperatures
        :param temperature: dict containing key:value pairs with keys being the tools, bed and their values being their corresponding temperatures
        """
        try:
            tool0_actual = temperature.get('tool0Actual', 0) or 0
            tool0_target = temperature.get('tool0Target', 0) or 0
            bed_actual = temperature.get('bedActual', 0) or 0
            bed_target = temperature.get('bedTarget', 0) or 0

            if tool0_target == 0:
                self.tool0TempBar.setMaximum(300)
                self.tool0TempBar.setStyleSheet(styles.bar_heater_cold)
            elif tool0_actual <= tool0_target:
                self.tool0TempBar.setMaximum(tool0_target)
                self.tool0TempBar.setStyleSheet(styles.bar_heater_heating)
            else:
                self.tool0TempBar.setMaximum(tool0_actual)
            self.tool0TempBar.setValue(tool0_actual)
            self.tool0ActualTemperature.setText(str(int(tool0_actual)))
            self.tool0TargetTemperature.setText(str(int(tool0_target)))

            if bed_target == 0:
                self.bedTempBar.setMaximum(150)
                self.bedTempBar.setStyleSheet(styles.bar_heater_cold)
            elif bed_actual <= bed_target:
                self.bedTempBar.setMaximum(bed_target)
                self.bedTempBar.setStyleSheet(styles.bar_heater_heating)
            else:
                self.bedTempBar.setMaximum(bed_actual)
            self.bedTempBar.setValue(bed_actual)
            self.bedActualTemperatute.setText(str(int(bed_actual)))
            self.bedTargetTemperature.setText(str(int(bed_target)))

            if self.changeFilamentHeatingFlag:
                if tool0_target == 0:
                    self.changeFilamentProgress.setMaximum(300)
                elif tool0_target - tool0_actual > 1:
                    self.changeFilamentProgress.setMaximum(tool0_target)
                else:
                    self.changeFilamentProgress.setMaximum(tool0_actual)
                    self.changeFilamentHeatingFlag = False
                    if self.loadFlag:
                        self.changeFilamentLoadFunction()
                    else:
                        octopiclient.extrude(5)
                        self.changeFilamentRetractFunction()
                self.changeFilamentProgress.setValue(tool0_actual)

        except Exception as e:
            logger.error("Error in MainUiClass.updateTemperature: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.updateTemperature: {}".format(e), overlay=True)

    def updatePrintStatus(self, file):
        """
        displays infromation of a particular file on the home page,is a slot for the signal emited from the thread that keeps pooling for printer status
        runs at 1HZ, so do things that need to be constantly updated only
        :param file: dict of all the attributes of a particualr file
        """

        try:
            if file is None:
                self.currentFile = None
                self.currentImage = None
                self.timeLeft.setText("-")
                self.fileName.setText("-")
                self.printProgressBar.setValue(0)
                self.printTime.setText("-")
                self.playPauseButton.setDisabled(True)

            else:
                self.playPauseButton.setDisabled(False)
                self.fileName.setText(file['job']['file']['name'])
                self.currentFile = file['job']['file']['name']
                if file['progress']['printTime'] is None:
                    self.printTime.setText("-")
                else:
                    m, s = divmod(file['progress']['printTime'], 60)
                    h, m = divmod(m, 60)
                    d, h = divmod(h, 24)
                    self.printTime.setText("%d:%d:%02d:%02d" % (d, h, m, s))

                if file['progress']['printTimeLeft'] is None:
                    self.timeLeft.setText("-")
                else:
                    m, s = divmod(file['progress']['printTimeLeft'], 60)
                    h, m = divmod(m, 60)
                    d, h = divmod(h, 24)
                    self.timeLeft.setText("%d:%d:%02d:%02d" % (d, h, m, s))

                if file['progress']['completion'] is None:
                    self.printProgressBar.setValue(0)
                else:
                    self.printProgressBar.setValue(file['progress']['completion'])

                if self.currentImage != self.currentFile:
                    self.currentImage = self.currentFile
                    self.displayThumbnail(self.printPreviewMain, self.currentFile, usb=False)
        except Exception as e:
            logger.error("Error in MainUiClass.updatePrintStatus: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.updatePrintStatus: {}".format(e), overlay=True)

    def updateStatus(self, status):
        """
        Updates the status bar, is a slot for the signal emited from the thread that constantly polls for printer status
        this function updates the status bar, as well as enables/disables relavent buttons
        :param status: String of the status text
        """
        try:
            self.printerStatusText = status
            self.printerStatus.setText(status)

            if status == "Printing":
                self.printerStatusColour.setStyleSheet(styles.printer_status_green)
            elif status == "Offline":
                self.printerStatusColour.setStyleSheet(styles.printer_status_red)
            elif status == "Paused":
                self.printerStatusColour.setStyleSheet(styles.printer_status_amber)
            elif status == "Operational":
                self.printerStatusColour.setStyleSheet(styles.printer_status_blue)

            if status == "Printing":
                self.playPauseButton.setChecked(True)
                self.stopButton.setDisabled(False)
                self.motionTab.setDisabled(True)
                self.changeFilamentButton.setDisabled(True)
                self.menuCalibrateButton.setDisabled(True)
                self.menuPrintButton.setDisabled(True)
                self.doorLockButton.setDisabled(False)

            elif status == "Paused":
                self.playPauseButton.setChecked(False)
                self.stopButton.setDisabled(False)
                self.motionTab.setDisabled(False)
                self.changeFilamentButton.setDisabled(False)
                self.menuCalibrateButton.setDisabled(True)
                self.menuPrintButton.setDisabled(True)
                self.doorLockButton.setDisabled(False)


            else:
                self.stopButton.setDisabled(True)
                self.playPauseButton.setChecked(False)
                self.motionTab.setDisabled(False)
                self.changeFilamentButton.setDisabled(False)
                self.menuCalibrateButton.setDisabled(False)
                self.menuPrintButton.setDisabled(False)
                self.doorLockButton.setDisabled(True)
        except Exception as e:
            logger.error("Error in MainUiClass.updateStatus: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.updateStatus: {}".format(e), overlay=True)

    ''' ++++++++++++++++++++++++++++Active Extruder/Tool Change++++++++++++++++++++++++ '''

    # def selectToolChangeFilament(self):
    #     """
    #     Selects the tool for filament change. Simplified for single extruder setup.
    #     """
    #     logger.info("MainUiClass.selectToolChangeFilament started")
    #     try:
    #         self.setActiveExtruder(0)
    #         octopiclient.selectTool(0)
    #         octopiclient.jog(tool0PurgePosition['X'], tool0PurgePosition["Y"], absolute=True, speed=10000)
    #         time.sleep(1)
    #     except Exception as e:
    #         logger.error("Error in MainUiClass.selectToolChangeFilament: {}".format(e))
    #         dialog.WarningOk(self, "Error in MainUiClass.selectToolChangeFilament: {}".format(e), overlay=True)

    # def setActiveExtruder(self, activeNozzle):
    #     """
    #     Sets the active extruder, and changes the UI accordingly. Simplified for single extruder setup.
    #     """
    #     logger.info("MainUiClass.setActiveExtruder started")
    #     try:
    #         self.tool0Label.setPixmap(QtGui.QPixmap(_fromUtf8("templates/img/activeNozzle.png")))
    #         self.toolToggleChangeFilamentButton.setChecked(False)
    #         self.toolToggleMotionButton.setChecked(False)
    #         self.toolToggleMotionButton.setText("0")
    #         self.activeExtruder = 0
    #     except Exception as e:
    #         logger.error("Error in MainUiClass.setActiveExtruder: {}".format(e))
    #         dialog.WarningOk(self, "Error in MainUiClass.setActiveExtruder: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++++++++++Control Screen+++++++++++++++++++++++++++++++ '''

    def control(self):
        """
        Sets the current page to the control page
        """
        logger.info("MainUiClass.control started")
        try:
            self.stackedWidget.setCurrentWidget(self.controlPage)
            self.toolTempSpinBox.setProperty("value", float(self.tool0TargetTemperature.text()))
            self.bedTempSpinBox.setProperty("value", float(self.bedTargetTemperature.text()))
        except Exception as e:
            logger.error("Error in MainUiClass.control: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.control: {}".format(e), overlay=True)

    def setStep(self, stepRate):
        """
        Sets the class variable "Step" which would be needed for movement and joging
        :param stepRate: step multiplier for movement in the move
        :return: nothing
        """
        logger.info("MainUiClass.setStep started")
        try:
            if stepRate == 100:
                self.step100Button.setFlat(True)
                self.step1Button.setFlat(False)
                self.step10Button.setFlat(False)
                self.step = 100
            if stepRate == 1:
                self.step100Button.setFlat(False)
                self.step1Button.setFlat(True)
                self.step10Button.setFlat(False)
                self.step = 1
            if stepRate == 10:
                self.step100Button.setFlat(False)
                self.step1Button.setFlat(False)
                self.step10Button.setFlat(True)
                self.step = 10
        except Exception as e:
            logger.error("Error in MainUiClass.setStep: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.setStep: {}".format(e), overlay=True)

    def setToolTemp(self):
        """
        Sets the temperature of the tool (tool0) for a single extruder setup.
        """
        logger.info("MainUiClass.setToolTemp started")
        try:
            octopiclient.gcode(command='M104 T0 S' + str(self.toolTempSpinBox.value()))
        except Exception as e:
            logger.error("Error in MainUiClass.setToolTemp: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.setToolTemp: {}".format(e), overlay=True)

    def preheatToolTemp(self, temp):
        """
        Preheats the tool (tool0) to the given temperature for a single extruder setup.
        :param temp: Temperature to preheat to
        """
        logger.info("MainUiClass.preheatToolTemp started")
        try:
            octopiclient.gcode(command='M104 T0 S' + str(temp))
            self.toolTempSpinBox.setProperty("value", temp)
        except Exception as e:
            logger.error("Error in MainUiClass.preheatToolTemp: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.preheatToolTemp: {}".format(e), overlay=True)

    def preheatBedTemp(self, temp):
        """
        Preheats the bed to the given temperature
        param temp: temperature to preheat to
        """
        logger.info("MainUiClass.preheatBedTemp started")
        try:
            octopiclient.gcode(command='M140 S' + str(temp))
            self.bedTempSpinBox.setProperty("value", temp)
        except Exception as e:
            logger.error("Error in MainUiClass.preheatBedTemp: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.preheatBedTemp: {}".format(e), overlay=True)

    def coolDownAction(self):
        """
        Turns off all heaters and fans for a single extruder setup.
        """
        logger.info("MainUiClass.coolDownAction started")
        try:
            octopiclient.gcode(command='M107')
            octopiclient.setToolTemperature({"tool0": 0})
            octopiclient.setBedTemperature(0)
            self.toolTempSpinBox.setProperty("value", 0)
            self.bedTempSpinBox.setProperty("value", 0)
        except Exception as e:
            logger.error("Error in MainUiClass.coolDownAction: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.coolDownAction: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++++++++++++Calibration++++++++++++++++++++++++++++++++ '''

    def inputShaperCalibrate(self):
        logger.info("MainUiClass.inputShaperCalibrate started")
        try:
            dialog.WarningOk(self, "Wait for all calibration movements to finish before proceeding.", overlay=True)
            octopiclient.gcode(command='G28')
            octopiclient.gcode(command='SHAPER_CALIBRATE')
            octopiclient.gcode(command='SAVE_CONFIG')

        except Exception as e:
            error_message = f"Error in inptuShaperCalibrate: {str(e)}"
            logger.error(error_message)
            dialog.WarningOk(error_message, overlay=True)

    # def setZToolOffset(self, offset):
    #     """
    #     Sets the home offset after the caliberation wizard is done, which is a callback to
    #     the response of M114 that is sent at the end of the Wizard in doneStep()
    #     :param offset: the value off the offset to set. is a str is coming from M114, and is float if coming from the nozzleOffsetPage
    #     :return:

    #     #TODO can make this simpler, asset the offset value to string float to begin with instead of doing confitionals
    #     """
    #     logger.info("MainUiClass.setZToolOffset started")
    #     self.currentZPosition = offset
    #     try:
    #         if self.setNewToolZOffsetFromCurrentZBool:
    #             print(self.toolOffsetZ)
    #             print(self.currentZPosition)
    #             newToolOffsetZ = (float(self.toolOffsetZ) + float(self.currentZPosition))
    #             octopiclient.gcode(command='M218 T1 Z{}'.format(newToolOffsetZ))
    #             self.setNewToolZOffsetFromCurrentZBool =False
    #             octopiclient.gcode(command='SAVE_CONFIG')
    #     except Exception as e:
    #         logger.error("Error in MainUiClass.setZToolOffset: {}".format(e))
    #         dialog.WarningOk(self, "Error in MainUiClass.setZToolOffset: {}".format(e), overlay=True)

    def showProbingFailed(self,msg='Probing Failed, Calibrate bed again or check for hardware issue',overlay=True):
        logger.info("MainUiClass.showProbingFailed started")
        try:
            if dialog.WarningOk(self, msg, overlay=overlay):
                octopiclient.cancelPrint()
                return True
            return False
        except Exception as e:
            logger.error("Error in MainUiClass.showProbingFailed: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.showProbingFailed: {}".format(e), overlay=True)

    def showPrinterError(self, msg='Printer error, Check Terminal', overlay=False):
        logger.info("MainUiClass.showPrinterError started")
        try:
            if any(error in msg for error in
                   ["Can not update MCU","Error loading template", "Must home axis first", "probe", "Error during homing move", "still triggered after retract", "'mcu' must be specified"]):
                logger.error("CRITICAL ERROR SHUTDOWN NEEDED")
                if self.printerStatusText in ["Starting","Printing","Paused"]:
                    octopiclient.cancelPrint()
                    octopiclient.gcode(command='M112')
                    try:
                        octopiclient.connectPrinter(port="/tmp/printer", baudrate=115200)
                    except Exception as e:
                        octopiclient.connectPrinter(port="VIRTUAL", baudrate=115200)
                    octopiclient.gcode(command='FIRMWARE_RESTART')
                    octopiclient.gcode(command='RESTART')
                    if not self.dialogShown:
                        self.dialogShown = True
                        if dialog.WarningOk(self, msg + ", Cancelling Print.", overlay=overlay):
                            self.dialogShown = False
                    logger.error("CRITICAL ERROR SHUTDOWN DONE")
                else:
                    if not self.dialogShown:
                        self.dialogShown = True
                        octopiclient.gcode(command='FIRMWARE_RESTART')
                        octopiclient.gcode(command='RESTART')
                        if dialog.WarningOk(self, msg, overlay=overlay):
                            self.dialogShown = False

            else:
                if not self.dialogShown:
                    self.dialogShown = True
                    if dialog.WarningOk(self, msg, overlay=overlay):
                        self.dialogShown = False

        except Exception as e:
            logger.error("Error in MainUiClass.showPrinterError: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.showPrinterError: {}".format(e), overlay=True)
    def updateEEPROMProbeOffset(self, offset):
        """
        Sets the spinbox value to have the value of the Z offset from the printer.
        the value is -ve so as to be more intuitive.
        :param offset:
        :return:
        """
        logger.info("MainUiClass.updateEEPROMProbeOffset started")
        try:
            self.currentNozzleOffset.setText(str(float(offset)))
            self.nozzleOffsetDoubleSpinBox.setValue(0)
        except Exception as e:
            logger.error("Error in MainUiClass.updateEEPROMProbeOffset: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.updateEEPROMProbeOffset: {}".format(e), overlay=True)


    def setZProbeOffset(self, offset):
        """
        Sets Z Probe offset from spinbox

        #TODO can make this simpler, asset the offset value to string float to begin with instead of doing confitionals
        """
        logger.info("MainUiClass.setZProbeOffset started")
        try:
            octopiclient.gcode(command='M851 Z{}'.format(round(float(offset),2)))
            self.nozzleOffsetDoubleSpinBox.setValue(0)
            _offset=float(self.currentNozzleOffset.text())+float(offset)
            self.currentNozzleOffset.setText(str(float(self.currentNozzleOffset.text())-float(offset)))
            octopiclient.gcode(command='M500')
        except Exception as e:
            logger.error("Error in MainUiClass.setZProbeOffset: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.setZProbeOffset: {}".format(e), overlay=True)

    def requestEEPROMProbeOffset(self):
        """
        Updates the value of M206 Z in the nozzle offset spinbox. Sends M503 so that the pritner returns the value as a websocket calback
        :return:
        """
        logger.info("MainUiClass.requestEEPROMProbeOffset started")
        try:
            octopiclient.gcode(command='M503')
            self.stackedWidget.setCurrentWidget(self.nozzleOffsetPage)
        except Exception as e:
            logger.error("Error in MainUiClass.requestEEPROMProbeOffset: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.requestEEPROMProbeOffset: {}".format(e), overlay=True)

    def nozzleOffset(self):
        """
        Updates the value of M206 Z in the nozzle offset spinbox. Sends M503 so that the pritner returns the value as a websocket calback
        :return:
        """
        logger.info("MainUiClass.nozzleOffset started")
        try:
            octopiclient.gcode(command='M503')
            self.stackedWidget.setCurrentWidget(self.nozzleOffsetPage)
        except Exception as e:
            logger.error("Error in MainUiClass.nozzleOffset: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.nozzleOffset: {}".format(e), overlay=True)

    def quickStep1(self):
        """
        Shows welcome message.
        Homes to MAX
        Goes to position where leveling screws can be opened.
        """
        logger.info("MainUiClass.quickStep1 started")
        try:
            octopiclient.gcode(command='M104 S200')
            octopiclient.gcode(command='M420 S0')
            self.stackedWidget.setCurrentWidget(self.quickStep1Page)
            octopiclient.home(['x', 'y', 'z'])
            octopiclient.jog(x=40, y=40, absolute=True, speed=2000)
        except Exception as e:
            logger.error("Error in MainUiClass.quickStep1: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.quickStep1: {}".format(e), overlay=True)

    def quickStep2(self):
        """
        Levels the first position (RIGHT).
        """
        logger.info("MainUiClass.quickStep2 started")
        try:
            self.stackedWidget.setCurrentWidget(self.quickStep2Page)
            octopiclient.jog(x=calibrationPosition['X1'], y=calibrationPosition['Y1'], absolute=True, speed=10000)
            octopiclient.jog(z=0, absolute=True, speed=1500)
            self.movie1 = QtGui.QMovie("templates/img/Calibration/CalibrationPoint1.gif")
            self.CalibrationPoint1.setMovie(self.movie1)
            self.movie1.start()
        except Exception as e:
            logger.error("Error in MainUiClass.quickStep2: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.quickStep2: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
            except:
                pass

    def quickStep3(self):
        """
        Levels the second leveling position (LEFT).
        """
        logger.info("MainUiClass.quickStep3 started")
        try:
            self.stackedWidget.setCurrentWidget(self.quickStep3Page)
            octopiclient.jog(z=10, absolute=True, speed=1500)
            octopiclient.jog(x=calibrationPosition['X2'], y=calibrationPosition['Y2'], absolute=True, speed=10000)
            octopiclient.jog(z=0, absolute=True, speed=1500)
            self.movie1.stop()
            self.movie2 = QtGui.QMovie("templates/img/Calibration/CalibrationPoint2.gif")
            self.CalibrationPoint2.setMovie(self.movie2)
            self.movie2.start()
        except Exception as e:
            logger.error("Error in MainUiClass.quickStep3: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.quickStep3: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
                self.movie2.stop()
            except:
                pass

    def quickStep4(self):
        """
        Levels the third leveling position (BACK).
        """
        logger.info("MainUiClass.quickStep4 started")
        try:
            self.stackedWidget.setCurrentWidget(self.quickStep4Page)
            octopiclient.jog(z=10, absolute=True, speed=1500)
            octopiclient.jog(x=calibrationPosition['X3'], y=calibrationPosition['Y3'], absolute=True, speed=10000)
            octopiclient.jog(z=0, absolute=True, speed=1500)
            self.movie2.stop()
            self.movie3 = QtGui.QMovie("templates/img/Calibration/CalibrationPoint3.gif")
            self.CalibrationPoint3.setMovie(self.movie3)
            self.movie3.start()
        except Exception as e:
            logger.error("Error in MainUiClass.quickStep4: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.quickStep4: {}".format(e), overlay=True)
            try:
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass


    # def nozzleHeightStep1(self):
    #     logger.info("MainUiClass.nozzleHeightStep1 started")
    #     try:
    #         self.movie3.stop()
    #         if self.toolZOffsetCaliberationPageCount == 0 :
    #             self.toolZOffsetLabel.setText("Move the bed up or down to the First Nozzle , testing height using paper")
    #             self.stackedWidget.setCurrentWidget(self.nozzleHeightStep1Page)
    #             octopiclient.jog(z=10, absolute=True, speed=1500)
    #             octopiclient.jog(x=calibrationPosition['X4'], y=calibrationPosition['Y4'], absolute=True, speed=10000)
    #             octopiclient.jog(z=1, absolute=True, speed=1500)
    #             self.toolZOffsetCaliberationPageCount = 1
    #         else:
    #             self.doneStep()
    #     except Exception as e:
    #         logger.error("Error in MainUiClass.nozzleHeightStep1: {}".format(e))
    #         dialog.WarningOk(self, "Error in MainUiClass.nozzleHeightStep1: {}".format(e), overlay=True)
    #         try:
    #             self.movie1.stop()
    #             self.movie2.stop()
    #             self.movie3.stop()
    #         except:
    #             pass

    def doneStep(self):
        """
        Exits leveling and finalizes the calibration process for a single extruder setup.
        """
        logger.info("MainUiClass.doneStep started")
        try:
            #self.setNewToolZOffsetFromCurrentZBool = True

            octopiclient.gcode(command='M114')
            octopiclient.jog(z=4, absolute=True, speed=1500)

            octopiclient.gcode(command='T0')

            self.stackedWidget.setCurrentWidget(self.calibratePage)
            octopiclient.home(['x', 'y', 'z'])

            octopiclient.gcode(command='M104 S0')
            octopiclient.gcode(command='M84')

            octopiclient.gcode(command='M500')
        except Exception as e:
            logger.error("Error in MainUiClass.doneStep: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.doneStep: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass

    def cancelStep(self):
        """
        Cancels the calibration process and resets the printer for a single extruder setup.
        """
        logger.info("MainUiClass.cancelStep started")
        try:
            self.stackedWidget.setCurrentWidget(self.calibratePage)

            octopiclient.home(['x', 'y', 'z'])

            octopiclient.gcode(command='M104 S0')

            octopiclient.gcode(command='M84')

# Stop any running animations
            try:
                self.movie1.stop()
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass
        except Exception as e:
            logger.error("Error in MainUiClass.cancelStep: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.cancelStep: {}".format(e), overlay=True)
            try:
                self.movie1.stop()
                self.movie2.stop()
                self.movie3.stop()
            except:
                pass

    
    def testPrint(self,tool0Diameter,gcode):
        """
        Prints a test print
        :param tool0Diameter: Diameter of tool 0 nozzle.04,06 or 08
        :param gcode: type of gcode to print, bed leveling, movement or sample prints in single. bedLevel, movementTest, singleTest
        :return:
        """
        logger.info("MainUiClass.testPrint started")
        try:
            if gcode is 'bedLevel':
                self.printFromPath('gcode/' + tool0Diameter + '_BedLeveling.gcode', True)
            elif gcode is 'movementTest':
                self.printFromPath('gcode/movementTest.gcode', True)
            elif gcode is 'singleTest':
                self.printFromPath('gcode/' + tool0Diameter + '_Fracktal_logo_Idex.gcode',True)

            else:
                print("gcode not found")
        except Exception as e:
            logger.error("Error in MainUiClass.testPrint: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.testPrint: {}".format(e), overlay=True)
    
    def printFromPath(self,path,prnt=True):
        """
        Transfers a file from a specific to octoprint's watched folder so that it gets automatically detected by Octoprint.
        Warning: If the file is read-only, octoprint API for reading the file crashes.
        """
        logger.info("MainUiClass.printFromPath started")
        try:
            self.uploadThread = ThreadFileUpload(path, prnt=prnt)
            self.uploadThread.start()
            if prnt:
                self.stackedWidget.setCurrentWidget(self.homePage)
        except Exception as e:
            logger.error("Error in MainUiClass.printFromPath: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.printFromPath: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++++++++++++Keyboard++++++++++++++++++++++++++++++++ '''

    def startKeyboard(self, returnFn, onlyNumeric=False, noSpace=False, text=""):
        """
        starts the keyboard screen for entering Password
        """
        logger.info("MainUiClass.startKeyboard started")
        try:
            keyBoardobj = keyboard.Keyboard(onlyNumeric=onlyNumeric, noSpace=noSpace, text=text)
            keyBoardobj.keyboard_signal.connect(returnFn)
            keyBoardobj.setWindowFlags(QtCore.Qt.FramelessWindowHint)
            keyBoardobj.show()
        except Exception as e:
            logger.error("Error in MainUiClass.startKeyboard: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.startKeyboard: {}".format(e), overlay=True)

    ''' ++++++++++++++++++++++++++++++Restore Defaults++++++++++++++++++++++++++++ '''

    def restoreFactoryDefaults(self):
        logger.info("MainUiClass.restoreFactoryDefaults started")
        try:
            if dialog.WarningYesNo(self, "Are you sure you want to restore machine state to factory defaults?\nWarning: Doing so will also reset printer profiles, WiFi & Ethernet config.",
                                   overlay=True):
                os.system('sudo cp -f config/dhcpcd.conf /etc/dhcpcd.conf')
                os.system('sudo cp -f config/wpa_supplicant.conf /etc/wpa_supplicant/wpa_supplicant.conf')
                os.system('sudo rm -rf /home/pi/.octoprint/users.yaml')
                os.system('sudo cp -f config/users.yaml /home/pi/.octoprint/users.yaml')
                os.system('sudo rm -rf /home/pi/.octoprint/printerProfiles/*')
                os.system('sudo rm -rf /home/pi/.octoprint/scripts/gcode')
                os.system('sudo rm -rf /home/pi/.octoprint/print_restore.json')
                os.system('sudo cp -f config/config.yaml /home/pi/.octoprint/config.yaml')
                self.tellAndReboot("Settings restored. Rebooting...")
        except Exception as e:
            logger.error("Error in MainUiClass.restoreFactoryDefaults: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.restoreFactoryDefaults: {}".format(e), overlay=True)

    def restorePrintDefaults(self):
        logger.info("MainUiClass.restorePrintDefaults started")
        try:
            if dialog.WarningYesNo(self, "Are you sure you want to restore default print settings?\nWarning: Doing so will erase offsets and bed leveling info",
                                   overlay=True):
                os.system('sudo cp -f firmware/FILAMENT_SENSOR_DRAGON.cfg /home/pi/FILAMENT_SENSOR_DRAGON.cfg')
                os.system('sudo cp -f firmware/COMMON_GCODE_MACROS.cfg /home/pi/COMMON_GCODE_MACROS.cfg')
                os.system('sudo cp -f firmware/MOTHERBOARD_DRAGON.cfg /home/pi/MOTHERBOARD_DRAGON.cfg')
                os.system('sudo cp -f firmware/PRINTERS_DRAGON_400x300.cfg /home/pi/PRINTERS_DRAGON_400x300.cfg')
                os.system('sudo cp -f firmware/PRINTERS_DRAGON_500x400.cfg /home/pi/PRINTERS_DRAGON_500x400.cfg')
                os.system('sudo cp -f firmware/PRINTERS_DRAGON_700x600.cfg /home/pi/PRINTERS_DRAGON_700x600.cfg')
                os.system('sudo cp -f firmware/TOOLHEADS_TD-01_TOOLHEAD0.cfg /home/pi/TOOLHEADS_TD-01_TOOLHEAD0.cfg')
                os.system('sudo cp -f firmware/variables.cfg /home/pi/variables.cfg')
                octopiclient.gcode(command='M502')
                octopiclient.gcode(command='M500')
                octopiclient.gcode(command='FIRMWARE_RESTART')
                octopiclient.gcode(command='RESTART')
        except Exception as e:
            logger.error("Error in MainUiClass.restorePrintDefaults: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.restorePrintDefaults: {}".format(e), overlay=True)

    ''' +++++++++++++++++++++++++++++++++++ Misc ++++++++++++++++++++++++++++++++ '''

    def tellAndReboot(self, msg="Rebooting...", overlay=True):
        if dialog.WarningOk(self, msg, overlay=overlay):
            os.system('sudo reboot now')
            return True
        return False

    def askAndReboot(self, msg="Are you sure you want to reboot?", overlay=True):
        if dialog.WarningYesNo(self, msg, overlay=overlay):
            os.system('sudo reboot now')
            return True
        return False

    def checkKlipperPrinterCFG(self):
        """
        Checks for valid printer.cfg and restores if needed
        """

        logger.info("MainUiClass.checkKlipperPrinterCFG started")
        try:
            try:
                with open('/home/pi/printer.cfg', 'r') as currentConfigFile:
                    currentConfig = currentConfigFile.read()
                    if "# MCU Config" in currentConfig:
                        configCorruptedFlag = False
                        logger.info("Printer Config File OK")
                    else:
                        configCorruptedFlag = True
                        logger.error("Printer Config File Corrupted, Attempting to restore Backup")

            except:
                configCorruptedFlag = True
                logger.error("Printer Config File Not Found, Attempting to restore Backup")

            if configCorruptedFlag:
                backupFiles = sorted(glob.glob('/home/pi/printer-*.cfg'), key=os.path.getmtime, reverse=True)
                print("\n".join(backupFiles))
                for backupFile in backupFiles:
                    with open(str(backupFile), 'r') as backupConfigFile:
                        backupConfig = backupConfigFile.read()
                        if "# MCU Config" in backupConfig:
                            try:
                                os.remove('/home/pi/printer.cfg')
                            except:
                                logger.error("printer.cfg does not exist for deletion")
                            try:
                                os.rename(backupFile, '/home/pi/printer.cfg')
                                logger.info("Printer Config File Restored")
                                return()
                            except:
                                pass
# If no valid backups found, show error dialog:
                dialog.WarningOk(self, "Printer Config File corrupted. Contact Fracktal support or raise a ticket at care.fracktal.in")
                if self.printerStatus == "Printing":
                    octopiclient.cancelPrint()
                    self.coolDownAction()
            elif not configCorruptedFlag:
                backupFiles = sorted(glob.glob('/home/pi/printer-*.cfg'), key=os.path.getmtime, reverse=True)
                try:
                    for backupFile in backupFiles[5:]:
                        os.remove(backupFile)
                except:
                    pass
        except Exception as e:
            logger.error("Error in MainUiClass.checkKlipperPrinterCFG: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.checkKlipperPrinterCFG: {}".format(e), overlay=True)

    def pairPhoneApp(self):
        logger.info("MainUiClass.pairPhoneApp started")
        try:
            if getIP(ThreadRestartNetworking.ETH) is not None:
                qrip = getIP(ThreadRestartNetworking.ETH)
            elif getIP(ThreadRestartNetworking.WLAN) is not None:
                qrip = getIP(ThreadRestartNetworking.WLAN)
            else:
                if dialog.WarningOk(self, "Network Disconnected"):
                    return
            self.QRCodeLabel.setPixmap(
                qrcode.make("http://"+ qrip, image_factory=Image).pixmap())
            self.stackedWidget.setCurrentWidget(self.QRCodePage)
        except Exception as e:
            logger.error("Error in MainUiClass.pairPhoneApp: {}".format(e))
            dialog.WarningOk(self, "Error in MainUiClass.pairPhoneApp: {}".format(e), overlay=True)

class QtWebsocket(QtCore.QThread):
    """
    https://pypi.python.org/pypi/websocket-client
    https://wiki.python.org/moin/PyQt/Threading,_Signals_and_Slots
    """
    z_home_offset_signal = QtCore.pyqtSignal(str)
    temperatures_signal = QtCore.pyqtSignal(dict)
    status_signal = QtCore.pyqtSignal(str)
    print_status_signal = QtCore.pyqtSignal('PyQt_PyObject')
    update_started_signal = QtCore.pyqtSignal(dict)
    update_log_signal = QtCore.pyqtSignal(dict)
    update_log_result_signal = QtCore.pyqtSignal(dict)
    update_failed_signal = QtCore.pyqtSignal(dict)
    connected_signal = QtCore.pyqtSignal()
    filament_sensor_triggered_signal = QtCore.pyqtSignal(str)
    firmware_updater_signal = QtCore.pyqtSignal(dict)
    z_probe_offset_signal = QtCore.pyqtSignal(str)
    z_probing_failed_signal = QtCore.pyqtSignal()
    printer_error_signal = QtCore.pyqtSignal(str)

    def __init__(self):
        logger.info("QtWebsocket started")
        super(QtWebsocket, self).__init__()
        self.ws = None
        self.heartbeat_timer = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        self._initialize_websocket()

    def _initialize_websocket(self):
        try:
            url = "ws://{}/sockjs/{:0>3d}/{}/websocket".format(
                ip,
                random.randrange(0, stop=999),
                uuid.uuid4()
            )
            self.ws = websocket.WebSocketApp(
                url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
        except Exception as e:
            logger.error("Error initializing WebSocket: {}".format(e))

    def run(self):
        logger.info("QtWebsocket.run started")
        try:
            self.ws.run_forever()
            self.reset_heartbeat_timer()
        except Exception as e:
            logger.error("Error in QtWebsocket.run: {}".format(e))

    def reset_heartbeat_timer(self):
        try:
            if self.heartbeat_timer is not None:
                self.heartbeat_timer.cancel()

            self.heartbeat_timer = threading.Timer(120, self.reestablish_connection)
            self.heartbeat_timer.start()
        except Exception as e:
            logger.error("Error in QtWebsocket.reset_heartbeat_timer: {}".format(e))

    def reestablish_connection(self):
        logger.info("Reestablishing WebSocket connection...")
        try:
            self.reconnect_attempts += 1
            if self.reconnect_attempts > self.max_reconnect_attempts:
                logger.error("Max reconnect attempts reached. Giving up.")
                return

            self._initialize_websocket()
            self.start()
            logger.info("Reconnection attempt {} succeeded.".format(self.reconnect_attempts))
        except Exception as e:
            logger.error("Error in QtWebsocket.reestablish_connection: {}".format(e))

    def send(self, data):
        logger.info("QtWebsocket.send started")
        try:
            payload = '["' + json.dumps(data).replace('"', '\\"') + '"]'
            self.ws.send(payload)
        except Exception as e:
            logger.error("Error in QtWebsocket.send: {}".format(e))

    def authenticate(self):
        logger.info("QtWebsocket.authenticate started")
        try:
            url = 'http://' + ip + '/api/login'
            headers = {'content-type': 'application/json', 'X-Api-Key': apiKey}
            payload = {"passive": True}
            response = requests.post(url, data=json.dumps(payload), headers=headers)
            data = response.json()

            # Prepare auth payload
            auth_message = {"auth": "{name}:{session}".format(**data)}

            # Send it
            self.send(auth_message)
        except Exception as e:
            logger.error("Error in QtWebsocket.authenticate: {}".format(e))

    def on_message(self, ws, message):
        message_type = message[0]
        if message_type == "h":
            # "heartbeat" message
            self.reset_heartbeat_timer()
            return
        elif message_type == "o":
            # "open" message
            return
        elif message_type == "c":
            # "close" message
            return

        message_body = message[1:]
        if not message_body:
            return
        data = json.loads(message_body)[0]

        if message_type == "m":
            data = [data, ]

        if message_type == "a":
            self.process(data)

    def on_open(self, ws):
        logger.info("WebSocket connection opened")
        self.reconnect_attempts = 0  # Reset reconnect attempts
        self.authenticate()

    def on_close(self, ws):
        logger.warning("WebSocket connection closed. Attempting to reconnect...")
        self.reestablish_connection()

    def on_error(self, ws, error):
        logger.error("WebSocket error: {}".format(error))
        self.reestablish_connection()

    @run_async
    def process(self, data):
        try:
            if "event" in data:
                if data["event"]["type"] == "Connected":
                    self.connected_signal.emit()
                    print("connected")
            if "plugin" in data:
                if data["plugin"]["plugin"] == 'softwareupdate':
                    if data["plugin"]["data"]["type"] == "updating":
                        self.update_started_signal.emit(data["plugin"]["data"]["data"])
                    elif data["plugin"]["data"]["type"] == "loglines":
                        self.update_log_signal.emit(data["plugin"]["data"]["data"]["loglines"])
                    elif data["plugin"]["data"]["type"] == "restarting":
                        self.update_log_result_signal.emit(data["plugin"]["data"]["data"]["results"])
                    elif data["plugin"]["data"]["type"] == "update_failed":
                        self.update_failed_signal.emit(data["plugin"]["data"]["data"])

            if "current" in data:
                if data["current"]["messages"]:
                    for item in data["current"]["messages"]:
                        if 'Filament Runout or clogged' in item:
                            self.filament_sensor_triggered_signal.emit(item[item.index('T') + 1:].split(' ', 1)[0])

                        if 'Primary FS Status' in item:
                            self.filament_sensor_triggered_signal.emit(item)

                        if 'M206' in item:
                            self.z_home_offset_signal.emit(item[item.index('Z') + 1:].split(' ', 1)[0])
                        # if 'Count' in item:
                        #     self.set_z_tool_offset_signal.emit(item[item.index('z') + 2:].split(',', 1)[0],
                        #               False)
                        if 'M851' in item:
                            self.z_probe_offset_signal.emit(item[item.index('Z') + 1:].split(' ', 1)[0])
                        if 'PROBING_FAILED' in item:
                            self.z_probing_failed_signal.emit()

                        for ignore_item in [
                            "!! Printer is not ready",
                            "!! Move out of range:",
                            "!! Shutdown due to M112"
                        ]:
                           if ignore_item in item:
                               break
                        else:
                           if item.startswith('!!') or item.startswith('Error'):
                               self.printer_error_signal.emit(item)
                               logger.error("Error From Klipper/Printer: {}".format(item))

                if data["current"]["state"]["text"]:
                    self.status_signal.emit(data["current"]["state"]["text"])

                fileInfo = {"job": data["current"]["job"], "progress": data["current"]["progress"]}
                if fileInfo['job']['file']['name'] is not None:
                    self.print_status_signal.emit(fileInfo)
                else:
                    self.print_status_signal.emit(None)

                def temp(data, tool, temp):
                    try:
                        if tool in data["current"]["temps"][0]:
                            return data["current"]["temps"][0][tool][temp]
                    except:
                        pass
                    return 0

                if data["current"]["temps"] and len(data["current"]["temps"]) > 0:
                    try:
                        temperatures = {'tool0Actual': temp(data, "tool0", "actual"),
                                        'tool0Target': temp(data, "tool0", "target"),
                                        'bedActual': temp(data, "bed", "actual"),
                                        'bedTarget': temp(data, "bed", "target")}
                        self.temperatures_signal.emit(temperatures)
                    except KeyError:
                        pass
        except Exception as e:
            logger.error("Error in QtWebsocket.process: {}".format(e))

class ThreadSanityCheck(QtCore.QThread):

    loaded_signal = QtCore.pyqtSignal()
    startup_error_signal = QtCore.pyqtSignal()

    def __init__(self, logger = None, virtual=False):
        super(ThreadSanityCheck, self).__init__()
        self.MKSPort = None
        self.virtual = virtual
        if not Development:
            self._logger = logger

    def run(self):
        global octopiclient
        self.shutdown_flag = False
        uptime = 0
        while (True):
            try:
                if (uptime > 60):
                    self.shutdown_flag = True
                    self.startup_error_signal.emit()
                    break
                octopiclient = octoprintAPI(ip, apiKey)
                if not self.virtual:
                    try:
                        octopiclient.connectPrinter(port="/tmp/printer", baudrate=115200)
                    except Exception as e:
                        octopiclient.connectPrinter(port="VIRTUAL", baudrate=115200)
                break
            except Exception as e:
                time.sleep(1)
                uptime = uptime + 1
                print("Not Connected!")
        if not self.shutdown_flag:
            self.loaded_signal.emit()

class ThreadFileUpload(QtCore.QThread):
    def __init__(self, file, prnt=False):
        super(ThreadFileUpload, self).__init__()
        self.file = file
        self.prnt = prnt

    def run(self):

        try:
            exists = os.path.exists(self.file.replace(".gcode", ".png"))
        except:
            exists = False
        if exists:
            octopiclient.uploadImage(self.file.replace(".gcode", ".png"))

        if self.prnt:
            octopiclient.uploadGcode(file=self.file, select=True, prnt=True)
        else:
            octopiclient.uploadGcode(file=self.file, select=False, prnt=False)

class ThreadRestartNetworking(QtCore.QThread):
    WLAN = "wlan0"
    ETH = "eth0"
    signal = QtCore.pyqtSignal('PyQt_PyObject')

    def __init__(self, interface):
        super(ThreadRestartNetworking, self).__init__()
        self.interface = interface
    def run(self):
        self.restart_interface()
        attempt = 0
        while attempt < 3:
            if getIP(self.interface):
                self.signal.emit(getIP(self.interface))
                break
            else:
                attempt += 1
                time.sleep(5)
        if attempt >= 3:
            self.signal.emit(None)

    def restart_interface(self):
        """
        restars wlan0 wireless interface to use new changes in wpa_supplicant.conf file
        :return:
        """
        if self.interface == "wlan0":
            subprocess.call(["wpa_cli","-i",  self.interface, "reconfigure"], shell=False)
        if self.interface == "eth0":
            subprocess.call(["ifconfig",  self.interface, "down"], shell=False)
            time.sleep(1)
            subprocess.call(["ifconfig", self.interface, "up"], shell=False)
        time.sleep(5)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
# Intialize the library (must be called once before other functions).
    # Creates an object of type MainUiClass
    MainWindow = MainUiClass()
    MainWindow.show()
# MainWindow.showFullScreen()
    # MainWindow.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    # Create NeoPixel object with appropriate configuration.
    # charm = FlickCharm()
    # charm.activateOn(MainWindow.FileListWidget)
sys.exit(app.exec_())

# 13 may 1807