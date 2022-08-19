import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic
from os import listdir,makedirs
from os.path import isfile, join, isdir
import datetime
import os.path
import numpy as np
import logging
from Log.LogStringHandler import LogStringHandler
from Security_Company.Kiwoom_Handle import Kiwoom_Handler
import finplot as fplt
import Quanti.OECD_CLI as OECD
import pandas as pd
import json
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import Rebalancing
from selenium import webdriver
import Quanti.MakeSPRPER as PSRPCR
import Quanti.StockCodeDown as StockCodeDown
import Quanti.BasicFomula as BF
import Quanti.InvestingCrawlerUSA_20220306 as Investing
import Quanti.MyLibrary_20180702 as MyLib
import time
import copy
import tempfile
import pickle
import logging
# Set the threshold for selenium to WARNING
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
seleniumLogger.setLevel(logging.WARNING)
# Set the threshold for urllib3 to WARNING
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)

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
        self.KiwoomPage()
        self.SWOTPage()
        self.OECDPage()
        self.ValuePage()

        self.pBtnSaveCurrentPage.clicked.connect(self.SaveCurrentPage)
        self.pBtnLoadCurrentPage.clicked.connect(self.LoadCurrentPage)
    def ValuePage(self):
        # 가치투자
        # init
        self.dfAccSummaryInValue = None
        self.dfAccDetailInValue = None
        self.dfCodeInValue = None
        self.dfChartInValue = None
        self.dfPriceInValue = None
        self.dfValueDataInValue = None
        self.dfRebalInValue = None
        # Information
        # StockPrice
        self.btnSaveFolderForCode.clicked.connect(lambda: self.SetFolder(self.laSaveFolderForCode))
        self.btnStartCodeDown.clicked.connect(self.StockCodeDown)
        self.btnCodeFile.clicked.connect(lambda: self.SetFile(self.laCodeFile))
        self.btnSaveFolderForPrice.clicked.connect(lambda: self.SetFolder(self.laSaveFolderForPrice))
        self.btnStartPriceDown.clicked.connect(self.StockDown)
        # Naver
        self.btnCodeFileNaver.clicked.connect(lambda: self.SetFile(self.laCodeFileNaver))
        self.btnSaveFolderForCrwal.clicked.connect(lambda: self.SetFolder(self.laSaveFolderForCrwal))
        self.btnStartCrwal.clicked.connect(self.StartCrwal)
        # Read
        self.btnCodeURLForRead.clicked.connect(lambda: self.SetFile(self.laCodeURLForRead))
        self.btnReadCode.clicked.connect(self.ReadCode)
        self.btnPriceURLForRead.clicked.connect(lambda: self.SetFile(self.laPriceURLForRead))
        self.btnReadPrice.clicked.connect(self.ReadPrice)
        # Read
        self.pBtnSelectInValue.clicked.connect(self.AccInfoInValue)
        self.cboxAccInValue.addItems(self.kiwoom_Handler.userInfo['accList'])
        # 잔고
        self.pBtnSelectInValue.clicked.connect(self.AccInfoInValue)
        self.cboxAccInValue.addItems(self.kiwoom_Handler.userInfo['accList'])
        # Calc
        self.btnValueDataFolder.clicked.connect(lambda: self.SetFolder(self.laValueDataFolder))
        self.btnPriceDataFolder.clicked.connect(lambda: self.SetFolder(self.laPriceDataFolder))
        self.pBtnScreening.clicked.connect(self.Screening)
        self.pBtnRebalancing.clicked.connect(self.CalRebalancing)
    def OECDPage(self):
        # OECD CLI
        # init
        self.liDate = None
        self.dfInterest = pd.DataFrame(columns=['Code', 'Company', 'Country'])
        self.dfChart = None
        self.dfAccSummary = None
        self.dfAccDetail = None
        # connect function
        # self.dfInterest = pd.DataFrame(columns=['Code','Company','Location','DateOECD','Score','ScoreDiff','Rebalancing'])
        self.btnGetOECDCLIDate.clicked.connect(self.OECDCLIDate)
        self.btnOECDCLIData.clicked.connect(self.OECDCLIData)
        self.btnShowOECDCLIDate.clicked.connect(self.ShowOECDCLIDate)
        self.RefreshDateNLoc()
        # 관심나라 등록
        # self.btnRemoveInOECD.clicked.connect(self.RemoveLocation)
        # self.btnLoadInOECD.clicked.connect(self.LoadLocation)
        # self.btnSaveInOECD.clicked.connect(self.SaveLocation)
        # self.btnEnrollInOECD.clicked.connect(self.EnrollCountry)
        self.leCodeInOECD.textChanged.connect(self.CodeChangeInOECD)
        self.btnEnrollInOECD.clicked.connect(self.EnrollCompany)
        self.btnRemoveInOECD.clicked.connect(self.RemoveCompany)
        self.btnLoadInOECD.clicked.connect(self.LoadCompany)
        self.btnSaveInOECD.clicked.connect(self.SaveCompany)
        self.pBtnResultInOECD.clicked.connect(self.OECDCLIResult)
        self.pBtnTradeInOECD.clicked.connect(self.OECDCLISendOrder)
        # Chart
        self.pbtnInspectInOECD.clicked.connect(self.ShowOECDChart)
        self.cboxDateInChartOECD.currentIndexChanged.connect(lambda: self.UpdateCountry(self.cboxLocInChartOECD, self.cboxDateInChartOECD))
        # 잔고
        self.pBtnSelectInOECD.clicked.connect(self.AccInfoInOECD)
        self.cboxAccInOECD.addItems(self.kiwoom_Handler.userInfo['accList'])
    def SWOTPage(self):
        # init
        self.dfSWOT = pd.DataFrame(columns=['Code', 'Company', 'Strength', 'Weakness', 'Opportunity', 'Threat'])
        self.dfValue = None
        self.dfInvesting = None
        self.dfNaver = None
        self.dfSWOTOECD = None
        self.dfSWOTResult = pd.DataFrame(columns=['Code', 'Company', 'EPS', 'Naver', 'Investing', 'OECD_Diff',
                                                  'CAGR', 'MDD(Now)', 'MDD(Target)', 'Portion', 'Price', 'Stock(Now)',
                                                  'Stock(Target)', 'Trade'])
        self.dfTradeHist = None
        self.setTabOrder(self.leCodeInSWOT, self.etxStrengths)
        self.setTabOrder(self.leCodeInSWOTResult, self.leEPSInSWOTResult)
        self.setTabOrder(self.leEPSInSWOTResult, self.leNaverInSWOTResult)
        self.setTabOrder(self.leNaverInSWOTResult, self.leInvestingInSWOTResult)
        self.setTabOrder(self.leInvestingInSWOTResult, self.leOECDInSWOTResult)
        self.setTabOrder(self.leOECDInSWOTResult, self.lePortionInSWOTResult)
        self.setTabOrder(self.lePortionInSWOTResult, self.leMDDInSWOTResult)
        # SWOT
        # codeToCompany는 ui에서.
        self.leCodeInSWOT.textChanged.connect(lambda: self.CodeToCompany(self.leCodeInSWOT, self.leCompanyInSWOT))
        # 경로 setting ui에서.
        self.btnLoadInSWOT.clicked.connect(lambda: self.SetFile2(self.laSWOTURLForRead, self.LoadSWOT))
        self.btnSWOTURLForSave.clicked.connect(lambda: self.SetFolder(self.laSWOTURLForSave))
        # self.btnLoadInSWOT.clicked.connect(self.LoadSWOT)
        # Save는 ui에서 경로를 읽어와서 Save로 던저줌.
        self.btnSaveInSWOT.clicked.connect(self.SaveSWOT)
        # 가치DATA
        self.leCodeInValue.textChanged.connect(lambda: self.CodeToCompany(self.leCodeInValue, self.leCompanyInValue))
        self.btnLoadInValue.clicked.connect(lambda: self.SetFile2(self.laSWOTURLForRead, self.LoadValue))
        # self.btnValueURLForSave.clicked.connect(lambda: self.SetFolder(self.laValueURLForSave))
        # crwal은 chromdrive위치를 ui에서 주고, 데이터를 받아옴.
        # 받아온데이터를 UI에서 표시.
        self.btnCrawlInValue.clicked.connect(self.GetValueData)
        # self.btnLoadInValue.clicked.connect(self.LoadValue)
        self.btnSaveInValue.clicked.connect(self.SaveValue)
        # Investing.
        # ui에서는 code를 주고, company를 받아서 등록
        self.leCodeInInvesting.textChanged.connect(
            lambda: self.CodeToCompany(self.leCodeInInvesting, self.leCompanyInInvesting))
        # 경로 설정은 UI에서.
        self.btnLoadInInvesting.clicked.connect(lambda: self.SetFile2(self.laSWOTURLForRead, self.LoadInvesting))
        # self.btnInvestingURLForSave.clicked.connect(lambda: self.SetFolder(self.laInvestingURLForSave))
        # crawling은 driver 위치를 주고 data를 받아서, display
        self.btnCrawlInInvesting.clicked.connect(self.GetInvestingData)
        # save load는 위치를 주고, data를저장.
        # self.btnLoadInInvesting.clicked.connect(self.LoadInvesting)
        self.btnSaveInInvesting.clicked.connect(self.SaveInvesting)
        # Naver.
        self.leCodeInNaver.textChanged.connect(lambda: self.CodeToCompany(self.leCodeInNaver, self.leCompanyInNaver))
        self.btnLoadInNaver.clicked.connect(lambda: self.SetFile2(self.laSWOTURLForRead, self.LoadNaver))
        # self.btnNaverURLForSave.clicked.connect(lambda: self.SetFolder(self.laNaverURLForSave))
        self.btnCrawlInNaver.clicked.connect(self.GetNaverData)
        # self.btnLoadInNaver.clicked.connect(self.LoadNaver)
        self.btnSaveInNaver.clicked.connect(self.SaveNaver)
        # OECD
        self.btnLoadInSWOTOECD.clicked.connect(lambda: self.SetFile2(self.laSWOTURLForRead, self.LoadSWOTOECD))
        # self.btnSWOTOECDURLForSave.clicked.connect(lambda: self.SetFolder(self.laSWOTOECDURLForSave))
        self.btnCrawlInSWOTOECD.clicked.connect(self.GetSWOTOECDData)
        # self.btnLoadInSWOTOECD.clicked.connect(self.LoadSWOTOECD)
        self.btnSaveInSWOTOECD.clicked.connect(self.SaveSWOTOECD)
        self.SetAllCountryInCBox()
        # 잔고
        # 이미되어 있음. Generalization.
        self.pBtnSelectInSWOT.clicked.connect(self.AccInfoInSWOT)
        self.cboxAccInSWOT.addItems(self.kiwoom_Handler.userInfo['accList'])
        # setting 에 등록된 account를 잡고
        # Quanti
        # self.leCodeInSWOTResult.textEdited.connect(self.tabNext)
        self.pBtnLoadInSWOTResult.clicked.connect(lambda: self.SetFile2(self.laSWOTURLForRead, self.LoadInSWOTResult))
        # self.btnSWOTResultURLForSave.clicked.connect(lambda: self.SetFolder(self.laSWOTResultURLForSave))
        self.leCodeInSWOTResult.textChanged.connect(
            lambda: self.CodeToCompany(self.leCodeInSWOTResult, self.leCompanyInSWOTResult))
        self.pBtnEnrollInSWOT.clicked.connect(self.EnrollInSWOT)  # 등록
        self.pBtnRemoveInSWOT.clicked.connect(self.RemoveInSWOT)  # 삭제
        # rebalancing 하기전 조건이 달라 class필요.
        # rebalancing의 여러 algo를 부모 클래스에.
        # Trade는 동일.(부모 클래스에 넣어놓음.)
        self.pBtnRebalancingInSWOT.clicked.connect(self.RebalancingInSWOT)  # 계산
        self.pBtnTradeInSWOT.clicked.connect(self.TradeInSWOT)  # 거래실행
        # self.pBtnLoadInSWOTResult.clicked.connect(self.LoadInSWOTResult)
        self.pBtnSaveInSWOTResult.clicked.connect(self.SaveInSWOTResult)
        # TradeHist
        #
        self.dtEndDayInSWOT.setDate(QDate.currentDate())
        self.dtStartDayInSWOT.setDate(QDate.currentDate())
        self.rBtnTotalHistoryInSWOT.clicked.connect(self.SetRadioBtnCodeInTradeHist)
        self.rBtnCodeHistoryInSWOT.clicked.connect(self.SetRadioBtnCodeInTradeHist)
        self.cboxAccInSWOTTradeHist.addItems(self.kiwoom_Handler.userInfo['accList'])
        self.pBtnSelectInSWOTHist.clicked.connect(self.TradeHist)
    def KiwoomPage(self):
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
        self.cBoxMarketPriceTab_1.stateChanged.connect(lambda: self.CheckMaketPriceInTrade('Buy'))
        self.pBtnCurPriceTab_1.clicked.connect(lambda: self.BtnCurPriceTab('Buy'))
        self.pBtnBuyInTrade.clicked.connect(self.BuyStock)
        self.cBoxKindStockTab_2.currentIndexChanged.connect(lambda: self.KindStockInTrade('Sell'))
        self.pBtnAccountInTrade.clicked.connect(self.AccountInTrade)
        self.cBoxPerTab_2.currentIndexChanged.connect(lambda: self.AutoCalAmountInTrade('Sell'))
        self.pBtnTotalTab_2.clicked.connect(lambda: self.AllAutoCalAmountInTrade('Sell'))
        self.pBtnCallingTab_2.clicked.connect(self.CallingPriceInTrade)
        self.cBoxMarketPriceTab_2.stateChanged.connect(lambda: self.CheckMaketPriceInTrade('Sell'))
        self.pBtnCurPriceTab_2.clicked.connect(lambda: self.BtnCurPriceTab('Sell'))
        self.pBtnSellInTrade.clicked.connect(self.SellStock)
        self.pBtnNoSignedInTrade.clicked.connect(self.NonTrade)
        self.tbNoSigned.doubleClicked.connect(self.ClickedItemInNoSigned)
    def LoadCurrentPage(self):
        with open('./Quanti/data.pickle', 'rb') as f:
            data = pickle.load(f)
        if self.tabWidget.tabText(self.tabWidget.currentIndex())=='Quant':
            if self.tabWidget_2.tabText(self.tabWidget_2.currentIndex()) == 'SWOT':
                self.dfSWOT = data['dfSWOT']
                self.dfValue = data['dfValue']
                self.dfInvesting = data['dfInvesting']
                self.dfNaver = data['dfNaver']
                self.dfSWOTOECD = data['dfSWOTOECD']
                self.dfSWOTResult = data['dfSWOTResult']
                self.leCodeInSWOT.setText(self.dfSWOT.loc[0, 'Code'])
                self.etxStrengths.setText(self.dfSWOT.loc[0, 'Strength'])
                self.etxWeaknesses.setText(self.dfSWOT.loc[0, 'Weakness'])
                self.etxOpportunities.setText(self.dfSWOT.loc[0, 'Opportunity'])
                self.etxThreats.setText(self.dfSWOT.loc[0, 'Threat'])
                self.leCodeInValue.setText(self.dfValue.iloc[0]['Code'])
                self._DataframeToTableWidget(self.tbDataInValue, self.dfValue)
                self.leCodeInInvesting.setText(self.dfInvesting.loc[0, 'Code'])
                self._DataframeToTableWidget(self.tbDataInInvesting, self.dfInvesting)
                self.leCodeInNaver.setText(self.dfNaver.loc[0, 'Code'])
                self._DataframeToTableWidget(self.tbDataInNaver, self.dfNaver)
                self.cboxLocInSWOTOECD.setCurrentText(self.dfSWOTOECD.iloc[0]['LOCATION'])
                self._DataframeToTableWidget(self.tbDataInSWOTOECD, self.dfSWOTOECD)
                self._DataframeToTableWidget(self.tbQuantiInSWOTResult, self.dfSWOTResult)
            elif self.tabWidget_2.tabText(self.tabWidget_2.currentIndex()) == 'ETF(OECD)':
                self.dfAccSummaryInValue = data['dfAccSummaryInValue']
                self.dfAccDetailInValue = data['dfAccDetailInValue']
                self.dfCodeInValue = data['dfCodeInValue']
                self.dfChartInValue = data['dfChartInValue']
                self.dfPriceInValue = data['dfPriceInValue']
                self.dfValueDataInValue = data['dfValueDataInValue']
                self.dfRebalInValue = data['dfRebalInValue']
            elif self.tabWidget_2.tabText(self.tabWidget_2.currentIndex()) == '가치투자':
                self.liDate = data['liDate']
                self.dfInterest = data['dfInterest']
                self.dfChart = data['dfChart']
                self.dfAccSummary = data['dfAccSummary']
                self.dfAccDetail = data['dfAccDetail']
                self._DataframeToTableWidget(_qTable=self.tbWOECDDate, _dfData=self.liDate)
                self._DataframeToTableWidget(self.tbWInterestInOECD, self.dfInterest)

                self.fig = plt.Figure()
                self.canvas = FigureCanvas(self.fig)
                self.verlayOECDChart.addWidget(self.canvas)
                self.fig.clear()
                ax = self.fig.add_subplot(111)
                x = self.dfChart['TIME'].tolist()[-7:]
                y1 = self.dfChart['Value'].tolist()[-7:]
                ax.plot(x, y1)
    def SaveCurrentPage(self):
        if self.tabWidget.tabText(self.tabWidget.currentIndex())=='Quant':
            if self.tabWidget_2.tabText(self.tabWidget_2.currentIndex()) == 'SWOT':
                self.SaveSWOT()
                self.SaveValue()
                self.SaveInvesting()
                self.SaveNaver()
                self.SaveSWOTOECD()
                self.SaveInSWOTResult()
                data = {'dfSWOT':self.dfSWOT,
                        'dfValue': self.dfValue,
                        'dfInvesting': self.dfInvesting,
                        'dfNaver': self.dfNaver,
                        'dfSWOTOECD': self.dfSWOTOECD,
                        'dfSWOTResult': self.dfSWOTResult,
                        }
            elif self.tabWidget_2.tabText(self.tabWidget_2.currentIndex()) == 'ETF(OECD)':
                data = {'dfAccSummaryInValue' : self.dfAccSummaryInValue,
                        'dfAccDetailInValue' : self.dfAccDetailInValue,
                        'dfCodeInValue' : self.dfCodeInValue,
                        'dfChartInValue' : self.dfChartInValue,
                        'dfPriceInValue' : self.dfPriceInValue,
                        'dfValueDataInValue' : self.dfValueDataInValue,
                        'dfRebalInValue' : self.dfRebalInValue,
                        }
            elif self.tabWidget_2.tabText(self.tabWidget_2.currentIndex()) == '가치투자':
                data = {'liDate': self.liDate,
                        'dfInterest': self.dfInterest,
                        'dfChart': self.dfChart,
                        'dfAccSummary': self.dfAccSummary,
                        'dfAccDetail': self.dfAccDetail,
                        }
        with open('./Quanti/data.pickle', 'wb') as f:
            pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    def TradeHist(self):
        accNumber = self.cboxAccInSWOTTradeHist.currentText()
        passward = self.leAccPWInSWOTTradeHist.text()
        startDay = self.dtStartDayInSWOT.date().toPyDate().strftime('%Y%m%d')
        endDay = self.dtEndDayInSWOT.date().toPyDate().strftime('%Y%m%d')
        tradeType = self.cboxTradeTypeInSWOT.currentText()
        if self.rBtnTotalHistoryInSWOT.isChecked():
            code = ''
        else:
            code = self.cBoxCodeInSWOT.currentText().split(' ')[0]
        self.kiwoom_Handler.GetTradeHist(accNumber, passward, startDay, endDay, tradeType, code, currency='')
        self.dfTradeHist = self.kiwoom_Handler.accInfo[accNumber]['TradeHist']
        self._DataframeToTableWidget(self.tbAccTradeHistInSWOT, self.dfTradeHist)
    def SetRadioBtnCodeInTradeHist(self):
        if self.rBtnTotalHistoryInSWOT.isChecked():
            self.cBoxCodeInSWOT.setEnabled(False)
        else:
            self.kiwoom_Handler.GetAccInfo('4555345411', password='6317', requestType=1)
            codeList = (pd.DataFrame.from_dict(self.kiwoom_Handler.accInfo['4555345411']['indivisual'], orient='index')['종목코드']
                        + ' ' +
                        pd.DataFrame.from_dict(self.kiwoom_Handler.accInfo['4555345411']['indivisual'], orient='index')['종목명'])\
                        .tolist()
            self.cBoxCodeInSWOT.addItems(codeList)
            self.cBoxCodeInSWOT.setEnabled(True)
    def RebalancingInSWOT(self):
        # 계좌 가져오기 # 비번 가져오기.
        accNumber = self.cboxAccInSWOT.currentText()
        accPW = self.leAccPWInSWOT.text()
        for idx, row in self.dfSWOTResult.iterrows():
            # read Stockdata.
            self.kiwoom_Handler.GetDayPrice(code=row['Code'], range='', requestType=0)
            dfStock = self.kiwoom_Handler.price['Price']
            dfStock.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            dfStock.sort_index(inplace=True)
            today = datetime.date.today()
            if row['Code'] in self.dfAccDetail['종목코드'].tolist():
                # 기존 있는 Code면 거래내역 확인--> 최근거래일을 거래시작일로.
                endDay = datetime.date.today()
                startDay = endDay - datetime.timedelta(days=300)
                dfTradeHist = pd.DataFrame()
                while endDay > datetime.datetime(2016,1,1).date():
                    self.kiwoom_Handler.GetTradeHist(accNumber, accPW, startDay.strftime('%Y%m%d'), endDay.strftime('%Y%m%d'),
                            tradeType='전체', code=row['Code'], currency='')
                    endDay = startDay
                    startDay = endDay - datetime.timedelta(days=300)
                    dfTradeHist = pd.concat([dfTradeHist, self.kiwoom_Handler.accInfo[accNumber]['TradeHist']], ignore_index=True)
                startTradeDay = dfTradeHist[dfTradeHist['입출구분명']=='매수'].iloc[-1]['거래일자']
                lastTradeDay = dfTradeHist[dfTradeHist['입출구분명']=='매수'].iloc[0]['거래일자']
                temp = self.dfAccDetail[self.dfAccDetail['종목코드'] == row['Code']].iloc[0]
                # 보유수량
                self.dfSWOTResult.loc[idx, 'Stock(Now)'] = temp['보유수량']
                # CAGR계산.
                endDay = MyLib.nearest(dfStock.index, today)
                period = BF.GetYear(startTradeDay, endDay)
                cagr = BF.GetCAGR(temp['매입금액'], temp['평가금액'] - temp['수수료합'] - temp['세금'], period)
                # MDD계산.
                mdd = BF.GetMDD(dfStock.loc[lastTradeDay:endDay, 'Close'])
            else:
                # 잔고에 구매한 이력이 없으면 오늘 날짜를 기준으로 1년전날짜를 거래시작일로.
                # 보유수량
                self.dfSWOTResult.loc[idx, 'Stock(Now)'] = 0
                # CAGR계산
                cagr = 0
                # MDD계산.
                mdd = 0
            self.dfSWOTResult.loc[idx, 'CAGR'] = cagr
            self.dfSWOTResult.loc[idx, 'MDD(Now)'] = mdd
            # 현재가
            self.kiwoom_Handler.GetCompanyInfo(row['Code'])
            self.dfSWOTResult.loc[idx, 'Price'] = abs(self.kiwoom_Handler.company['현재가'])
        # Rebalancing계산.
        _totalValue = self.dfAccSummary.iloc[0]['추정예탁자산']
        portfolioRatio = self.dfSWOTResult['Portion'].tolist()
        _priceList = self.dfSWOTResult['Price'].tolist()
        _nowStockNum = self.dfSWOTResult['Stock(Now)'].tolist()
        tradeStockNum, targetStockNum = Rebalancing.Rebalancing5(_totalValue, _priceList, _nowStockNum, portfolioRatio)
        self.dfSWOTResult['Trade'] = tradeStockNum
        self.dfSWOTResult['Stock(Target)'] = targetStockNum
        self._DataframeToTableWidget(self.tbQuantiInSWOTResult, self.dfSWOTResult)
    def TradeInSWOT(self):
        pass
    def EnrollInSWOT(self):
        code = self.leCodeInSWOTResult.text()
        company = self.leCompanyInSWOTResult.text()
        eps = float(self.leEPSInSWOTResult.text())
        naver = float(self.leNaverInSWOTResult.text())
        investing = self.leInvestingInSWOTResult.text()
        oecdDiff = float(self.leOECDInSWOTResult.text())
        portion = float(self.lePortionInSWOTResult.text())
        targetMDD = float(self.leMDDInSWOTResult.text())
        # if there is not same code: enroll
        # else :  update the info
        if code not in self.dfSWOTResult['Code'].tolist():
            newIdx = len(self.dfSWOTResult)
            self.dfSWOTResult.loc[newIdx, 'Code'] = code
            self.dfSWOTResult.loc[newIdx, 'Company'] = company
            self.dfSWOTResult.loc[newIdx, 'EPS'] = eps
            self.dfSWOTResult.loc[newIdx, 'Naver'] = naver
            self.dfSWOTResult.loc[newIdx, 'Investing'] = investing
            self.dfSWOTResult.loc[newIdx, 'OECD_Diff'] = oecdDiff
            self.dfSWOTResult.loc[newIdx, 'MDD(Target)'] = targetMDD
            self.dfSWOTResult.loc[newIdx, 'Portion'] = portion
        else:
            # update
            updateIdx = self.dfSWOTResult[self.dfSWOTResult['Code']==code].index[0]
            self.dfSWOTResult.loc[updateIdx, 'EPS'] = eps
            self.dfSWOTResult.loc[updateIdx, 'Naver'] = naver
            self.dfSWOTResult.loc[updateIdx, 'Investing'] = investing
            self.dfSWOTResult.loc[updateIdx, 'OECD_Diff'] = oecdDiff
            self.dfSWOTResult.loc[updateIdx, 'MDD(Target)'] = targetMDD
            self.dfSWOTResult.loc[updateIdx, 'Portion'] = portion
        self._DataframeToTableWidget(self.tbQuantiInSWOTResult, self.dfSWOTResult)
    def RemoveInSWOT(self):
        index_list = []
        for model_index in self.tbQuantiInSWOTResult.selectionModel().selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)
        for index in index_list:
            idxRow = index.row()
            self.tbQuantiInSWOTResult.removeRow(idxRow)
            self.dfSWOTResult.drop(idxRow, inplace=True)
            self.dfSWOTResult.reset_index(drop=True, inplace=True)
    def LoadInSWOTResult(self):
        fileURL = self.laSWOTURLForRead.text()
        # file read.
        self.dfSWOTResult = pd.read_csv(fileURL, encoding='cp949')
        self.dfSWOTResult['Code'] = self.dfSWOTResult['Code'].apply(lambda x: str(x).zfill(6))
        self._DataframeToTableWidget(self.tbQuantiInSWOTResult, self.dfSWOTResult)
    def SaveInSWOTResult(self):
        saveURL = self.laSWOTURLForSave.text()
        today = datetime.date.today().strftime('%Y-%m-%d')
        saveURL = saveURL + '/%s/Result/' % (today)
        if not isdir(saveURL): makedirs(saveURL)
        self.dfSWOTResult.to_csv(saveURL + 'SWOTResult.csv', encoding='cp949', index=False)
    def AccInfoInSWOT(self):
        accNumber = self.cboxAccInSWOT.currentText()
        accPW = self.leAccPWInSWOT.text()
        # 조회구분(requestType) = 1:합산, 2:개별
        self.kiwoom_Handler.GetAccInfo(accNumber, password=accPW, requestType=1)
        self.dfAccSummary = pd.DataFrame.from_dict(self.kiwoom_Handler.accInfo[accNumber]['total'],
                                                   orient='index').transpose()
        self.dfAccDetail = pd.DataFrame.from_dict(self.kiwoom_Handler.accInfo[accNumber]['indivisual'], orient='index')
        self._DataframeToTableWidget(self.tbAccSummaryInSWOT, self.dfAccSummary)
        self._DataframeToTableWidget(self.tbAccDetailInSWOT, self.dfAccDetail)
    def SetAllCountryInCBox(self):
        locFile = r'./Quanti\OECD\temp\OECD_CLI_2022-02-03.csv'
        # 없으면 경고창. data를 먼저 받으시오.
        if not os.path.exists(locFile): return True
        dfOECD = pd.read_csv(locFile)
        liOECDLoc = dfOECD['LOCATION'].tolist()
        liOECDLoc = list(set(liOECDLoc))
        liOECDLoc.sort()
        self.cboxLocInSWOTOECD.addItems(liOECDLoc)
    def GetSWOTOECDData(self):
        tempURL = tempfile.mkdtemp() + '/'
        # saveFolder = r'./Quanti/OECD/Data/'
        locOECD = self.cboxLocInSWOTOECD.currentText()
        today = datetime.date.today()
        driver = webdriver.Chrome(r'./Setting\chromdriver\chromedriver.exe')
        driver.implicitly_wait(1)
        driver.set_window_position(-2000, 0)
        driver.maximize_window()
        OECD.GetCLIDataAll(driver)
        newFileName = 'OECD_CLI_%s.csv' % (today)
        # 파일 옮기고
        if not isdir(tempURL): makedirs(tempURL)
        OECD.MoveFile(tempURL, '.csv', newFileName)
        self.dfSWOTOECD = pd.read_csv(tempURL+'/'+newFileName)
        self.dfSWOTOECD = self.dfSWOTOECD[self.dfSWOTOECD['LOCATION']==locOECD]
        self._DataframeToTableWidget(self.tbDataInSWOTOECD, self.dfSWOTOECD)
    def SaveSWOTOECD(self):
        # code = self.leCodeInSWOTOECD.text()
        locOECD = self.cboxLocInSWOTOECD.currentText()
        saveURL = self.laSWOTURLForSave.text()
        today = datetime.date.today().strftime('%Y-%m-%d')
        saveURL = saveURL + '/%s/%s/' % (today, locOECD)
        if not isdir(saveURL): makedirs(saveURL)
        self.dfSWOTOECD.to_csv(saveURL + 'SWOTOECD.csv', encoding='cp949', index=False)
    def LoadSWOTOECD(self):
        fileURL = self.laSWOTURLForRead.text()
        # file read.
        self.dfSWOTOECD = pd.read_csv(fileURL, encoding='cp949')
        # self.dfSWOTOECD['Code'] = self.dfSWOTOECD['Code'].apply(lambda x: str(x).zfill(6))
        self.cboxLocInSWOTOECD.setCurrentText(self.dfSWOTOECD.iloc[0]['LOCATION'])
        self._DataframeToTableWidget(self.tbDataInSWOTOECD, self.dfSWOTOECD)
    def GetValueData(self):
        code = self.leCodeInValue.text()
        company = self.leCompanyInValue.text()
        driverURL = r'./Setting\chromdriver\chromedriver.exe'
        driver = webdriver.Chrome(driverURL)
        driver.implicitly_wait(0.1)
        self.dfValue = GetNASI.GetNaverStatementIndex(driver=driver,code=code,company_name=company,folder='',item='가치분석')
        self.dfValue = self.dfValue.loc[['펼치기 EPS', '펼치기 BPS', '펼치기 CPS', '펼치기 SPS', '펼치기 PER', '펼치기 PBR',
                                         '펼치기 PCR', '펼치기 PSR']]
        self.dfValue.index = ['EPS','BPS','CPS','SPS','PER','PBR','PCR','PSR']
        self.dfValue.insert(0, "Code", code)
        self.dfValue.insert(1, "Company", company)
        self._DataframeToTableWidget(self.tbDataInValue, self.dfValue)
        driver.close()
    def SaveValue(self):
        code = self.leCodeInValue.text()
        saveURL = self.laSWOTURLForSave.text()
        today = datetime.date.today().strftime('%Y-%m-%d')
        saveURL = saveURL + '/%s/%s/' % (today, code)
        if not isdir(saveURL): makedirs(saveURL)
        self.dfValue.to_csv(saveURL + 'Value.csv', encoding='cp949')
    def LoadValue(self):
        fileURL = self.laSWOTURLForRead.text()
        # file read.
        self.dfValue = pd.read_csv(fileURL, encoding='cp949')
        self.dfValue['Code'] = self.dfValue['Code'].apply(lambda x: str(x).zfill(6))
        self.leCodeInValue.setText(self.dfValue.iloc[0]['Code'])
        self._DataframeToTableWidget(self.tbDataInValue, self.dfValue)
    def GetInvestingData(self):
        code = self.leCodeInInvesting.text()
        company = self.leCompanyInInvesting.text()
        driverURL = r'./Setting\chromdriver\chromedriver.exe'
        # Get dfCompanyInfo
        options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("--start-maximized")
        # options.add_argument("disable-gpu")
        driver = webdriver.Chrome(driverURL, chrome_options=options)
        # driver = webdriver.Chrome(driverURL)
        driver.implicitly_wait(0.1)
        url = 'https://kr.investing.com/equities/united-states/'
        driver.get(url)
        # driver.find_element_by_link_text('Sign In').click()
        Investing.LoginInvesting(driver)
        Investing.SearchByCode(driver, code, company)
        driver.find_element_by_link_text('기술 분석').click()
        driver.find_element_by_link_text('월간').click()

        dfSummary = pd.DataFrame(columns=['Code','Company','요약','이동평균:요약','기술적지표:요약','이동평균:매수',
                                          '이동평균:매도','기술적지표:매수','기술적지표:매도'])
        summary = []
        tbSummary = driver.find_element_by_id('techStudiesInnerWrap')
        for tbRow in tbSummary.find_elements_by_tag_name('div'):
            for tbCell in tbRow.find_elements_by_tag_name('span'):
                summary.append(tbCell.text)
        # dfSummary.loc[len(dfSummary)] = ['요약', summary[0], '', '']
        # dfSummary.loc[len(dfSummary)] = [summary[1], summary[2], summary[3], summary[4]]
        # dfSummary.loc[len(dfSummary)] = [summary[5], summary[6], summary[7], summary[8]]
        dfSummary.loc[len(dfSummary)] = [code, company, summary[0], summary[2], summary[5], summary[3], summary[4],
                                         summary[7],summary[8]]
        self.dfInvesting = copy.deepcopy(dfSummary)
        self._DataframeToTableWidget(self.tbDataInInvesting, self.dfInvesting)
        driver.close()
    def SaveInvesting(self):
        code = self.leCodeInInvesting.text()
        saveURL = self.laSWOTURLForSave.text()
        today = datetime.date.today().strftime('%Y-%m-%d')
        saveURL = saveURL + '/%s/%s/' % (today, code)
        if not isdir(saveURL): makedirs(saveURL)
        self.dfInvesting.to_csv(saveURL + 'Investing.csv', encoding='cp949', index=False)
    def LoadInvesting(self):
        fileURL = self.laSWOTURLForRead.text()
        # file read.
        self.dfInvesting = pd.read_csv(fileURL, encoding='cp949')
        self.dfInvesting['Code'] = self.dfInvesting['Code'].apply(lambda x: str(x).zfill(6))
        self.leCodeInInvesting.setText(self.dfInvesting.loc[0, 'Code'])
        self._DataframeToTableWidget(self.tbDataInInvesting, self.dfInvesting)
    def GetNaverData(self):
        code = self.leCodeInNaver.text()
        company = self.leCompanyInNaver.text()
        driverURL = r'./Setting\chromdriver\chromedriver.exe'
        # Get dfCompanyInfo
        # options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        # options.add_argument('window-size=1920x1080')
        # options.add_argument("--start-maximized")
        # options.add_argument("disable-gpu")
        # driver = webdriver.Chrome(driverURL, chrome_options=options)
        driver = webdriver.Chrome(driverURL)
        driver.implicitly_wait(0.1)
        url = 'http://companyinfo.stock.naver.com/v1/company/c1010001.aspx?cmp_cd=' + code
        driver.get(url)
        table = driver.find_element_by_id('cTB15')
        col_names = [col_name.text for col_name in table.find_elements_by_css_selector('tbody > tr:nth-child(1) > th')]
        dfOpinion = pd.DataFrame(columns=col_names)
        dfOpinion.loc[len(dfOpinion)] = [data.text for data in table.find_elements_by_css_selector('tbody > tr:nth-child(2) > td')]
        driver.close()
        self.dfNaver = copy.deepcopy(dfOpinion)
        self.dfNaver.insert(0, "Code", [code])
        self.dfNaver.insert(1, "Company", [company])
        self._DataframeToTableWidget(self.tbDataInNaver, self.dfNaver)
    def SaveNaver(self):
        code = self.leCodeInNaver.text()
        saveURL = self.laSWOTURLForSave.text()
        today = datetime.date.today().strftime('%Y-%m-%d')
        saveURL = saveURL + '/%s/%s/' % (today, code)
        if not isdir(saveURL): makedirs(saveURL)
        self.dfNaver.to_csv(saveURL + 'Naver.csv', encoding='cp949', index=False)
    def LoadNaver(self):
        fileURL = self.laSWOTURLForRead.text()
        # file read.
        self.dfNaver = pd.read_csv(fileURL, encoding='cp949')
        self.dfNaver['Code'] = self.dfNaver['Code'].apply(lambda x: str(x).zfill(6))
        self.leCodeInNaver.setText(self.dfNaver.loc[0, 'Code'])
        self._DataframeToTableWidget(self.tbDataInNaver, self.dfNaver)
    def CodeToCompany(self, codeSlot, companySlot):
        code = codeSlot.text()
        if len(code) < 6:
            return True
        company = self.kiwoom_Handler.GetCompanyName(code)
        companySlot.setText(company)
    def SaveSWOT(self):
        code = self.leCodeInSWOT.text()
        company = self.leCompanyInSWOT.text()
        saveURL = self.laSWOTURLForSave.text()
        today = datetime.date.today().strftime('%Y-%m-%d')
        saveURL = saveURL + '/%s/%s/'%(today,code)
        # get SWOT data from text widget.
        strength = self.etxStrengths.toPlainText()
        weakness = self.etxWeaknesses.toPlainText()
        opportunity = self.etxOpportunities.toPlainText()
        threat = self.etxThreats.toPlainText()
        # if code in self.dfSWOT['Code'].tolist():
        #     sameIdx = self.dfSWOT.index[self.dfSWOT['Code'] == code][0]
        #     self.dfSWOT.loc[sameIdx, 'Strength'] += strength
        #     self.dfSWOT.loc[sameIdx, 'Weakness'] += weakness
        #     self.dfSWOT.loc[sameIdx, 'Opportunity'] += opportunity
        #     self.dfSWOT.loc[sameIdx, 'Threat'] += threat
        # else:
        #     self.dfSWOT.loc[len(self.dfSWOT)] = [code, company, strength, weakness, opportunity, threat]
        self.dfSWOT.loc[len(self.dfSWOT)] = [code, company, strength, weakness, opportunity, threat]
        # 날짜/Code/SWOT(Naver,MDD,Investing,OECD)
        if not isdir(saveURL): makedirs(saveURL)
        self.dfSWOT.to_csv(saveURL + 'SWOT.csv', encoding='cp949', index=False)
        # if not os.path.isfile(saveURL + 'SWOT.csv'):
        #     self.dfSWOT.to_csv(saveURL + 'SWOT.csv', encoding='cp949', index=False, mode='w')
        # else:
        #     self.dfSWOT.to_csv(saveURL + 'SWOT.csv', encoding='cp949', index=False, mode='a', header=False)
    def LoadSWOT(self):
        # file URL
        fileURL = self.laSWOTURLForRead.text()
        # file read.
        self.dfSWOT = pd.read_csv(fileURL, encoding='cp949')
        self.dfSWOT['Code'] = self.dfSWOT['Code'].apply(lambda x: str(x).zfill(6))
        self.leCodeInSWOT.setText(self.dfSWOT.loc[0, 'Code'])
        self.etxStrengths.setText(self.dfSWOT.loc[0, 'Strength'])
        self.etxWeaknesses.setText(self.dfSWOT.loc[0, 'Weakness'])
        self.etxOpportunities.setText(self.dfSWOT.loc[0, 'Opportunity'])
        self.etxThreats.setText(self.dfSWOT.loc[0, 'Threat'])
    def ReadCode(self):
        codeURL = self.laCodeURLForRead.text()
        dfCompanyInfo = pd.read_csv(codeURL, encoding='cp949')
        dfCompanyInfo = dfCompanyInfo[['종목코드', '종목명']]
        dfCompanyInfo.rename(columns={'종목코드': 'Code', '종목명': 'Company'}, inplace=True)
        self.dfCodeInValue = copy.deepcopy(dfCompanyInfo)
        self._DataframeToTableWidget(self.tbWReadDataInValue, self.dfCodeInValue)
    def ReadPrice(self):
        priceURL = self.laPriceURLForRead.text()
        dfStock = pd.read_csv(priceURL, encoding='cp949', engine='python')
        dfStock.drop_duplicates(subset=['Date'], inplace=True)
        dfStock['Date'] = pd.to_datetime(dfStock['Date'])
        dfStock.sort_values(by='Date', ascending=True, inplace=True)
        dfStock.set_index(['Date'], drop=True, inplace=True)
        self.dfPriceInValue = copy.deepcopy(dfStock)
        self._DataframeToTableWidget(self.tbWReadDataInValue, self.dfPriceInValue)
    def AccInfoInValue(self):
        accNumber = self.cboxAccInValue.currentText()
        accPW = self.leAccPWInValue.text()
        # 조회구분(requestType) = 1:합산, 2:개별
        self.kiwoom_Handler.GetAccInfo(accNumber, password=accPW, requestType=1)
        self.dfAccSummary = pd.DataFrame.from_dict(self.kiwoom_Handler.accInfo[accNumber]['total'],
                                                   orient='index').transpose()
        self.dfAccDetail = pd.DataFrame.from_dict(self.kiwoom_Handler.accInfo[accNumber]['indivisual'], orient='index')
        self._DataframeToTableWidget(self.tbAccSummaryInValue, self.dfAccSummary)
        self._DataframeToTableWidget(self.tbAccDetailInValue, self.dfAccDetail)
    def StockCodeDown(self):
        field = self.cboxICodeForDown.currentText()
        saveFolder = self.laSaveFolderForCode.text()
        StockCodeDown.main(field, saveFolder)
    def StockDown(self):
        # read code.
        codeURL = self.laCodeFile.text()
        dfCompanyInfo = pd.read_csv(codeURL, encoding='cp949')
        # saveFolder.
        save_folder = self.laSaveFolderForPrice.text()

        if not isdir(save_folder):
            makedirs(save_folder)
        else:
            downfiles = [f for f in listdir(save_folder) if isfile(join(save_folder, f))]
            downCodes = [file.split('_')[1].replace('.csv', '') for file in downfiles]
            missedCode = MyLib.GetMissedCode(dfCompanyInfo['종목코드'].tolist(), downCodes)
            dfCompanyInfo = dfCompanyInfo[dfCompanyInfo['종목코드'].isin(missedCode)]

        for idx, data in dfCompanyInfo.iterrows():
            Code = str(data['종목코드']).zfill(6)
            Company = data[[colName for colName in data.index if '한글종목약명'==colName or '종목명'==colName][0]]
            print('%s) Code : %s  || Company : %s start......' % (idx, Code, Company), end='')
            sys.stdout.flush()
            dfPrice = pd.DataFrame()
            while True:
                if dfPrice.empty:
                    # today range.
                    sStartday = datetime.date.today().strftime('%Y%m%d')
                else:
                    dStartday = dfPrice.index.min() - datetime.timedelta(days=1)
                    sStartday = dStartday.strftime('%Y%m%d')
                time.sleep(5)
                self.kiwoom_Handler.GetDayPrice(code=Code, range=sStartday, requestType=0)
                # dfPrice = self.kiwoom_Handler.price['Price']
                dfNewPrice = self.kiwoom_Handler.price['Price']
                if dfNewPrice.empty:
                    break
                else:
                    dfPrice = dfPrice.append(dfNewPrice)
                    dfPrice.sort_index(inplace=True)
                    dfPrice = dfPrice[~dfPrice.index.duplicated(keep='last')]
                    dfPrice.to_csv(save_folder + '/%s_%s.csv' % (Code, Company), encoding='cp949', index=True)
            del dfPrice
            print('Done!!')
    def Screening(self):
        financeFolder = self.laValueDataFolder.text()
        priceFolder = self.laPriceDataFolder.text()
        # codeURL = self.laCodeFile.text()
        # dfCompanyInfo = pd.read_csv(codeURL, encoding='cp949')
        thisDay = datetime.date.today().strftime('%Y-%m-%d')
        self.dfValueDataInValue = PSRPCR.GetPERDebitRatioFiltered2(thisDay, priceFolder, financeFolder)
        self._DataframeToTableWidget(self.tbWCalcInValue, self.dfValueDataInValue)
        # multiProcessPERPBR = Process(target=PSRPCR.RunPERPBRPCRPSR, args=(thisDayStr, thisDayStr2, filename, field,))
        # multiProcessPERPBR.start()
    def CalRebalancing(self):
        pass
    def StartCrwal(self):
        from Infomation.NaverCrawl import NaverInfo
        # Get driverURL
        driverURL = r'./Setting\chromdriver\chromedriver.exe'
        # Get dfCompanyInfo
        codeURL = self.laCodeFileNaver.text()
        # Get item
        item = self.cboxItemForCrawl.currentText()
        # Get save_folder
        save_folder = self.laSaveFolderForCrwal.text()

        naverInfo = NaverInfo()
        naverInfo.SetDriverURL(driverURL)
        naverInfo.SetCodeURL(codeURL)
        naverInfo.SetSaveURL(save_folder)
        naverInfo.SetItem(item)
        naverInfo.InfoDown()
    def SetFile2(self, label, btnFunc):
        file = QFileDialog.getOpenFileName(self, 'Select File', './')
        label.setText(file[0])
        btnFunc()
        # if button == self.btnSWOTURLForRead:
        #     self.LoadSWOT()
        # elif button == self.btnLoadInValue:
        #     self.LoadValue()
        # elif button == self.btnLoadInInvesting:
        #     self.LoadInvesting()
        # elif button == self.btnLoadInNaver:
        #     self.LoadNaver()
        # elif button == self.btnLoadInSWOTOECD:
        #     self.LoadSWOTOECD()
        # elif button == self.pBtnLoadInSWOTResult:
        #     self.LoadInSWOTResult()
    def SetFile(self, label):
        file = QFileDialog.getOpenFileName(self, 'Select File', './')
        label.setText(file[0])
    def SetFolder(self, label):
        FileFolder = QFileDialog.getExistingDirectory(self, 'Find Folder')
        label.setText(FileFolder)
    def OECDCLISendOrder(self):
        accNumber = self.cboxAccInOECD.currentText()
        accPW = self.leAccPWInOECD.text()
        for idx,row in self.dfInterest.iterrows():
            nTrade = row['TradeNum']
            if nTrade>0:
                code = row['Code']
                price = row['Price']
                # 신규매수 - 조건부지정가
                buyInfo = {'account': accNumber, 'nOrderType': 1, 'sCode': code, 'nQty': nTrade,'nPrice': price,
                           'sHogaGb': '05', 'sOrgOrderNo': ''}
                self.kiwoom_Handler.BuyStock(self, buyInfo)
            elif nTrade<0:
                code = row['Code']
                price = row['Price']
                # 신규매도 - 조건부지정가
                sellInfo = {'account': accNumber, 'nOrderType': 2, 'sCode': code, 'nQty': nTrade, 'nPrice': price,
                            'sHogaGb': '05', 'sOrgOrderNo': ''}
                self.kiwoom_Handler.SellStock(sellInfo)
    def OECDCLIResult(self):
        today = datetime.date.today()
        saveFolder = r'./Quanti\OECD/result'
        saveFilename = 'OECDCLI_%s.csv' % (today.strftime('%Y%m%d'))
        dataOECD = r'./\Quanti\OECD\Data'

        date = self.cboxDateTradeInOECD.currentText()
        numCountry = len(set(self.dfInterest['Country'].tolist()))
        self.dfInterest['Date'] = None
        self.dfInterest['Score'] = None
        self.dfInterest['ScoreDiff'] = None
        self.dfInterest['Percentage'] = None
        self.dfInterest['Price'] = None
        self.dfInterest['HavingNum'] = None
        for idx,row in self.dfInterest.iterrows():
            # get score
            dateOECD, score, scoreDiff = OECD.CLIResult4(dataOECD,date, row['Country'])
            # condition buy or sell.
            # how much for stock?
            if scoreDiff > 0:
                numCompany = sum(self.dfInterest['Country']==row['Country'])
                allocPercentage = 100 / numCountry / numCompany
            else:
                allocPercentage = 0
            # stockPrice
            self.kiwoom_Handler.GetCompanyInfo(row['Code'])
            price = self.kiwoom_Handler.company['현재가']
            self.dfInterest.loc[idx, 'Date'] = dateOECD
            self.dfInterest.loc[idx, 'Score'] = round(score,2)
            self.dfInterest.loc[idx, 'ScoreDiff'] = round(scoreDiff,2)
            self.dfInterest.loc[idx, 'Percentage'] = round(allocPercentage,2)
            self.dfInterest.loc[idx, 'Price'] = price
            if self.dfAccDetail.empty:
                self.dfInterest.loc[idx, 'HavingNum'] = 0
                continue
            havingStock = self.dfAccDetail[row['Code']==self.dfAccDetail['종목코드']]
            if havingStock.empty:
                self.dfInterest.loc[idx, 'HavingNum'] = 0
            else:
                self.dfInterest.loc[idx, 'HavingNum'] = havingStock['보유수량'].iloc[0]
        # get rebalancing result.
        diffStockNum, targetStockNum = Rebalancing.Rebalancing5(int(self.dfAccSummary['추정예탁자산'].iloc[0]),
                                    self.dfInterest['Price'].tolist(),self.dfInterest['HavingNum'].tolist(),
                                    self.dfInterest['Percentage'].tolist())
        # OEDC 파일날짜, 나라, 현재금액, 총금액, 퍼센티지.
        self.dfInterest['TargetNum'] = targetStockNum
        self.dfInterest['TradeNum'] = diffStockNum
        self.dfInterest.to_csv(saveFolder + '/' + saveFilename, encoding='cp949', index=False)
        self.tbWInterestInOECD.clear()
        self._DataframeToTableWidget(self.tbWInterestInOECD, self.dfInterest)
    def EnrollCompany(self):
        # get Company Code.
        code = self.leCodeInOECD.text()
        # get Company Name.
        company = self.leCompanyInOECD.text()
        # get Loc.
        location = self.cboxLocInOECD.currentText()
        row = len(self.dfInterest)
        self.dfInterest.loc[row, 'Code']    = code
        self.dfInterest.loc[row, 'Company'] = company
        self.dfInterest.loc[row, 'Country'] = location
        self._DataframeToTableWidget(self.tbWInterestInOECD, self.dfInterest)
    def RemoveCompany(self):
        index_list = []
        for model_index in self.tbWInterestInOECD.selectionModel().selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)
        for index in index_list:
            idxRow = index.row()
            self.tbWInterestInOECD.removeRow(idxRow)
            self.dfInterest.drop(idxRow, inplace=True)
            self.dfInterest.reset_index(drop=True, inplace=True)
    def LoadCompany(self):
        dataFile = r"./Quanti\OECD\temp\InterestCompany.json"
        df = pd.read_json(dataFile)
        df['Code'] = df['Code'].apply(lambda x: str(x).zfill(6))
        self.dfInterest = df
        self.tbWInterestInOECD.clear()
        self._DataframeToTableWidget(self.tbWInterestInOECD, self.dfInterest)
    def SaveCompany(self):
        # save file items.
        dataFile = r"./Quanti\OECD\temp\InterestCompany.json"
        self.dfInterest.to_json(dataFile)
        # number_of_rows = self.tbWInterestInOECD.rowCount()
        # number_of_columns = self.tbWInterestInOECD.columnCount()
        # colNames = [self.tbWInterestInOECD.horizontalHeaderItem(idx).text() for idx in range(number_of_columns)]
        # tmp_df = pd.DataFrame(columns=colNames,index=range(number_of_rows))
        # for i in range(number_of_rows):
        #     for j, colName in enumerate(colNames):
        #         data = self.tbWInterestInOECD.item(i, j)
        #         if data!=None:
        #             tmp_df.at[i, colName] = data.text()
        #         else:
        #             tmp_df.at[i, colName] = data
        # tmp_df.to_json(dataFile)
        # return tmp_df
    def CodeChangeInOECD(self):
        code = self.leCodeInOECD.text()
        if len(code) < 6:
            return True
        company = self.kiwoom_Handler.GetCompanyName(code)
        self.leCompanyInOECD.setText(company)
    def AccInfoInOECD(self):
        accNumber = self.cboxAccInOECD.currentText()
        accPW = self.leAccPWInOECD.text()
        # 조회구분(requestType) = 1:합산, 2:개별
        self.kiwoom_Handler.GetAccInfo(accNumber, password=accPW, requestType=1)
        self.dfAccSummary = pd.DataFrame.from_dict(self.kiwoom_Handler.accInfo[accNumber]['total'], orient='index').transpose()
        self.dfAccDetail = pd.DataFrame.from_dict(self.kiwoom_Handler.accInfo[accNumber]['indivisual'], orient='index')
        self._DataframeToTableWidget(self.tbAccSummaryInOECD, self.dfAccSummary)
        self._DataframeToTableWidget(self.tbAccDetailInOECD, self.dfAccDetail)

    def ShowOECDChart(self):
        # get date
        date = self.cboxDateInChartOECD.currentText()
        # get country
        loc = self.cboxLocInChartOECD.currentText()
        # read data
        dataOECD = r'./\Quanti\OECD\Data'
        dateFiles = [f for f in listdir(dataOECD) if isfile(join(dataOECD, f)) and '.csv' in f and 'OECD_CLI' in f and date in f]
        dfOECD = pd.read_csv(dataOECD+'/'+dateFiles[0])
        # display country
        dfOECD = dfOECD[dfOECD['LOCATION']==loc]
        self.dfChart = dfOECD
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)
        self.verlayOECDChart.addWidget(self.canvas)
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        x = dfOECD['TIME'].tolist()[-7:]
        y1 = dfOECD['Value'].tolist()[-7:]
        ax.plot(x, y1)
        # ax.xticks(fontsize=7)
        ax.tick_params(axis='x', labelsize=7)
        self.canvas.draw()
    def EnrollCountry(self):
        text = self.cboxLocInOECD.currentText()
        self.liwOECDLoc.addItem(text)
    def UpdateDate(self, cboxDate):
        cboxDate.clear()
        dataFolder = r'./Quanti\OECD\Data'
        dataFiles = [f.replace('OECD_CLI_', '') for f in listdir(dataFolder) if
                     isfile(join(dataFolder, f)) and '.csv' in f]
        dataFiles.sort(reverse=True)
        if len(dataFiles) <= 0: return True
        for date in dataFiles:
            cboxDate.addItem(date.replace('.csv', ''))
    def UpdateCountry(self, cboxLoc, cboxDate=None):
        cboxLoc.clear()
        # get date.
        if cboxDate is None:
            date = '2022-02-03'
        else:
            date = cboxDate.currentText()
        # read file.
        dataOECD = r'./\Quanti\OECD\Data'
        dateFiles = [f for f in listdir(dataOECD) if
                     isfile(join(dataOECD, f)) and '.csv' in f and 'OECD_CLI' in f and date in f]
        dfOECD = pd.read_csv(dataOECD + '/' + dateFiles[0])
        # update loc.
        liOECDLoc = dfOECD['LOCATION'].tolist()
        liOECDLoc = list(set(liOECDLoc))
        cboxLoc.addItems(liOECDLoc)
    def RefreshDateNLoc(self):
        self.UpdateDate(self.cboxDateInChartOECD)
        self.UpdateCountry(self.cboxLocInChartOECD,self.cboxDateInChartOECD)
        self.UpdateDate(self.cboxDateTradeInOECD)
        self.UpdateCountry(self.cboxLocInOECD)
    def SaveLocation(self):
        # save file items.
        items = [self.liwOECDLoc.item(i).text() for i in range(self.liwOECDLoc.count())]
        dataFile = r"./Quanti\OECD\temp\InterestLoc.json"
        with open(dataFile, "w") as fp:
            json.dump(items, fp)
    def LoadLocation(self):
        # read lastest interest loc in list widget.
        dataFile = r'./Quanti\OECD\temp\InterestLoc.json'
        if not os.path.exists(dataFile): return True
        with open(dataFile, "r") as fp:
            items = json.load(fp)
        self.liwOECDLoc.addItems(items)
    def RemoveLocation(self):
        selectedItem = self.liwOECDLoc.selectedItems()
        if not selectedItem: return True
        for item in selectedItem:
            self.liwOECDLoc.takeItem(self.liwOECDLoc.row(item))
    def OECDCLIDate(self):
        saveFolder = r'./Quanti/OECD/ReleaseDate'
        today = datetime.date.today()
        dateOECDCLI = OECD.GetCLIDate()
        self.liDate = dateOECDCLI['date'].tolist()
        if not os.path.isdir(saveFolder): os.makedirs(saveFolder)
        dateOECDCLI.to_csv(saveFolder + r'/date_OECD_CLI_%s.csv' % (today), encoding='cp949', index=False)
        self._DataframeToTableWidget(_qTable=self.tbWOECDDate, _dfData=dateOECDCLI)
    def ShowOECDCLIDate(self):
        file = QFileDialog.getOpenFileName(self, 'Select File', './')
        dateOECDCLI = pd.read_csv(file[0],encoding='cp949')
        self._DataframeToTableWidget(_qTable=self.tbWOECDDate, _dfData=dateOECDCLI)
    def OECDCLIData(self):
        saveFolder = r'./Quanti/OECD/Data/'
        today = datetime.date.today()
        # 데이터다운 받고
        OECD.GetCLIData()
        newFileName = 'OECD_CLI_%s.csv' % (today)
        # 파일 옮기고
        if not isdir(saveFolder): makedirs(saveFolder)
        OECD.MoveFile(saveFolder, '.csv', newFileName)
        # update
        self.RefreshDateNLoc()
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