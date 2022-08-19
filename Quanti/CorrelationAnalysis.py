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
# 신호 데이터 만들기.
# Price데이터에 신호 데이터를 넣기.
# 신호데이터를 가공 해서 매수, 매도 데이터를 정확한 날짜에 넣는다.
def ChangeFormat(stock_folder,code):
    stockfiles = [f for f in listdir(stock_folder) if isfile(join(stock_folder, f))]  # folder내 파일name list
    stockfile = [filename for filename in stockfiles if code in filename]
    if len(stockfile) != 1:
        return False
    df_stock = pd.read_csv(stock_folder + '/' + stockfile[0],  engine='python')
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
    df_stock.to_csv(stock_folder+'/'+stockfile[0], encoding='cp949')
    df_stock.rename(columns={'Price': 'Close'}, inplace=True)
    return df_stock
# ChangeFormat(r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Stock_data\index', '801')

dfRefData = pd.read_csv(r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Quanti\OECD\Data\OECD_CLI_2022-07-31.csv')
dfRefData = dfRefData[dfRefData['LOCATION']=='USA']
dfRefData['PCT'] = dfRefData['Value'].pct_change() * 100
dfRefData['TIME'] = pd.to_datetime(dfRefData['TIME'])
dfRefData['ReleaseDate'] = pd.to_datetime(dfRefData['TIME']) + datetime.timedelta(days=45)

price = MyLib.ReadStockData2(r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Stock_data\index', '801')
if dfRefData.iloc[0]['ReleaseDate'] > price.index[0]:
    startDate = dfRefData.iloc[0]['TIME']
else:
    startDate = price.index[0]

if dfRefData.iloc[-1]['ReleaseDate'] > price.index[-1]:
    endDate = price.index[-1]
else:
    endDate = dfRefData.iloc[-1]['TIME']
dfRefData = dfRefData[dfRefData['ReleaseDate']>=startDate]
dfRefData = dfRefData[dfRefData['ReleaseDate']<=endDate]
price = price[price.index>=startDate]
price = price[price.index<=endDate]
dfRefData['TradeDate'] = [MyLib.AfterNearest(price.index, dfRefData.iloc[i]['ReleaseDate']) for i in range(len(dfRefData))]
dfRefData['Signal'] = None
dfRefData.loc[dfRefData['PCT']>=0,'Signal'] = 'Buy'
dfRefData.loc[dfRefData['PCT']<0,'Signal'] = 'Sell'

price['Signal'] = None
price.loc[dfRefData['TradeDate'],'Signal'] = dfRefData['Signal'].tolist()
idxAccount = price.index.tolist()
idxAccount.insert(0,price.index[0]-datetime.timedelta(days=1))
dfAccount = pd.DataFrame(index=idxAccount, columns=['Cash', 'Stock', 'Asset', 'Signal','CAGR','MDD','Accuracy','Precision'])
dfAccount.iloc[0]['Cash'] = 1000000
dfAccount.iloc[0]['Stock'] = [0]
dfAccount.iloc[0]['Asset'] = 1000000
dfAccount.iloc[0]['Signal'] = None
dfAccount.iloc[0]['CAGR'] = 0
dfAccount.iloc[0]['MDD'] = 0
dfAccount.iloc[0]['Accuracy'] = 0
dfAccount.iloc[0]['Precision'] = 0

dfRefAccount = pd.DataFrame(index=idxAccount, columns=['Cash', 'Stock', 'Asset', 'Signal','CAGR','MDD','Accuracy','Precision'])
dfRefAccount.iloc[0]['Cash'] = 1000000
dfRefAccount.iloc[0]['Stock'] = [0]
dfRefAccount.iloc[0]['Asset'] = 1000000
dfRefAccount.iloc[0]['Signal'] = None
dfRefAccount.iloc[0]['CAGR'] = 0
dfRefAccount.iloc[0]['MDD'] = 0
dfRefAccount.iloc[0]['Accuracy'] = 0
dfRefAccount.iloc[0]['Precision'] = 0

for date, data in price.iterrows():
    if dfRefAccount.index[1]==date:
        print('Buy Ref')
        idxDate = dfRefAccount.index.get_loc(date)
        cash = dfRefAccount.iloc[idxDate - 1]['Cash']
        stock = dfRefAccount.iloc[idxDate - 1]['Stock']
        thisDayOpen = data['Open']
        thisAsset = Rebal.GetNowValue(cash, [thisDayOpen], stock)
        diffStock, newStock = Rebal.Rebalancing5(thisAsset, [thisDayOpen], stock, [100])

        dfRefAccount.loc[date, 'Cash'] = int(Rebal.TradeStock(cash, [thisDayOpen], diffStock))
        dfRefAccount.loc[date, 'Stock'] = newStock
        dfRefAccount.loc[date, 'Asset'] = thisAsset
        dfRefAccount.loc[date, 'Signal'] = 'Buy'
        dfRefAccount.loc[date, 'CAGR'] = BF.GetCAGR(dfRefAccount.iloc[0]['Asset'], thisAsset,
                                                 BF.GetYear(dfRefAccount.index[0], date))
        dfRefAccount.loc[date, 'MDD'] = BF.GetMDD(dfRefAccount.loc[dfRefAccount.index[0]:date, 'Asset'])
    else:
        idxDate = dfRefAccount.index.get_loc(date)
        cash = dfRefAccount.iloc[idxDate - 1]['Cash']
        stock = dfRefAccount.iloc[idxDate - 1]['Stock']
        thisDayClose = data['Close']
        thisAsset = Rebal.GetNowValue(cash, [thisDayClose], stock)
        dfRefAccount.loc[date, 'Cash'] = cash
        dfRefAccount.loc[date, 'Stock'] = stock
        dfRefAccount.loc[date, 'Asset'] = thisAsset
        dfRefAccount.loc[date, 'Signal'] = 'Hold'
        dfRefAccount.loc[date, 'CAGR'] = BF.GetCAGR(dfRefAccount.iloc[0]['Asset'], thisAsset,
                                                 BF.GetYear(dfRefAccount.index[0], date))
        dfRefAccount.loc[date, 'MDD'] = BF.GetMDD(dfRefAccount.loc[dfRefAccount.index[0]:date, 'Asset'])
    if data['Signal']=='Buy':
        print('Buy')
        idxDate = dfAccount.index.get_loc(date)
        cash = dfAccount.iloc[idxDate - 1]['Cash']
        stock = dfAccount.iloc[idxDate - 1]['Stock']
        thisDayOpen = data['Open']
        thisAsset = Rebal.GetNowValue(cash, [thisDayOpen], stock)
        diffStock, newStock = Rebal.Rebalancing5(thisAsset, [thisDayOpen], stock, [100])

        dfAccount.loc[date,'Cash'] = int(Rebal.TradeStock(cash, [thisDayOpen], diffStock))
        dfAccount.loc[date,'Stock'] = newStock
        dfAccount.loc[date,'Asset'] = thisAsset
        dfAccount.loc[date,'Signal'] = 'Buy'
        dfAccount.loc[date, 'CAGR'] = BF.GetCAGR(dfAccount.iloc[0]['Asset'], thisAsset,
                                                 BF.GetYear(dfAccount.index[0], date))
        dfAccount.loc[date, 'MDD'] = BF.GetMDD(dfAccount.loc[dfAccount.index[0]:date, 'Asset'])

    elif data['Signal']=='Sell':
        print('Sell')
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
        print('Hold')
        # print('Calc')
        # print('TotalValue')
        # print('CAGR')
        # print('MDD')
        # print('Acc')
        # print('Precision')
        idxDate = dfAccount.index.get_loc(date)
        cash = dfAccount.iloc[idxDate - 1]['Cash']
        stock = dfAccount.iloc[idxDate - 1]['Stock']
        thisDayClose = data['Close']
        thisAsset = Rebal.GetNowValue(cash, [thisDayClose], stock)
        dfAccount.loc[date, 'Cash'] = cash
        dfAccount.loc[date, 'Stock'] = stock
        dfAccount.loc[date, 'Asset'] = thisAsset
        dfAccount.loc[date, 'Signal'] = 'Hold'
        dfAccount.loc[date, 'CAGR'] = BF.GetCAGR(dfAccount.iloc[0]['Asset'], thisAsset,BF.GetYear(dfAccount.index[0], date))
        dfAccount.loc[date, 'MDD'] = BF.GetMDD(dfAccount.loc[dfAccount.index[0]:date, 'Asset'])

    # dfAccount.loc[date, 'Accuracy'] = 0
    # dfAccount.loc[date, 'Precision'] = 0
print()
dfAccuracy = pd.DataFrame(index=dfRefData['TradeDate'].tolist(), columns=['Signal', 'Price'])
dfAccuracy['Signal'] = dfAccount.loc[dfAccuracy.index,'Signal']
dfAccuracy['Price'] = price.loc[dfAccuracy.index,'Close']
accuracy, dfAccuracy = BF.Accuracy2(dfAccuracy)

dfRefAccuracy = pd.DataFrame(index=dfRefData['TradeDate'].tolist(), columns=['Signal', 'Price'])
dfRefAccuracy['Signal'] = 'Buy'
dfRefAccuracy['Price'] = price.loc[dfRefAccuracy.index,'Close']
refAccuracy, dfRefAccuracy = BF.Accuracy2(dfRefAccuracy)
dfAccount.to_csv('./dfAccount.csv',encoding='cp949')