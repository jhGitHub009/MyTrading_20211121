# from mplfinance import candlestick2_ohlc
# from mplfinance.original_flavor import candlestick_ohlc, candlestick2_ohlc
import mplfinance as mpf
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import datetime
import pandas as pd
import MyLibrary_20180702 as MyLib
import numpy as np
import Rebalancing
from os.path import isfile, join, isdir
from os import listdir, makedirs
import BasicFomula
def Main(code,company, dayforBollinger=20, rangeforBollinger=2):
    # # read stock data.
    price = MyLib.ReadStockData2(r'../Infomation\Stock_data\20220517\kospi',code)
    price.index.name = 'Date'
    # dayforBollinger = 20
    # rangeforBollinger = 2

    datelist = price.index.tolist()
    dfMyAsset = pd.DataFrame(index=datelist, columns=['Cash','Stock','Asset','Signal','PortfolioRatio',
                                                                          'Close','BolinUpper','BolinLower','BuyPrice','SellPrice'])
    dfMyAsset.iloc[dayforBollinger-1] = [1000000,0,0,'hold',0,0,0,0, np.nan, np.nan]
    yesterday = datelist[dayforBollinger-1]
    for today in datelist[dayforBollinger:]:
        todayPrice = price[:today]
        # calculating asset and trade
        if dfMyAsset.loc[yesterday,'Signal'] != 'hold':
            totalValue = Rebalancing.GetNowValue(dfMyAsset.loc[yesterday, 'Cash'], [todayPrice.loc[today, 'Open']],
                                                 [dfMyAsset.loc[yesterday, 'Stock']])
            diffStockNum, thisStockNum = Rebalancing.Rebalancing5(totalValue, [todayPrice.loc[today,'Open']],
                                                [dfMyAsset.loc[yesterday, 'Stock']], portfolioRatio=[dfMyAsset.loc[yesterday, 'PortfolioRatio']])
            balance = Rebalancing.TradeStock(dfMyAsset.loc[yesterday,'Cash'], [todayPrice.loc[today,'Open']], diffStockNum)

            dfMyAsset.loc[today, 'Cash'] = balance
            dfMyAsset.loc[today, 'Stock'] = thisStockNum[0]
            totalValue = Rebalancing.GetNowValue(dfMyAsset.loc[today, 'Cash'], [todayPrice.loc[today, 'Close']],
                                                 [dfMyAsset.loc[today, 'Stock']])
            dfMyAsset.loc[today, 'Asset'] = totalValue
            if diffStockNum[0] > 0:
                dfMyAsset.loc[today, 'BuyPrice'] = todayPrice.loc[today, 'Open'] + (todayPrice.loc[today, 'Open'] * 0.5/100)
            else:
                dfMyAsset.loc[today, 'SellPrice'] = todayPrice.loc[today, 'Open'] + (todayPrice.loc[today, 'Open'] * 0.5/100)
        else:
            dfMyAsset.loc[today, 'Cash'] = dfMyAsset.loc[yesterday, 'Cash']
            dfMyAsset.loc[today, 'Stock'] = dfMyAsset.loc[yesterday, 'Stock']
            totalValue = Rebalancing.GetNowValue(dfMyAsset.loc[today, 'Cash'], [todayPrice.loc[today, 'Close']],
                                                 [dfMyAsset.loc[today, 'Stock']])
            dfMyAsset.loc[today, 'Asset'] = totalValue
        # calculation for bollinger band
        ma20 = todayPrice['Close'].rolling(window=dayforBollinger).mean()
        todayPrice.loc[:,'BolinUpper'] = ma20 + rangeforBollinger * todayPrice['Close'].rolling(window=dayforBollinger).std()
        todayPrice.loc[:,'BolinLower'] = ma20 - rangeforBollinger * todayPrice['Close'].rolling(window=dayforBollinger).std()
        bol_upper = ma20 + rangeforBollinger * todayPrice['Close'].rolling(window=dayforBollinger).std()
        bol_down = ma20 - rangeforBollinger * todayPrice['Close'].rolling(window=dayforBollinger).std()
        #get signal
        if todayPrice.iloc[-1]['Close'] <= bol_down[-1] and dfMyAsset.loc[today, 'Stock']== 0:
            # buy stock
            dfMyAsset.loc[today, 'Signal'] = 'buy'
            dfMyAsset.loc[today, 'PortfolioRatio'] = 100
            yesterday = today
        elif todayPrice.iloc[-1]['Close'] >= bol_upper[-1] and dfMyAsset.loc[today, 'Stock']!= 0 :
            # sell stock
            dfMyAsset.loc[today, 'Signal'] = 'sell'
            dfMyAsset.loc[today, 'PortfolioRatio'] = 0
            yesterday = today
        else:
            # hold
            dfMyAsset.loc[today, 'Signal'] = 'hold'
            dfMyAsset.loc[today, 'PortfolioRatio'] = 0
            yesterday = today
        # additional info for debug
        dfMyAsset.loc[today, 'Close'] = todayPrice.iloc[-1]['Close']
        dfMyAsset.loc[today, 'BolinUpper'] = bol_upper[-1]
        dfMyAsset.loc[today, 'BolinLower'] = bol_down[-1]
    apds = [ mpf.make_addplot(todayPrice[['BolinUpper','BolinLower']]),
             mpf.make_addplot(dfMyAsset[['BuyPrice']],type='scatter',markersize=50,marker='^'),
             mpf.make_addplot(dfMyAsset[['SellPrice']],type='scatter',markersize=50,marker='v'),
           ]
    folder = r'./Bollinger_test/%s_%s' % (company, code)
    if not isdir(folder): makedirs(folder)
    mpf.plot(price,type='candle', savefig=dict(fname= folder + r'/%s_day%s.png'%(code, dayforBollinger), dpi=100) ,
             addplot=apds,volume=True,show_nontrading=False)
    # mpf.plot(df, volume=True, savefig=dict(fname= folder + r'/%s.png'%(code), dpi=100))
    # make folder and save
    # plt.savefig(fname= folder + r'/%s.png'%(code), dpi=500, format='png')

    return dfMyAsset
# read stock code
stockCode = pd.read_csv(r'../Infomation\StockCode\20220511\kospi_20220511.csv',encoding='cp949')
totalInfo = pd.DataFrame(columns=['Code','Company','FinalAsset','Period','MDD','CAGR','CAGR/MDD','Accuracy','Count of Invest'])
dayforBollingers = [20, 60, 120, 240]
rangeforBollinger = 2
for dayforBollinger in dayforBollingers:
    totalInfo.drop(totalInfo.index, inplace=True)
    for idx, row in stockCode.iterrows():
        try:
            print('------------  %s  ------------  %s  ------------'%(row['종목명'],row['종목코드']))
            dfMyAsset = Main(row['종목코드'],row['종목명'], dayforBollinger, rangeforBollinger)
            dfMyAsset.dropna(inplace=True,how='all', axis=0)
            dfMyAsset = dfMyAsset[1:]
            finalAsset = dfMyAsset.iloc[-1]['Asset']
            times = BasicFomula.GetYear(dfMyAsset.index[0], dfMyAsset.index[-1])
            mdd = BasicFomula.GetMDD(dfMyAsset['Asset'])
            cagr = BasicFomula.GetCAGR(dfMyAsset.iloc[0]['Asset'], dfMyAsset.iloc[-1]['Asset'], times)

            dfMyAssetForAcc = pd.DataFrame(columns=['Signal', 'Price'])
            dfMyAssetForAcc['Signal'] = dfMyAsset[dfMyAsset.Signal != 'hold'].Signal
            dfMyAssetForAcc.loc[dfMyAssetForAcc['Signal'] == 'buy', 'Price'] = dfMyAsset.loc[
                dfMyAsset['BuyPrice'].notnull(), 'BuyPrice'].tolist()
            dfMyAssetForAcc.loc[dfMyAssetForAcc['Signal'] == 'sell', 'Price'] = dfMyAsset.loc[
                dfMyAsset['SellPrice'].notnull(), 'SellPrice'].tolist()
            accuracy, cntInvest = BasicFomula.Accuracy(dfMyAssetForAcc['Signal'], dfMyAssetForAcc['Price'])
            finalAsset = round(finalAsset,0)
            times=round(times,3)
            mdd=round(mdd,3)
            cagr=round(cagr,3)
            accuracy=round(accuracy,3)

            print('Final Asset: %s' % (finalAsset))
            print('Final Period: %s' % (times))
            print('Final MDD: %s' % (mdd))
            print('Final CAGR: %s' % (cagr))
            print('Final Accuracy: %s' % (accuracy))
            print('Total Invest: %s' % (cntInvest))
            print('------------------------------------------------')

            dfMyAsset.to_csv(fr"./Bollinger_test/{row['종목명']}_{row['종목코드']}/{row['종목코드']}_day{dayforBollinger}.csv", encoding='cp949')
            totalInfo.loc[len(totalInfo)]=[row['종목코드'],row['종목명'],finalAsset,times,mdd,cagr,round(cagr/mdd,3),accuracy, cntInvest]
            totalInfo.to_csv(r'./Bollinger_test/totalInfo_day%s.csv'%(dayforBollinger),encoding='cp949',mode='w')
        except:
            continue
