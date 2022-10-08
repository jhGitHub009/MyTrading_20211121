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

def GetDrawDown(_series):
    _DrawDown = (_series - _series.cummax())/_series.cummax()*100
    return _DrawDown.iloc[-1]
def GetDrawUp(_series):
    _DrawUp = (_series - _series.cummin())/_series.cummin()*100
    return _DrawUp.iloc[-1]
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
def GetSignal(dfPrice):
    # dfRefData = pd.read_csv(r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Quanti\OECD\Data\OECD_CLI_2022-07-31.csv')
    dfRefData = pd.read_csv(r'C:\Users\jhmai\PycharmProjects\QuantiBook_20181215\OECD\OECD_CLI.csv')
    dfRefData = dfRefData[dfRefData['LOCATION'] == 'USA']
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
def DoBacktesting(dfPrice, dfAccount, portion):
    for date, data in dfPrice.iterrows():
        if data['Signal'] == 'Buy':
            # print('Buy')
            idxDate = dfAccount.index.get_loc(date)
            cash = dfAccount.iloc[idxDate - 1]['Cash']
            stock = dfAccount.iloc[idxDate - 1]['Stock']
            thisDayOpen = data['Open']
            thisAsset = Rebal.GetNowValue(cash, [thisDayOpen], stock)
            diffStock, newStock = Rebal.Rebalancing5(thisAsset, [thisDayOpen], stock, [portion])

            dfAccount.loc[date, 'Cash'] = int(Rebal.TradeStock(cash, [thisDayOpen], diffStock))
            dfAccount.loc[date, 'Stock'] = newStock
            dfAccount.loc[date, 'Asset'] = Rebal.GetNowValue(cash, [thisDayOpen], stock)
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
            diffStock, newStock = Rebal.Rebalancing5(thisAsset, [thisDayOpen], stock, [int(100 - portion)
                                                                                       ])

            dfAccount.loc[date, 'Cash'] = int(Rebal.TradeStock(cash, [thisDayOpen], diffStock))
            dfAccount.loc[date, 'Stock'] = newStock
            dfAccount.loc[date, 'Asset'] = Rebal.GetNowValue(cash, [thisDayOpen], stock)
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
#####################################################################
#                           Do Backtesting                      #
#####################################################################
# dfPrice = MyLib.ReadStockData2(r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Stock_data\index', '803')
dfPrice = MyLib.ReadStockData2(r'C:\Users\jhmai\PycharmProjects\QuantiBook_20181215\Stock_dataKiwoom3\etf\Index', 'Nasdaq')
# dfPrice = dfPrice.loc[dfPrice.index>='2002-01-01']
portions = np.arange(20, 110, 10)
portions = [round(portion,0) for portion in portions]
summary = pd.DataFrame(columns=['Portion','Prec','Recall','Accuracy','FScore','AltCostScore','IniAsset',
                                'FinalAsset','CAGR','MDD'])
# for knee in knees:
#     for shoulder in shoulders:
for portion in portions:
    print('%s --------------------'%(portion))
    dfPrice = GetSignal(dfPrice)
    dfAccount = intialAccount(dfPrice)
    dfPrice, dfAccount = DoBacktesting(dfPrice, dfAccount, portion)

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
    summary.loc[idxSum, 'Portion'] = portion
    summary.loc[idxSum, 'Prec'] = precision
    summary.loc[idxSum, 'Recall'] = recall
    summary.loc[idxSum, 'Accuracy'] = accuracy
    summary.loc[idxSum, 'FScore'] = fScore
    summary.loc[idxSum, 'AltCostScore'] = costScore
    summary.loc[idxSum, 'IniAsset'] = dfAccount.iloc[0]['Asset']
    summary.loc[idxSum, 'FinalAsset'] = dfAccount.iloc[-1]['Asset']
    summary.loc[idxSum, 'CAGR'] = dfAccount.iloc[-1]['CAGR']
    summary.loc[idxSum, 'MDD'] = dfAccount.iloc[-1]['MDD']
    summary.to_csv('./OECD/Backtesting/OECDPortion\SummaryOECDPortion.csv', encoding='cp949',mode='w')
    dfAccount.to_csv('./OECD\Backtesting\OECDPortion\Raw\dfAccount_Portion%s.csv'%(portion),encoding='cp949')
    dfAccuracy.to_csv('./OECD\Backtesting\OECDPortion\Raw\dfAccuracy_Portion%s.csv'%(portion),encoding='cp949')
    del dfAccount
    del dfAccuracy
# del summary