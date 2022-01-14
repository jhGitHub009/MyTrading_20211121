import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3
import datetime

TR_REQ_TIME_INTERVAL = 0.2
class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._CreateKiwoomInstance()
        self._SetSignalSlots()
    # private function
    def _CommConnect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()
    def _CreateKiwoomInstance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")
    def _SetSignalSlots(self):
        self.OnEventConnect.connect(self._EventConnect)
        self.OnReceiveTrData.connect(self._OnReceiveTrData)
        self.OnReceiveChejanData.connect(self._OnReceiveChejanData)  # 이부분 확인.
        self.OnReceiveMsg.connect(self._OnReceiveMsg)
    def _EventConnect(self, err_code):
        if err_code == 0:print("connected")
        else:print("disconnected")
        self.login_event_loop.exit()
    # 주문전송 후 주문접수, 체결통보, 잔고통보를 수신할 때 마다 발생됩니다.
    def _OnReceiveChejanData(self, sGubun, nItemCnt, sFIdList):
        kind = sGubun  # 체결 구분
        code = self.get_chejan_data(9001).replace('A', '')  # 종목코드
        company = self.get_chejan_data(302).strip()  # 종목명
        state = self.get_chejan_data(913)  # 주문상태
        orderQuan = self.get_chejan_data(900)  # 주문수량
        notConcluded = self.get_chejan_data(902)  # 미체결수량
        orderNum = self.get_chejan_data(9203)  # 주문번호
        tradePrice = self.get_chejan_data(901)  # 주문가격
        print('==========================================')
        print("체결구분 : %s" % kind)
        print("종목명 : %s" % company)
        print("종목코드 : %s" % code)
        print("주문상태 : %s" % state)
        print("주문수량 : %s" % orderQuan)
        print("미체결수량 : %s" % notConcluded)
        print("주문번호 : %s" % orderNum)
        print("주문가격 : %s" % tradePrice)
        print('==========================================')
    # (주문메세지수신)
    def _OnReceiveMsg(self, sScrNo, sRQName, sTrCode, sMsg):
        print('화면번호 : %s' % (sScrNo))
        print('사용자 구분명 : %s' % (sRQName))
        print('sTrCode : %s' % (sTrCode))
        print('sMsg : %s' % (sMsg))
    def _CommGetData(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip()
    # 서버와 현재 접속 상태를 알려줍니다. 리턴값 1:연결, 0:연결안됨
    def _GetConnectState(self):
        return self.dynamicCall("GetConnectState()")
    def _GetLoginInfo(self):
        # "ACCOUNT_CNT" : 보유계좌 갯수를 반환합니다.
        numOfAcc = self.dynamicCall('GetLoginInfo("ACCOUNT_CNT")')
        # "ACCLIST" 또는 "ACCNO" : 구분자 ';'로 연결된 보유계좌 목록을 반환합니다.
        accList = self.dynamicCall('GetLoginInfo("ACCNO")')
        accList = accList.split(";")
        accList = list(filter(None, accList))
        # "USER_ID" : 사용자 ID를 반환합니다.
        userID = self.dynamicCall('GetLoginInfo("USER_ID")')
        # "USER_NAME" : 사용자 이름을 반환합니다.
        userName = self.dynamicCall('GetLoginInfo("USER_NAME")')
        # "GetServerGubun" : 접속서버 구분을 반환합니다.(1 : 모의투자, 나머지 : 실거래서버)
        typeOfConn = self.dynamicCall('GetLoginInfo("GetServerGubun")')
        # "KEY_BSECGB" : 키보드 보안 해지여부를 반환합니다.(0 : 정상, 1 : 해지)
        keySecurity = self.dynamicCall('GetLoginInfo("KEY_BSECGB")')
        # "FIREW_SECGB" : 방화벽 설정여부를 반환합니다.(0 : 미설정, 1 : 설정, 2 : 해지)
        firewall = self.dynamicCall('GetLoginInfo("FIREW_SECGB")')
        return {"numOfAcc":numOfAcc,"accList":accList,"userID":userID,"userName":userName,"typeOfConn":typeOfConn,
                "keySecurity":keySecurity,"firewall":firewall}
    # 조회요청 함수입니다. 리턴값 0이면 조회요청 정상 나머지는 에러
    def _CommRqData(self, rqname, trcode, next, screen_no):
        ret = self.dynamicCall("CommRqData(QString, QString, long, QString)", rqname, trcode, next, screen_no)
        if ret!=0:
            print('Communation error')
        else:
            # self.dynamicCall("CommRqData(QString, QString, QString, QString)", rqname, trcode, next, screen_no)
            self.tr_event_loop = QEventLoop()
            self.tr_event_loop.exec_()
    # 조회요청시 TR의 Input값을 지정하는 함수입니다.
    def _SetInputValue(self, id, value):
        self.dynamicCall("SetInputValue(QString, QString)", id, value)
    def _DisconnectRealData(self,sScnNo):
        self.dynamicCall("DisconnectRealData(QString)",sScnNo)
        #DisconnectRealData(BSTR sScnNo(화면번호))
          # 시세데이터를 요청할때 사용된 화면번호를 이용하여
          # 해당 화면번호로 등록되어져 있는 종목의 실시간시세를 서버에 등록해지 요청합니다.
          # 이후 해당 종목의 실시간시세는 수신되지 않습니다.
          # 단, 해당 종목이 또다른 화면번호로 실시간 등록되어 있는 경우 해당종목에대한 실시간시세 데이터는 계속 수신됩니다.

    # 데이터 수신시 멀티데이터의 갯수(반복수)를 얻을수 있습니다.
    def _GetRepeatCnt(self, trcode, rqname):
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret
    # 한번에 100종목까지 조회할 수 있는 복수종목 조회함수 입니다.
    def _CommKwRqData(self, sArrCode, bNext, nCodeCount, nTypeFlag, sRQName, sScreenNo):
        self.dynamicCall("CommKwRqData(QString,Bool,int,int,QString,QString)")
    # OnReceiveTRData()이벤트가 발생될때 수신한 데이터를 얻어오는 함수입니다.
    def _GetCommData(self,sTrCode,sRecordName,nIndex,strItemName):
        self.dynamicCall("GetCommData(QString,QString,long,QString)",sTrCode,sRecordName,nIndex,strItemName)
    # 실시간시세 데이터 수신 이벤트인 OnReceiveRealData() 가 발생될때 실시간데이터를 얻어오는 함수입니다.
    def _GetCommRealData(self,sCode,nFid):
        self.dynamicCall("GetCommRealData(QString,long)",sCode,nFid)
    # 조회 수신데이터 크기가 큰 차트데이터를 한번에 가져올 목적으로 만든 차트조회 전용함수입니다.
    def _GetCommDataEx(self,sTrCode,sRecordName):
        self.dynamicCall("GetCommDataEx(QString,QString)",sTrCode,sRecordName)

    # 실시간시세 데이터가 수신될때마다 종목단위로 발생됩니다.
    def _OnReceiveRealData(self,sCode,sRealType,sRealData):
        self.dynamicCall("OnReceiveRealData(QString,QString,QString)",sCode,sRealType,sRealData)

    def _SendOrder(self, rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])
    # 코스피지수200 선물옵션 전용 주문함수입니다.
    def _SendOrderFO(self,sRQName,sScreenNo,sAccNo,sCode,lOrdKind,sSlbyTp,sOrdTp,lQty,sPrice,sOrgOrdNo):
        self.dynamicCall("SendOrderFO(QString,QString,QString,QString,long,QString,QString,long,QString,QString)",
                         sRQName, sScreenNo, sAccNo, sCode, lOrdKind, sSlbyTp, sOrdTp, lQty, sPrice, sOrgOrdNo)
    # 국내주식 신용주문 전용함수입니다. 대주거래는 지원하지 않습니다.
    def _SendOrderCredit(self,sRQName,sScreenNo,sAccNo,nOrderType,sCode,nQty,nPrice,sHogaGb,sCreditGb,sLoanDate,sOrgOrderNo):
        self.dynamicCall("SendOrderCredit(QString,QString,QString,long,QString,long,long,QString,QString,QString,QString)",
                         sRQName, sScreenNo, sAccNo, nOrderType, sCode, nQty, nPrice, sHogaGb, sCreditGb, sLoanDate,
                         sOrgOrderNo)
    # OnReceiveChejan()이벤트가 발생될때 FID에 해당되는 값을 구하는 함수입니다.
    # 이 함수는 OnReceiveChejan() 이벤트 안에서 사용해야 합니다.
    def _GetChejanData(self,nFid):
        ret = self.dynamicCall("GetChejanData(int)", nFid)
        return ret

    # 서버에 저장된 사용자 조건검색 목록을 요청합니다.
        # 조건검색 목록 요청을 성공하면 1, 아니면 0을 리턴합니다.
    def _GetConditionLoad(self):
        pass
    # 서버에서 수신한 사용자 조건식을 조건식의 고유번호와 조건식 이름을 한 쌍으로 하는 문자열들로 전달합니다.
    def _GetConditionNameList(self):
        pass
    # 서버에 조건검색을 요청하는 함수입니다.
    def _SendCondition(self):
        pass
    # 실시간 조건검색을 중지할 때 사용하는 함수입니다.
    def _SendConditionStop(self):
        pass
    # 종목코드와 FID 리스트를 이용해서 실시간 시세를 등록하는 함수입니다.
    def _SetRealReg(self):
        pass
    # 실시간시세 해지 함수이며 화면번호와 종목코드를 이용해서 상세하게 설정할 수 있습니다.
    def _SetRealRemove(self):
        pass
    # 저장된 사용자 조건식 불러오기 요청에 대한 응답 수신시 발생되는 이벤트입니다.
    def _OnReceiveConditionVer(self):
        pass
    # 조건검색 요청에대한 서버 응답 수신시 발생하는 이벤트입니다.
    def _OnReceiveTrCondition(self):
        pass
    # 실시간 조건검색 요청으로 신규종목이 편입되거나 기존 종목이 이탈될때 마다 발생됩니다.
    def _OnReceiveRealCondition(self):
        pass
    # 주식 시장별 종목코드 리스트를 ';'로 구분해서 전달합니다.
    def get_code_list_by_market(self, market):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
        code_list = code_list.split(';')
        return code_list[:-1]
    # 종목코드에 해당하는 종목명을 전달합니다.
    def _GetMasterCodeName(self):
        pass
    # 입력한 종목코드에 해당하는 종목 상장주식수를 전달합니다.
    def _GetMasterListedStockCnt(self):
        pass
    # 입력한 종목코드에 해당하는 종목의 감리구분을 전달합니다.
    def _GetMasterConstruction(self):
        pass
    # 입력한 종목의 상장일을 전달합니다.
    def _GetMasterListedStockDate(self):
        pass
    # 입력한 종목의 당일 기준가를 전달합니다.
    def _GetMasterLastPrice(self):
        pass
    # 입력한 종목의 증거금 비율, 거래정지, 관리종목, 감리종목, 투자융의종목, 담보대출, 액면분할, 신용가능 여부를 전달합니다.
    def _GetMasterStockState(self):
        pass
    # 특정TR 조회에 필요한 회원사 정보를 회원사 코드와 회원사 이름으로 구성해서 전달합니다.
    def _GetBranchCodeName(self):
        pass
    #  지수선물 종목코드 리스트를 ';'로 구분해서 전달합니다.
    def _GetFutureList(self):
        pass
    # 지수옵션 행사가에 100을 곱해서 소수점이 없는 값을 ';'로 구분해서 전달합니다.
    def _GetActPriceList(self):
        pass
    #  지수옵션 월물정보를 ';'로 구분해서 전달하는데 순서는 콜 11월물 ~ 콜 최근월물 풋 최근월물 ~ 풋 최근월물가 됩니다.
    def _GetMonthList(self):
        pass
    # 인자로 지정한 지수옵션 코드를 전달합니다.
    def _GetOptionCode(self):
        pass
    # 지수옵션 소수점을 제거한 ATM값을 전달합니다.
    def _GetOptionATM(self):
        pass
    # 기초자산 구분값을 인자로 받아서 주식선물 종목코드, 종목명, 기초자산이름을 구할수 있습니다.
    def _GetSFutureList(self):
        pass
    def _GetMasterStockState(self, code):
        stockState = self.dynamicCall("GetMasterStockState(QString)", code)
        # 정상, 투자주의, 투자경고, 투자위험, 투자주의환기종목
        return stockState
    def _GetMasterNodeByCode(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name
    # 조회데이터를 수신했을때 발생됩니다.
    def _OnReceiveTrData(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        if rqname == "opt10001_req":  # 주식기본정보요청
            self._opt10001(rqname, trcode)
        elif rqname == "opt10004_req":  # 주식기본정보요청
            self._opt10004(rqname, trcode)
        elif rqname == "opt10075_req":  # 미체결요청
            self._opt10075(rqname, trcode)
        elif rqname == "opt10076_req":  # 체결요청
            self._opt10076(rqname, trcode)
        elif rqname == "opt10079_req" or rqname == "opt10080_req":  # 틱요청
            self._tickMinPrice(rqname, trcode)
        elif rqname == "opt10081_req" or rqname == "opt10082_req" or rqname == "opt10083_req" or rqname == "opt10094_req":  # 일봉요청
            self._dayWeekMonthYearPrice(rqname, trcode)
        elif rqname == "opt20004_req" or rqname == "opt20005_req":  # 업종틱요청
            self._tickMinPrice(rqname, trcode)
        elif rqname == "opt20006_req" or rqname == "opt20007_req" or rqname == "opt20008_req" or rqname == "opt20019_req":  # 업종일봉요청
            self._dayWeekMonthYearPrice(rqname, trcode)
        elif rqname == "opw00001_req":  # 미체결요청
            self._opw00001(rqname, trcode)
        elif rqname == "opw00007_req":  # 계좌별주문체결내역상세요청
            self._opw00007(rqname, trcode)
        elif rqname == "opw00018_req":  # 계좌 잔고 요청
            self._opw00018(rqname, trcode)
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opt10076(self, rqname, trcode):
        Data_1 = self._CommGetData(trcode, "", rqname, 0, "미체결수량")
        Data_2 = self._CommGetData(trcode, "", rqname, 0, "당일매매수수료")
        Data_3 = self._CommGetData(trcode, "", rqname, 0, "당일매매세금")
        Data_4 = self._CommGetData(trcode, "", rqname, 0, "주문상태")
        Data_5 = self._CommGetData(trcode, "", rqname, 0, "주문시간")
        Data_6 = self._CommGetData(trcode, "", rqname, 0, "종목코드")

        company = self._CommGetData(trcode, "", rqname, 0, "종목명")
        orderType = self._CommGetData(trcode, "", rqname, 0, "주문구분")
        orderAmount = self._CommGetData(trcode, "", rqname, 0, "주문수량")
        signedAmount = self._CommGetData(trcode, "", rqname, 0, "체결량")
        orderPrice = self._CommGetData(trcode, "", rqname, 0, "주문가격")
        signedPrice = self._CommGetData(trcode, "", rqname, 0, "체결가")
        orderNum = self._CommGetData(trcode, "", rqname, 0, "주문번호")
        oriNum = self._CommGetData(trcode, "", rqname, 0, "원주문번호")
        tradeType = self._CommGetData(trcode, "", rqname, 0, "매매구분")
        pass
    def _opw00007(self, rqname, trcode):
        data = {}
        nData = int(self._CommGetData(trcode, "", rqname, 0, "출력건수"))
        for i in range(nData):
            # iData_2 = self._CommGetData(trcode, "", rqname, i, "종목번호")
            # iData_4 = self._CommGetData(trcode, "", rqname, i, "신용구분")
            # iData_7 = self._CommGetData(trcode, "", rqname, i, "확인수량")
            # iData_9 = self._CommGetData(trcode, "", rqname, i, "반대여부")
            # iData_10 = self._CommGetData(trcode, "", rqname, i, "주문시간")
            # iData_17 = self._CommGetData(trcode, "", rqname, i, "주문잔량")
            # iData_18 = self._CommGetData(trcode, "", rqname, i, "통신구분")
            # iData_20 = self._CommGetData(trcode, "", rqname, i, "확인시간")

            company         = self._CommGetData(trcode, "", rqname, i, "종목명")
            orderType       = self._CommGetData(trcode, "", rqname, i, "주문구분")
            orderAmount     = int(self._CommGetData(trcode, "", rqname, i, "주문수량"))
            tradeAmount     = int(self._CommGetData(trcode, "", rqname, i, "체결수량"))
            orderPrice      = int(self._CommGetData(trcode, "", rqname, i, "주문단가"))
            if tradeAmount != 0:
                tradePrice  = int(self._CommGetData(trcode, "", rqname, i, "체결단가"))
            else:
                tradePrice  = ''
            reOrderCancel   = self._CommGetData(trcode, "", rqname, i, "정정취소")
            orderNum        = self._CommGetData(trcode, "", rqname, i, "주문번호")[-5:]
            if reOrderCancel != '':
                oriNum      = self._CommGetData(trcode, "", rqname, i, "원주문")[-5:]
            else:
                oriNum      = ''
            tradeType       = self._CommGetData(trcode, "", rqname, i, "매매구분")
            dateLoan        = self._CommGetData(trcode, "", rqname, i, "대출일")
            receiptType     = self._CommGetData(trcode, "", rqname, i, "접수구분")
            data[i] = [company, orderType, orderAmount, tradeAmount, orderPrice, tradePrice,
                                      reOrderCancel, orderNum, oriNum, tradeType, dateLoan, receiptType]

        self.opw00007Output = pd.DataFrame.from_dict(data, orient='index', columns=['종목','주문구분','주문량','체결량',
                                                                                    '주문가','체결가','정정/취소',
                                                                                    '주문번호','원주문','매매구분','대출일',
                                                                                    '접수구분'])
    def _opw00001(self, rqname, trcode):  # 미체결요청
        self.opw00001Output = {}
        # deposit = self._CommGetData(trcode, "", rqname, 0, "예수금")  # 인출가능금액
        # deposit2 = self._CommGetData(trcode, "", rqname, 0, "수익증권증거금현금")  # 해외원화주문설정금
        # deposit3 = self._CommGetData(trcode, "", rqname, 0, "익일수익증권매도정산대금")  # 주문번호
        # deposit5 = self._CommGetData(trcode, "", rqname, 0, "신용보증금현금")  # 주문번호
        # deposit6 = self._CommGetData(trcode, "", rqname, 0, "신용담보금현금")  # 주문번호
        # deposit7 = self._CommGetData(trcode, "", rqname, 0, "추가담보금현금")  # 주문번호
        # deposit8 = self._CommGetData(trcode, "", rqname, 0, "기타증거금")  # 주문번호
        # deposit9 = self._CommGetData(trcode, "", rqname, 0, "미수확보금")  # 주문번호
        # deposit10 = self._CommGetData(trcode, "", rqname, 0, "공매도대금")  # 주문번호
        # deposit11 = self._CommGetData(trcode, "", rqname, 0, "신용설정평가금")  # 주문번호
        # deposit14 = self._CommGetData(trcode, "", rqname, 0, "신용담보재사용")  # 주문번호
        # deposit15 = self._CommGetData(trcode, "", rqname, 0, "코넥스기본예탁금")  # 주문번호
        # deposit16 = self._CommGetData(trcode, "", rqname, 0, "ELW예탁평가금")  # 주문번호
        # deposit17 = self._CommGetData(trcode, "", rqname, 0, "신용대주권리예정금액")  # 주문번호
        # deposit18 = self._CommGetData(trcode, "", rqname, 0, "생계형가입금액")  # 주문번호
        # deposit19 = self._CommGetData(trcode, "", rqname, 0, "생계형입금가능금액")  # 주문번호
        # deposit21 = self._CommGetData(trcode, "", rqname, 0, "잔고대용평가금액")  # 주문번호
        # deposit22 = self._CommGetData(trcode, "", rqname, 0, "위탁대용잔고평가금액")  # 주문번호
        # deposit23 = self._CommGetData(trcode, "", rqname, 0, "수익증권대용평가금액")  # 주문번호
        # deposit30 = self._CommGetData(trcode, "", rqname, 0, "랩출금가능금액")  # 주문번호
        # deposit32 = self._CommGetData(trcode, "", rqname, 0, "수익증권매수가능금액")  # 주문번호
        # deposit33 = self._CommGetData(trcode, "", rqname, 0, "20%종목주문가능금액")  # 주문번호
        # deposit34 = self._CommGetData(trcode, "", rqname, 0, "30%종목주문가능금액")  # 주문번호
        # deposit35 = self._CommGetData(trcode, "", rqname, 0, "40%종목주문가능금액")  # 주문번호
        # deposit36 = self._CommGetData(trcode, "", rqname, 0, "100%종목주문가능금액")  # 주문번호
        # deposit46 = self._CommGetData(trcode, "", rqname, 0, "미상환융자금")  # 주문번호
        # deposit47 = self._CommGetData(trcode, "", rqname, 0, "융자금합계")  # 주문번호
        # deposit48 = self._CommGetData(trcode, "", rqname, 0, "대주금합계")  # 주문번호
        # deposit49 = self._CommGetData(trcode, "", rqname, 0, "신용담보비율")  # 주문번호
        # deposit50 = self._CommGetData(trcode, "", rqname, 0, "중도이용료")  # 주문번호
        # deposit51 = self._CommGetData(trcode, "", rqname, 0, "최소주문가능금액")  # 주문번호
        # deposit52 = self._CommGetData(trcode, "", rqname, 0, "대출총평가금액")  # 주문번호
        # deposit53 = self._CommGetData(trcode, "", rqname, 0, "예탁담보대출잔고")  # 주문번호
        # deposit54 = self._CommGetData(trcode, "", rqname, 0, "매도담보대출잔고")  # 주문번호
        # deposit57 = self._CommGetData(trcode, "", rqname, 0, "d+1매수정산금")  # 주문번호
        # deposit58 = self._CommGetData(trcode, "", rqname, 0, "d+1미수변제소요금")  # 주문번호
        # deposit59 = self._CommGetData(trcode, "", rqname, 0, "d+1매도정산금")  # 주문번호
        # deposit62 = self._CommGetData(trcode, "", rqname, 0, "d+2매도매수정산금")  # 주문번호
        # deposit63 = self._CommGetData(trcode, "", rqname, 0, "d+2매수정산금")  # 주문번호
        # deposit64 = self._CommGetData(trcode, "", rqname, 0, "d+2미수변제소요금")  # 주문번호
        # deposit67 = self._CommGetData(trcode, "", rqname, 0, "출력건수")  # 주문번호
        amountCheck             = int(self._CommGetData(trcode, "", rqname, 0, "수표입금액"))
        amountOtherCheck        = int(self._CommGetData(trcode, "", rqname, 0, "기타수표입금액"))
        amountCheckTotal        = amountCheck + amountOtherCheck                                   # 수표금액
        amountWdrawl            = int(self._CommGetData(trcode, "", rqname, 0, "출금가능금액"))               # 인출가능금액
        amountOverseeStcokLoan  = int(self._CommGetData(trcode, "", rqname, 0, "해외주식원화대용설정금"))          # 해외원화주문설정금

        d1Deposite          = int(self._CommGetData(trcode, "", rqname, 0, "d+1추정예수금"))               # d+1예수금
        d1AsTradeDeposite   = int(self._CommGetData(trcode, "", rqname, 0, "d+1매도매수정산금"))      # d+1정산금
        d1AvWdrawal         = int(self._CommGetData(trcode, "", rqname, 0, "d+1출금가능금액"))             # d+1추정인출가능금액
        d2Deposite          = int(self._CommGetData(trcode, "", rqname, 0, "d+2추정예수금"))               # d+2예수금
        d2AsTradeDeposite   = int(self._CommGetData(trcode, "", rqname, 0, "d+2매도정산금"))         # d+2정산금
        d2AvWdrawal         = int(self._CommGetData(trcode, "", rqname, 0, "d+2출금가능금액"))              # d+2추정인출가능금액

        amountAvailOrder    = int(self._CommGetData(trcode, "", rqname, 0, "주문가능금액"))           # 예수금잔액
        amountStockMargin   = int(self._CommGetData(trcode, "", rqname, 0, "주식증거금현금"))        # 예수증거금
        amountLoan          = int(self._CommGetData(trcode, "", rqname, 0, "대용금평가금액(합계)"))          # 대용금잔액
        cSignMargin         = int(self._CommGetData(trcode, "", rqname, 0, "위탁증거금대용"))
        creditSignMargin    = int(self._CommGetData(trcode, "", rqname, 0, "신용보증금대용"))
        creditCollateral    = int(self._CommGetData(trcode, "", rqname, 0, "신용담보금대용"))
        addCollateral       = int(self._CommGetData(trcode, "", rqname, 0, "추가담보금대용"))
        rightLoan           = int(self._CommGetData(trcode, "", rqname, 0, "권리대용금"))
        amountLoanMargin    = cSignMargin + creditSignMargin + creditCollateral + addCollateral + rightLoan    # 대용증거금

        receCash            = int(self._CommGetData(trcode, "", rqname, 0, "현금미수금"))                    # 현금미수금
        receCashInter       = int(self._CommGetData(trcode, "", rqname, 0, "신용이자미납"))              # 이자미납미수금
        otherLoan           = int(self._CommGetData(trcode, "", rqname, 0, "기타대여금"))                   # 기타대여미수금
        receCashFee         = int(self._CommGetData(trcode, "", rqname, 0, "현금미수연체료"))               # 현금미수연체이자
        receCashInterFee    = int(self._CommGetData(trcode, "", rqname, 0, "신용이자미납연체료"))        # 이자미납연체이자
        otherLoanFee        = int(self._CommGetData(trcode, "", rqname, 0, "기타대여금연체료"))             # 기타대여연체이자
        receCashInterTotal  = int(self._CommGetData(trcode, "", rqname, 0, "신용이자미납합계"))
        receCashTotal       = int(self._CommGetData(trcode, "", rqname, 0, "현금미수금합계"))
        otherLoanTotal      = int(self._CommGetData(trcode, "", rqname, 0, "기타대여금합계"))
        receTotal           = receCashInterTotal + receCashTotal + otherLoanTotal                         # 총미수금
        self.opw00001Output['table1'] = pd.DataFrame(data=[[amountCheckTotal,amountOverseeStcokLoan,amountWdrawl]],
                                                     columns=['수표금액', '해외원화주문설정금', '인출가능금액'])
        self.opw00001Output['table2'] = pd.DataFrame(
            data=[[d1Deposite, d2Deposite], [d1AsTradeDeposite, d2AsTradeDeposite], [d1AvWdrawal, d2AvWdrawal]],
            columns=['d+1', 'd+2'], index=['예수금', '정산금', '추정인출가능금액'])

        self.opw00001Output['table3'] = pd.DataFrame(
            data=[[amountAvailOrder, amountLoan], [amountStockMargin, amountLoanMargin]],
            columns=['예수금', '대용금'], index=['잔액', '증거금'])

        self.opw00001Output['table4'] = pd.DataFrame(
            data=[[receCash, receCashFee], [receCashInter, receCashInterFee], [otherLoan, otherLoanFee],[None,receTotal]],
            columns=['미수금', '연체이자'], index=['현금미수금', '이자미납', '기타대여','총미납금'])

    def _opt10075(self, rqname, trcode):    # 미체결요청
        self.opt10075Output = {}
        rows = self._GetRepeatCnt(trcode, rqname)
        for i in range(rows):
            orderNum    = self._CommGetData(trcode, "", rqname, i, "주문번호")         # 주문번호
            company     = self._CommGetData(trcode, "", rqname, i, "종목명")           # 종목명
            orderQty    = int(self._CommGetData(trcode, "", rqname, i, "주문수량"))     # 주문수량
            nNonTrade   = int(self._CommGetData(trcode, "", rqname, i, "미체결수량"))  # 미체결수량
            stockType   = self._CommGetData(trcode, "", rqname, i, "매매구분")    # 주문종류
            tradeType   = self._CommGetData(trcode, "", rqname, i, "주문구분").replace('-','')    # 구분
            orderPrice  = int(self._CommGetData(trcode, "", rqname, i, "주문가격"))   # 주문가
            nowPrice    = int(self._CommGetData(trcode, "", rqname, i, "현재가"))  # 현재가
            oriOrderNum = self._CommGetData(trcode, "", rqname, i, "원주문번호")  # 원주문번호
            orderTime   = self._CommGetData(trcode, "", rqname, i, "시간")  # 주문시간
            orderTime   = datetime.datetime.strptime(orderTime, '%H%M%S').time()
            self.opt10075Output[i] = {"주문번호": orderNum, "종목명": company, "주문수량": orderQty,
                                        "미체결수량": nNonTrade, "매매구분": stockType, "주문구분": tradeType,
                                        "주문가격": orderPrice, "현재가": nowPrice, "원주문번호": oriOrderNum,
                                        "시간": orderTime}
    def _opt10004(self, rqname, trcode):    # 주식호가요청
        sell6RemainRatio = self._CommGetData(trcode, "", rqname, 0, "매도6차선잔량대비")
        sell6Remain      = self._CommGetData(trcode, "", rqname, 0, "매도6우선잔량")
        sell6Quote       = self._CommGetData(trcode, "", rqname, 0, "매도6차선호가")
        sell5RemainRatio = self._CommGetData(trcode, "", rqname, 0, "매도5차선잔량대비")
        sell5Remain      = self._CommGetData(trcode, "", rqname, 0, "매도5차선잔량")
        sell5Quote       = self._CommGetData(trcode, "", rqname, 0, "매도5차선호가")
        sell4RemainRatio = self._CommGetData(trcode, "", rqname, 0, "매도4차선잔량대비")
        sell4Remain      = self._CommGetData(trcode, "", rqname, 0, "매도4차선잔량")
        sell4Quote       = self._CommGetData(trcode, "", rqname, 0, "매도4차선호가")
        sell3RemainRatio = self._CommGetData(trcode, "", rqname, 0, "매도3차선잔량대비")
        sell3Remain      = self._CommGetData(trcode, "", rqname, 0, "매도3차선잔량")
        sell3Quote       = self._CommGetData(trcode, "", rqname, 0, "매도3차선호가")
        sell2RemainRatio = self._CommGetData(trcode, "", rqname, 0, "매도2차선잔량대비")
        sell2Remain      = self._CommGetData(trcode, "", rqname, 0, "매도2차선잔량")
        sell2Quote       = self._CommGetData(trcode, "", rqname, 0, "매도2차선호가")
        sell1RemainRatio = self._CommGetData(trcode, "", rqname, 0, "매도1차선잔량대비")
        sell1Remain      = self._CommGetData(trcode, "", rqname, 0, "매도최우선잔량")
        sell1Quote       = self._CommGetData(trcode, "", rqname, 0, "매도최우선호가")

        buy1Quote        = self._CommGetData(trcode, "", rqname, 0, "매수최우선호가")
        buy1Remain       = self._CommGetData(trcode, "", rqname, 0, "매수최우선잔량")
        buy1RemainRatio  = self._CommGetData(trcode, "", rqname, 0, "매수1차선잔량대비")
        buy2Quote        = self._CommGetData(trcode, "", rqname, 0, "매수2차선호가")
        buy2Remain       = self._CommGetData(trcode, "", rqname, 0, "매수2차선잔량")
        buy2RemainRatio  = self._CommGetData(trcode, "", rqname, 0, "매수2차선잔량대비")
        buy3Quote        = self._CommGetData(trcode, "", rqname, 0, "매수3차선호가")
        buy3Remain       = self._CommGetData(trcode, "", rqname, 0, "매수3차선잔량")
        buy3RemainRatio  = self._CommGetData(trcode, "", rqname, 0, "매수3차선잔량대비")
        buy4Quote        = self._CommGetData(trcode, "", rqname, 0, "매수4차선호가")
        buy4Remain       = self._CommGetData(trcode, "", rqname, 0, "매수4차선잔량")
        buy4RemainRatio  = self._CommGetData(trcode, "", rqname, 0, "매수4차선잔량대비")
        buy5Quote        = self._CommGetData(trcode, "", rqname, 0, "매수5차선호가")
        buy5Remain       = self._CommGetData(trcode, "", rqname, 0, "매수5차선잔량")
        buy5RemainRatio  = self._CommGetData(trcode, "", rqname, 0, "매수5차선잔량대비")
        buy6Quote        = self._CommGetData(trcode, "", rqname, 0, "매수6우선호가")
        buy6Remain       = self._CommGetData(trcode, "", rqname, 0, "매수6우선잔량")
        buy6RemainRatio  = self._CommGetData(trcode, "", rqname, 0, "매수6차선잔량대비")

    def _opt10001(self, rqname, trcode):
        code = self._CommGetData(trcode, "", rqname, 0, "종목코드")
        name = self._CommGetData(trcode, "", rqname, 0, "종목명")
        accMonth = self._CommGetData(trcode, "", rqname, 0, "결산월")
        faceValue = self._CommGetData(trcode, "", rqname, 0, "액면가")
        capital = self._CommGetData(trcode, "", rqname, 0, "자본금")
        listedStock = self._CommGetData(trcode, "", rqname, 0, "상장주식")
        creditRatio = self._CommGetData(trcode, "", rqname, 0, "신용비율")
        annaulHighest = self._CommGetData(trcode, "", rqname, 0, "연중최고")
        annaulLowest = self._CommGetData(trcode, "", rqname, 0, "연중최저")
        aggValue = self._CommGetData(trcode, "", rqname, 0, "시가총액")
        aggValueRatio = self._CommGetData(trcode, "", rqname, 0, "시가총액비중")
        foreRatio = self._CommGetData(trcode, "", rqname, 0, "외인소진율")
        subPrice = self._CommGetData(trcode, "", rqname, 0, "대용가")
        per = self._CommGetData(trcode, "", rqname, 0, "PER")
        eps = self._CommGetData(trcode, "", rqname, 0, "EPS")
        roe = self._CommGetData(trcode, "", rqname, 0, "ROE")
        pbr = self._CommGetData(trcode, "", rqname, 0, "PBR")
        ev = self._CommGetData(trcode, "", rqname, 0, "EV")
        bps = self._CommGetData(trcode, "", rqname, 0, "BPS")
        revenue = self._CommGetData(trcode, "", rqname, 0, "매출액")
        operIncome = self._CommGetData(trcode, "", rqname, 0, "영업이익")
        netIncome = self._CommGetData(trcode, "", rqname, 0, "당기순이익")
        highest250 = self._CommGetData(trcode, "", rqname, 0, "250최고")
        lowest250 = self._CommGetData(trcode, "", rqname, 0, "250최저")
        openPrice = self._CommGetData(trcode, "", rqname, 0, "시가")
        highPrice = self._CommGetData(trcode, "", rqname, 0, "고가")
        lowPrice = self._CommGetData(trcode, "", rqname, 0, "저가")
        upLimitPrice = self._CommGetData(trcode, "", rqname, 0, "상한가")
        downLimitPrice = self._CommGetData(trcode, "", rqname, 0, "하한가")
        standPrice = self._CommGetData(trcode, "", rqname, 0, "기준가")
        expTradePrice = self._CommGetData(trcode, "", rqname, 0, "예상체결가")
        expTradeNum = self._CommGetData(trcode, "", rqname, 0, "예상체결수량")
        highest250Day = self._CommGetData(trcode, "", rqname, 0, "250최고가일")
        highest250Ratio = self._CommGetData(trcode, "", rqname, 0, "250최고가대비율")
        lowest250Day = self._CommGetData(trcode, "", rqname, 0, "250최저가일")
        lowest250Ratio = self._CommGetData(trcode, "", rqname, 0, "250최저가대비율")
        nowPrice = self._CommGetData(trcode, "", rqname, 0, "현재가")
        contSign = self._CommGetData(trcode, "", rqname, 0, "대비기호")
        dayToDay = self._CommGetData(trcode, "", rqname, 0, "전일대비")
        fluctRate = self._CommGetData(trcode, "", rqname, 0, "등락율")
        volume = self._CommGetData(trcode, "", rqname, 0, "거래량")
        transRatio = self._CommGetData(trcode, "", rqname, 0, "거래대비")
        faceValueUnit = self._CommGetData(trcode, "", rqname, 0, "액면가단위")
        circStock = self._CommGetData(trcode, "", rqname, 0, "유통주식")
        circRatio = self._CommGetData(trcode, "", rqname, 0, "유통비율")

    def _tickMinPrice(self, rqname, trcode):    # 틱/분요청
        self.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
        data_cnt = self._GetRepeatCnt(trcode, rqname)
        for i in range(data_cnt):
            date = self._CommGetData(trcode, "", rqname, i, "체결시간")
            open = self._CommGetData(trcode, "", rqname, i, "시가")
            high = self._CommGetData(trcode, "", rqname, i, "고가")
            low = self._CommGetData(trcode, "", rqname, i, "저가")
            close = self._CommGetData(trcode, "", rqname, i, "현재가")
            volume = self._CommGetData(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(datetime.datetime.strptime(date, '%Y%m%d%H%M%S'))
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    def _dayWeekMonthYearPrice(self, rqname, trcode):  # 일/주/월/년봉요청
        self.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}
        data_cnt = self._GetRepeatCnt(trcode, rqname)
        for i in range(data_cnt):
            date = self._CommGetData(trcode, "", rqname, i, "일자")
            open = self._CommGetData(trcode, "", rqname, i, "시가")
            high = self._CommGetData(trcode, "", rqname, i, "고가")
            low = self._CommGetData(trcode, "", rqname, i, "저가")
            close = self._CommGetData(trcode, "", rqname, i, "현재가")
            volume = self._CommGetData(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(datetime.datetime.strptime(date, '%Y%m%d'))
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    def _opw00018(self, rqname, trcode):
        self.opw00018Output = {'total': {}, 'indivisual': {}}
        # total data
        totalBuyingAmount = int(self._CommGetData(trcode, "", rqname, 0, "총매입금액"))
        totalEvalAmount = int(self._CommGetData(trcode, "", rqname, 0, "총평가금액"))
        totalEarning = int(self._CommGetData(trcode, "", rqname, 0, "총평가손익금액"))
        totalEarningRate = float(self._CommGetData(trcode, "", rqname, 0, "총수익률(%)")) / 100
        estimatedAsset = int(self._CommGetData(trcode, "", rqname, 0, "추정예탁자산"))
        # totalLoan = int(self._CommGetData(trcode, "", rqname, 0, "총대출금"))
        # totalLoanAmount = int(self._CommGetData(trcode, "", rqname, 0, "총융자금액"))
        # totalLoanEquityAmount = int(self._CommGetData(trcode, "", rqname, 0, "총대주금액"))
        numberOfRequest = int(self._CommGetData(trcode, "", rqname, 0, "조회건수"))
        self.opw00018Output['total'] = {"총매입금액": totalBuyingAmount, "총평가금액": totalEvalAmount,
                                        "총평가손익금액": totalEarning, "총수익률(%)": totalEarningRate,
                                        "추정예탁자산": estimatedAsset}
        # indivisual data
        # rows = self._GetRepeatCnt(trcode, rqname)
        for i in range(numberOfRequest):
            code = self._CommGetData(trcode, "", rqname, i, "종목번호").replace('A', '')
            name = self._CommGetData(trcode, "", rqname, i, "종목명")
            purchasPrice = int(self._CommGetData(trcode, "", rqname, i, "매입가"))
            profit = int(self._CommGetData(trcode, "", rqname, i, "평가손익"))
            profitRate = float(self._CommGetData(trcode, "", rqname, i, "수익률(%)")) / 100
            availableQuantity = int(self._CommGetData(trcode, "", rqname, i, "매매가능수량"))
            quantity = int(self._CommGetData(trcode, "", rqname, i, "보유수량"))
            nowPrice = int(self._CommGetData(trcode, "", rqname, i, "현재가"))
            purchaseAmount = int(self._CommGetData(trcode, "", rqname, i, "매입금액"))
            totalAmount = int(self._CommGetData(trcode, "", rqname, i, "평가금액"))
            sumOfFee = int(self._CommGetData(trcode, "", rqname, i, "수수료합"))
            tax = int(self._CommGetData(trcode, "", rqname, i, "세금"))
            amountRatio = float(self._CommGetData(trcode, "", rqname, i, "보유비중(%)")) / 100
            creditType = int(self._CommGetData(trcode, "", rqname, i, "신용구분"))
            # credit_name = self._CommGetData(trcode, "", rqname, i, "신용구분명")
            # loan_date = self._CommGetData(trcode, "", rqname, i, "대출일")
            # yesterday_close_price = int(self._CommGetData(trcode, "", rqname, i, "전일종가"))
            # yesterday_buy_num = int(self._CommGetData(trcode, "", rqname, i, "전일매수수량"))
            # yesterday_sell_num = int(self._CommGetData(trcode, "", rqname, i, "전일매도수량"))
            # today_buy_num = int(self._CommGetData(trcode, "", rqname, i, "금일매수수량"))
            # today_sell_num = int(self._CommGetData(trcode, "", rqname, i, "금일매도수량"))
            # purchase_fee = int(self._CommGetData(trcode, "", rqname, i, "매입수수료"))
            # estimated_fee = int(self._CommGetData(trcode, "", rqname, i, "평가수수료"))
            # # 손익분기매입가 = 매입가+(수수료+세금)/보유수량
            bep_price = int(purchasPrice + ((sumOfFee + tax) / quantity))
            self.opw00018Output['indivisual'][i] = {"종목코드": code, "종목명": name, "매입가": purchasPrice,
                                                    "평가손익": profit,
                                                    "수익률(%)": profitRate,
                                                    "매매가능수량": availableQuantity, "보유수량": quantity,
                                                    "현재가": nowPrice,
                                                    "매입금액": purchaseAmount, "평가금액": totalAmount,
                                                    "수수료합": sumOfFee, "세금": tax,
                                                    "보유비중(%)": amountRatio, "신용구분": creditType,
                                                    "손익분기매입가": bep_price}
if __name__ == '__main__':
    app = QApplication(sys.argv)

    kiwoom = Kiwoom()
    kiwoom._GetConnectState()
    kiwoom.Login()
    kiwoom._CommTerminate()
    kiwoom._GetConnectState()
