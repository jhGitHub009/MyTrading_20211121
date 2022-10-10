import pandas as pd
import numpy as np
from BasicFomula import *
from Rebalancing import *
import datetime
from Talib import *
import matplotlib.pyplot as plt
from os import listdir,makedirs
from os.path import isfile, join, isdir, basename
import sys

def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))
def MakeRank(df_summery,indicators,ascendings):
    df_summery['Rank'] = 0
    for indicator,ascend in zip(indicators,ascendings):
        df_summery[indicator+'_Rank'] = df_summery[indicator].rank(ascending=ascend)
        df_summery['Rank'] += df_summery[indicator+'_Rank']
    df_summery = df_summery.sort_values(by=['Rank'], ascending=True, na_position='last')
    return df_summery
def GetData(folder,code,item,date):
    files = [f for f in listdir(folder) if isfile(join(folder, f))]  # folder내 파일name list
    file = [filename for filename in files if code in filename]
    if len(file) != 1:
        sys.stdout.flush()
        return False
    df_data = pd.read_csv(folder + file[0], encoding='cp949',engine='python')
    df_data.dropna(axis=1, inplace=True, how='all')
    df_data.dropna(axis=0, inplace=True, how='all')
    df_data.set_index(keys=df_data.columns[0], inplace=True)
    item = [index for index in df_data.index if item in index][0]
    col_name = [col for col in df_data.columns if date in col][0]
    data = df_data.loc[item, col_name]
    stop_words=[',','억','원','/','%']
    if isinstance(data,str):
        for stop_word in stop_words:
            if stop_word in data:
                data = data.replace(stop_word,'')
        data = float(data)
    return data
def GetDataFnGuide(folder,code,item,date,valueCategory):
    files = [f for f in listdir(folder) if isfile(join(folder, f))]  # folder내 파일name list
    file = [filename for filename in files if (code in filename) and (valueCategory in filename)]
    # df_data = pd.read_excel(open(folder + file[0], 'rb'), sheetname='개별기업 재무제표 추이')
    df_data = pd.ExcelFile(folder + file[0])
    df_data = df_data.parse("개별기업 재무제표 추이")

    df_data.set_index(keys=df_data.columns[0], inplace=True)
    df_data.columns = [str(name).replace('.03','/12').replace('.12','/12') for name in list(df_data.loc['계정과목'])]
    item = [index for index in df_data.index if item in str(index)][0]
    col_name = [col for col in df_data.columns if date in str(col)][0]
    data = df_data.loc[item, col_name]
    stop_words=[',','억','원','/','%']
    if isinstance(data,str):
        for stop_word in stop_words:
            if stop_word in data:
                data = data.replace(stop_word,'')
        # data = float(data)
    return float(data)
def GetClosePrice(thisDay,stockFolder,code):
    stockFiles = [f for f in listdir(stockFolder) if isfile(join(stockFolder, f))]  # folder내 파일name list
    stockFile = [filename for filename in stockFiles if code in filename][0]
    dfStock = pd.read_csv(stockFolder + stockFile, encoding='cp949',engine='python')
    dfStock['Date'] = pd.to_datetime(dfStock['Date'])
    thisDay = datetime.datetime.strptime(thisDay, '%Y-%m-%d')
    nowDay = nearest(dfStock['Date'], thisDay)
    diffDays = nowDay - thisDay
    if 14 < abs(diffDays.days):
        price = dfStock.loc[dfStock['Date'] == thisDay, 'Close'].iloc[0]
    price = dfStock.loc[dfStock['Date'] == nowDay, 'Close'].iloc[0]
    return price
def GetDate(date):
    if type(date)==str:
        dateDt = datetime.datetime.strptime(date,'%Y-%m-%d')
    else:
        dateDt = date
    if dateDt.month<4:
        dateYear = dateDt.year - 2
    else:
        dateYear = dateDt.year - 1
    targetDate = str(dateYear) + '/12'
    return targetDate
def GetPERDebitRatio(thisDay,stockFolder,financeFolder):
    financeFiles = [f for f in listdir(financeFolder) if isfile(join(financeFolder, f))]
    dfFinance = pd.DataFrame(columns=['Code','Company','MarketCapitalization','PER','PBR','PCR','PSR'])
    for financeFile in financeFiles:
        company = financeFile.replace('.csv', '').split('_')[0]
        code = financeFile.replace('.csv', '').split('_')[1]
        targetDate = GetDate(thisDay)
        try:
            closePrice = float(GetClosePrice(thisDay, stockFolder, code))
            # stockNum = GetData(financeFolder, code, '발행주식수(보통주)', targetDate)
            stockNum = GetDataFnGuide('./FnGuide2/', code, '*발행한주식총수', targetDate, '재무상태표')
            marketCapitalization = closePrice * stockNum
            # EPS = GetData('./Main/', code, 'EPS', targetDate)
            EPS = GetDataFnGuide('./FnGuide2/', code, '수정EPS', targetDate, '재무비율')
            PER = closePrice / EPS
            # BPS = GetData('./Main/', code, 'BPS', targetDate)
            BPS = GetDataFnGuide('./FnGuide2/', code, '수정BPS', targetDate, '재무비율')
            PBR = closePrice / BPS
            # CPS = GetData('./Main/', code, 'CPS', targetDate)
            CPS = GetDataFnGuide('./FnGuide2/', code, '수정CFPS', targetDate, '재무비율')
            PCR = closePrice / CPS
            # SPS = GetData('./Main/', code, 'SPS', targetDate)
            SPS = GetDataFnGuide('./FnGuide2/', code, '수정SPS', targetDate, '재무비율')
            PSR = closePrice / SPS
            dfFinance.loc[len(dfFinance)] = [code,company,marketCapitalization,PER,PBR,PCR,PSR]
        except:
            print('%s_%s no data!!'%(code,company))
            continue
    print('Finish!')
    return dfFinance
def GetPERDebitRatioFiltered(thisDay):
    financeFolder = './financial_summery_Year2/'
    # kospiFolder = './Stock_data2/total/'
    kospiFolder = './Investing/Monthly_AfterTreat/'
    # kospiFolder = './Stock_dataKiwoom3/kospi/'
    dfFinance = GetPERDebitRatio(thisDay, kospiFolder, financeFolder)
    dfFinance = dfFinance.sort_values(by=['MarketCapitalization'], ascending=True, na_position='last')
    smallCapStocks = int(len(dfFinance) * 0.2)
    dfFinance = dfFinance.iloc[:smallCapStocks]
    dfFinance = dfFinance.loc[dfFinance['PER'] > 0]
    dfFinance = dfFinance.loc[dfFinance['PBR'] > 0]
    dfFinance = dfFinance.loc[dfFinance['PCR'] > 0]
    dfFinance = dfFinance.loc[dfFinance['PSR'] > 0]
    dfFinanceRanked = MakeRank(dfFinance, ['PER','PBR','PCR','PSR'], [True,True,True,True])
    dfFinanceRanked.reset_index(drop=True, inplace=True)
    if len(dfFinanceRanked) > 20:
        dfFinanceRanked = dfFinanceRanked.iloc[:20].copy()
    return dfFinanceRanked
def GetMergedData(dfFinanace):
    stockFolder = './Investing/Monthly_AfterTreat/'
    stockFiles = [f for f in listdir(stockFolder) if isfile(join(stockFolder, f))]
    for idxFinanace, rowFinanace in dfFinanace.iterrows():
        code = rowFinanace['Code']
        stockFile = [stockFile for stockFile in stockFiles if code in stockFile]
        if idxFinanace == 0:
            dfMerged = pd.read_csv(stockFolder + stockFile[0], encoding='cp949',engine='python')
            dfMerged.drop_duplicates(subset=['Date'], inplace=True)
            dfMerged['Date'] = pd.to_datetime(dfMerged['Date'])
            dfMerged.sort_values(by='Date', ascending=True, inplace=True)
            dfMerged.set_index(['Date'], drop=True, inplace=True)
            # dfMerged = dfMerged[['Close']]
            dfMerged.columns = ['%s_%s'%(colName,code) for colName in dfMerged.columns]
            # dfMerged.columns = ['Close_%s' % (code)]
        else:
            dfStock = pd.read_csv(stockFolder + stockFile[0], encoding='cp949',engine='python')
            dfStock.drop_duplicates(subset=['Date'], inplace=True)
            dfStock['Date'] = pd.to_datetime(dfStock['Date'])
            dfStock.sort_values(by='Date', ascending=True, inplace=True)
            dfStock.set_index(['Date'], drop=True, inplace=True)
            # dfStock = dfStock[['Close']]
            dfStock.columns = ['%s_%s' % (colName, code) for colName in dfStock.columns]
            # dfStock.columns = ['Close_%s' % (code)]
            dfMerged = pd.merge(dfMerged, dfStock, how='outer', left_index=True, right_index=True)
            # dfMerged = pd.merge(dfMerged, dfStock, how='outer', on='Date')
    return dfMerged
def GetBuyCompany(tradeDate,numOfCompany = 20):
    tradeDateDT = datetime.datetime.strptime(tradeDate,'%Y-%m-%d')
    selectName = 'S&P500'  # 미국모든주식 # 나스닥종합 # 다우존스 # S&P500
    filePathforIndex = r'../Infomation\Investing\20220511\StockName\%s.csv' % (selectName)
    filePathforHistorical = r'../Infomation\Investing\20220511\StockData_USA\Historical_Data\Daily\S&P500'
    filePathforInfoSummary = r'../Infomation\Investing\20220511\StockData_USA\Financial information summary\S&P500'
    filePathforGeneralSummary = r'../Infomation\Investing\20220511\StockData_USA\General Summary\S&P500'
    # index파일리딩.
    indexData = pd.read_csv(filePathforIndex, encoding='cp949', engine='python')
    indexData = indexData[['종목','현재가','고가','저가','변동']]
    dfScreening = pd.DataFrame(index=indexData['종목'],columns=['EPS','BPS','CPS','SPS','PER','PBR','PCR','PSR',
                                                              'MarketCap','AvgVolume','Close'])
    for idxIndexData, rowIndexData in indexData.iterrows():
        companyName = rowIndexData['종목'].replace('/','')
        print('     %s - %s) %s.....'%(len(indexData),idxIndexData, companyName),end='')
        sys.stdout.flush()
        if (idxIndexData==149):
            print('duplicated company!!')
            continue
        # if (idxIndexData==142) or (idxIndexData==532) or (idxIndexData==594) or (idxIndexData==627) or (idxIndexData==716) or (idxIndexData==878):
        #     print('Fail!!')
        #     continue
        # 항목의 히스토리컬 데이터 열고.
        dfHistorical = pd.read_csv(filePathforHistorical + '/%s.csv'%companyName, encoding='cp949', engine='python')
        dfHistorical['Date'] = pd.to_datetime(arg=dfHistorical['Date'], format='%Y-%m-%d')
        dfHistorical.set_index(['Date'], drop=True, inplace=True)
        # 트레이드 날짜를 다시 설정.
        thisTradeDateDT = nearest(dfHistorical.index, tradeDateDT)
        thisTradeDateDT = datetime.datetime.strptime(thisTradeDateDT._date_repr,'%Y-%m-%d')
        if abs(thisTradeDateDT-tradeDateDT).days > 10:
            print('Data is not match!!')
            continue
        # 종가를 가져옴.
        close = dfHistorical.loc[thisTradeDateDT]['Close']
        if type(close)==str:
            close = float(close.replace(',',''))
        # 재무 정보 가져옴.
        dfInfoSummary = pd.read_csv(filePathforInfoSummary + '/%s.csv' % companyName, encoding='cp949', engine='python')
        dfInfoSummary.set_index(dfInfoSummary.columns[0], drop=True, inplace=True)
        dfInfoSummary.columns = [datetime.datetime.strptime(newCol,'%Y년 %m월 %d일') for newCol in list(dfInfoSummary.columns)]
        # [for newCol in list(dfInfoSummary.columns)]
        pastYear = [newCol for newCol in list(dfInfoSummary.columns) if thisTradeDateDT > newCol]
        if not pastYear:
            print('%s no annual data !!'%(companyName))
            continue
        annualDataDT = nearest([newCol for newCol in list(dfInfoSummary.columns) if thisTradeDateDT > newCol], thisTradeDateDT)
        earning = dfInfoSummary.loc['순이익', annualDataDT] * 1e6
        equity = dfInfoSummary.loc['총자본',annualDataDT] * 1e6
        cashFlow = dfInfoSummary.loc['영업활동 현금', annualDataDT] * 1e6
        revenue = dfInfoSummary.loc['총매출', annualDataDT] * 1e6
        # 주식수 가져옴.
        dfGeneralSum = pd.read_csv(filePathforGeneralSummary + '/%s.csv' % companyName, encoding='cp949', engine='python')
        dfGeneralSum.set_index(dfGeneralSum.columns[0], drop=True, inplace=True)
        issuedShares = dfGeneralSum.loc['발행주식수','Data']
        try:
            issuedShares = float(issuedShares.replace(',', ''))
        except:
            issuedShares = issuedShares
        if issuedShares=='-':
            continue
        avgVolume = float(dfGeneralSum.loc['평균 거래량', 'Data'].replace(',', ''))
        marketCap = dfGeneralSum.loc['총 시가', 'Data'].replace(',', '')
        if 'B' in marketCap:
            marketCap = float(marketCap.replace('B', '')) * 1e9
        elif 'T' in marketCap:
            marketCap = float(marketCap.replace('T', '')) * 1e12
        elif 'M' in marketCap:
            marketCap = float(marketCap.replace('M', '')) * 1e6
        elif 'K' in marketCap:
            marketCap = float(marketCap.replace('K', '')) * 1e3
        else:
            print('Reset market capitalization!!'%marketCap)
            continue
        # EPS 등을 계산
        # PER PCR PSR PBR 계산.
        # if idxIndexData>=71:
        #     print()
        EPS = earning/issuedShares
        BPS = equity / issuedShares
        CPS = cashFlow / issuedShares
        SPS = revenue / issuedShares
        PER = close / EPS
        PBR = close / BPS
        PCR = close / CPS
        PSR = close / SPS
        dfScreening.loc[companyName] = [EPS, BPS, CPS, SPS, PER, PBR, PCR, PSR, marketCap, avgVolume, close]
        print('Done!!')
    dfScreening = dfScreening.sort_values(by=['MarketCap'], ascending=True, na_position='last')
    smallCapStocks = int(len(dfScreening) * 0.2)
    dfScreening = dfScreening.iloc[:smallCapStocks]
    dfScreening = dfScreening.loc[dfScreening['PER'] > 0]
    dfScreening = dfScreening.loc[dfScreening['PBR'] > 0]
    dfScreening = dfScreening.loc[dfScreening['PCR'] > 0]
    dfScreening = dfScreening.loc[dfScreening['PSR'] > 0]
    dfScreening = MakeRank(dfScreening, ['PER', 'PBR', 'PCR', 'PSR'], [True, True, True, True])
    dfScreening.reset_index(inplace=True)
    dfScreening.to_csv(logFolder + 'dfScreening_%s.csv' % tradeDate, encoding='cp949')
    if len(dfScreening) > numOfCompany:
        dfScreening = dfScreening.iloc[:numOfCompany].copy()
    return dfScreening
if __name__ == '__main__':
    # logFolder = './Log/Investment24_20190129/'
    numOfBuys = [20]
    for numOfBuy in numOfBuys:
        logFolder = './Log/%s_%s/' % (
            basename(__file__).replace('.py', ''), datetime.datetime.today().strftime('%Y%m%d_%H%M%S'))
        if not isdir(logFolder): makedirs(logFolder)
        # 날짜를 받아서
        # tradeDate = ['2017-05-01', '2018-05-01', '2019-05-01', '2020-05-01']
        tradeDate = ['2022-05-11']
        dfAccount = pd.DataFrame(columns=['Date', 'TotalValue'])
        balance = 10000
        for idxTradeDate, thisTradeDate in enumerate(tradeDate):
            # 거래할 종목을 골라서
            dfScreening = GetBuyCompany(thisTradeDate, numOfBuy)
            if idxTradeDate == 0:
                stockValues = [0 for _ in range(len(dfScreening))]
                thisStockNum = [0 for _ in range(len(dfScreening))]
            totalValue = GetNowValue(balance, stockValues, thisStockNum)
            stockValues = dfScreening['Close'].tolist()
            # 현재 잔고와 거래할 종목,전체 금액을 따져서 Rebalancing.
            diffStockNum, thisStockNum = Rebalancing(totalValue, stockValues, thisStockNum, tradeFee=7.0)
            balance = TradeStock(balance, stockValues, diffStockNum, tradeFee=7.0)
            totalValue = GetNowValue(balance, stockValues, thisStockNum)
            dfAccount.loc[len(dfAccount)] = [thisTradeDate, totalValue]
            del dfScreening
        # 전체 기간과 최종 금액을 통해 연간 수익 환산.
        # plt.plot(dfAccount['Date'], dfAccount['TotalValue'])
        # plt.legend()
        # plt.show()
        # year = GetYear(dfAccount.iloc[0]['Date'], dfAccount.iloc[-1]['Date'])
        # mddValue = GetMDD(dfAccount['TotalValue'])
        # cagrValue = GetCAGR(10000, dfAccount.iloc[-1]['TotalValue'], year)
        # dfAccount.loc[len(dfAccount)] = [mddValue, cagrValue]
        dfAccount.to_csv(logFolder + 'dfAccount_%s.csv' % numOfBuy, encoding='cp949')
    print()