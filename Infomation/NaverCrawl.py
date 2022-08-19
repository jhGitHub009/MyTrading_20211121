from selenium import webdriver
import pandas as pd
import Quanti.GetNaverAnalysisFinancial_190406 as GetNAF
import Quanti.GetNaverAnalysisSector_190406 as GetNAS
import Quanti.GetNaverAnalysisStatementIndex_190406 as GetNASI
import Quanti.GetNaverFSQC_190406 as GetNAFSQC
from Infomation.DataCrawl import *
import logging
# Set the threshold for selenium to WARNING
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
seleniumLogger.setLevel(logging.WARNING)
# Set the threshold for urllib3 to WARNING
from urllib3.connectionpool import log as urllibLogger
urllibLogger.setLevel(logging.WARNING)

class NaverInfo(DataCrawl):
    def __init__(self):
        self.driverURL = ''
        self.codeURL = ''
        self.saveURL = ''
        self.loadURL = ''
        self.item = ''
    def InfoDown(self):
        # Get dfCompanyInfo
        dfCompanyInfo = pd.read_csv(self.codeURL, encoding='cp949')
        # Get item
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("--start-maximized")
        # options.add_argument("--log-level=3")
        # options.add_argument('--disable-logging')
        # options.add_argument("--disable-notifications")
        # options.add_argument("disable-gpu")
        driver = webdriver.Chrome(self.driverURL, options=options)
        # 포괄손익계산서, 재무상태표, 현금흐름표
        if self.item == '포괄손익계산서' or self.item == '재무상태표' or self.item == '현금흐름표':
            if self.item not in self.saveURL:
                self.saveURL = self.saveURL + '/재무분석/%s/' % (self.item)
            GetNAF.main(driver, dfCompanyInfo, self.saveURL, self.item)
        elif self.item == 'Sector':
            if self.item not in self.saveURL:
                self.saveURL = self.saveURL + '/%s/' % (self.item)
            GetNAS.main(driver, dfCompanyInfo, self.saveURL, self.item)
        ## 가치분석, '수익성', '성장성', '안정성', '활동성'
        elif self.item == '가치분석' or self.item == '수익성' or self.item == '성장성' or self.item == '안정성' or self.item == '활동성':
            if self.item not in self.saveURL:
                self.saveURL = self.saveURL + '/투자지표/%s/' % (self.item)
            GetNASI.main(driver, dfCompanyInfo, self.saveURL, self.item)
        elif self.item == '기업현황':
            if self.item not in self.saveURL:
                self.saveURL = self.saveURL + '/%s/' % (self.item)
            GetNAFSQC.main(driver, dfCompanyInfo, self.saveURL, self.item)
        driver.quit()
    def InfoSave(self, SaveFolder):
        pass
    def InfoLoad(self, LoadFileURL):
        pass
    def InfoAfterTreat(self):
        pass
    def Login(self):
        pass

    # For this class
    def SetDriverURL(self, driverURL):
        self.driverURL = driverURL
    def GetDriverURL(self):
        return self.driverURL
    def SetCodeURL(self, codeURL):
        self.codeURL = codeURL
    def GetCodeURL(self):
        return self.codeURL
    def SetSaveURL(self, saveURL):
        self.saveURL = saveURL
    def GetSaveURL(self):
        return self.SaveURL
    def SetLoadURL(self, loadURL):
        self.loadURL = loadURL
    def GetLoadURL(self):
        return self.loadURL
    def SetItem(self, item):
        self.item = item
    def GetItem(self):
        return self.item
if __name__ == '__main__':
    driverURL = r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Setting\chromdriver\chromedriver.exe'
    codeURL = r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\StockCode\20220511\kosdaq_20220511.csv'
    save_folder = r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Naver\20220511\Kosdaq'
    # naverCrawl.loadURL = r''
    item = r'포괄손익계산서'
    print(item)
    naverInfo = NaverInfo()
    naverInfo.SetDriverURL(driverURL)
    naverInfo.SetCodeURL(codeURL)
    naverInfo.SetSaveURL(save_folder)
    naverInfo.SetItem(item)
    for i in range(500):
        try:
            naverInfo.InfoDown()
        except:
            print('----------   Error occurred!!   ----------')
            continue