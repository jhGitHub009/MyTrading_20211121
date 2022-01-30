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
import finplot as fplt
import Quanti.OECD_CLI as OECD

fplt.candle_bull_color = "#FF0000"
fplt.candle_bull_body_color = "#FF0000"
fplt.candle_bear_color = "#0000FF"
form_class = uic.loadUiType("./UI/MyTrade_211121.ui")[0]
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.logger = None
        self.SetLogger()

        self.watch = QTimer(self)
        self.watch.start(1000)
        self.watch.timeout.connect(self.UpdateWatch)

        # 키움 API
        self.kiwoom_Handler = Kiwoom_Handler()
        self.kiwoom_Handler.Login()
        self.kiwoom_Handler.GetUserINFO()

        self.cboxAccInManage.addItems(self.kiwoom_Handler.userInfo['accList'])
        self.pbtnSelect.clicked.connect(self.AccInfo)
        self.tbAccDetail.doubleClicked.connect(self.ClickedItemInAccTable)

        self.pbtnSelect_2.clicked.connect(self.NonTrade)
        self.pbtnSelect_3.clicked.connect(self.Deposit)
        self.dtDateInAccTab_4.setDate(QDate.currentDate())
        self.pbtnSelect_4.clicked.connect(self.OrderHistory)

        self.pbtnSelect_5.clicked.connect(self.SignedTrade)

        self.leCodeInChart.textChanged.connect(lambda: self.CodeChanged('Chart'))
        self.pbtnInspectInChart.clicked.connect(self.Chart)

        self.leCodeCallingPrice.textChanged.connect(lambda: self.CodeChanged('CallingPrice'))
        self.pbtnInspectInCallingPrice.clicked.connect(self.CallingPrice)
        self.twCallingPrice.doubleClicked.connect(self.ClickedItemInTable)

        self.leCodeInTrade.textChanged.connect(lambda: self.CodeChanged('Trade'))
        self.cboxAccInTrade.addItems(self.kiwoom_Handler.userInfo['accList'])
        self.cBoxKindStockTab_1.currentIndexChanged.connect(lambda: self.KindStockInTrade('Buy'))
        self.cBoxPerTab_1.currentIndexChanged.connect(lambda: self.AutoCalAmountInTrade('Buy'))
        self.pBtnTotalTab_1.clicked.connect(lambda: self.AllAutoCalAmountInTrade('Buy'))
        self.pBtnCallingTab_1.clicked.connect(self.CallingPriceInTrade)
        self.cBoxMarketPriceTab_1.stateChanged.connect(lambda :self.CheckMaketPriceInTrade('Buy'))
        self.pBtnCurPriceTab_1.clicked.connect(lambda :self.BtnCurPriceTab('Buy'))
        self.pBtnBuyInTrade.clicked.connect(self.BuyStock)

        self.cBoxKindStockTab_2.currentIndexChanged.connect(lambda: self.KindStockInTrade('Sell'))
        self.pBtnAccountInTrade.clicked.connect(self.AccountInTrade)
        self.cBoxPerTab_2.currentIndexChanged.connect(lambda: self.AutoCalAmountInTrade('Sell'))
        self.pBtnTotalTab_2.clicked.connect(lambda: self.AllAutoCalAmountInTrade('Sell'))
        self.pBtnCallingTab_2.clicked.connect(self.CallingPriceInTrade)
        self.cBoxMarketPriceTab_2.stateChanged.connect(lambda :self.CheckMaketPriceInTrade('Sell'))
        self.pBtnCurPriceTab_2.clicked.connect(lambda :self.BtnCurPriceTab('Sell'))
        self.pBtnSellInTrade.clicked.connect(self.SellStock)

        self.pBtnNoSignedInTrade.clicked.connect(self.NonTrade)
        self.tbNoSigned.doubleClicked.connect(self.ClickedItemInNoSigned)

        # OECD CLI
        self.btnOECDCLIDate.clicked.connect(self.OECDCLIDate)
        self.btnOECDCLIData.clicked.connect(self.OECDCLIData)
    def OECDCLIDate(self):
        saveFolder = r'./Quanti/OECD/ReleaseDate'
        today = datetime.date.today()
        dateOECDCLI = OECD.GetCLIDate()
        if not os.path.isdir(saveFolder): os.makedirs(saveFolder)
        dateOECDCLI.to_csv(saveFolder + r'/date_OECD_CLI_%s.csv' % (today), encoding='cp949', index=False)
        self._DataframeToTableWidget(_qTable=self.tbWOECDDate, _dfData=dateOECDCLI)
    def OECDCLIData(self):
        saveFolder = r'./Quanti/OECD/Data/'
        today = datetime.date.today()
        # 데이터다운 받고
        # OECD.GetCLIData()
        newFileName = 'OECD_CLI_%s.csv' % (today)
        # 파일 옮기고
        if not isdir(saveFolder): makedirs(saveFolder)
        OECD.MoveFile(saveFolder, '.csv', newFileName)
        import pandas as pd
        cliOECD = pd.read_csv(saveFolder+'/'+newFileName)
        cliOECDJPN = cliOECD[cliOECD['LOCATION']=='JPN']
        # self.gviewOECDChart.plot(cliOECD[cliOECD['LOCATION'] == 'JPN']['Value'].tolist())
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)
        self.verlayOECDChart.addWidget(self.canvas)
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        x = cliOECDJPN['TIME'].tolist()[-10:]
        y1 = cliOECDJPN['Value'].tolist()[-10:]
        ax.plot(x, y1)
        self.canvas.draw()
        # self.gviewOECDChart.plot(cliOECD[cliOECD['LOCATION']=='JPN'].index,cliOECD[cliOECD['LOCATION']=='JPN']['Value'])
    def OECDCLIResult(self):
        today = datetime.date.today()
        saveFolder = './Quanti/%s' % (today.strftime('%Y-%m-%d'))
        saveFilename = 'OECDCLI_%s.csv' % (today.strftime('%Y%m%d'))
        # 계산하고
        df_summery = OECD.CLIResult2(today)
        # df_summery = OECD.CLIResult(today)
        # 파일 만들어서 트레이딩 준비 완료
        if not isdir(saveFolder): makedirs(saveFolder)
        df_summery.to_csv(saveFolder + '/' + saveFilename, encoding='cp949', index=False)
        print('Finish OECDCLIResult!!')
    def ClickedItemInNoSigned(self):
        selectedText = self.tbNoSigned.currentItem().text().replace(',', '')
        if not selectedText.isdigit():
            return True
        else:
            self.sBoxPriceTab_1.setValue(int(selectedText))
            self.sBoxPriceTab_2.setValue(int(selectedText))
    def ClickedItemInAccTable(self):
        selectedRow = self.tbAccDetail.currentRow()
        accuntInfo = {}
        for i in range(0,self.tbAccDetail.columnCount()):
            accuntInfo[self.tbAccDetail.horizontalHeaderItem(i).text()] = self.tbAccDetail.item(selectedRow, i).text()
        self.leCodeInTrade.setText(accuntInfo['종목코드'])
        self.AllAutoCalAmountInTrade('Sell')
    def AccountInTrade(self):
        accNumber = self.cboxAccInTrade.currentText()
        passward = self.leditPWInTrade.text()
        self.cboxAccInManage.setCurrentText(accNumber)
        self.leditAccPW.setText(passward)
        self.AccInfo()
    def KindStockInTrade(self, tab = None):
        if tab=='Buy':
            orderType = self.cBoxKindStockTab_1.currentText()
            if '보통' in orderType or '조건부지정가' in orderType:
                self.sBoxPriceTab_1.setEnabled(True)
                self.pBtnCurPriceTab_1.setEnabled(True)
                self.pBtnCallingTab_1.setEnabled(True)
            else:
                self.sBoxPriceTab_1.setEnabled(False)
                self.pBtnCurPriceTab_1.setEnabled(False)
                self.pBtnCallingTab_1.setEnabled(False)
        elif tab=='Sell':
            orderType = self.cBoxKindStockTab_2.currentText()
            if '보통' in orderType or '조건부지정가' in orderType:
                self.sBoxPriceTab_2.setEnabled(True)
                self.pBtnCurPriceTab_2.setEnabled(True)
                self.pBtnCallingTab_2.setEnabled(True)
            else:
                self.sBoxPriceTab_2.setEnabled(False)
                self.pBtnCurPriceTab_2.setEnabled(False)
                self.pBtnCallingTab_2.setEnabled(False)
    def CodeChanged(self, id=None):
        if id == 'Chart':
            code = self.leCodeInChart.text()
            if len(code) < 6:
                return True
            company = self.kiwoom_Handler.GetCompanyName(code)
            self.leCompanyInChart.setText(company)
        elif id == 'CallingPrice':
            code = self.leCodeCallingPrice.text()
            if len(code) < 6:
                return True
            company = self.kiwoom_Handler.GetCompanyName(code)
            self.leCompanyCallingPrice.setText(company)
        elif id == 'Trade':
            code = self.leCodeInTrade.text()
            if len(code) < 6:
                return True
            self.kiwoom_Handler.GetCompanyInfo(code)
            self.leCompanyInTrade.setText(self.kiwoom_Handler.company['종목명'])
            if self.kiwoom_Handler.company['현재가'] < 0:
                self.laPriceInTrade.setStyleSheet("Color : blue")
                self.laPriceCompareInTrade.setStyleSheet("Color : blue")
                self.laPriceRateInTrade.setStyleSheet("Color : blue")
            elif self.kiwoom_Handler.company['현재가'] > 0:
                self.laPriceInTrade.setStyleSheet("Color : red")
                self.laPriceCompareInTrade.setStyleSheet("Color : red")
                self.laPriceRateInTrade.setStyleSheet("Color : red")
            else:
                self.laPriceInTrade.setStyleSheet("Color : black")
                self.laPriceCompareInTrade.setStyleSheet("Color : black")
                self.laPriceRateInTrade.setStyleSheet("Color : black")
            self.laPriceInTrade.setText(str(abs(self.kiwoom_Handler.company['현재가'])))
            self.laPriceCompareInTrade.setText(str(self.kiwoom_Handler.company['전일대비']))
            self.laPriceRateInTrade.setText('%s %%'%(str(self.kiwoom_Handler.company['등락율']).zfill(2)))
            self.sBoxPriceTab_1.setValue(abs(self.kiwoom_Handler.company['현재가']))
            self.sBoxPriceTab_2.setValue(abs(self.kiwoom_Handler.company['현재가']))
    def ClickedItemInTable(self):
        selectedText = self.twCallingPrice.currentItem().text().replace(',','')
        if not selectedText.isdigit():
            return True
        else:
            self.sBoxPriceTab_1.setValue(int(selectedText))
            self.sBoxPriceTab_2.setValue(int(selectedText))
    def BtnCurPriceTab(self,tab = None):
        code = self.leCodeInTrade.text()
        if len(code) < 6:
            QMessageBox.warning(self, "Warnning", "코드를 입력하시오.")
        else:
            self.CodeChanged('Trade')
            curPrice = self.laPriceInTrade.text()
        if tab == 'Buy':
            self.sBoxPriceTab_1.setValue(int(curPrice))
        if tab == 'Sell':
            self.sBoxPriceTab_2.setValue(int(curPrice))
    def AllAutoCalAmountInTrade(self, tab = None):
        if tab=='Buy':
            self.cBoxPerTab_1.setCurrentText('100%')
            self.AutoCalAmountInTrade(tab)
        if tab=='Sell':
            self.cBoxPerTab_2.setCurrentText('100%')
            self.AutoCalAmountInTrade(tab)
    def CallingPriceInTrade(self):
        code = self.leCodeInTrade.text()
        self.leCodeCallingPrice.setText(code)
        self.CallingPrice()
    def CheckMaketPriceInTrade(self, tab = None):
        if tab=='Buy':
            if self.cBoxMarketPriceTab_1.isChecked():
                self.cBoxKindStockTab_1.setCurrentText("시장가")
            else:
                self.cBoxKindStockTab_1.setCurrentText('보통')
        if tab == 'Sell':
            if self.cBoxMarketPriceTab_2.isChecked():
                self.cBoxKindStockTab_2.setCurrentText("시장가")
            else:
                self.cBoxKindStockTab_2.setCurrentText('보통')
    def AutoCalAmountInTrade(self,tab = None):
        # 퍼센트 받아오기.
        if tab=='Buy':
            percentage = self.cBoxPerTab_1.currentText()
            if percentage == '%':
                self.sBoxAmountTab_1.setValue('0')
                return True
            else:
                percentage = int(percentage.replace('%', ''))
            # 가격 받아오기
            orderType = self.cBoxKindStockTab_1.currentText()
            if orderType == '시장가':
                price = int(self.laPriceInTrade.text())
            else:
                price = int(self.sBoxPriceTab_1.value())
            if price == 0:
                QMessageBox.warning(self, "Warnning", "가격을 입력해주세요.")
                return True
            accNumber = self.cboxAccInTrade.currentText()
            passward = self.leditPWInTrade.text()
            self.kiwoom_Handler.GetDeposit(accNumber, passward)
            # 예수금에서 가능금액.
            accMoney = self.kiwoom_Handler.accInfo[accNumber]['deposite']['table1']['인출가능금액'][0]
            # 수량 계산.
            investMoney = accMoney*percentage/100
            amountBuy = int(investMoney//price)
            # 수량 입력.
            self.sBoxAmountTab_1.setValue(amountBuy)
        elif tab=='Sell':
            # 어카운트 정보 받아오고.
            # 어카운트내에 동일 코드가 있으면 수량계산.
            # 퍼센티지 정보를 받아옴.
            percentage = self.cBoxPerTab_2.currentText()
            if percentage == '%':
                return True
            else:
                percentage = int(percentage.replace('%', ''))
            code = self.leCodeInTrade.text()
            accNumber = self.cboxAccInTrade.currentText()
            accPW = self.leditPWInTrade.text()
            self.kiwoom_Handler.GetAccInfo(accNumber, password=accPW, requestType=1)
            for key, val in self.kiwoom_Handler.accInfo[accNumber]['indivisual'].items():
                if val['종목코드'] == code:
                    num = int(val['매매가능수량'])
                    self.sBoxAmountTab_2.setValue(int(num * percentage / 100))
                    return True
            self.sBoxAmountTab_2.setValue(0)
    def SellStock(self):
        accNumber = self.cboxAccInTrade.currentText()
        accPW = self.leditPWInTrade.text()
        code = self.leCodeInTrade.text()
        orderType = self.cBoxKindStockTab_2.currentText()
        if self.rBtnCashTab_2.isChecked():
            cash = True
        elif self.rBtnCreditTab_2.isChecked():
            cash = False
        amount = self.sBoxAmountTab_2.value()
        price = self.sBoxPriceTab_2.value()
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4, '매수정정' : 5, '매도정정':6}
        hoga_lookup = {'보통': "00", '시장가': "03", '조건부지정가': "05", '최유리지정가': "06", '최우선지정가': "07",
                       '보통(IOC)': "10", '시장가(IOC)': "13", '최유리(IOC)': "16", '보통(FOK)': "20", '시장가(FOK)': "23",
                       '최유리(FOK)': "26", '장전시간외종가': "61",'시간외단일가매매': "62",'장후시간외종가':'81'}
        sellInfo = {'account':accNumber, 'nOrderType':order_type_lookup['신규매도'], 'sCode':code, 'nQty':amount,
                   'nPrice':price, 'sHogaGb':hoga_lookup[orderType], 'sOrgOrderNo':''}
        self.kiwoom_Handler.SellStock(sellInfo)
    def BuyStock(self):
        accNumber = self.cboxAccInTrade.currentText()
        accPW = self.leditPWInTrade.text()
        code = self.leCodeInTrade.text()
        orderType = self.cBoxKindStockTab_1.currentText()
        if self.rBtnCashTab_1.isChecked():
            cash = True
        elif self.rBtnCreditTab_1.isChecked():
            cash = False
        amount = self.sBoxAmountTab_1.value()
        price = self.sBoxPriceTab_1.value()
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4, '매수정정' : 5, '매도정정':6}
        hoga_lookup = {'보통': "00", '시장가': "03", '조건부지정가': "05", '최유리지정가': "06", '최우선지정가': "07",
                       '보통(IOC)': "10", '시장가(IOC)': "13", '최유리(IOC)': "16", '보통(FOK)': "20", '시장가(FOK)': "23",
                       '최유리(FOK)': "26", '장전시간외종가': "61",'시간외단일가매매': "62",'장후시간외종가':'81'}
        buyInfo = {'account':accNumber, 'nOrderType':order_type_lookup['신규매수'], 'sCode':code, 'nQty':amount,
                   'nPrice':price, 'sHogaGb':hoga_lookup[orderType], 'sOrgOrderNo':''}
        self.kiwoom_Handler.BuyStock(buyInfo)
    def _DataframeToTableWidget(self, _qTable, _dfData):
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
    def CallingPrice(self):
        code = self.leCodeCallingPrice.text()
        self.kiwoom_Handler.GetAskingPrice(code)
        self._DataframeToTableWidget(self.twCallingPrice, self.kiwoom_Handler.callInfo)
    def Chart(self):
        code = self.leCodeInChart.text()        # 코드
        date = datetime.datetime.today()
        date = date.strftime('%Y%m%d')
        # 일 분 틱?
        if self.cboxMinInChart.currentText() != '분':
            #get number for min
            minTerm = int(self.cboxMinInChart.currentText())
            self.kiwoom_Handler.GetMinPrice(code, range=minTerm, requestType = 0)
        elif self.cboxTickInChart.currentText() != '틱':
            # get number for tick
            tickTerm = int(self.cboxTickInChart.currentText())
            self.kiwoom_Handler.GetTickPrice(code, range=tickTerm, requestType=0)
        elif self.cboxDayInChart.currentText() == '일':
            self.kiwoom_Handler.GetDayPrice(code, date, requestType = 0)
        elif self.cboxDayInChart.currentText() == '주':
            self.kiwoom_Handler.GetWeekPrice(code, date, requestType=0)
        elif self.cboxDayInChart.currentText() == '월':
            self.kiwoom_Handler.GetMonthPrice(code, date, requestType=0)
        elif self.cboxDayInChart.currentText() == '년':
            self.kiwoom_Handler.GetYearPrice(code, date, requestType=0)
        price = self.kiwoom_Handler.price

        if self.vlayChart.count()>0:
            curWidget = self.vlayChart.itemAt(0)
            self.vlayChart.removeItem(curWidget)
        ax = fplt.create_plot(init_zoom_periods=10)
        self.vlayChart.addWidget(ax.vb.win, 0)

        price['Price'].rename(columns={'open': "Open", "high": "High", "low": "Low", "close": "Close"}, inplace=True)
        fplt.candlestick_ochl(price['Price'].iloc[::-1][['Open','Close','High','Low']])
        fplt.show(qt_exec=False)

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
        self._DataframeToTableWidget(self.tbOderHist_1, self.kiwoom_Handler.accInfo[accNumber]['orderHist'])
    def Deposit(self):
        qtbDeposit = [self.tbDeposit_1,self.tbDeposit_2,self.tbDeposit_3,self.tbDeposit_4]
        accNumber = self.cboxAccInManage.currentText()
        accPW = self.leditAccPW.text()
        self.kiwoom_Handler.GetDeposit(accNumber, accPW)
        for _qTable, (_,_dfData) in zip(qtbDeposit, self.kiwoom_Handler.accInfo[accNumber]['deposite'].items()):
            self._DataframeToTableWidget(_qTable=_qTable,_dfData=_dfData)
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