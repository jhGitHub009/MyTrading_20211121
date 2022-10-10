import pandas as pd
from os import listdir
from os.path import isfile, join
import datetime
import sys
from PyQt5.QtWidgets import QMessageBox
def GetClosePrice(thisDay,stockFolder,code):
    stockFiles = [f for f in listdir(stockFolder) if isfile(join(stockFolder, f))]  # folder내 파일name list
    stockFile = [filename for filename in stockFiles if code in filename][0]
    dfStock = pd.read_csv(stockFolder + '/' +stockFile, encoding='cp949',engine='python')
    dfStock['Date'] = pd.to_datetime(dfStock['Date'])
    if '-' in thisDay:
        thisDay = datetime.datetime.strptime(thisDay, '%Y-%m-%d')
    else:
        thisDay = datetime.datetime.strptime(thisDay, '%Y%m%d')
    nowDay = nearest(dfStock['Date'], thisDay)
    # diffDays = nowDay - thisDay
    # if 14 < abs(diffDays.days):
    #     price = dfStock.loc[dfStock['Date'] == thisDay, 'Close'].iloc[0]
    price = dfStock.loc[dfStock['Date'] == nowDay, 'Close'].iloc[0]
    return price
def showdialog(title,message,infoText):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setInformativeText(infoText)
    # msg.setDetailedText("The details are as follows:")
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    retval = msg.exec_()
    # print("value of pressed message box button:", retval)
    return retval
def GetData(folder,code,item,date):
    files = [f for f in listdir(folder) if isfile(join(folder, f))]  # folder내 파일name list
    file = [filename for filename in files if code in filename]
    # if len(file) != 1:
    #     sys.stdout.flush()
    #     return False
    df_data = pd.read_csv(folder + '/' + file[0], encoding='cp949',engine='python')
    df_data.dropna(axis=1, inplace=True, how='all')
    df_data.dropna(axis=0, inplace=True, how='all')
    df_data.set_index(keys=df_data.columns[0], inplace=True)
    item = [index for index in df_data.index if item in index][0]
    col_name = [col for col in df_data.columns if (date in col) and ('E' not in col)][0]
    data = df_data.loc[item, col_name]
    stop_words=[',','억','원','/','%']
    if isinstance(data,str):
        for stop_word in stop_words:
            if stop_word in data:
                data = data.replace(stop_word,'')
        data = float(data)
    return data
def GetDate(date,type='Year'):
    date_Dt = datetime.datetime.strptime(date,'%Y-%m-%d')
    if type=='Year':
        if date_Dt.month < 5:
            lastYear = date_Dt - datetime.timedelta(days=365*2)
            yearBefore = lastYear - datetime.timedelta(days=365)
        elif date_Dt.month >= 5:
            lastYear = date_Dt - datetime.timedelta(days=365)
            yearBefore = lastYear - datetime.timedelta(days=365)

        lastYearDate = str(lastYear.year) + '/12'
        yearBeforeDate = str(yearBefore.year) + '/12'
        return [lastYearDate, yearBeforeDate]
    elif type=='Quater':
        if date_Dt.month < 5:
            lastyear = date_Dt - datetime.timedelta(days=365)
            quaterBeforeDate = str(lastyear.year) + '/09'
            lastQuaterDate = str(lastyear.year) + '/12'
        elif date_Dt.month >= 5 and date_Dt.month < 8:
            lastyear = date_Dt - datetime.timedelta(days=365)
            quaterBeforeDate = str(lastyear.year) + '/12'
            lastQuaterDate = str(lastyear.year) + '/03'
        elif date_Dt.month >= 8 and date_Dt.month < 11:
            quaterBeforeDate = str(date_Dt.year) + '/03'
            lastQuaterDate = str(date_Dt.year) + '/06'
        else:
            quaterBeforeDate = str(date_Dt.year) + '/06'
            lastQuaterDate = str(date_Dt.year) + '/09'
        return [lastQuaterDate,quaterBeforeDate]
def ReadStockData(code):
    stock_folder = './Stock_data/total/'
    stockfiles = [f for f in listdir(stock_folder) if isfile(join(stock_folder, f))]  # folder내 파일name list
    stockfile = [filename for filename in stockfiles if code in filename]
    if len(stockfile) != 1:
        return False
    df_stock = pd.read_csv(stock_folder + stockfile[0], encoding='cp949')
    df_stock.drop_duplicates(subset=['Date'],keep='first',inplace=True)
    df_stock['Date'] = pd.to_datetime(df_stock['Date'])
    df_stock.sort_values(by='Date', ascending=True, inplace=True)
    # for idx_stock, row_stock in df_stock.iterrows():
    #     df_stock.loc[idx_stock, 'Date'] = datetime.datetime.strptime(row_stock['Date'], '%Y-%m-%d')
    df_stock.set_index(keys='Date', inplace=True)
    return df_stock
def nearest(items, pivot):
    return min(items, key=lambda x: abs(x - pivot))
def MakeRank(df_summery,indicators,ascendings):
    df_summery['Rank'] = 0
    for indicator,ascend in zip(indicators,ascendings):
        df_summery[indicator+'_Rank'] = df_summery[indicator].rank(ascending=ascend)
        df_summery['Rank'] += df_summery[indicator+'_Rank']
    df_summery = df_summery.sort_values(by=['Rank'], ascending=True, na_position='last')
    return df_summery
def GetCodeFile(thisDayDt,field):
    if thisDayDt==datetime.date(2000,1,1):
        codeFolder = './StockCode/'
        codeFiles = [f for f in listdir(codeFolder) if isfile(join(codeFolder, f))]  # folder내 파일name list
        codeFiles = [codeFile for codeFile in codeFiles if field in codeFile]
        codeFiles.sort()
        codefile = codeFiles[-1]
        thisDayStr = codefile.split('_')[1].split('.')[0]
        thisDayStr2 = datetime.datetime.strptime(thisDayStr,'%Y%m%d').strftime('%Y-%m-%d')
        filename = codefile
    else:
        thisDayStr = datetime.datetime.strftime(thisDayDt, '%Y%m%d')
        thisDayStr2 = datetime.datetime.strftime(thisDayDt, '%Y-%m-%d')
        filename = '%s_%s.csv' % (field,thisDayStr)
    return thisDayStr,thisDayStr2,filename
def GetMissedCode(srcList,dstList):
    missedCode = [items for items in srcList if not items in dstList]
    return missedCode