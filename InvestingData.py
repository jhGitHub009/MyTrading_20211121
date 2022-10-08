import sys
from os import listdir,makedirs
from os.path import isfile, join, isdir
import pandas as pd

def MergeData(fileURL1, fileURL2, SaveURL):
    print('(%s and %s) will be merged on %s...' % (fileURL1.split('\\')[-1], fileURL2.split('\\')[-1], SaveURL), end='')
    sys.stdout.flush()
    dfData1 = pd.read_csv(fileURL1)
    dfData2 = pd.read_csv(fileURL2)
    dfMergedData = dfData1.append(dfData2)
    dfMergedData = dfMergedData[['날짜', '오픈', '종가', '고가', '저가']]
    dfMergedData.columns = ['Date', 'Open', 'Close', 'High', 'Low']
    dfMergedData.drop_duplicates(subset=['Date'], inplace=True)
    dfMergedData.sort_values(by='Date', ascending=True, inplace=True)
    # dfMergedData['Date'] = dfMergedData['Date'].dt.strftime('%Y-%m-%d')
    dfMergedData.to_csv(SaveURL, encoding='cp949', index=False)
    print('...Done!!!')
    return dfMergedData
def ChangeNumber(fileURL, SaveURL):
    dfData = pd.read_csv(fileURL)
    for col in dfData.columns[1:]:
        dfData[col] = pd.to_numeric(dfData[col].str.replace(',',''))
    dfData.to_csv(SaveURL, encoding='cp949', index=False)
def ChangseFormat(fileURL, SaveURL):
    try:
        dfData = pd.read_csv(fileURL)
        dfData = dfData[['날짜', '오픈', '종가', '고가', '저가']]
        dfData.columns = ['Date', 'Open', 'Close', 'High', 'Low']
        dfData.drop_duplicates(subset=['Date'], inplace=True)
        # dfData['Date'] = pd.to_datetime(arg=dfData['Date'], format='%Y년 %m월 %d일')
        dfData.sort_values(by='Date', ascending=True, inplace=True)
        # dfData['Date'] = dfData['Date'].dt.strftime('%Y-%m-%d')
        dfData.to_csv(SaveURL, encoding='cp949', index=False)
    except:
        dfData = pd.read_csv(fileURL, engine='python')
        dfData.columns = ['Date', 'Close', 'Open', 'High', 'Low', 'Volume', 'Change %']
        dfData = dfData[['Date', 'Open', 'Close', 'High', 'Low', 'Volume']]
        dfData['Date'] = pd.to_datetime(arg=dfData['Date'], format='%Y�뀈 %m�썡 %d�씪')
        dfData.sort_values(by='Date', ascending=True, inplace=True)
        dfData.drop_duplicates(subset=['Date'], inplace=True)
        dfData['Date'] = dfData['Date'].dt.strftime('%Y-%m-%d')
        dfData.to_csv(SaveURL, encoding='cp949', index=False)

if __name__ == '__main__':
    stockFolder1 = r'D:\PycharmProjects_220926\MyTrading_20211121\Infomation\Investing\20220511\StockData_USA\Historical_Data\Index'
    fileURL = join(stockFolder1, 'Nasdaq.csv')
    ChangeNumber(fileURL, fileURL)

    stockFolder1 = r'D:\PycharmProjects_220926\MyTrading_20211121\Infomation\Investing\20220511\StockData_USA\Historical_Data\Index'
    fileURL = join(stockFolder1, '유로 스톡스 50 내역.csv')
    ChangseFormat(fileURL, fileURL)

    stockFolder1 = r'D:\PycharmProjects_220926\MyTrading_20211121\Infomation\Investing\20220511\StockData_USA\Historical_Data\Index'
    stockFolder2 = r'D:\PycharmProjects_220926\MyTrading_20211121\Infomation\Investing\20220511\StockData_USA\Historical_Data\Index\20191001~'
    stockfiles1 = [f for f in listdir(stockFolder1) if isfile(join(stockFolder1, f))]  # folder내 파일name list
    stockfiles1 = [filename for filename in stockfiles1 if '코스닥 내역' in filename]
    stockfiles2 = [f for f in listdir(stockFolder2) if isfile(join(stockFolder2, f))]  # folder내 파일name list
    for stockfile1 in stockfiles1:
        stockfile2 = [filename for filename in stockfiles2 if stockfile1.replace('.csv','') in filename]
        for stock2 in stockfile2:
            fileURL1 = join(stockFolder1, stockfile1)
            fileURL2 = join(stockFolder2, stock2)
            MergeData(fileURL1, fileURL2, fileURL1)