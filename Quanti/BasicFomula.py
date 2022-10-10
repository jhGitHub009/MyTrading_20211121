import numpy as np
import pandas as pd
import math
import datetime
import Quanti.MyLibrary_20180702
# get CAGR - Compound Annual Growth Rate 연복리 수익율
def GetCAGR(_initalAsset,_finalAsset,_times):
    cagr=(_finalAsset/_initalAsset)**(1/_times) - 1
    return cagr*100
def GetFinalAsset(_initalAsset,_cagr,_times):
    _cagr /= 100
    _finalAsset = (1+_cagr)**_times
    _finalAsset *= _initalAsset
    return _finalAsset
def GetInitalAsset(_finalAsset,_cagr,_times):
    _cagr /= 100
    _initalAsset = (1+_cagr)**_times
    _initalAsset = _finalAsset/_initalAsset
    return _initalAsset
def GetTimes(_initalAsset,_finalAsset,_cagr):
    _cagr /= 100
    _times = math.log10(_finalAsset) - math.log10(_initalAsset)
    _times /= math.log10(_cagr + 1)
    return _times
def GetMDD(_series):    # MDD는 이 방법을 사용할 것.
    _MDD = (_series.cummax()-_series)/_series.cummax()*100
    _MDD = _MDD.max()
    return _MDD
def GetMDD_df(_dataframe):    # MDD는 이 방법을 사용할 것.
    # _MDD = (_dataframe['High'].cummax() - _dataframe['Low']) / _dataframe['High'].cummax()*100
    _MDD = (_dataframe['Close'].cummax() - _dataframe['Close']) / _dataframe['Close'].cummax() * 100
    _MDD = _MDD.max()
    return _MDD
def GetMDDList(_List):
    _MDD = max(_List) - min(_List)
    _MDD /= max(_List)
    return _MDD*100
def RetirmentFunds(_AnnualSpend,_cagr,_inflationRate,_times):
    _cagr /= 100
    _inflationRate /= 100
    _RetireFund = _AnnualSpend * (1+_inflationRate)**_times
    _RetireFund /= (_cagr - _inflationRate)
    return _RetireFund
def GetSharp(_data,_depoInterest):
    interest = _data[-1] / _data[0] * 100
    excessInterest = interest - _depoInterest
    std = _data.std()
    sharp = excessInterest / std
    return sharp
def GetdfOneDay(_df,_thisDay):
    # 특정일만 모아놓은 df를 반환.
    dateList = pd.date_range(_df.index[0],_df.index[-1],freq='M')
    dateListThis = [datetime.datetime(thatDay.year,thatDay.month,_thisDay) for thatDay in dateList]
    oneDayList = [MyLib.nearest(_df.index, thisDay) for thisDay in dateListThis]
    return _df.loc[oneDayList]
def GetAvgMomentumValueScore(_df,_num,_colNameClose,_colNameMoM):
    # N개월동안 매달 몇%오르거나 내렸는가?! #
    _df = _df.iloc[::-1]
    _df[_colNameMoM] = np.NaN
    for idxloc, (idx, data) in enumerate(_df[:-_num].iterrows()):
        _df.loc[idx, _colNameMoM] = GetCAGR(_df.iloc[idxloc + _num][_colNameClose], data[_colNameClose], _num)
    _df = _df.iloc[::-1]
    _df = _df[_num:]
    return _df
def GetAvgMomentumScore(_df,_num,_colNameClose,_colNameMoM):
    # 현재 종가를 가지고 과거 12개월의 높낮이를 계산.
    # 과거 12개의 점수를 계산
    # 12로 나누어 평균 모멘텀을 계산.
    _df = _df.iloc[::-1]
    _df[_colNameMoM] = np.NaN
    for idxloc, (idx, data) in enumerate(_df.iterrows()):
        _dfTemp = data[_colNameClose] - _df.iloc[idxloc + 1:idxloc + _num + 1][_colNameClose]
        #현재 data- 과거 몇개의 data
        _df.loc[idx, _colNameMoM] = len(_dfTemp.loc[_dfTemp > 0])/_num*100
        # 위의 data중 양수인것들의 갯수/전체갯수
    _df = _df.iloc[::-1]
    _df = _df[_num:]
    return _df
def GetYear(startDay,endDay):
    if type(startDay)==str:
        startDay = datetime.datetime.strptime(startDay,'%Y-%m-%d')
    if type(endDay) == str:
        endDay = datetime.datetime.strptime(endDay, '%Y-%m-%d')
    period = endDay - startDay
    year = period.days / 365
    return year
def Accuracy(tradeSignal,BuySellPrice):
    if tradeSignal[0].lower=='sell':
        del tradeSignal[0]
        del BuySellPrice[0]
    if tradeSignal[-1].lower == 'buy':
        del tradeSignal[-1]
        del BuySellPrice[-1]
    score = 0
    total = 0
    buyPrices = BuySellPrice.tolist()[0::2]
    sellPrices = BuySellPrice.tolist()[1::2]
    for buy, sell in zip(buyPrices,sellPrices):
        if (sell-buy)>0:
            score+=1
        else:
            score-=1
        total+=1
    return score/total * 100, total
def GetScore(dfData):
    dfData['PTC_Price'] = (dfData['Price'].pct_change() * 100).shift(-1)
    dfData.dropna(inplace=True)
    # dfData['Score'] = None
    # dfData.loc[(dfData['Signal'] == 'Buy') & (dfData['PTC_Price'] >= 0),'Score'] = 'TP'   # TP
    # dfData.loc[(dfData['Signal'] == 'Buy') & (dfData['PTC_Price'] < 0),'Score'] = 'FP'   # FP
    # dfData.loc[(dfData['Signal'] == 'Sell') & (dfData['PTC_Price'] > 0),'Score'] = 'FN'  # FN
    # dfData.loc[(dfData['Signal'] == 'Sell') & (dfData['PTC_Price'] <= 0),'Score'] = 'FP'  # FP
    TP = ((dfData['Signal'] == 'Buy') & (dfData['PTC_Price'] >= 0)).sum()
    FP = ((dfData['Signal'] == 'Buy') & (dfData['PTC_Price'] < 0)).sum()
    FN = ((dfData['Signal'] == 'Sell') & (dfData['PTC_Price'] > 0)).sum()
    TN = ((dfData['Signal'] == 'Sell') & (dfData['PTC_Price'] <= 0)).sum()

    # precision =  (dfData['Score'] == 'TP').sum()/((dfData['Score'] == 'TP').sum()+(dfData['Score'] == 'FP').sum())*100
    # recall = (dfData['Score'] == 'TP').sum() / ((dfData['Score'] == 'TP').sum() + (dfData['Score'] == 'FP').sum()) * 100
    # accuracy = ((dfData['Score'] == 'TP').sum()+(dfData['Score'] == 'TN').sum()) / len(dfData) * 100
    precision = TP / (TP + FP) * 100
    recall = TP / (TP + FN) * 100
    accuracy = (TP+TN) / len(dfData) * 100
    fScore = 2 / ((1 / recall) + (1 / precision))
    return precision,recall,accuracy, fScore, dfData
# def Recall(dfData):
#     dfData['PTC_Price'] = (dfData['Price'].pct_change() * 100).shift(-1)
#     dfData.dropna(inplace=True)
#     dfData['Score'] = 0
#     dfData.loc[(dfData['Signal'] == 'Buy') & (dfData['PTC_Price'] >= 0), 'Score'] = 'TP'  # TP
#     # dfData.loc[(dfData['Signal'] == 'Buy') & (dfData['PTC_Price'] < 0),'Score'] = 'FP'   # FP
#     dfData.loc[(dfData['Signal'] == 'Sell') & (dfData['PTC_Price'] > 0),'Score'] = 'FN'  # FN
#     # dfData.loc[(dfData['Signal'] == 'Sell') & (dfData['PTC_Price'] <= 0), 'Score'] = 'FP'  # FP
#     return recall, dfData
def CostScore(dfData):
    dfData['PTC_Price'] = (dfData['Price'].pct_change() * 100).shift(-1)
    dfData.dropna(inplace=True)
    dfData['Score'] = 0
    dfData.loc[(dfData['Signal'] == 'Buy') & (dfData['PTC_Price'] >= 0), 'Score'] = +1  # TP value +10
    dfData.loc[(dfData['Signal'] == 'Buy') & (dfData['PTC_Price'] < 0),'Score'] = -1   # FP value -10
    dfData.loc[(dfData['Signal'] == 'Sell') & (dfData['PTC_Price'] > 0),'Score'] = -1  # FN value +10
    dfData.loc[(dfData['Signal'] == 'Sell') & (dfData['PTC_Price'] <= 0), 'Score'] = +1  # FP   value -10
    dfData['CostScore'] = dfData['Score']*abs(dfData['PTC_Price'])
    CostScore = dfData['CostScore'].sum()/abs(dfData['CostScore']).sum()*100
    return CostScore, dfData
if __name__ == '__main__':
    years = GetYear('2006-01-01', '2006-02-01')
    CAGR_All = GetCAGR(294.6, 248.2, years)
    CAGR_Seoul = GetCAGR(521.3, 1412.3, years)
    CAGR_Gyongi = GetCAGR(308.7, 640.9, years)
    years2 = GetYear('2006-01-01', '2020-01-01')
    CAGR_All2 = GetCAGR(294.6, 474.1, years)
    CAGR_Seoul2 = GetCAGR(521.3, 1011.5, years)
    CAGR_Gyongi2 = GetCAGR(308.7, 500.3, years)

    Expect_All      = GetFinalAsset(_initalAsset=294.6, _cagr=CAGR_All2, _times=years)
    Expect_Seoul2   = GetFinalAsset(_initalAsset=521.3, _cagr=CAGR_Seoul2, _times=years)
    Expect_Gyongi2  = GetFinalAsset(_initalAsset=308.7, _cagr=CAGR_Gyongi2, _times=years)
    # test = GetFinalAsset(3, 20, 10)
    # test = GetInitalAsset(18.57, 20, 10)
    # test = GetTimes(3, 18.57, 20)
    data = pd.read_csv('./Stock_dataKiwoom/index/201_KOSPI200.csv',encoding='cp949',engine='python')
    # test = GetAvgMomentumScore(data,12,'Close','Close_AvgMoM')
    test = GetMDD(data['Close'])
    test = GetMDD_df(data)
    # test = RetirmentFunds(_AnnualSpend = 500*12, _cagr=15, _inflationRate=5, _times=40)
    test = GetYear('2008-01-01','2018-09-01')
    test = GetCAGR(1000000, 15404267.79, 44)
    print(test)