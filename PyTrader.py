import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from os import listdir,makedirs
from os.path import isfile, join, isdir
import shutil
from threading import Timer
import datetime
import os.path
import copy
from multiprocessing import Process
import math
import numpy as np
import logging
from Log.LogStringHandler import LogStringHandler
from Security_Company.Kiwoom_Handle import Kiwoom_Handler
form_class = uic.loadUiType("./UI/MyTrade_211121.ui")[0]
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.logger = None
        self.SetLogger()

        self.kiwoom_Handler = Kiwoom_Handler()
        self.kiwoom_Handler.Login()
        self.kiwoom_Handler.GetUserINFO()

        self.cboxAccInManage.addItems(self.kiwoom_Handler.userInfo['accList'])
        self.pbtnSelect.clicked.connect(self.AccInfo)

        self.pbtnSelect_2.clicked.connect(self.NonTrade)

        self.pbtnSelect_3.clicked.connect(self.Deposit)

        self.dtDateInAccTab_4.setDate(QDate.currentDate())
        self.pbtnSelect_4.clicked.connect(self.OrderHistory)

        self.pbtnSelect_5.clicked.connect(self.SignedTrade)

        self.leCodeInChart.textChanged.connect(self.CodeChangedInChart)
        self.pbtnInspectInChart.clicked.connect(self.Chart)

        self.watch = QTimer(self)
        self.watch.start(1000)
        self.watch.timeout.connect(self.UpdateWatch)
    def Chart(self):
        # # 종목
        # company = self.leCompanyInChart.text()
        # 코드
        code = self.leCodeInChart.text()
        # 일 분 틱?
        if self.cboxDayInChart.currentText() == '일':
            # getData.
            date = datetime.datetime.today()
            date = date.strftime('%Y%m%d')
            self.kiwoom_Handler.GetDayPrice(code, date, requestType = 0)
            price = self.kiwoom_Handler.price
        # show data.
        
        pass
    def CodeChangedInChart(self):
        code = self.leCodeInChart.text()
        company = self.kiwoom_Handler.GetCompanyName(code)
        self.leCompanyInChart.setText(company)
    def SignedTrade(self):
        accNumber = self.cboxAccInManage.currentText()
        accPW = self.leditAccPW.text()
        if self.rbtnTotalInAccTab_5.isChecked():
            tradeType = 0
        elif self.rbtnBuyInAccTab_5.isChecked():
            tradeType = 2
        elif self.rbtnSellInAccTab_5.isChecked():
            tradeType = 1
        self.kiwoom_Handler.CheckSignedTrade(accNumber, accPW, tradeType)   #안됨.
    def OrderHistory(self):
        accNumber = self.cboxAccInManage.currentText()
        accPW = self.leditAccPW.text()
        orderDate = self.dtDateInAccTab_4.date()
        if self.rbtnTotalInAccTab_4.isChecked():
            tradeType = 0
        elif self.rbtnBuyInAccTab_4.isChecked():
            tradeType = 2
        elif self.rbtnSellInAccTab_4.isChecked():
            tradeType = 1
        self.kiwoom_Handler.GetOrderHist(orderDate.toString('yyyyMMdd'), accNumber, accPW, tradeType, code='')
        _dfData = self.kiwoom_Handler.accInfo[accNumber]['orderHist']
        _qTable = self.tbOderHist_1
        _qTable.horizontalHeader().setVisible(True)
        _qTable.verticalHeader().setVisible(True)

        rowNum = len(_dfData.index)
        colNum = len(_dfData.columns)
        _qTable.setRowCount(rowNum)
        _qTable.setColumnCount(colNum)

        _qTable.setHorizontalHeaderLabels(_dfData.columns.tolist())
        _qTable.setVerticalHeaderLabels([str(i) for i in _dfData.index.tolist()])
        # set data
        for nRow in range(rowNum):
            for nCol in range(colNum):
                qValue = QTableWidgetItem(self.CurrencyFormat(_dfData.iloc[nRow, nCol]))
                qValue.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                _qTable.setItem(nRow, nCol, qValue)
        _qTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        _qTable.resizeColumnsToContents()
        _qTable.resizeRowsToContents()
    def Deposit(self):
        qtbDeposit = [self.tbDeposit_1,self.tbDeposit_2,self.tbDeposit_3,self.tbDeposit_4]
        accNumber = self.cboxAccInManage.currentText()
        accPW = self.leditAccPW.text()
        self.kiwoom_Handler.GetDeposit(accNumber, accPW)
        for _qTable, (_,_dfData) in zip(qtbDeposit, self.kiwoom_Handler.accInfo[accNumber]['deposite'].items()):
            # dataframe to QtabelWidget.
            _qTable.horizontalHeader().setVisible(True)
            _qTable.verticalHeader().setVisible(True)

            rowNum = len(_dfData.index)
            colNum = len(_dfData.columns)
            _qTable.setRowCount(rowNum)
            _qTable.setColumnCount(colNum)

            _qTable.setHorizontalHeaderLabels(_dfData.columns.tolist())
            _qTable.setVerticalHeaderLabels([str(i) for i in _dfData.index.tolist()])
            # set data
            for nRow in range(rowNum):
                for nCol in range(colNum):
                    qValue = QTableWidgetItem(self.CurrencyFormat(_dfData.iloc[nRow,nCol]))
                    qValue.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                    _qTable.setItem(nRow, nCol, qValue)
            _qTable.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
            _qTable.resizeColumnsToContents()
            _qTable.resizeRowsToContents()
    def NonTrade(self):
        accNumber = self.cboxAccInManage.currentText()
        accPW = self.leditAccPW.text()
        if self.rbtnTradeTypeTotal_2.isChecked():
            tradeType = 0
        elif self.rbtnTradeTypeBuy_2.isChecked():
            tradeType = 2
        elif self.rbtnTradeTypeSell_2.isChecked():
            tradeType = 1
        self.kiwoom_Handler.NonTrade(accNumber, tradeType)

        rowNum = len(self.kiwoom_Handler.accInfo[accNumber]['nonTrade'])
        colNum = len(self.kiwoom_Handler.accInfo[accNumber]['nonTrade'][0])
        self.tbNoSigned.setRowCount(rowNum)
        self.tbNoSigned.setColumnCount(colNum)

        for nRow, nDict in self.kiwoom_Handler.accInfo[accNumber]['nonTrade'].items():
            for nIdxCol, (nCol, nValue) in enumerate(nDict.items()):
                if nRow == 0:
                    header_item = QTableWidgetItem(nCol)
                    self.tbNoSigned.setHorizontalHeaderItem(nIdxCol, header_item)
                qValue = QTableWidgetItem(self.CurrencyFormat(nValue))
                qValue.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tbNoSigned.setItem(nRow, nIdxCol, qValue)
        self.tbNoSigned.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tbNoSigned.resizeColumnsToContents()
    def AccInfo(self):
        accNumber = self.cboxAccInManage.currentText()
        accPW = self.leditAccPW.text()
        # 조회구분(requestType) = 1:합산, 2:개별
        self.kiwoom_Handler.GetAccInfo(accNumber, password=accPW, requestType=1)
        dataNum = len(self.kiwoom_Handler.accInfo[accNumber]['total'])
        self.tbAccSummary.setRowCount(2)
        self.tbAccSummary.setColumnCount(dataNum)
        for idx, (key, value) in enumerate(self.kiwoom_Handler.accInfo[accNumber]['total'].items()):
            qKey = QTableWidgetItem(key)
            qKey.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tbAccSummary.setItem(0, idx, qKey)
            qValue = QTableWidgetItem(self.CurrencyFormat(value))
            qValue.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tbAccSummary.setItem(1, idx, qValue)
        self.tbAccSummary.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tbAccSummary.resizeColumnsToContents()

        rowNum = len(self.kiwoom_Handler.accInfo[accNumber]['indivisual'])
        # keys = list(self.kiwoom_Handler.accInfo[accNumber]['indivisual'][0].keys())
        colNum = len(self.kiwoom_Handler.accInfo[accNumber]['indivisual'][0])
        self.tbAccDetail.setRowCount(rowNum)
        self.tbAccDetail.setColumnCount(colNum)

        # self.tbAccDetail.setHorizontalHeaderLabels(['종목코드', '종목명', '매입가', '평가손익', '수익률(%)', '매매가능수량',
        #                                             '보유수량', '현재가', '매입금액', '평가금액', '수수료합', '세금', '보유비중(%)', '신용구분', '손익분기매입가'])
        for nRow, nDict in self.kiwoom_Handler.accInfo[accNumber]['indivisual'].items():
            for nIdxCol,(nCol, nValue) in enumerate(nDict.items()):
                if nRow==0:
                    header_item = QTableWidgetItem(nCol)
                    self.tbAccDetail.setHorizontalHeaderItem(nIdxCol, header_item)
                qValue = QTableWidgetItem(self.CurrencyFormat(nValue))
                qValue.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tbAccDetail.setItem(nRow, nIdxCol, qValue)
        self.tbAccDetail.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.tbAccDetail.resizeColumnsToContents()
    def CurrencyFormat(self,value):
        if type(value)==float:
            return "{:,.2f}".format(value)
        elif isinstance(value, (int, np.integer, np.float64, np.float)):
            return "{:,}".format(value)
        elif type(value)==datetime or type(value)==datetime.date or type(value)==datetime.time:
            return "{:}".format(value)
        else:
            return value
    def SetLogger(self):
        self.logger = logging.getLogger()
        self.logger.addHandler(LogStringHandler(self.txbrowserLog))
        # logger.error('Error test!')
        # logger.info('Info test!')
        # logger.warning('Warning test!')
        # logger.debug('Debug test!')

    def UpdateWatch(self):
        current_time = QTime.currentTime()
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time
        if self.kiwoom_Handler.GetConnectState()==True:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"
        self.statusbar.showMessage(state_msg + " | " + time_msg)
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()