
import pandas as pd
import datetime
import Quanti.MyLibrary_20180702 as MyLib
import Quanti.BasicFomula as BF
import Rebalancing as Rebal
from os import listdir,makedirs
from os.path import isfile, join, isdir, basename
import sys
import numpy as np
import copy

# 오른달이 많으면 +, 내린달이 많으면 -
def GetSignal(dfPrice, avgNumMonth = 6, threshold = 0):
    # dfMPrice = copy.deepcopy(dfPrice)
    dfMPrice = MyLib.MakePeriodData2(dfPrice)
    dfRefData = BF.GetAvgMomentumScore(dfMPrice, avgNumMonth, 'Close', 'AvgMoM')

    dfRefData['TradeDate'] = [MyLib.AfterNearest(dfPrice.index, dfRefData.index[i]) for i in range(1,len(dfRefData-1),1)] + [None]
    dfRefData.dropna(inplace=True)
    dfRefData['Signal'] = None
    dfRefData.loc[dfRefData['AvgMoM']>= threshold,'Signal'] = 'Buy'
    dfRefData.loc[dfRefData['AvgMoM']< threshold,'Signal'] = 'Sell'

    dfPrice['Signal'] = None
    dfPrice.loc[dfRefData['TradeDate'], 'Signal'] = dfRefData['Signal'].tolist()
    # dfPrice['AvgMoM'] = None
    # dfPrice.loc[dfRefData['TradeDate'], 'AvgMoM'] = dfRefData['AvgMoM'].tolist()
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

#####################################################################
#                           Do Backtesting                      #
#####################################################################
priceFolder = r'C:\Users\jhmai\PycharmProjects\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index'
# keywordPrice = 'S&P'
keywordPrice = 'Nasdaq'
saveFolder = './AvgMoM\Backtesting\AvgMoM_Thresold2\%s'%(keywordPrice)
avgNumMonths = [2,3,4,5,6,7,8,9,10,11,12]

dfPrice = MyLib.ReadStockData2(priceFolder, keywordPrice)

summary = pd.DataFrame(columns=['NumMonth','PosNumMonth','AvgMoM','Prec','Recall','Accuracy','FScore','AltCostScore',
                                'IniAsset', 'FinalAsset','CAGR','MDD'])
saveRawFolder = saveFolder + '\Raw'
if not isdir(saveRawFolder):
    makedirs(saveRawFolder)

for avgNumMonth in avgNumMonths:
    threStep = 100 / avgNumMonth
    thresolds = np.arange(0-threStep, 100+threStep, threStep) + (threStep/2)
    thresolds = [round(thresold, 2) for thresold in thresolds]

    for idx,thresold in enumerate(thresolds):
        print('AvgMoM : %s --------------------'%(thresold))
        dfPrice = GetSignal(dfPrice, avgNumMonth = avgNumMonth, threshold = thresold)
        dfAccount = intialAccount(dfPrice)
        dfPrice, dfAccount = DoBacktesting(dfPrice, dfAccount)

        dfAccuracy = pd.DataFrame(index=dfPrice[~dfPrice['Signal'].isnull()].index.tolist(), columns=['Signal', 'Price'])
        dfAccuracy['Signal'] = dfAccount.loc[dfAccuracy.index,'Signal']
        dfAccuracy['Price'] = dfPrice.loc[dfAccuracy.index,'Close']
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

        idxSum = len(summary)
        summary.loc[idxSum, 'NumMonth'] = avgNumMonth
        summary.loc[idxSum, 'PosNumMonth'] = idx
        summary.loc[idxSum, 'AvgMoM'] = thresold
        summary.loc[idxSum, 'Prec'] = precision
        summary.loc[idxSum, 'Recall'] = recall
        summary.loc[idxSum, 'Accuracy'] = accuracy
        summary.loc[idxSum, 'FScore'] = fScore
        summary.loc[idxSum, 'AltCostScore'] = costScore
        summary.loc[idxSum, 'IniAsset'] = dfAccount.iloc[0]['Asset']
        summary.loc[idxSum, 'FinalAsset'] = dfAccount.iloc[-1]['Asset']
        summary.loc[idxSum, 'CAGR'] = dfAccount.iloc[-1]['CAGR']
        summary.loc[idxSum, 'MDD'] = dfAccount.iloc[-1]['MDD']

        summary.to_csv(saveFolder + '\SummaryAvgMoMThreshold.csv', encoding='cp949',mode='w')
        dfAccount.to_csv(saveRawFolder + '\dfAccount_NumMonth%s_Threshold%s.csv'%(avgNumMonth,thresold),encoding='cp949')
        dfAccuracy.to_csv(saveRawFolder + '\dfAccuracy_NumMonth%s_Threshold%s.csv'%(avgNumMonth,thresold),encoding='cp949')
        del dfPrice['Signal']
        del dfAccount
        del dfAccuracy
    # del summary