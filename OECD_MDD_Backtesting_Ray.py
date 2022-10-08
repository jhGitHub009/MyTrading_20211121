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
import math

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
    dfRefData['DrawUp'] = None
    dfRefData['DrawDown'] = None
    dfRefData['Signal'] = 0
    startIdx = dfRefData.index[0]
    thisStatus = 'Hold'

    for idx in dfRefData.index:
        if thisStatus=='Hold':
            drawUp = GetDrawUp(dfRefData.loc[startIdx:idx]['Value'])  # 무릎만큼 올라가면.
            drawDown = GetDrawDown(dfRefData.loc[startIdx:idx]['Value'])  # 어깨만큼 내려가면.
        elif thisStatus == 'Buy':
            drawUp = 0.0
            drawDown = GetDrawDown(dfRefData.loc[startIdx:idx]['Value'])  # 어깨만큼 내려가면.
        elif thisStatus == 'Sell':
            drawUp = GetDrawUp(dfRefData.loc[startIdx:idx]['Value'])  # 무릎만큼 올라가면.
            drawDown = 0.0
        dfRefData.loc[idx, 'DrawUp'] = drawUp
        dfRefData.loc[idx, 'DrawDown'] = drawDown

        if drawUp > knee:
            if thisStatus=='Sell':
                startIdx = idx
            thisStatus = 'Buy'
            dfRefData.loc[idx, 'Signal'] = thisStatus
        elif drawDown < shoulder:
            if thisStatus == 'Buy':
                startIdx = idx
            thisStatus = 'Sell'
            dfRefData.loc[idx, 'Signal'] = thisStatus
        else:
            dfRefData.loc[idx, 'Signal'] = thisStatus

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
# @ray.remote(num_cpus = 1, num_gpus = 1)
@ray.remote(num_cpus = 1)
def func2(dfPrice,OECDURL,OECDLoc,shoulder,knee,saveFolder,saveRawFolder):
    start = timer()
    # print("ray.get_gpu_ids(): {}".format(ray.get_gpu_ids()))
    # print(os.environ["CUDA_VISIBLE_DEVICES"])
    print('------- knee : %s, shoulder : %s ' % (knee, shoulder), end='')
    sys.stdout.flush()
    dfPrice = GetSignal(dfPrice, OECDURL=OECDURL, OECDLoc=OECDLoc, shoulder=shoulder, knee=knee)
    dfAccount = intialAccount(dfPrice)
    dfPrice, dfAccount = DoBacktesting(dfPrice, dfAccount)

    dfAccuracy = pd.DataFrame(index=dfPrice[~dfPrice['Signal'].isnull()].index.tolist(),
                                      columns=['Signal', 'Price'])
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
    # return summaryTemp
    print(",func_OneLoop : %s"%(timer() - start))
    return summaryTemp
def func2Normal(dfPrice,OECDURL,OECDLoc,shoulder,knee,saveFolder,saveRawFolder):
    start = timer()
    # print("ray.get_gpu_ids(): {}".format(ray.get_gpu_ids()))
    # print(os.environ["CUDA_VISIBLE_DEVICES"])
    print('------- knee : %s, shoulder : %s ' % (knee, shoulder), end='')
    sys.stdout.flush()
    dfPrice = GetSignal(dfPrice, OECDURL=OECDURL, OECDLoc=OECDLoc, shoulder=shoulder, knee=knee)
    dfAccount = intialAccount(dfPrice)
    dfPrice, dfAccount = DoBacktesting(dfPrice, dfAccount)

    dfAccuracy = pd.DataFrame(index=dfPrice[~dfPrice['Signal'].isnull()].index.tolist(),
                                      columns=['Signal', 'Price'])
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
    # return summaryTemp
    print(",func_OneLoop : %s"%(timer() - start))
    return summaryTemp
# @ray.remote(num_cpus=1, num_gpus=1, max_calls=1)
@ray.remote(num_cpus = 1, num_gpus = 1)
def func_GPU(dfPrice,OECDURL,OECDLoc,shoulders,knees,saveFolder,saveRawFolder,summary):
    for shoulder in shoulders:
        for knee in knees:
            start = timer()
            # print("ray.get_gpu_ids(): {}".format(ray.get_gpu_ids()))
            # print(os.environ["CUDA_VISIBLE_DEVICES"])
            print('------- knee : %s, shoulder : %s ' % (knee, shoulder), end='')
            sys.stdout.flush()
            dfPrice = GetSignal(dfPrice, OECDURL=OECDURL, OECDLoc=OECDLoc, shoulder=shoulder, knee=knee)
            dfAccount = intialAccount(dfPrice)
            dfPrice, dfAccount = DoBacktesting(dfPrice, dfAccount)

            dfAccuracy = pd.DataFrame(index=dfPrice[~dfPrice['Signal'].isnull()].index.tolist(),
                                              columns=['Signal', 'Price'])
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
            # summaryTemp = pd.DataFrame(
            #     columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
            #              'FinalAsset', 'CAGR', 'MDD'])
            idxSum = len(summary)
            summary.loc[idxSum, 'Knee'] = knee
            summary.loc[idxSum, 'Shoulder'] = shoulder
            summary.loc[idxSum, 'Prec'] = precision
            summary.loc[idxSum, 'Recall'] = recall
            summary.loc[idxSum, 'Accuracy'] = accuracy
            summary.loc[idxSum, 'FScore'] = fScore
            summary.loc[idxSum, 'AltCostScore'] = costScore
            summary.loc[idxSum, 'IniAsset'] = dfAccount.iloc[0]['Asset']
            summary.loc[idxSum, 'FinalAsset'] = dfAccount.iloc[-1]['Asset']
            summary.loc[idxSum, 'CAGR'] = dfAccount.iloc[-1]['CAGR']
            summary.loc[idxSum, 'MDD'] = dfAccount.iloc[-1]['MDD']

            summary.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
            dfAccount.to_csv(saveRawFolder + '\dfAccount_Knee%s_Shoulder%s.csv' % (knee, shoulder), encoding='cp949')
            dfAccuracy.to_csv(saveRawFolder + '\dfAccuracy_Knee%s_Shoulder%s.csv' % (knee, shoulder), encoding='cp949')
            del dfAccount
            del dfAccuracy
            # return summaryTemp
            print(",func_OneLoop : %s"%(timer() - start))
    return summary
@ray.remote(num_cpus = 1, num_gpus = 0.15)
def funcDistribution(dfPrice,OECDURL,OECDLoc,listKneeShoulders,saveFolder,saveRawFolder):
    summary = pd.DataFrame(
        columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
                 'FinalAsset', 'CAGR', 'MDD'])
    for shoulder, knee in listKneeShoulders:
        start = timer()
        # print("ray.get_gpu_ids(): {}".format(ray.get_gpu_ids()))
        # print(os.environ["CUDA_VISIBLE_DEVICES"])
        print('------- knee : %s, shoulder : %s ' % (knee, shoulder), end='')
        sys.stdout.flush()
        dfPrice = GetSignal(dfPrice, OECDURL=OECDURL, OECDLoc=OECDLoc, shoulder=shoulder, knee=knee)
        dfAccount = intialAccount(dfPrice)
        dfPrice, dfAccount = DoBacktesting(dfPrice, dfAccount)
        dfAccuracy = pd.DataFrame(index=dfPrice[~dfPrice['Signal'].isnull()].index.tolist(),
                                          columns=['Signal', 'Price'])
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
        # summaryTemp = pd.DataFrame(
        #     columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
        #              'FinalAsset', 'CAGR', 'MDD'])
        idxSum = len(summary)
        summary.loc[idxSum, 'Knee'] = knee
        summary.loc[idxSum, 'Shoulder'] = shoulder
        summary.loc[idxSum, 'Prec'] = precision
        summary.loc[idxSum, 'Recall'] = recall
        summary.loc[idxSum, 'Accuracy'] = accuracy
        summary.loc[idxSum, 'FScore'] = fScore
        summary.loc[idxSum, 'AltCostScore'] = costScore
        summary.loc[idxSum, 'IniAsset'] = dfAccount.iloc[0]['Asset']
        summary.loc[idxSum, 'FinalAsset'] = dfAccount.iloc[-1]['Asset']
        summary.loc[idxSum, 'CAGR'] = dfAccount.iloc[-1]['CAGR']
        summary.loc[idxSum, 'MDD'] = dfAccount.iloc[-1]['MDD']
        summary.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
        dfAccount.to_csv(saveRawFolder + '\dfAccount_Knee%s_Shoulder%s.csv' % (knee, shoulder), encoding='cp949')
        dfAccuracy.to_csv(saveRawFolder + '\dfAccuracy_Knee%s_Shoulder%s.csv' % (knee, shoulder), encoding='cp949')
        del dfAccount
        del dfAccuracy
        # return summaryTemp
        print(",func_OneLoop : %s"%(timer() - start))
    return summary
# @ray.remote(num_cpus=0.8, num_gpus=0.12, max_calls=1)
@ray.remote(num_cpus=5, num_gpus=0.8, max_calls=1)
def func3(dfPrice,OECDURL,OECDLoc,shoulders,knees,saveFolder,saveRawFolder,summary):
    for shoulder in shoulders:
        start = timer()
        for knee in knees:
            # print("ray.get_gpu_ids(): {}".format(ray.get_gpu_ids()))
            # print(os.environ["CUDA_VISIBLE_DEVICES"])
            print('------- knee : %s, shoulder : %s -------' % (knee, shoulder))
            dfPrice = GetSignal(dfPrice, OECDURL=OECDURL, OECDLoc=OECDLoc, shoulder=shoulder, knee=knee)
            dfAccount = intialAccount(dfPrice)
            dfPrice, dfAccount = DoBacktesting(dfPrice, dfAccount)

            dfAccuracy = pd.DataFrame(index=dfPrice[~dfPrice['Signal'].isnull()].index.tolist(),
                                              columns=['Signal', 'Price'])
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
            # summaryTemp = pd.DataFrame(
            #     columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
            #              'FinalAsset', 'CAGR', 'MDD'])
            idxSum = len(summary)
            summary.loc[idxSum, 'Knee'] = knee
            summary.loc[idxSum, 'Shoulder'] = shoulder
            summary.loc[idxSum, 'Prec'] = precision
            summary.loc[idxSum, 'Recall'] = recall
            summary.loc[idxSum, 'Accuracy'] = accuracy
            summary.loc[idxSum, 'FScore'] = fScore
            summary.loc[idxSum, 'AltCostScore'] = costScore
            summary.loc[idxSum, 'IniAsset'] = dfAccount.iloc[0]['Asset']
            summary.loc[idxSum, 'FinalAsset'] = dfAccount.iloc[-1]['Asset']
            summary.loc[idxSum, 'CAGR'] = dfAccount.iloc[-1]['CAGR']
            summary.loc[idxSum, 'MDD'] = dfAccount.iloc[-1]['MDD']

            summary.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
            dfAccount.to_csv(saveRawFolder + '\dfAccount_Knee%s_Shoulder%s.csv' % (knee, shoulder), encoding='cp949')
            dfAccuracy.to_csv(saveRawFolder + '\dfAccuracy_Knee%s_Shoulder%s.csv' % (knee, shoulder), encoding='cp949')
            del dfAccount
            del dfAccuracy
        print("without GPU:", timer() - start)
    return summary
# #####################################################################
# #                           Do Backtesting                      #
# #####################################################################
# priceFolder = r'D:\PycharmProjects_220926\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index'
# keywordPrice = 'Kospi'
# OECDURL = r'./Quanti\OECD\Data\OECD_CLI_2022-07-31.csv'
# OECDLoc = 'KOR'
# saveFolder = './Quanti\OECD\Backtesting\OECDKneeSholder\%s'%(keywordPrice)
# shoulders = np.arange(-0.02, -2.02, -0.02)
# knees = np.arange(0.02, 2.02, 0.02)
#
# dfPrice = MyLib.ReadStockData2(priceFolder, keywordPrice)
# knees = [round(knee, 2) for knee in knees]
# shoulders = [round(shoulder, 2) for shoulder in shoulders]
# summary = pd.DataFrame(columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
#                                 'FinalAsset', 'CAGR', 'MDD'])
# saveRawFolder = saveFolder + '\Raw'
# if not isdir(saveRawFolder):
#     makedirs(saveRawFolder)
# # ray.init(num_cpus = 10000, num_gpus=10000)
# ray.init(num_cpus = 5, num_gpus=1)
# for shoulder in shoulders:
#     start = timer()
#     futures = [func2.remote(dfPrice, OECDURL, OECDLoc, shoulder, knee, saveFolder, saveRawFolder) for knee in knees]
#     ret = ray.get(futures)
#     for tempSummary in ret:
#         summary = summary.append(tempSummary)
#     summary.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
#     print("without GPU:", timer() - start)
#     del ret

# #####################################################################
# #                           Do Backtesting                      #
# #####################################################################
# priceFolder = r'D:\PycharmProjects_220926\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index'
# keywordPrice = 'Euro'
# OECDURL = r'./Quanti\OECD\Data\OECD_CLI_2022-07-31.csv'
# OECDLoc = 'EA19'
# saveFolder = './Quanti\OECD\Backtesting\OECDKneeSholder\%s'%(keywordPrice)
# # shoulders = np.arange(-1.62, -2.0, -0.02)
# shoulders = np.arange(-0.02, -2.02, -0.02)
# knees = np.arange(0.02, 2.02, 0.02)
# nCPU = 5
#
# dfPrice = MyLib.ReadStockData2(priceFolder, keywordPrice)
# knees = [round(knee, 2) for knee in knees]
# shoulders = [round(shoulder, 2) for shoulder in shoulders]
# summary = pd.DataFrame(columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
#                                 'FinalAsset', 'CAGR', 'MDD'])
# saveRawFolder = saveFolder + '\Raw'
# if not isdir(saveRawFolder):
#     makedirs(saveRawFolder)
# ray.init(num_cpus = nCPU, num_gpus = 1)
# # ray.init()
# nTotalActor = len(shoulders)*len(knees)
# nOneTimeActors = math.ceil(nTotalActor / nCPU)
# i = 0
# listKneeAndShoulders = []
# temp = []
# for shoulder in shoulders:
#     for knee in knees:
#         temp.append((shoulder, knee))
#         i += 1
#         if i == nOneTimeActors:
#             listKneeAndShoulders.append(temp)
#             temp = []
#             i = 0
# if temp:
#     listKneeAndShoulders.append(temp)
# start = timer()
# futures = [funcDistribution.remote(dfPrice, OECDURL, OECDLoc, listKneeAndShoulder, saveFolder, saveRawFolder) for listKneeAndShoulder in listKneeAndShoulders]
# ret = ray.get(futures)
# print("funcDistribution:", timer() - start)
#####################################################################
#                           Do Backtesting                      #
#####################################################################
priceFolder = r'D:\PycharmProjects_220926\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index'
keywordPrice = 'Euro'
OECDURL = r'./Quanti\OECD\Data\OECD_CLI_2022-07-31.csv'
OECDLoc = 'EA19'
saveFolder = './Quanti\OECD\Backtesting\OECDKneeSholder\%s'%(keywordPrice)
shoulders = np.arange(-0.02, -2.02, -0.02)
knees = np.arange(0.02, 2.02, 0.02)
nCPU = 5
dfPrice = MyLib.ReadStockData2(priceFolder, keywordPrice)
knees = [round(knee, 2) for knee in knees]
shoulders = [round(shoulder, 2) for shoulder in shoulders]
summary = pd.DataFrame(columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
                                'FinalAsset', 'CAGR', 'MDD'])
saveRawFolder = saveFolder + '\Raw'
if not isdir(saveRawFolder):
    makedirs(saveRawFolder)
# ray.init(num_cpus = 10000, num_gpus=10000)
ray.init(num_cpus = 5)
i = 0
futures = []
for shoulder in shoulders:
    for knee in knees:
        knee = 0.06
        shoulder = -0.02
        func2Normal(dfPrice, OECDURL, OECDLoc, shoulder, knee, saveFolder, saveRawFolder)
        if i < nCPU:
            futures.append(func2.remote(dfPrice, OECDURL, OECDLoc, shoulder, knee, saveFolder, saveRawFolder))
            i+=1
        else:
            ret = ray.get(futures)
            for tempSummary in ret:
                summary = summary.append(tempSummary)
            summary.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
            del ret
            i = 0
            futures = []
ray.shutdown()
# #####################################################################
# #                           Do Backtesting                      #
# #####################################################################
# priceFolder = r'D:\PycharmProjects_220926\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index'
# keywordPrice = 'Kospi'
# OECDURL = r'./Quanti\OECD\Data\OECD_CLI_2022-07-31.csv'
# OECDLoc = 'KOR'
# saveFolder = './Quanti\OECD\Backtesting\OECDKneeSholder\%s'%(keywordPrice)
# shoulders = np.arange(-1.62, -2.0, -0.02)
# knees = np.arange(0.02, 2.0, 0.02)
#
# dfPrice = MyLib.ReadStockData2(priceFolder, keywordPrice)
# knees = [round(knee, 2) for knee in knees]
# shoulders = [round(shoulder, 2) for shoulder in shoulders]
# summary = pd.DataFrame(columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
#                                 'FinalAsset', 'CAGR', 'MDD'])
# saveRawFolder = saveFolder + '\Raw'
# if not isdir(saveRawFolder):
#     makedirs(saveRawFolder)
# # ray.init(num_cpus = 10000, num_gpus=10000)
# ray.init()
# func2.remote(dfPrice, OECDURL, OECDLoc, shoulders, knees, saveFolder, saveRawFolder, summary)
# for shoulder in shoulders:
#     start = timer()
#     futures = [func2.remote(dfPrice, OECDURL, OECDLoc, shoulder, knee, saveFolder, saveRawFolder) for knee in knees]
#     ret = ray.get(futures)
#     for tempSummary in ret:
#         summary = summary.append(tempSummary)
#     summary.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
#     print("without GPU:", timer() - start)
#     del ret

# #####################################################################
# #                           Do Backtesting                      #
# #####################################################################
# priceFolder = r'D:\PycharmProjects_220926\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index'
# keywordPrice = 'Nikkei'
# OECDURL = r'./Quanti\OECD\Data\OECD_CLI_2022-07-31.csv'
# OECDLoc = 'JAP'
# saveFolder = './Quanti\OECD\Backtesting\OECDKneeSholder\%s'%(keywordPrice)
# shoulders = np.arange(-0.02, -2.0, -0.02)
# knees = np.arange(0.02, 2.0, 0.02)
#
# dfPrice = MyLib.ReadStockData2(priceFolder, keywordPrice)
# knees = [round(knee, 2) for knee in knees]
# shoulders = [round(shoulder, 2) for shoulder in shoulders]
# summary = pd.DataFrame(columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
#                                 'FinalAsset', 'CAGR', 'MDD'])
# saveRawFolder = saveFolder + '\Raw'
# if not isdir(saveRawFolder):
#     makedirs(saveRawFolder)
# ray.init()
# for shoulder in shoulders:
#     start = timer()
#     futures = [func2.remote(dfPrice, OECDURL, OECDLoc, shoulder, knee, saveFolder, saveRawFolder) for knee in knees]
#     ret = ray.get(futures)
#     for tempSummary in ret:
#         summary = summary.append(tempSummary)
#     summary.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
#     print("without GPU:", timer() - start)
#     del ret
# #####################################################################
# #                           Do Backtesting                      #
# #####################################################################
# priceFolder = r'D:\PycharmProjects_220926\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index'
# keywordPrice = 'Euro'
# OECDURL = r'./Quanti\OECD\Data\OECD_CLI_2022-07-31.csv'
# OECDLoc = 'EA19'
# saveFolder = './Quanti\OECD\Backtesting\OECDKneeSholder\%s'%(keywordPrice)
# shoulders = np.arange(-0.02, -2.0, -0.02)
# knees = np.arange(0.02, 2.0, 0.02)
#
# dfPrice = MyLib.ReadStockData2(priceFolder, keywordPrice)
# knees = [round(knee, 2) for knee in knees]
# shoulders = [round(shoulder, 2) for shoulder in shoulders]
# summary = pd.DataFrame(columns=['Knee', 'Shoulder', 'Prec', 'Recall', 'Accuracy', 'FScore', 'AltCostScore', 'IniAsset',
#                                 'FinalAsset', 'CAGR', 'MDD'])
# saveRawFolder = saveFolder + '\Raw'
# if not isdir(saveRawFolder):
#     makedirs(saveRawFolder)
# ray.init()
# for shoulder in shoulders:
#     start = timer()
#     futures = [func2.remote(dfPrice, OECDURL, OECDLoc, shoulder, knee, saveFolder, saveRawFolder) for knee in knees]
#     ret = ray.get(futures)
#     for tempSummary in ret:
#         summary = summary.append(tempSummary)
#     summary.to_csv(saveFolder + '\SummaryOECDKneeShoulder.csv', encoding='cp949', mode='w')
#     print("without GPU:", timer() - start)
#     del ret