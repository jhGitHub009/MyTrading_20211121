import pandas as pd
from os import listdir,makedirs
from os.path import isfile, join,isdir
import datetime
import sys
import Quanti.MyLibrary_20180702 as MyLib

def GetPERDebitRatio(thisDay,stockFolder,financeFolder):
    financeFiles = [f for f in listdir(financeFolder) if isfile(join(financeFolder, f))]
    dfFinance = pd.DataFrame(columns=['Code','Company','MarketCapitalization','Close','PER','PBR','PCR','PSR'])
    for financeFile in financeFiles:
        company = financeFile.replace('.csv', '').split('_')[0]
        code = financeFile.replace('.csv', '').split('_')[1]
        if '-' in thisDay:
            thisDayDt = datetime.datetime.strptime(thisDay, '%Y-%m-%d')
            thisYear = thisDayDt.year
        else:
            thisDayDt = datetime.datetime.strptime(thisDay, '%Y%m%d')
            thisYear = thisDayDt.year
        try:
            if code == '058860':
                print()
            closePrice = float(MyLib.GetClosePrice(thisDay, stockFolder, code))
            stockNum = MyLib.GetData(r'./NaverAnalysis\%s\기업현황'%(thisDayDt.strftime('%Y%m%d')), code, '발행주식수(보통주)', str(thisYear-1))
            marketCapitalization = closePrice * stockNum
            EPS = MyLib.GetData(financeFolder, code, 'EPS', str(thisYear-1))
            PER = closePrice / EPS
            BPS = MyLib.GetData(financeFolder, code, 'BPS', str(thisYear-1))
            PBR = closePrice / BPS
            CPS = MyLib.GetData(financeFolder, code, 'CPS', str(thisYear-1))
            PCR = closePrice / CPS
            SPS = MyLib.GetData(financeFolder, code, 'SPS', str(thisYear-1))
            PSR = closePrice / SPS

            dfFinance.loc[len(dfFinance)] = [code,company,marketCapitalization,closePrice,PER,PBR,PCR,PSR]
        except:
            print('%s_%s no data!!'%(code,company))
            continue
    print('Finish!')
    return dfFinance
def GetPERDebitRatioFiltered(thisDay,filename,field):
    # import os
    # thisFolder = os.path.dirname(os.path.abspath(__file__))
    if '-' in thisDay:
        thisDayDt = datetime.datetime.strptime(thisDay, '%Y-%m-%d')
    else:
        thisDayDt = datetime.datetime.strptime(thisDay, '%Y%m%d')
    financeFolder = r'./NaverAnalysis\%s\투자지표\가치분석'%(thisDayDt.strftime('%Y%m%d'))
    stockFolder = './Stock_data/20210502/%s'%(field)
    dfFinance = GetPERDebitRatio(thisDay, stockFolder, financeFolder)
    dfFinance = dfFinance.sort_values(by=['MarketCapitalization'], ascending=True, na_position='last')
    smallCapStocks = int(len(dfFinance) * 0.2)
    dfFinance = dfFinance.iloc[:smallCapStocks]
    dfFinance = dfFinance.loc[dfFinance['PER'] > 0]
    dfFinance = dfFinance.loc[dfFinance['PBR'] > 0]
    dfFinance = dfFinance.loc[dfFinance['PCR'] > 0]
    dfFinance = dfFinance.loc[dfFinance['PSR'] > 0]
    dfFinanceRanked = MyLib.MakeRank(dfFinance, ['PER','PBR','PCR','PSR'], [True,True,True,True])
    dfFinanceRanked.reset_index(drop=True, inplace=True)
    if len(dfFinanceRanked) > 20:
        dfFinanceRanked = dfFinanceRanked.iloc[:20].copy()
    return dfFinanceRanked
def GetPERDebitRatio2(thisDay,stockFolder,financeFolder):
    financeFolderStockNum = financeFolder + r'\기업현황'
    financeFolderValue = financeFolder + r'\투자지표\가치분석'
    financeFiles = [f for f in listdir(financeFolderValue) if isfile(join(financeFolderValue, f))]
    dfFinance = pd.DataFrame(columns=['Code','Company','MarketCapitalization','Close','EPS','PER','BPS','PBR','CPS','PCR','SPS','PSR'])
    for financeFile in financeFiles:
        company = financeFile.replace('.csv', '').split('_')[0]
        code = financeFile.replace('.csv', '').split('_')[1]
        if '-' in thisDay:
            thisDayDt = datetime.datetime.strptime(thisDay, '%Y-%m-%d')
            thisYear = thisDayDt.year
        else:
            thisDayDt = datetime.datetime.strptime(thisDay, '%Y%m%d')
            thisYear = thisDayDt.year
        try:
            closePrice = float(MyLib.GetClosePrice(thisDay, stockFolder, code))
            stockNum = MyLib.GetData(financeFolderStockNum, code, '발행주식수(보통주)', str(thisYear-1))
            marketCapitalization = closePrice * stockNum
            EPS = MyLib.GetData(financeFolderValue, code, 'EPS', str(thisYear-1))
            PER = closePrice / EPS
            BPS = MyLib.GetData(financeFolderValue, code, 'BPS', str(thisYear-1))
            PBR = closePrice / BPS
            CPS = MyLib.GetData(financeFolderValue, code, 'CPS', str(thisYear-1))
            PCR = closePrice / CPS
            SPS = MyLib.GetData(financeFolderValue, code, 'SPS', str(thisYear-1))
            PSR = closePrice / SPS

            dfFinance.loc[len(dfFinance)] = [code,company,marketCapitalization,closePrice,EPS,PER,BPS,PBR,CPS,PCR,SPS,PSR]
        except:
            print('%s_%s no data!!'%(code,company))
            continue
    print('Finish!')
    return dfFinance
def GetPERDebitRatioFiltered2(thisDay, priceFolder, financeFolder):
    dfFinance = GetPERDebitRatio2(thisDay, priceFolder, financeFolder)
    dfFinance = dfFinance.sort_values(by=['MarketCapitalization'], ascending=True, na_position='last')
    smallCapStocks = int(len(dfFinance) * 0.2)
    dfFinance = dfFinance.iloc[:smallCapStocks]
    dfFinance = dfFinance.loc[dfFinance['PER'] > 0]
    dfFinance = dfFinance.loc[dfFinance['PBR'] > 0]
    dfFinance = dfFinance.loc[dfFinance['PCR'] > 0]
    dfFinance = dfFinance.loc[dfFinance['PSR'] > 0]
    dfFinanceRanked = MyLib.MakeRank(dfFinance, ['PER','PBR','PCR','PSR'], [True,True,True,True])
    dfFinanceRanked.reset_index(drop=True, inplace=True)
    if len(dfFinanceRanked) > 20:
        dfFinanceRanked = dfFinanceRanked.iloc[:20].copy()
    return dfFinanceRanked
def RunPERPBRPCRPSR(thisDayStr,filename,field):
    # combo box - field str 참조.
    if '-' not in thisDayStr:
        thisDayDt = datetime.datetime.strptime(thisDayStr, '%Y%m%d')
    else:
        thisDayDt = datetime.datetime.strptime(thisDayStr, '%Y-%m-%d')
    thisDayStr = thisDayDt.strftime('%Y-%m-%d')
    thisDayStr2 = thisDayDt.strftime('%Y%m%d')
    save_folder = './Result/%s/' % (thisDayStr)
    if not isdir(save_folder): makedirs(save_folder)
    print('============================================ PBR PBR PCR PSR ============================================')
    df_PERPBRRanked = GetPERDebitRatioFiltered(thisDayStr,filename,field)
    df_PERPBRRanked.to_csv(save_folder +'PERPBRPCRPSR_%s.csv' % (thisDayStr2), encoding='cp949', index=False)
    print('RunPERPBRPCRPSR Finish!!')
if __name__ == '__main__':
    # RunPERPBRPCRPSR('2019-03-29')
    thisDay = datetime.date.today().strftime('%Y-%m-%d')
    priceFolder = r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Stock_data\20220517\kospi'
    financeFolder = r'C:\Users\jhmai\PycharmProjects\MyTrading_20211121\Infomation\Naver\20220511\Kospi'
    test = GetPERDebitRatioFiltered2(thisDay, priceFolder, financeFolder)
    print()