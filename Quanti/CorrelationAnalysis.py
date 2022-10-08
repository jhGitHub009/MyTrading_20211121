# OECD계수 읽어오고.
# 발표날짜 구하고.
# Stock data reading 하고.
# 상관관계분석하고.
# Stock investing backtesting.
# accuracy,
# precision 분석.
#
import pandas as pd
import datetime
import Quanti.MyLibrary_20180702 as MyLib
import Quanti.BasicFomula as BF
import Rebalancing as Rebal
from os import listdir
from os.path import isfile, join
import sys
import numpy as np
# 신호 데이터 만들기.
# Price데이터에 신호 데이터를 넣기.
# 신호데이터를 가공 해서 매수, 매도 데이터를 정확한 날짜에 넣는다.
def ChangeFormat(stock_folder,code):
    stockfiles = [f for f in listdir(stock_folder) if isfile(join(stock_folder, f))]  # folder내 파일name list
    stockfile = [filename for filename in stockfiles if code in filename]
    if len(stockfile) != 1:
        return False
    df_stock = pd.read_csv(stock_folder + '/' + stockfile[0],  engine='python')
    korToEng = {'날짜':'Date','종가':'Price','오픈':'Open','고가':'High','저가':'Low','거래량':'Vol.','변동 %':'Change %'}
    for colName in df_stock.columns:
        if colName in korToEng.keys():
            df_stock.rename(columns={colName: korToEng[colName]}, inplace=True)
    if 'Change %' in df_stock.columns:
        df_stock = df_stock.drop(df_stock.columns[-1], axis=1) # change(%) drop
    if 'Vol.' in df_stock.columns:
        df_stock = df_stock.drop(df_stock.columns[-1], axis=1) # volumn drop
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
def GetSignal(dfPrice,oecdValDiff):
    # dfRefData = pd.read_csv(r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Quanti\OECD\Data\OECD_CLI_2022-07-31.csv')
    dfRefData = pd.read_csv(r'C:\Users\jhmai\PycharmProjects\QuantiBook_20181215\OECD\OECD_CLI.csv')
    dfRefData = dfRefData[dfRefData['LOCATION']=='USA']
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
    dfRefData = dfRefData[dfRefData['ReleaseDate']>=startDate]
    dfRefData = dfRefData[dfRefData['ReleaseDate']<=endDate]
    dfPrice = dfPrice[dfPrice.index>=startDate]
    dfPrice = dfPrice[dfPrice.index<=endDate]
    dfRefData['TradeDate'] = [MyLib.AfterNearest(dfPrice.index, dfRefData.iloc[i]['ReleaseDate']) for i in range(len(dfRefData))]
    dfRefData['Signal'] = None
    dfRefData.loc[dfRefData['PCT']>= oecdValDiff,'Signal'] = 'Buy'
    dfRefData.loc[dfRefData['PCT']< oecdValDiff,'Signal'] = 'Sell'
    dfPrice['Signal'] = None
    dfPrice.loc[dfRefData['TradeDate'], 'Signal'] = dfRefData['Signal'].tolist()
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
            # print('Buy')
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
            # print('Sell')
            # dfAccount.
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
            # print('Hold')
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

# # dfPrice = MyLib.ReadStockData2(r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Stock_data\index', '803')
# dfPrice = MyLib.ReadStockData2(r'C:\Users\jhmai\PycharmProjects\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index', 'Nasdaq')
# # dfPrice = dfPrice.loc[dfPrice.index>='2002-01-01']
# oecdValDiffs = np.arange(-0.1, -0.3, -0.0001)
# for oecdValDiff in oecdValDiffs:
#     print('-------------------- %s --------------------'%(oecdValDiff))
#     dfPrice = GetSignal(dfPrice, oecdValDiff)
#     dfAccount = intialAccount(dfPrice)
#     dfPrice, dfAccount = DoBacktesting(dfPrice, dfAccount)
#
#     # dfRefPrice = MyLib.ReadStockData2(r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Stock_data\index', '803')
#     dfRefPrice = MyLib.ReadStockData2(r'C:\Users\jhmai\PycharmProjects\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index', 'Nasdaq')
#     dfRefPrice = dfRefPrice.loc[dfPrice.index.tolist()]
#     dfRefPrice['Signal'] = None
#     dfRefPrice.loc[dfRefPrice.index[0],'Signal'] = 'Buy'
#     dfRefAccount = intialAccount(dfRefPrice)
#     dfRefPrice, dfRefAccount = DoBacktesting(dfRefPrice, dfRefAccount)
#
#     dfAccuracy = pd.DataFrame(index=dfPrice[~dfPrice['Signal'].isnull()].index.tolist(), columns=['Signal', 'Price'])
#     dfAccuracy['Signal'] = dfAccount.loc[dfAccuracy.index,'Signal']
#     dfAccuracy['Price'] = dfPrice.loc[dfAccuracy.index,'Close']
#     # accuracy1 = GetAccuracy(dfAccuracy)
#     precision, recall, accuracy, fScore, dfScore = BF.GetScore(dfAccuracy)
#     costScore, dfCostScore = BF.CostScore(dfAccuracy)
#     dfAccuracy['Prec'] = None
#     dfAccuracy['Recall'] = None
#     dfAccuracy['Accuracy'] = None
#     dfAccuracy['FScore'] = None
#     dfAccuracy['AltCostScore'] = None
#     dfAccuracy.loc[dfAccuracy.index[0], 'Prec'] = precision
#     dfAccuracy.loc[dfAccuracy.index[0], 'Recall'] = recall
#     dfAccuracy.loc[dfAccuracy.index[0], 'Accuracy'] = accuracy
#     dfAccuracy.loc[dfAccuracy.index[0], 'FScore'] = fScore
#     dfAccuracy.loc[dfAccuracy.index[0], 'AltCostScore'] = costScore
#
#     dfRefAccuracy = pd.DataFrame(index=dfPrice[~dfPrice['Signal'].isnull()].index.tolist(), columns=['Signal', 'Price'])
#     dfRefAccuracy['Signal'] = 'Buy'
#     dfRefAccuracy['Price'] = dfPrice.loc[dfRefAccuracy.index,'Close']
#     # refAccuracy1 = GetAccuracy(dfRefAccuracy)
#     # refAccuracy, dfRefAccuracy = BF.Accuracy2(dfRefAccuracy)
#     refPrecision, refRecall, refAccuracy, refFScore, dfRefScore = BF.GetScore(dfRefAccuracy)
#     refCostScore, dfRefCostScore = BF.CostScore(dfRefAccuracy)
#     dfRefAccuracy['Prec'] = None
#     dfRefAccuracy['Recall'] = None
#     dfRefAccuracy['Accuracy'] = None
#     dfRefAccuracy['FScore'] = None
#     dfRefAccuracy['AltCostScore'] = None
#     dfRefAccuracy.loc[dfRefAccuracy.index[0], 'Prec'] = refPrecision
#     dfRefAccuracy.loc[dfRefAccuracy.index[0], 'Recall'] = refRecall
#     dfRefAccuracy.loc[dfRefAccuracy.index[0], 'Accuracy'] = refAccuracy
#     dfRefAccuracy.loc[dfRefAccuracy.index[0], 'FScore'] = refFScore
#     dfRefAccuracy.loc[dfRefAccuracy.index[0], 'AltCostScore'] = refCostScore
#
#     dfAccount.to_csv('./OECD/Backtesting/dfAccount_oecdValDiff_%s.csv'%(oecdValDiff),encoding='cp949')
#     dfRefAccount.to_csv('./OECD/Backtesting/dfRefAccount_oecdValDiff_%s.csv'%(oecdValDiff),encoding='cp949')
#
#     dfAccuracy.to_csv('./OECD/Backtesting/dfAccuracy_oecdValDiff_%s.csv'%(oecdValDiff),encoding='cp949')
#     dfRefAccuracy.to_csv('./OECD/Backtesting/dfRefAccuracy_oecdValDiff_%s.csv'%(oecdValDiff),encoding='cp949')
#     del dfAccount
#     del dfAccuracy
#     del dfRefAccount
#     del dfRefAccuracy

# import shutil
# def MoveFile(src, dst,fileKeyword,newFileName):
#     srcFiles = [f for f in listdir(src) if isfile(join(src, f))]  # folder내 파일name list
#     srcFile = [filename for filename in srcFiles if fileKeyword in filename]
#     for file in srcFile:
#         print('%s,'%file, end='')
#         sys.stdout.flush()
#         shutil.move(src+file, dst + newFileName)
#     return srcFile
# oecdValDiffs = []
# # file = open(r"C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Quanti\OECD\Backtesting\number.txt", "r")
# file = open(r"C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Quanti\OECD\Backtesting\number2.txt", "r")
# lines = file.readlines()
# for line in lines:
#     numbering = line.split()[0]
#     numbering = float(numbering)
#     oecdValDiffs.append(numbering)
# file.close()
# # oecdValDiffs = np.arange(-0.088, -0.4, -0.001)
# for oecdValDiff in oecdValDiffs:
#     # if oecdValDiff > -0.213:
#     #     continue
#     print('%s : '%round(oecdValDiff,4), end='')
#     sys.stdout.flush()
#     src = r'./OECD/Backtesting/'
#     fileKeyword0 = 'dfAccount_oecdValDiff_%s.csv' % (oecdValDiff)
#     fileKeyword1 = 'dfAccuracy_oecdValDiff_%s.csv' % (oecdValDiff)
#     fileKeyword2 = 'dfRefAccount_oecdValDiff_%s.csv' % (oecdValDiff)
#     fileKeyword3 = 'dfRefAccuracy_oecdValDiff_%s.csv' % (oecdValDiff)
#     dst = r'./OECD\Backtesting\-0.1_-0.3_-0.0001/'
#     newFileName0 = 'dfAccount_oecdValDiff_%s.csv' % (round(oecdValDiff, 4))
#     newFileName1 = 'dfAccuracy_oecdValDiff_%s.csv' % (round(oecdValDiff, 4))
#     newFileName2 = 'dfRefAccount_oecdValDiff_%s.csv' % (round(oecdValDiff, 4))
#     newFileName3 = 'dfRefAccuracy_oecdValDiff_%s.csv' % (round(oecdValDiff, 4))
#     MoveFile(src, dst, fileKeyword0, newFileName0)
#     MoveFile(src, dst, fileKeyword1, newFileName1)
#     MoveFile(src, dst, fileKeyword2, newFileName2)
#     MoveFile(src, dst, fileKeyword3, newFileName3)
#     print()

# import os.path
# numberings = np.arange(-0.0, -0.4, -0.001)
# for numbering in numberings:
#     numbering = round(numbering,3)
#
#     print('%s : ' % numbering, end='')
#     sys.stdout.flush()
#
#     src = r'./OECD\Backtesting\0~-0.399~-0.001/core/'
#     fileKeyword0 = 'dfAccount_oecdValDiff_%s.csv' % (numbering)
#     fileKeyword1 = 'dfAccuracy_oecdValDiff_%s.csv' % (numbering)
#     fileKeyword2 = 'dfRefAccount_oecdValDiff_%s.csv' % (numbering)
#     fileKeyword3 = 'dfRefAccuracy_oecdValDiff_%s.csv' % (numbering)
#     if not os.path.exists(src + fileKeyword0):
#         print('%s,' % fileKeyword0, end='')
#         sys.stdout.flush()
#     if not os.path.exists(src + fileKeyword1):
#         print('%s,' % fileKeyword1, end='')
#         sys.stdout.flush()
#     if not os.path.exists(src + fileKeyword2):
#         print('%s,' % fileKeyword2, end='')
#         sys.stdout.flush()
#     if not os.path.exists(src + fileKeyword3):
#         print('%s,' % fileKeyword3, end='')
#         sys.stdout.flush()
#     print()

import os.path
# make number
# read file
# number Prec Recall Accuracy FScore AltCostScore iniAsset finalAsset
numberings = np.arange(-0.0, -0.4, -0.001)
numberings = [round(numbering,3) for numbering in numberings]
dfSummery = pd.DataFrame(index=numberings,
                         columns=['Prec','Recall','Accuracy','FScore','AltCostScore','IniAsset','FinalAsset','CAGR','MDD'])
dfSummery.index.names = ['Number']

for numbering in numberings:
    dst = r'./OECD\Backtesting\0~-0.399~-0.001/'
    fileName = 'dfAccuracy_oecdValDiff_%s.csv'%(numbering)
    url = dst + fileName
    if not os.path.exists(url):
        continue
    fileName1 = 'dfAccount_oecdValDiff_%s.csv' % (numbering)
    url1 = dst + fileName1
    if not os.path.exists(url1):
        continue
    dfData = pd.read_csv(url)
    dfData1 = pd.read_csv(url1)
    dfSummery.loc[numbering, 'Prec'] = dfData.iloc[0]['Prec']
    dfSummery.loc[numbering, 'Recall'] = dfData.iloc[0]['Recall']
    dfSummery.loc[numbering, 'Accuracy'] = dfData.iloc[0]['Accuracy']
    dfSummery.loc[numbering, 'FScore'] = dfData.iloc[0]['FScore']
    dfSummery.loc[numbering, 'AltCostScore'] = dfData.iloc[0]['AltCostScore']
    dfSummery.loc[numbering, 'IniAsset'] = dfData1.iloc[0]['Asset']
    dfSummery.loc[numbering, 'FinalAsset'] = dfData1.iloc[-1]['Asset']
    dfSummery.loc[numbering, 'CAGR'] = dfData1.iloc[-1]['CAGR']
    dfSummery.loc[numbering, 'MDD'] = dfData1.iloc[-1]['MDD']
print()
dfSummery.to_csv(dst+'Summary.csv', encoding='cp949')