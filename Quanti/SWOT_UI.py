import pandas as pd

# SWOT
class SWOTUI():
    # init
    def __init__(self):
        # 멤버변수
        self.dfSWOT = pd.DataFrame(columns=['Code','Company','Strength','Weakness','Opportunity','Threat'])
        self.dfValue = None
        self.dfInvesting = None
        self.dfNaver = None
        self.dfSWOTOECD = None
        self.dfSWOTResult = pd.DataFrame(columns=['Code','Company','EPS','Naver','Investing','OECD_Diff',
                                                  'CAGR','MDD(Now)','MDD(Target)','Portion','Price','Stock(Now)',
                                                  'Stock(Target)','Trade'])
        self.dfTradeHist = None

        # self.setTabOrder(self.leCodeInSWOT, self.etxStrengths)    # UI쪽에서 설정.
        # self.setTabOrder(self.leCodeInSWOTResult, self.leEPSInSWOTResult)
        # self.setTabOrder(self.leEPSInSWOTResult, self.leNaverInSWOTResult)
        # self.setTabOrder(self.leNaverInSWOTResult, self.leInvestingInSWOTResult)
        # self.setTabOrder(self.leInvestingInSWOTResult, self.leOECDInSWOTResult)
        # self.setTabOrder(self.leOECDInSWOTResult, self.lePortionInSWOTResult)
        # self.setTabOrder(self.lePortionInSWOTResult, self.leMDDInSWOTResult)
        # SWOT

        self.leCodeInSWOT.textChanged.connect(lambda: self.CodeChangeInSWOT(self.leCodeInSWOT, self.leCompanyInSWOT))
        self.btnLoadInSWOT.clicked.connect(lambda: self.SetFile2(self.laSWOTURLForRead, self.LoadSWOT))
        self.btnSWOTURLForSave.clicked.connect(lambda: self.SetFolder(self.laSWOTURLForSave))
        # self.btnLoadInSWOT.clicked.connect(self.LoadSWOT)
        self.btnSaveInSWOT.clicked.connect(self.SaveSWOT)
        # 가치DATA
        self.leCodeInValue.textChanged.connect(lambda: self.CodeChangeInSWOT(self.leCodeInValue, self.leCompanyInValue))
        self.btnLoadInValue.clicked.connect(lambda: self.SetFile2(self.laSWOTURLForRead, self.LoadValue))
        # self.btnValueURLForSave.clicked.connect(lambda: self.SetFolder(self.laValueURLForSave))
        self.btnCrawlInValue.clicked.connect(self.GetValueData)
        # self.btnLoadInValue.clicked.connect(self.LoadValue)
        self.btnSaveInValue.clicked.connect(self.SaveValue)
        # Investing.
        self.leCodeInInvesting.textChanged.connect(lambda: self.CodeChangeInSWOT(self.leCodeInInvesting, self.leCompanyInInvesting))
        self.btnLoadInInvesting.clicked.connect(lambda: self.SetFile2(self.laSWOTURLForRead, self.LoadInvesting))
        # self.btnInvestingURLForSave.clicked.connect(lambda: self.SetFolder(self.laInvestingURLForSave))
        self.btnCrawlInInvesting.clicked.connect(self.GetInvestingData)
        # self.btnLoadInInvesting.clicked.connect(self.LoadInvesting)
        self.btnSaveInInvesting.clicked.connect(self.SaveInvesting)
        # Naver.
        self.leCodeInNaver.textChanged.connect(lambda: self.CodeChangeInSWOT(self.leCodeInNaver, self.leCompanyInNaver))
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
        self.pBtnSelectInSWOT.clicked.connect(self.AccInfoInSWOT)
        self.cboxAccInSWOT.addItems(self.kiwoom_Handler.userInfo['accList'])
        # Quanti
        # self.leCodeInSWOTResult.textEdited.connect(self.tabNext)
        self.pBtnLoadInSWOTResult.clicked.connect(lambda: self.SetFile2(self.laSWOTURLForRead, self.LoadInSWOTResult))
        # self.btnSWOTResultURLForSave.clicked.connect(lambda: self.SetFolder(self.laSWOTResultURLForSave))
        self.leCodeInSWOTResult.textChanged.connect(lambda: self.CodeChangeInSWOT(self.leCodeInSWOTResult, self.leCompanyInSWOTResult))
        self.pBtnEnrollInSWOT.clicked.connect(self.EnrollInSWOT)                # 등록
        self.pBtnRemoveInSWOT.clicked.connect(self.RemoveInSWOT)                # 삭제
        self.pBtnRebalancingInSWOT.clicked.connect(self.RebalancingInSWOT)      # 계산
        self.pBtnTradeInSWOT.clicked.connect(self.TradeInSWOT)                  # 거래실행
        # self.pBtnLoadInSWOTResult.clicked.connect(self.LoadInSWOTResult)
        self.pBtnSaveInSWOTResult.clicked.connect(self.SaveInSWOTResult)
        # TradeHist
        self.dtEndDayInSWOT.setDate(QDate.currentDate())
        self.dtStartDayInSWOT.setDate(QDate.currentDate())
        self.rBtnTotalHistoryInSWOT.clicked.connect(self.SetRadioBtnCodeInTradeHist)
        self.rBtnCodeHistoryInSWOT.clicked.connect(self.SetRadioBtnCodeInTradeHist)
        self.cboxAccInSWOTTradeHist.addItems(self.kiwoom_Handler.userInfo['accList'])
        self.pBtnSelectInSWOTHist.clicked.connect(self.TradeHist)
    def CodeToCompany(self):
        pass
    def SaveSWOT(self):
        pass
    def GetValueData(self):
        pass
    def GetValueData(self):
        pass
    def SaveValue(self):
        pass
    def GetInvestingData(self):
        pass
    def SaveValue(self):
        pass
    def GetNaverData(self):
        pass
    def SaveNaver(self):
        pass
    def GetSWOTOECDData(self):
        pass
    def SaveSWOTOECD(self):
        pass
    def EnrollInSWOT(self):
        pass
    def RemoveInSWOT(self):
        pass