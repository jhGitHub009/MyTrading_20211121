import pandas as pd
from os import listdir,makedirs
from os.path import isfile, join, isdir
import datetime,time
from selenium import webdriver
import shutil
import Quanti.MyLibrary_20180702 as MyLib

def MoveFile(dst,fileKeyword,newFileName):
    # src='C:/Users/user/Downloads/'
    src = r'C:\Users\jhmai\Downloads/'
    # stockFolder = './NaverAnalysis/'
    srcFiles = [f for f in listdir(src) if isfile(join(src, f))]  # folder내 파일name list
    srcFile = [filename for filename in srcFiles if fileKeyword in filename]
    for file in srcFile:
        # os.rename("path/to/current/file.foo", "path/to/new/destination/for/file.foo")
        shutil.move(src+file, dst + newFileName)
    return srcFile
def GetCLIData():
    sleepCon = 2
    countryList = ['USA','EA19','KOR','JPN','IND']
    driver = webdriver.Chrome(r'./Setting\chromdriver\chromedriver.exe')
    driver.implicitly_wait(1)
    driver.set_window_position(-2000, 0)
    driver.maximize_window()

    url = 'https://data.oecd.org/leadind/composite-leading-indicator-cli.htm'
    driver.get(url)
    time.sleep(1.5*sleepCon)
    driver.find_element_by_css_selector('#indicator-chart > div.chart-controls-bottom.row > div.col-4.locations > div > a').click()
    time.sleep(5*sleepCon)
    countryListHTML = driver.find_elements_by_css_selector('#indicator-chart > div.chart-controls-bottom.row > div.col-4.locations > div > div > div > div.overlay-column.find-locations > ul > li')
    time.sleep(0.5*sleepCon)
    countryListHTML = [countryHTML for countryHTML in countryListHTML for country in countryList if country in countryHTML.text]
    for countryHTML in countryListHTML:
        countryHTML.find_element_by_tag_name('a').click()
    time.sleep(1.5 * sleepCon)
    driver.find_elements_by_class_name('close-btn')[0].click()
    indicatorChartHTML = driver.find_element_by_id('indicator-chart')
    liListHTML = indicatorChartHTML.find_elements_by_tag_name('li')
    tableHTML = [li for li in liListHTML if 'Table' in li.text]
    tableHTML[0].click()
    chartButtonPanelHTML = driver.find_element_by_class_name('chart-button-panel')
    liChartButtonPanelHTML = chartButtonPanelHTML.find_elements_by_tag_name('li')
    [li for li in liChartButtonPanelHTML if 'download' in li.text][0].click()
    time.sleep(1.5 * sleepCon)
    dropdownOverlayDarkHTML = chartButtonPanelHTML.find_element_by_class_name('dropdown-overlay')
    liDropdownOverlayDarkHTML = dropdownOverlayDarkHTML.find_elements_by_tag_name('li')
    liDropdownOverlayDarkHTML[1].click()
    time.sleep(10 * sleepCon)
    driver.quit()
def GetCLIDataAll(driver):
    sleepCon = 2
    url = 'https://data.oecd.org/leadind/composite-leading-indicator-cli.htm'
    driver.get(url)
    time.sleep(1.5*sleepCon)
    # indicatorChartHTML = driver.find_element_by_id('indicator-chart')
    # liListHTML = indicatorChartHTML.find_elements_by_tag_name('li')
    # tableHTML = [li for li in liListHTML if 'Table' in li.text]
    # tableHTML[0].click()
    chartButtonPanelHTML = driver.find_element_by_class_name('chart-button-panel')
    liChartButtonPanelHTML = chartButtonPanelHTML.find_elements_by_tag_name('li')
    [li for li in liChartButtonPanelHTML if 'download' in li.text][0].click()
    time.sleep(1.5 * sleepCon)
    dropdownOverlayDarkHTML = chartButtonPanelHTML.find_element_by_class_name('dropdown-overlay')
    liDropdownOverlayDarkHTML = dropdownOverlayDarkHTML.find_elements_by_tag_name('li')
    liDropdownOverlayDarkHTML[0].click()
    time.sleep(5 * sleepCon)
    driver.quit()
def GetCLIDate():
    driver = webdriver.Chrome(r'./Setting\chromdriver\chromedriver.exe')
    driver.implicitly_wait(1)
    driver.set_window_position(-2000, 0)
    driver.maximize_window()

    url = 'https://www.oecd.org/sdd/leading-indicators/scheduleforcompositeleadingindicatorupdates.htm'
    driver.get(url)
    time.sleep(1.5)
    contentsHTML = driver.find_element_by_id('webEditContent')
    contentsHTML = contentsHTML.find_elements_by_tag_name('p')
    contentsHTML = [item for item in contentsHTML if (item.text != ' ') and (item.text != '')][1:]
    dateOECDCLI = []
    for contents in contentsHTML:
        data = contents.text.split('\n')
        data = [_data.split('(', 1)[0] for _data in data]
        dateOECDCLI += data
    dateOECDCLI = [date.strip() for date in dateOECDCLI]
    dateOECDCLI = [date for date in dateOECDCLI if len(date)>=5]
    dateOECDCLI = [item.split('-')[0].rstrip() if '-' in item else item for item in dateOECDCLI]
    dateOECDCLI = [
        datetime.datetime.strptime(date, '%d-%B-%Y') if '-' in date else datetime.datetime.strptime(date, '%d %B %Y')
        for date in dateOECDCLI]
    dateOECDCLI = [date.strftime('%Y-%m-%d') for date in dateOECDCLI]
    dateOECDCLI = pd.DataFrame(data={"date": dateOECDCLI})
    driver.close()
    return dateOECDCLI
def GetScore2(dfOECD,location):
    dfOECD = dfOECD[dfOECD['LOCATION'] == location]  # 나라 데이터 sorting
    dfOECD['ValueDiffPCT'] = dfOECD['Value'].pct_change() * 100  # 차이 percentage.

    date = dfOECD.iloc[-1]['TIME']
    score = dfOECD.iloc[-1]['Value']
    scoreDiff = dfOECD.iloc[-1]['ValueDiffPCT']  # 마지막 score

    return score, scoreDiff, date
def GetScore(today,cliOECD,location):
    cliOECD = cliOECD[cliOECD['LOCATION'] == location]  # 나라 데이터 sorting
    cliOECD['ValueDiffPCT'] = cliOECD['Value'].pct_change() * 100   # 차이 percentage.

    date = cliOECD.iloc[-1]['TIME']
    score = cliOECD.iloc[-1]['Value']
    scoreDiff = cliOECD.iloc[-1]['ValueDiffPCT']    # 마지막 score

    return score, scoreDiff, date
def CLIResult4(folderOECD, dateOECDFile, country):
    # read file
    dateFiles = [f for f in listdir(folderOECD) if
                 isfile(join(folderOECD, f)) and '.csv' in f and 'OECD_CLI' in f and dateOECDFile in f]
    dfOECD = pd.read_csv(folderOECD + '/' + dateFiles[0])
    # get OECD score
    score, scoreDiff, dateOECD = GetScore2(dfOECD, country)
    return dateOECD, score, scoreDiff
def CLIResult3(cliOECD, dfOECD):
    # OECD Data read
    today = datetime.datetime.today()
    lastDate = cliOECD.iloc[-1]['TIME']
    lastDate = datetime.datetime.strptime(lastDate, '%Y-%m')
    if abs((today - lastDate).days) >= 90:  # 두달 넘으면 데이터 안받은 걸로 간주.
        print('Please, download the OECD CLI data!!')
    # making result
    dfOECD['Time'] = None
    dfOECD['Score'] = None
    dfOECD['ScoreDiff'] = None
    dfOECD['Rebalancing'] = None
    numCountry = len(list(set(dfOECD['Location'].tolist())))
    for idx, row in dfOECD.iterrows():
        score, scoreDiff, dateOECD = GetScore(today, cliOECD, row['Location'])
        if score < 100 and scoreDiff < 0:
            rebalancing = 0
        else:
            rebalancing = 100 / numCountry
            if len(dfOECD[dfOECD['Location']==row['Location']]) > 1:
                rebalancing = rebalancing / len(dfOECD[dfOECD['Location']==row['Location']])
        dfOECD.loc[idx,'Time'] = dateOECD
        dfOECD.loc[idx,'Score'] = score
        dfOECD.loc[idx,'ScoreDiff'] = scoreDiff
        dfOECD.loc[idx,'Rebalancing'] = rebalancing
    return dfOECD
def CLIResult2(today):
    # input
    market = 'etf'
    stock_folder = './Stock_dataKiwoom_20210502/%s/' % market
    countryDict = {'USA':['133690', '225040'], 'EA19':['195930'], 'JPN':['238720'],'KOR':['226490'],'IND':['200250']}
    # OECD Data read
    cliOECD = pd.read_csv('./OECD/OECD_CLI_%s.csv' % (today))
    lastDate = cliOECD.iloc[-1]['TIME']
    lastDate = datetime.datetime.strptime(lastDate, '%Y-%m')
    if abs(today.month - lastDate.month) >= 2:  # 두달 넘으면 데이터 안받은 걸로 간주.
        print('Please, download the OECD CLI data!!')
    # making result
    numOfETFs = {key: len(value) for key, value in countryDict.items()}.__len__()
    df_summery = pd.DataFrame(columns=['Code', 'Loc', 'Date', 'Close', 'Rebalancing'])

    for country in list(countryDict.keys()):
        score, scoreDiff, date = GetScore(today, cliOECD, country)
        if score<100 and scoreDiff < 0:
            rebalancing = 0
        else:
            rebalancing = 100/numOfETFs

        for code in countryDict[country]:
            dfStock = MyLib.LoadStockData(stock_folder, code)
            date = dfStock.index[-1]._date_repr
            close = dfStock.iloc[-1]['Close']
            df_summery.loc[len(df_summery)] = [code, country, date, close, rebalancing]
    return df_summery
def CLIResult(today):
    # 올라온 데이터확인하고.
    cliOECD = pd.read_csv('./OECD/OECD_CLI_%s.csv' % (today))
    lastDate = cliOECD.iloc[-1]['TIME']
    lastDate = datetime.datetime.strptime(lastDate, '%Y-%m')
    # lastDate = datetime.datetime.strptime(lastDate, '%b-%y')
    if abs(today.month - lastDate.month) > 2:
        print('Please, download the OECD CLI data!!')
    cliOECDUSA = cliOECD[cliOECD['LOCATION'] == 'USA']
    cliOECDEU = cliOECD[cliOECD['LOCATION'] == 'EA19']
    cliOECDJPN = cliOECD[cliOECD['LOCATION'] == 'JPN']
    cliOECDKR = cliOECD[cliOECD['LOCATION'] == 'KOR']

    cliOECDUSA['ValueDiffPCT'] = cliOECDUSA['Value'].pct_change() * 100
    cliOECDEU['ValueDiffPCT'] = cliOECDEU['Value'].pct_change() * 100
    cliOECDJPN['ValueDiffPCT'] = cliOECDJPN['Value'].pct_change() * 100
    cliOECDKR['ValueDiffPCT'] = cliOECDKR['Value'].pct_change() * 100

    # 투자수치 넣어주고.
    codeList = ['225040', '195930', '238720', '226490']
    companyList = ['TIGER 미국S&P500레버리지', 'TIGER 유로스탁스50(합성 H)', 'KINDEX 일본Nikkei225', 'KODEX 코스피']
    market = 'etf'
    stock_folder = './Stock_dataKiwoom_20210502/%s/' % market
    df_summery = pd.DataFrame(columns=['Code', 'Company', 'Date', 'Close', 'Rebalancing'])
    for code, company in zip(codeList, companyList):
        dfStock = MyLib.LoadStockData(stock_folder, code)
        date = dfStock.index[-1]._date_repr
        close = dfStock.iloc[-1]['Close']
        if code == '225040':
            rebalancing = cliOECDUSA.iloc[-1]['ValueDiffPCT']
        elif code == '195930':
            rebalancing = cliOECDEU.iloc[-1]['ValueDiffPCT']
        elif code == '238720':
            rebalancing = cliOECDJPN.iloc[-1]['ValueDiffPCT']
        elif code == '226490':
            rebalancing = cliOECDKR.iloc[-1]['ValueDiffPCT']
        if rebalancing > 0:
            rebalancing = 25
        else:
            rebalancing = 0
        df_summery.loc[len(df_summery)] = [code, company, date, close, rebalancing]
    return df_summery
if __name__ == '__main__':
    # read file and
    data = pd.read_csv(r'D:\PycharmProjects_220926\MyTrading_20211121\Quanti\OECD\Data\OECD_CLI_2022-09-27.csv')
    locations = list(set(data['LOCATION']))
    liPositiveLoc = []
    for loc in locations:
        if data.loc[data['LOCATION']==loc,'Value'].pct_change().tolist()[-1]>0:
            liPositiveLoc.append(loc)
    print(liPositiveLoc)
    # GetAllLoc
    # PTC value.
    # increase 된것만 Loc을 저장.