import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3
import datetime
from .Kiwoom_API import Kiwoom

class Kiwoom_Handler(QAxWidget):
    def __init__(self):
        self.kiwoom = Kiwoom()
        self.userInfo = None
        self.accInfo = {}
        self.price = {}
        self.lastTrade = {}
        self.company = {}
        self.callInfo = {}
    # public function.
    # Login
    # CommConnect(사용자 호출) -> 로그인창 출력 -> OnEventConnect(이벤트 발생)
    def Login(self):
        self.kiwoom._CommConnect()
    def GetConnectState(self):
        ret = self.kiwoom._GetConnectState()
        if ret==1:
            return True
        else:
            return False
        # if ret == 1:print("connected")
        # else:print("disconnected")
    # 기본정보 - 계좌, 개인정보, 내계좌 갯수, 내계좌
    def GetUserINFO(self):
        self.userInfo = self.kiwoom._GetLoginInfo()
        for accNum in self.userInfo['accList']:
            self.accInfo[accNum] = {}
        # print(self.userInfo)
    # 계좌 정보.
    def GetAccInfo(self, accNumber, password, requestType):
        self.kiwoom._SetInputValue("계좌번호", accNumber)
        self.kiwoom._SetInputValue("비밀번호", password)
        self.kiwoom._SetInputValue("비밀번호입력매체구분", 00)
        self.kiwoom._SetInputValue("조회구분", requestType)
        self.kiwoom._CommRqData("opw00018_req", "opw00018", "0", "2000")
        self.accInfo[accNumber] = self.kiwoom.opw00018Output
    # 주식정보
        # 회사 정보 opt10001 : 주식기본정보요청
    def GetCompanyInfo(self, code):
        self.kiwoom._SetInputValue("종목코드", code)
        self.kiwoom._CommRqData("opt10001_req", "opt10001", "0", "2000")
    # 호가정보  opt10004
    def GetAskingPrice(self, code):
        self.kiwoom._SetInputValue("종목코드", code)
        self.kiwoom._CommRqData("opt10004_req", "opt10004", "0", "2000")
    # 차트정보 일봉 주봉 월봉, 년봉, 틱봉, 분봉, 초봉
    def GetTickPrice(self,code,range,requestType):
        self.price['DataType'] = 'tick'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = requestType
        self.price['Price'] = self._GetStockPrice(chartType='tick', code=code, range=range, requestType=requestType)
    def GetMinPrice(self,code,range,requestType):
        self.price['DataType'] = 'min'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = requestType
        self.price['Price'] = self._GetStockPrice(chartType='min', code=code, range=range, requestType=requestType)
    def GetDayPrice(self,code,range,requestType):
        self.price['DataType'] = 'day'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = requestType
        self.price['Price'] = self._GetStockPrice(chartType='day', code=code, range=range, requestType=requestType)
    def GetWeekPrice(self,code,range,requestType):
        self.price['DataType'] = 'week'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = requestType
        self.price['Price'] = self._GetStockPrice(chartType='week', code=code, range=range, requestType=requestType)
    def GetMonthPrice(self,code,range,requestType):
        self.price['DataType'] = 'month'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = requestType
        self.price['Price'] = self._GetStockPrice(chartType='month', code=code, range=range, requestType=requestType)
    def GetYearPrice(self, code, range, requestType):
        self.price['DataType'] = 'year'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = requestType
        self.price['Price'] = self._GetStockPrice(chartType='year', code=code, range=range, requestType=requestType)

    def GetIndexTickPrice(self, code, range):
        self.price['DataType'] = 'indextick'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = None
        dfPrice = self._GetStockPrice(chartType='indextick', code=code, range=range)
    def GetIndexMinPrice(self, code, range):
        self.price['DataType'] = 'indexmin'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = None
        dfPrice = self._GetStockPrice(chartType='indexmin', code=code, range=range)
    def GetIndexDayPrice(self, code, range):
        self.price['DataType'] = 'indexday'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = None
        dfPrice = self._GetStockPrice(chartType='indexday', code=code, range=range)
    def GetIndexWeekPrice(self, code, range):
        self.price['DataType'] = 'indexweek'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = None
        dfPrice = self._GetStockPrice(chartType='indexweek', code=code, range=range)
    def GetIndexMonthPrice(self, code, range):
        self.price['DataType'] = 'indexmonth'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = None
        self._GetStockPrice(chartType='indexmonth', code=code, range=range)
    def GetIndexYearPrice(self, code, range):
        self.price['DataType'] = 'indexyear'
        self.price['Code'] = code
        self.price['Range'] = range
        self.price['RequestType'] = None
        self._GetStockPrice(chartType='indexyear', code=code, range=range)

    def CheckSignedTrade(self, accNumber, passward, tradeType):
        self.kiwoom._SetInputValue("종목코드", "")
        self.kiwoom._SetInputValue("조회구분", 0)
        self.kiwoom._SetInputValue("매도수구분", tradeType)
        self.kiwoom._SetInputValue("계좌번호", accNumber)
        self.kiwoom._SetInputValue("비밀번호", "")
        self.kiwoom._SetInputValue("주문번호", "")
        self.kiwoom._SetInputValue("체결구분", 0)

        self.kiwoom._CommRqData("opt00076_req", "opt00076", "0", "2000")

        # self.kiwoom._SetInputValue("주문일자", "20220111")
        # self.kiwoom._SetInputValue("계좌번호", accNumber)
        # self.kiwoom._SetInputValue("비밀번호", passward)
        # self.kiwoom._SetInputValue("비밀번호입력매체구분", "00")
        # self.kiwoom._SetInputValue("조회구분", "1")
        # self.kiwoom._SetInputValue("주식채권구분", "0")
        # self.kiwoom._SetInputValue("매도수구분", tradeType)
        # self.kiwoom._SetInputValue("종목코드", "")
        # self.kiwoom._SetInputValue("시작주문번호", "")
        #
        # self.kiwoom._CommRqData("opw00007_req", "opw00007", "0", "2000")
        # self.accInfo[accNumber]['signedTrade'] = self.kiwoom.opt00076Output
    def GetDeposit(self, accNumber, passward):
        self.kiwoom._SetInputValue("계좌번호", accNumber)
        self.kiwoom._SetInputValue("비밀번호", passward)
        self.kiwoom._SetInputValue("비밀번호입력매체구분", "00")
        self.kiwoom._SetInputValue("조회구분", "3")

        self.kiwoom._CommRqData("opw00001_req", "opw00001", "0", "2000")
        self.accInfo[accNumber]['deposite'] = self.kiwoom.opw00001Output
    def GetOrderHist(self, orderDate, accNumber, passward, tradeType, code=''):
        self.kiwoom._SetInputValue("주문일자", orderDate)
        self.kiwoom._SetInputValue("계좌번호", accNumber)
        self.kiwoom._SetInputValue("비밀번호", passward)   # 비밀번호 = 사용안함(공백)
        self.kiwoom._SetInputValue("비밀번호입력매체구분", '00')  # 비밀번호입력매체구분 = 00
        self.kiwoom._SetInputValue("조회구분", '2')   # 조회구분 = 1:주문순, 2:역순, 3:미체결, 4:체결내역만
        self.kiwoom._SetInputValue("주식채권구분", '0')  # 주식채권구분 = 0:전체, 1:주식, 2:채권
        self.kiwoom._SetInputValue("매도수구분", tradeType)  # 매도수구분 = 0:전체, 1:매도, 2:매수
        self.kiwoom._SetInputValue("종목코드", code)    # 종목코드 = 공백허용 (공백일때 전체종목)
        self.kiwoom._SetInputValue("시작주문번호", '')  # 시작주문번호 = 공백허용 (공백일때 전체주문)

        self.kiwoom._CommRqData("opw00007_req", "opw00007", "0", "2000")
        self.accInfo[accNumber]['orderHist'] = self.kiwoom.opw00007Output
    def _GetStockPrice(self, chartType, code, range, requestType=0):
        # dataframe.

        chartType = chartType.lower()
        if chartType=='tick' or chartType=='min':    # 틱차트, 분봉차트
            self.kiwoom._SetInputValue("종목코드", code)              # 종목코드 = 전문 조회할 종목코드
            self.kiwoom._SetInputValue("틱범위", range)              # 틱범위 = 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱
            self.kiwoom._SetInputValue("수정주가구분", requestType)     # 수정주가구분 = 0 or 1
        elif chartType=='day' or chartType=='week' or chartType=='month' or chartType=='year':   # 일,주,월봉차트
            self.kiwoom._SetInputValue("종목코드", code)  # 종목코드 = 전문 조회할 종목코드
            self.kiwoom._SetInputValue("기준일자", range)  # 기준일자 = YYYYMMDD (20160101 연도4자리, 월 2자리, 일 2자리 형식)
            self.kiwoom._SetInputValue("수정주가구분", requestType)  # 수정주가구분 = 0 or 1
        elif chartType=='indextick' or chartType=='indexmin':   # 업종 틱차트, 분봉차트
            self.kiwoom._SetInputValue("업종코드", code)
            self.kiwoom._SetInputValue("틱범위", range)
        elif chartType=='indexday' or chartType=='indexweek' or chartType=='indexmonth' or chartType=='indexyear': # 업종 일봉차트
            self.kiwoom._SetInputValue("업종코드", code)
            self.kiwoom._SetInputValue("기준일자", range)

        if chartType=='tick':
            trNumber = 'opt10079'
        elif chartType == 'min':
            trNumber = 'opt10080'
        elif chartType == 'day':
            trNumber = 'opt10081'
        elif chartType == 'week':
            trNumber = 'opt10082'
        elif chartType == 'month':
            trNumber = 'opt10083'
        elif chartType == 'year':
            trNumber = 'opt10094'

        elif chartType == 'indextick':
            trNumber = 'opt20004'
        elif chartType == 'indexmin':
            trNumber = 'opt20005'
        elif chartType == 'indexday':
            trNumber = 'opt20006'
        elif chartType == 'indexweek':
            trNumber = 'opt20007'
        elif chartType == 'indexmonth':
            trNumber = 'opt20008'
        elif chartType == 'indexyear':
            trNumber = 'opt20019'
        self.kiwoom._CommRqData("%s_req"%(trNumber), trNumber, 0, "2000")
        dfPrice = pd.DataFrame(self.kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'],
                               index=self.kiwoom.ohlcv['date'])
        return dfPrice
    # 증거금율
    def GetMarignRate(self):
        pass
    # 거래소
    def GetExchange(self):
        pass
    # 신용군
    def GetCredit(self):
        pass
    # 시총
    def GetMarketCap(self):
        pass
    # 코드
    def GetStockStatus(self, code):
        stockState = self.kiwoom._GetMasterStockState(code)
        return stockState
    # 회사Name
    def GetCompanyName(self, code):
        name = self.kiwoom._GetMasterNodeByCode(code)
        return name
    # 관심종목.
    def GetInterests(self):
        # CommKwRqData("종목코드"		, "연속조회여부"	, "조회종목개수"	, "0",  "RQName"	,  "화면번호");
	    # CommKwRqData("03940;023590"	, "연속조회여부"	, "2"	, "0",  "RQName"	,  "0130");
        pass
    # 거래 일지.
        # 전재산조회.
        # 거래 내역 조회.
        # 이체 내역 조회.
    # 주문
        # 미체결 조회.
    def NonTrade(self, accNumber, tradeType):
        self.kiwoom._SetInputValue("계좌번호", accNumber)
        self.kiwoom._SetInputValue("전체종목구분", "0")
        self.kiwoom._SetInputValue("매매구분", tradeType)
        self.kiwoom._SetInputValue("종목코드", "")
        self.kiwoom._SetInputValue("체결구분", "0")
        self.kiwoom._CommRqData("opt10075_req", "opt10075", "0", "2000")
        self.accInfo[accNumber]['nonTrade'] = self.kiwoom.opt10075Output
        # 매수
    def BuyStock(self, buyInfo):
        # sRQName, // 사용자 구분명, sScreenNo, // 화면번호
        # sAccNo,  // 계좌번호 10자리, LONG nOrderType,  // 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
        # sCode, // 종목코드 (6자리), LONG nQty,  // 주문수량
        # LONG nPrice, // 주문가격, sHogaGb,   // 거래구분(혹은 호가구분)은 아래 참고
        # sOrgOrderNo  // 원주문번호. 신규주문에는 공백 입력, 정정/취소시 입력합니다.
        self.lastTrade['buyInfo'] = buyInfo
        account = self.lastTrade['buyInfo']['account']
        # account 가 있어야 된다.
        nOrderType = self.lastTrade['buyInfo']['nOrderType']
        # 1번 3번 5번 중하나.
        sCode = self.lastTrade['buyInfo']['sCode']
        # company조회 가능
        nQty = self.lastTrade['buyInfo']['nQty']
        # 수량은 1이상인지 체크
        nPrice = self.lastTrade['buyInfo']['nPrice']
        # 지정가이면 0이아니여야됨.
        # 시장가이면 수량만 price는 0을 체크
        sHogaGb = self.lastTrade['buyInfo']['sHogaGb']
        # 00 : 지정가, 03 : 시장가, 05 : 조건부지정가
        # 06 : 최유리지정가, 07 : 최우선지정가, 10 : 지정가IOC
        # 13 : 시장가IOC, 16 : 최유리IOC, 20 : 지정가FOK
        # 23 : 시장가FOK, 26 : 최유리FOK, 61 : 장전시간외종가
        # 62 : 시간외단일가매매, 81 : 장후시간외종가
        # 이것들중 하나이여야 됨.
        sOrgOrderNo = self.lastTrade['buyInfo']['sOrgOrderNo']
        # 매수정정이 아니면 ''.
        # 매수정정일 경우 원주문번호.
        self.kiwoom._SendOrder("send_order_req", '0101', account, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo)
        # 매도
    def SellStock(self, sellInfo):
        # sRQName, // 사용자 구분명, sScreenNo, // 화면번호
        # sAccNo,  // 계좌번호 10자리, LONG nOrderType,  // 주문유형 1:신규매수, 2:신규매도 3:매수취소, 4:매도취소, 5:매수정정, 6:매도정정
        # sCode, // 종목코드 (6자리), LONG nQty,  // 주문수량
        # LONG nPrice, // 주문가격, sHogaGb,   // 거래구분(혹은 호가구분)은 아래 참고
        # sOrgOrderNo  // 원주문번호. 신규주문에는 공백 입력, 정정/취소시 입력합니다.
        # acc_no, order_type, code, quantity, price, hoga, order_no
        self.lastTrade['sellInfo'] = sellInfo
        account = self.lastTrade['buyInfo']['account']
        nOrderType = self.lastTrade['buyInfo']['nOrderType']
        sCode = self.lastTrade['buyInfo']['sCode']
        nQty = self.lastTrade['buyInfo']['nQty']
        nPrice = self.lastTrade['buyInfo']['nPrice']
        sHogaGb = self.lastTrade['buyInfo']['sHogaGb']
        sOrgOrderNo = self.lastTrade['buyInfo']['sOrgOrderNo']
        self.kiwoom._SendOrder("send_order_req", '0101', account, nOrderType, sCode, nQty, nPrice, sHogaGb, sOrgOrderNo)
if __name__ == '__main__':
    app = QApplication(sys.argv)

    kiwoom_Handler = Kiwoom_Handler()
    # kiwoom._GetConnectState()
    kiwoom_Handler.Login()
    kiwoom_Handler.GetConnectState()
    kiwoom_Handler.GetUserINFO()
    print(kiwoom_Handler.userInfo)
    kiwoom_Handler.GetAccInfo(accNumber='4555345411', password='6317', requestType=1)
    print(kiwoom_Handler.accInfo)
    # kiwoom_Handler.GetTickPrice(code='000660', range='1', requestType=0)
    # kiwoom_Handler.GetMinPrice(code='000660', range='3', requestType=0)
    # kiwoom_Handler.GetDayPrice(code='000660', range='20211230', requestType=0)
    # kiwoom_Handler.GetWeekPrice(code='000660', range='20211230', requestType=0)
    # kiwoom_Handler.GetMonthPrice(code='000660', range='20211230', requestType=0)
    # kiwoom_Handler.GetYearPrice(code='000660', range='20210101', requestType=0)
    # print(kiwoom_Handler.price)
    # # 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지
    # kiwoom_Handler.GetIndexTickPrice(code='001', range='30')
    # kiwoom_Handler.GetIndexMinPrice(code='001', range='5')
    # kiwoom_Handler.GetIndexDayPrice(code='001', range='20211230')
    # kiwoom_Handler.GetIndexWeekPrice(code='001', range='20211230')
    # kiwoom_Handler.GetIndexMonthPrice(code='001', range='20211230')
    # kiwoom_Handler.GetIndexYearPrice(code='001', range='20211230')
    # print(kiwoom_Handler.price)
    # # buyInfo = {'account':'4555345411', 'sCode':'000660', 'nQty':1, 'nPrice':128000, 'nOrderType':1, 'sHogaGb':"00",
    # #             'sOrgOrderNo':''}
    # # kiwoom_Handler.BuyStock(buyInfo)
    # kiwoom_Handler.GetCompanyInfo('000660')
    kiwoom_Handler.GetAskingPrice('000660')
    # kiwoom._CommTerminate()
    # kiwoom._GetConnectState()
    # opt10076 : 체결요청
    # opt10075 : 미체결요청