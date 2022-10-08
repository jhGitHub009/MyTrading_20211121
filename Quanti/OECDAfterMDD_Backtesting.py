# OECD계수 읽어오고.
# 발표날짜 구하고.
# Stock data reading 하고.
# 상관관계분석하고.
# Stock investing backtesting.
# accuracy,
# precision 분석.
import os
from timeit import default_timer as timer
import ray
from numba import jit, cuda
import pandas as pd
import datetime
import Quanti.MyLibrary_20180702 as MyLib
import Quanti.BasicFomula as BF
import Rebalancing as Rebal
from os import listdir, makedirs
from os.path import isfile, join, isdir, basename
import sys
import numpy as np


def GetDrawDown(_series):
    _DrawDown = (_series - _series.cummax())/_series.cummax()*100
    return _DrawDown.iloc[-1]


def GetDrawUp(_series):
    _DrawUp = (_series - _series.cummin())/_series.cummin()*100
    return _DrawUp.iloc[-1]
# 신호 데이터 만들기.
# Price데이터에 신호 데이터를 넣기.
# 신호데이터를 가공 해서 매수, 매도 데이터를 정확한 날짜에 넣는다.


def ChangeFormat(stock_folder, code):
    stockfiles = [f for f in listdir(stock_folder) if isfile(join(stock_folder, f))]  # folder내 파일name list
    stockfile = [filename for filename in stockfiles if code in filename]
    if len(stockfile) != 1:
        return False
    df_stock = pd.read_csv(stock_folder + '/' + stockfile[0],  engine='python')
    korToEng = {'날짜': 'Date', '종가': 'Price', '오픈': 'Open', '고가': 'High', '저가': 'Low', '거래량': 'Vol.', '변동 %': 'Change %'}
    for colName in df_stock.columns:
        if colName in korToEng.keys():
            df_stock.rename(columns={colName: korToEng[colName]}, inplace=True)
    if 'Change %' in df_stock.columns:
        df_stock = df_stock.drop(df_stock.columns[-1], axis=1)   # change(%) drop
    if 'Vol.' in df_stock.columns:
        df_stock = df_stock.drop(df_stock.columns[-1], axis=1)   # volumn drop
    df_stock.drop_duplicates(subset=['Date'], keep='first', inplace=True)
    df_stock['Date'] = pd.to_datetime(df_stock['Date'])
    df_stock.sort_values(by='Date', ascending=True, inplace=True)
    df_stock.set_index(keys='Date', inplace=True)
    for colName in df_stock.columns:
        # df_stock[colName] = pd.to_numeric(df_stock[colName], errors='coerce')
        df_stock[colName] = df_stock[colName].str.replace(',', '').astype(float)
    df_stock.rename(columns={'Price': 'Close'}, inplace=True)
    df_stock.to_csv(stock_folder+'/'+stockfile[0], encoding='cp949')
    return df_stock
# ChangeFormat(r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Stock_data\index', '803')


def GetSignal(dfPrice, OECDURL, OECDLoc, shoulder=-5, knee=5):
    dfRefData = pd.read_csv(OECDURL)
    dfRefData = dfRefData[dfRefData['LOCATION']==OECDLoc]

    dfRefData['PCT'] = dfRefData['Value'].pct_change() * 100
    dfRefData['TIME'] = pd.to_datetime(dfRefData['TIME'])
    dfRefData['ReleaseDate'] = pd.to_datetime(dfRefData['TIME']) + datetime.timedelta(days=45)
    if dfRefData.iloc[0]['ReleaseDate'] > dfPrice.index[0]:
        startDate = dfRefData.iloc[0]['TIME']
    else:
        startDate = dfPrice.index[0]

    if dfRefData.iloc[-1]['ReleaseDate'] > dfPrice.index[-1]:
        endDate = dfPrice.index[-1]
    else:
        endDate = dfRefData.iloc[-1]['TIME']
    dfRefData = dfRefData[dfRefData['ReleaseDate'] >= startDate]
    dfRefData = dfRefData[dfRefData['ReleaseDate'] <= endDate]
    dfPrice = dfPrice[dfPrice.index >= startDate]
    dfPrice = dfPrice[dfPrice.index <= endDate]
    dfRefData['TradeDate'] = [MyLib.AfterNearest(dfPrice.index, dfRefData.iloc[i]['ReleaseDate']) for i in
                              range(len(dfRefData))]

    dfRefData['Signal'] = None
    dfRefData.loc[dfRefData['PCT'] >= 0, 'Signal'] = 'Buy'
    dfRefData.loc[dfRefData['PCT'] < 0, 'Signal'] = 'Sell'
    dfPrice['OECDSignal'] = None
    dfPrice.loc[dfRefData['TradeDate'], 'OECDSignal'] = dfRefData['Signal'].tolist()
    dfPrice['DrawUp'] = None
    dfPrice['DrawDown'] = None
    dfPrice['Signal'] = None

    lastSignal = None
    thisSignal = None
    startIdx = None
    thisStatus = None
    for idx, rowData in dfPrice.iterrows():
        if rowData['OECDSignal'] != None:
            lastSignal = thisSignal
            thisSignal = rowData['OECDSignal']
        if thisSignal =='Buy':
            if lastSignal!='Buy' and rowData['OECDSignal'] == 'Buy':    # 오늘이 발표날이고, 기존은 sell, 오늘발표한것은 buy.
                startIdx = idx
            drawUp = GetDrawUp(dfPrice.loc[startIdx:idx]['Close'])  # 무릎만큼 울라가면.
            drawDown = 0.0
        elif thisSignal == 'Sell':
            if lastSignal != 'Sell' and rowData['OECDSignal'] == 'Sell':
                startIdx = idx
            drawUp = 0.0
            drawDown = GetDrawDown(dfPrice.loc[startIdx:idx]['Close'])  # 무릎만큼 울라가면.
        else:
            drawUp = 0.0
            drawDown = 0.0
        dfPrice.loc[idx, 'DrawUp'] = drawUp
        dfPrice.loc[idx, 'DrawDown'] = drawDown

        if drawUp > knee:
            if thisStatus != 'Buy':
                thisStatus = 'Buy'
                dfPrice.loc[idx, 'Signal'] = 'Buy'
        elif drawDown < shoulder:
            if thisStatus != 'Sell':
                thisStatus = 'Sell'
                dfPrice.loc[idx, 'Signal'] = 'Sell'
    return dfPrice
def intialAccount(dfPrice):
    idxAccount = dfPrice.index.tolist()
    idxAccount.insert(0,dfPrice.index[0]-datetime.timedelta(days=1))
    dfAccount = pd.DataFrame(index=idxAccount, columns=['Cash', 'Stock', 'Asset', 'Signal','CAGR','MDD','Accuracy','Precision'])
    dfAccount.iloc[0]['Cash'] = 1000000
    dfAccount.iloc[0]['Stock'] = [0]
    dfAccount.iloc[0]['Asset'] = 1000000
    dfAccount.iloc[0]['Signal'] = None
    dfAccount.iloc[0]['CAGR'] = 0
    dfAccount.iloc[0]['MDD'] = 0
    dfAccount.iloc[0]['Accuracy'] = 0
    dfAccount.iloc[0]['Precision'] = 0
    return dfAccount


def DoBacktesting(dfPrice, dfAccount):
    for date, data in dfPrice.iterrows():
        if data['Signal'] == 'Buy':
            idxDate = dfAccount.index.get_loc(date)
            cash = dfAccount.iloc[idxDate - 1]['Cash']
            stock = dfAccount.iloc[idxDate - 1]['Stock']
            thisDayOpen = data['Open']
            thisAsset = Rebal.GetNowValue(cash, [thisDayOpen], stock)
            diffStock, newStock = Rebal.Rebalancing5(thisAsset, [thisDayOpen], stock, [100])

            dfAccount.loc[date, 'Cash'] = int(Rebal.TradeStock(cash, [thisDayOpen], diffStock))
            dfAccount.loc[date, 'Stock'] = newStock
            dfAccount.loc[date, 'Asset'] = thisAsset
            dfAccount.loc[date, 'Signal'] = 'Buy'
            dfAccount.loc[date, 'CAGR'] = BF.GetCAGR(dfAccount.iloc[0]['Asset'], thisAsset,
                                                     BF.GetYear(dfAccount.index[0], date))
            dfAccount.loc[date, 'MDD'] = BF.GetMDD(dfAccount.loc[dfAccount.index[0]:date, 'Asset'])
        elif data['Signal'] == 'Sell':
            idxDate = dfAccount.index.get_loc(date)
            cash = dfAccount.iloc[idxDate - 1]['Cash']
            stock = dfAccount.iloc[idxDate - 1]['Stock']
            thisDayOpen = data['Open']
            thisAsset = Rebal.GetNowValue(cash, [thisDayOpen], stock)
            diffStock, newStock = Rebal.Rebalancing5(thisAsset, [thisDayOpen], stock, [0])

            dfAccount.loc[date, 'Cash'] = int(Rebal.TradeStock(cash, [thisDayOpen], diffStock))
            dfAccount.loc[date, 'Stock'] = newStock
            dfAccount.loc[date, 'Asset'] = thisAsset
            dfAccount.loc[date, 'Signal'] = 'Sell'
            dfAccount.loc[date, 'CAGR'] = BF.GetCAGR(dfAccount.iloc[0]['Asset'], thisAsset,
                                                     BF.GetYear(dfAccount.index[0], date))
            dfAccount.loc[date, 'MDD'] = BF.GetMDD(dfAccount.loc[dfAccount.index[0]:date, 'Asset'])
        else:
            idxDate = dfAccount.index.get_loc(date)
            cash = dfAccount.iloc[idxDate - 1]['Cash']
            stock = dfAccount.iloc[idxDate - 1]['Stock']
            thisDayClose = data['Close']
            thisAsset = Rebal.GetNowValue(cash, [thisDayClose], stock)
            dfAccount.loc[date, 'Cash'] = cash
            dfAccount.loc[date, 'Stock'] = stock
            dfAccount.loc[date, 'Asset'] = thisAsset
            dfAccount.loc[date, 'Signal'] = 'Hold'
            dfAccount.loc[date, 'CAGR'] = BF.GetCAGR(dfAccount.iloc[0]['Asset'], thisAsset,
                                                     BF.GetYear(dfAccount.index[0], date))
            dfAccount.loc[date, 'MDD'] = BF.GetMDD(dfAccount.loc[dfAccount.index[0]:date, 'Asset'])
    return dfPrice, dfAccount


def GetAccuracy(df):
    # signalIdx = [idx for idx, status in enumerate(df['Status'].tolist()) if '신호' in status]
    # dfSignal = df.loc[signalIdx]
    dfSignal = df.loc[df[~df['Signal'].isnull()].index.tolist()]
    dfSignal['Score'] = 0
    for idx,(idxDfSignal,dataDfSignal) in enumerate(dfSignal.iterrows()):
        if (len(dfSignal)-1) == idx:        # 마지막 index이면 전체 계산.
            return (dfSignal['Score'].sum()) / (len(dfSignal['Score']) - 1) * 100
        # '매수 신호'일 (다음 신호의 가격 - 경우 현재 가격) 값이 + 이면 +1 - 이면 -1
        elif dataDfSignal['Signal']=='Buy':
            result = dfSignal.iloc[idx+1]['Price'] - dfSignal.iloc[idx]['Price']
            if result > 0:
                dfSignal.loc[idxDfSignal,'Score'] = 1
        # '매도 신호'일 (다음 신호의 가격 - 경우 현재 가격) 값이 - 이면 +1 + 이면 -1
        elif dataDfSignal['Signal']=='Sell':
            result = dfSignal.iloc[idx]['Price'] - dfSignal.iloc[idx + 1]['Price']
            if result > 0:
                dfSignal.loc[idxDfSignal,'Score'] = 1

def NormalMain(dfPrice,OECDURL,OECDLoc,shoulder,knee,saveFolder,saveRawFolder):
    start = timer()
    print('------- knee : %s, shoulder : %s -------' % (knee, shoulder))
    sys.stdout.flush()
    dfPrice = GetSignal(dfPrice, OECDURL=OECDURL, OECDLoc=OECDLoc, shoulder=shoulder, knee=knee)
    dfAccount = intialAccount(dfPrice)
    dfPrice, dfAccount = DoBacktesting(dfPrice, dfAccount)

    dfAccuracy = pd.DataFrame(index=dfPrice[~dfPrice['Signal'].isnull()].index.tolist(), columns=['Signal', 'Price'])
    dfAccuracy['Signal'] = dfAccount.loc[dfAccuracy.index, 'Signal']
    dfAccuracy['Price'] = dfPrice.loc[dfAccuracy.index, 'Close']
    precision, recall, accuracy, fScore, dfScore = BF.GetScore(dfAccuracy)
    costScore, dfCostScore = BF.CostScore(dfAccuracy)
    dfAccuracy['Prec'] = None
    dfAccuracy['Recall'] = None
    dfAccuracy['Accuracy'] = None
    dfAccuracy['FScore'] = None
    dfAccuracy['AltCostScore'] = None
    dfAccuracy.loc[dfAccuracy.index[0], 'Prec'] = precision
    dfAccuracy.loc[dfAccuracy.index[0], 'Recall'] = recall
    dfAccuracy.loc[dfAccuracy.index[0], 'Accuracy'] = accuracy
    dfAccuracy.loc[dfAccuracy.index[0], 'FScore'] = fScore
    dfAccuracy.loc[dfAccuracy.index[0], 'AltCostScore'] = costScore

    summaryTemp = pd.DataFrame(
        columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
                 'FinalAsset', 'CAGR', 'MDD'])

    idxSum = len(summaryTemp)
    summaryTemp.loc[idxSum, 'Knee'] = knee
    summaryTemp.loc[idxSum, 'Shoulder'] = shoulder
    summaryTemp.loc[idxSum, 'Prec'] = precision
    summaryTemp.loc[idxSum, 'Recall'] = recall
    summaryTemp.loc[idxSum, 'Accuracy'] = accuracy
    summaryTemp.loc[idxSum, 'FScore'] = fScore
    summaryTemp.loc[idxSum, 'AltCostScore'] = costScore
    summaryTemp.loc[idxSum, 'IniAsset'] = dfAccount.iloc[0]['Asset']
    summaryTemp.loc[idxSum, 'FinalAsset'] = dfAccount.iloc[-1]['Asset']
    summaryTemp.loc[idxSum, 'CAGR'] = dfAccount.iloc[-1]['CAGR']
    summaryTemp.loc[idxSum, 'MDD'] = dfAccount.iloc[-1]['MDD']

    # summaryTemp.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
    dfAccount.to_csv(saveRawFolder + '\dfAccount_Knee%s_Shoulder%s.csv' % (knee, shoulder), encoding='cp949')
    dfAccuracy.to_csv(saveRawFolder + '\dfAccuracy_Knee%s_Shoulder%s.csv' % (knee, shoulder), encoding='cp949')
    del dfAccount
    del dfAccuracy
    print(",func_OneLoop : %s" % (timer() - start))
    return summaryTemp

@ray.remote(num_cpus = 1)
def RayMain(dfPrice,OECDURL,OECDLoc,shoulder,knee,saveFolder,saveRawFolder):
    start = timer()
    print('------- knee : %s, shoulder : %s -------' % (knee, shoulder))
    sys.stdout.flush()
    dfPrice = GetSignal(dfPrice, OECDURL=OECDURL, OECDLoc=OECDLoc, shoulder=shoulder, knee=knee)
    dfAccount = intialAccount(dfPrice)
    dfPrice, dfAccount = DoBacktesting(dfPrice, dfAccount)

    dfAccuracy = pd.DataFrame(index=dfPrice[~dfPrice['Signal'].isnull()].index.tolist(), columns=['Signal', 'Price'])
    dfAccuracy['Signal'] = dfAccount.loc[dfAccuracy.index, 'Signal']
    dfAccuracy['Price'] = dfPrice.loc[dfAccuracy.index, 'Close']
    precision, recall, accuracy, fScore, dfScore = BF.GetScore(dfAccuracy)
    costScore, dfCostScore = BF.CostScore(dfAccuracy)
    dfAccuracy['Prec'] = None
    dfAccuracy['Recall'] = None
    dfAccuracy['Accuracy'] = None
    dfAccuracy['FScore'] = None
    dfAccuracy['AltCostScore'] = None
    dfAccuracy.loc[dfAccuracy.index[0], 'Prec'] = precision
    dfAccuracy.loc[dfAccuracy.index[0], 'Recall'] = recall
    dfAccuracy.loc[dfAccuracy.index[0], 'Accuracy'] = accuracy
    dfAccuracy.loc[dfAccuracy.index[0], 'FScore'] = fScore
    dfAccuracy.loc[dfAccuracy.index[0], 'AltCostScore'] = costScore

    summaryTemp = pd.DataFrame(
        columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
                 'FinalAsset', 'CAGR', 'MDD'])

    idxSum = len(summaryTemp)
    summaryTemp.loc[idxSum, 'Knee'] = knee
    summaryTemp.loc[idxSum, 'Shoulder'] = shoulder
    summaryTemp.loc[idxSum, 'Prec'] = precision
    summaryTemp.loc[idxSum, 'Recall'] = recall
    summaryTemp.loc[idxSum, 'Accuracy'] = accuracy
    summaryTemp.loc[idxSum, 'FScore'] = fScore
    summaryTemp.loc[idxSum, 'AltCostScore'] = costScore
    summaryTemp.loc[idxSum, 'IniAsset'] = dfAccount.iloc[0]['Asset']
    summaryTemp.loc[idxSum, 'FinalAsset'] = dfAccount.iloc[-1]['Asset']
    summaryTemp.loc[idxSum, 'CAGR'] = dfAccount.iloc[-1]['CAGR']
    summaryTemp.loc[idxSum, 'MDD'] = dfAccount.iloc[-1]['MDD']

    # summaryTemp.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
    dfAccount.to_csv(saveRawFolder + '\dfAccount_Knee%s_Shoulder%s.csv' % (knee, shoulder), encoding='cp949')
    dfAccuracy.to_csv(saveRawFolder + '\dfAccuracy_Knee%s_Shoulder%s.csv' % (knee, shoulder), encoding='cp949')
    del dfAccount
    del dfAccuracy
    print(",func_OneLoop : %s" % (timer() - start))
    return summaryTemp

def Main(priceFolder, keywordPrice, OECDURL, OECDLoc, saveFolder, shoulders, knees, nCPU):
    dfPrice = MyLib.ReadStockData2(priceFolder, keywordPrice)
    knees = [round(knee, 2) for knee in knees]
    shoulders = [round(shoulder, 2) for shoulder in shoulders]
    summary = pd.DataFrame(
        columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
                 'FinalAsset', 'CAGR', 'MDD'])
    saveRawFolder = saveFolder + '\Raw'
    if not isdir(saveRawFolder):
        makedirs(saveRawFolder)
    NormalMain(dfPrice, OECDURL, OECDLoc, shoulder=shoulders[0], knee=knees[0], saveFolder=saveFolder, saveRawFolder=saveRawFolder)
    ray.init(num_cpus = nCPU)
    i = 0
    futures = []
    for shoulder in shoulders:
        for knee in knees:
            if i < nCPU:
                futures.append(RayMain.remote(dfPrice, OECDURL, OECDLoc, shoulder, knee, saveFolder, saveRawFolder))
                i += 1
            else:
                ret = ray.get(futures)
                for tempSummary in ret:
                    summary = summary.append(tempSummary)
                summary.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
                del ret
                i = 0
                futures = []

#####################################################################
#                           Do Backtesting                      #
#####################################################################
# MyLib.ChangeFormat(r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Investing','APPLE.csv')
# priceFolder = r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Investing'
# keywordPrice = 'APPLE'
# OECDURL = r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Quanti\OECD\Data\OECD_CLI_2022-07-31.csv'
# OECDLoc = 'USA'
# saveFolder = './OECD\Backtesting\OECDKneeSholder\%s'%(keywordPrice)
# shoulders = np.arange(-0.02, -2.0, -0.02)
# knees = np.arange(0.02, 2.0, 0.02)

# priceFolder = r'C:\Users\jhmai\PycharmProjects\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index'
# keywordPrice = 'S&P'
# OECDURL = r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Quanti\OECD\Data\OECD_CLI_2022-07-31.csv'
# OECDLoc = 'USA'
# saveFolder = './OECD\Backtesting\OECDKneeSholder\%s2'%(keywordPrice)
# shoulders = np.arange(-0.1, -0.4, -0.02)
# knees = np.arange(0.02, 0.4, 0.02)

priceFolder = r'../Infomation\Investing\20220511\StockData_USA\Historical_Data\Index'
keywordPrice = 'Nasdaq.csv'
OECDURL = r'./OECD\Data\OECD_CLI_2022-07-31.csv'
OECDLoc = 'USA'
saveFolder = './OECD\Backtesting\OECDAfterMDD\%s'%(keywordPrice)
shoulders = np.arange(-0.02, -2.02, -0.02)
knees = np.arange(0.02, 2.02, 0.02)
nCPU = 5
Main(priceFolder, keywordPrice, OECDURL, OECDLoc, saveFolder, shoulders, knees, nCPU)
