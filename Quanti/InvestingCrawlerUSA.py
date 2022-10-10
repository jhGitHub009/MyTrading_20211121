import pandas as pd
from os import listdir,makedirs
from os.path import isfile, join, isdir
import datetime,time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import random
import sys
import numpy as np
import os.path
import shutil
from bs4 import BeautifulSoup
import copy
import re
def LoginInvesting(driver):
    print('Login Start...', end='')
    sys.stdout.flush()
    time.sleep(1)
    login = driver.find_element_by_id('userAccount')
    login.find_element_by_link_text('로그인').click()
    time.sleep(2)
    loginPopup = driver.find_element_by_id('loginPopup')
    loginEmail = loginPopup.find_element_by_id('loginFormUser_email')
    time.sleep(2)
    loginEmail.click()
    loginEmail.clear()
    time.sleep(2)
    loginEmail.send_keys('jhmail009@gmail.com')
    loginPW = loginPopup.find_element_by_id('loginForm_password')
    time.sleep(2)
    loginPW.click()
    loginPW.clear()
    time.sleep(2)
    loginPW.send_keys('**gs10728')
    loginPopup.find_element_by_link_text('로그인').click()
    print('...Complete!!')
    sys.stdout.flush()
def GetSelectID(section):
    if section=='미국모든주식':
        selectID = 'all'  # 미국모든주식
    elif section=='나스닥종합':
        selectID = '14958'      # 나스닥종합
    elif  section=='다우존스':
        selectID = '169'  # 다우존스
    elif section == 'S&P500':
        selectID = '166'  # S&P500
    return selectID
def GetTable(table):
    # 미국주식 메인페이지.--> 데이터 저장.
    tHeads = table.find_elements_by_tag_name('thead > tr > th')
    listHead = []
    for tHead in tHeads:
        text = tHead.text
        # if text == ' ' or text == '': continue
        listHead.append(text)
    dfCompanyInfo = pd.DataFrame(columns=listHead)
    tRows = table.find_elements_by_tag_name('tbody > tr')
    for row in tRows:
        tDatas = row.find_elements_by_tag_name('td')
        rowData = []
        for tData in tDatas:
            text = tData.text
            # if text == ' ' or text == '': continue
            rowData.append(text)
        dfCompanyInfo.loc[len(dfCompanyInfo)] = rowData
    return dfCompanyInfo
def SaveTable(table,fileFullPath):
    dfCompanyInfo = GetTable(table)
    # dfCompanyInfo = GetTablebyBS(table)
    dfCompanyInfo.replace('', np.nan, inplace=True)
    dfCompanyInfo.replace(' ', np.nan, inplace=True)
    dfCompanyInfo = dfCompanyInfo.dropna(axis=1, how='all').dropna(axis=0, how='all')
    dfCompanyInfo.to_csv(fileFullPath, encoding='cp949', index=False)
def DownHistoricalData(driver,startIdx,startDate,endDate,downFolder,dst):
    table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
    for idx,row in enumerate(table_rows):
        if idx < startIdx[0]:
            continue
        row = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')[idx]
        row.click()

        headTxt = driver.find_element_by_css_selector('#leftColumn > div.instrumentHead > h1').text
        fullName = headTxt.split('(')[0].strip()
        abbreviations = headTxt.split('(')[1].replace(')','').strip()
        print('%s - %s) Downloading Stock Data...%s' % (len(table_rows), idx, headTxt), end='')
        sys.stdout.flush()
        # 과거 데이터 클릭
        subRow = driver.find_elements_by_css_selector('#pairSublinksLevel2>li')
        subRow[2].click()   # 과거 데이터
        # 날짜 설정.
        time.sleep(0.2)
        driver.find_element_by_css_selector('#widgetFieldDateRange').click()
        time.sleep(0.2)
        driver.find_element_by_css_selector('#startDate').clear()
        time.sleep(0.1)
        driver.find_element_by_css_selector('#startDate').send_keys(startDate)
        time.sleep(0.2)
        driver.find_element_by_css_selector('#endDate').clear()
        time.sleep(0.1)
        driver.find_element_by_css_selector('#endDate').send_keys(endDate)
        time.sleep(0.2)
        driver.find_element_by_css_selector('#applyBtn').click()
        time.sleep(2)
        # 다운버튼 클릭.
        driver.find_element_by_css_selector('#column-content > div.float_lang_base_2.downloadDataWrap > div > a').click()
        time.sleep(3)
        # back 버튼 두번 --> 메인페이지.
        driver.back()
        time.sleep(1)
        driver.back()
        time.sleep(1)
        # 파일 무빙.
        files = listdir(downFolder)
        downFile = [file for file in files if abbreviations in file]
        if os.path.exists(downFolder+'/'+downFile[0]):
            shutil.move(downFolder+'/'+downFile[0], dst+'/%s_%s.csv'%(fullName,abbreviations))
        print('...Done!!')
        sys.stdout.flush()
        startIdx[0]+=1
    driver.quit()
def GetTableHead(table):
    tHeads = table.find_elements_by_tag_name('thead > tr > th')
    listHead = []
    for tHead in tHeads:
        text = tHead.text
        listHead.append(text)
    df = pd.DataFrame(columns=listHead)
    return df
def GetTableBody(df, table, startRow):
    tRows = table.find_elements_by_tag_name('tbody > tr')
    for idx,row in enumerate(tRows):
        if idx < startRow : continue
        tDatas = row.find_elements_by_tag_name('td')
        rowData = []
        for tData in tDatas:
            text = tData.text
            # if text == ' ' or text == '': continue
            rowData.append(text)
        df.loc[len(df)] = rowData
    return df
def GetRatioData(driver, startIdx, filePath):
    table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
    for idx, row in enumerate(table_rows):
        if idx < startIdx[0]:
            continue
        row = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')[idx]
        row.click()
        time.sleep(1)
        headTxt = driver.find_element_by_css_selector('#leftColumn > div.instrumentHead > h1').text
        fullName = headTxt.split('(')[0].strip()
        abbreviations = headTxt.split('(')[1].replace(')', '').strip()
        print('%s - %s) Downloading Stock Data...%s' % (len(table_rows), idx, headTxt), end='')
        sys.stdout.flush()
        # 과거 데이터 클릭
        mainRows = driver.find_elements_by_css_selector('#pairSublinksLevel1>li')
        financialStatusIdx = [idxmainRow for idxmainRow,mainRow in enumerate(mainRows) if mainRow.text=='재정 상황'][0]
        mainRows[financialStatusIdx].find_element_by_tag_name('a').click()  # 과거 데이터
        subRows = driver.find_elements_by_css_selector('#pairSublinksLevel2>li')
        ratioIdx = [idxSubRows for idxSubRows, subRows in enumerate(subRows) if subRows.text == '관련 각종 비율'][0]
        subRows[ratioIdx].find_element_by_tag_name('a').click()  # 과거 데이터

        table = driver.find_element_by_css_selector('#rrTable')
        dfCompanyInfo = GetTableHead(table)
        subTables = driver.find_elements_by_tag_name('body > div')[4]
        subTables = subTables.find_elements_by_tag_name('section > table > tbody > tr')
        subTable = subTables[1].find_element_by_tag_name('td > div > table')
        dfCompanyInfo = GetTableBody(dfCompanyInfo, subTable, 0)
        subTable = subTables[3].find_element_by_tag_name('td > div > table')
        dfCompanyInfo = GetTableBody(dfCompanyInfo, subTable, 1)
        subTable = subTables[5].find_element_by_tag_name('td > div > table')
        dfCompanyInfo = GetTableBody(dfCompanyInfo, subTable, 0)
        subTable = subTables[7].find_element_by_tag_name('td > div > table')
        dfCompanyInfo = GetTableBody(dfCompanyInfo, subTable, 1)
        subTable = subTables[9].find_element_by_tag_name('td > div > table')
        dfCompanyInfo = GetTableBody(dfCompanyInfo, subTable, 0)
        subTable = subTables[11].find_element_by_tag_name('td > div > table')
        dfCompanyInfo = GetTableBody(dfCompanyInfo, subTable, 0)
        subTable = subTables[13].find_element_by_tag_name('td > div > table')
        dfCompanyInfo = GetTableBody(dfCompanyInfo, subTable, 0)
        subTable = subTables[15].find_element_by_tag_name('td > div > table')
        dfCompanyInfo = GetTableBody(dfCompanyInfo, subTable, 0)
        # Save
        dfCompanyInfo.replace('', np.nan, inplace=True)
        dfCompanyInfo.replace(' ', np.nan, inplace=True)
        dfCompanyInfo = dfCompanyInfo.dropna(axis=1, how='all').dropna(axis=0, how='all')
        dfCompanyInfo.to_csv(filePath+'/%s_%s.csv'%(fullName,abbreviations), encoding='cp949', index=False)

        driver.back()
        time.sleep(0.5)
        driver.back()
        time.sleep(0.5)
        driver.back()
        time.sleep(0.5)
        print('...Done!!')
        sys.stdout.flush()
        startIdx[0] += 1
def Main(startIdx):
    # folder = r'G:\PycharmProjects_20171228\stock\Kiwoom_stock_20180529\StockData_USA'
    # 페이지에 들어가고,
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    # options.add_argument('window-size=1920x1080')
    # options.add_argument("disable-gpu")
    driver = webdriver.Chrome(r'../Setting\chromdriver\chromedriver.exe', chrome_options=options)
    # driver = webdriver.Chrome('C:/Users/user/chromedriver')
    driver.implicitly_wait(1)
    driver.set_window_position(-2000, 0)
    driver.maximize_window()
    url = 'https://kr.investing.com/equities/united-states'
    driver.get(url)
    # 로그인 하고
    LoginInvesting(driver)
    time.sleep(0.1)
    selectName = 'S&P500'  # 미국모든주식 # 나스닥종합 # 다우존스 # S&P500
    selectID = GetSelectID(selectName)
    # 미국의 모든주식 드롭박스에서 설정.
    driver.find_element_by_id(selectID).click()
    time.sleep(5)
    filePath = r'../Infomation\Investing\20220511\Financial Status'
    if not isdir(filePath): makedirs(filePath)
    GetRatioData(driver, startIdx, filePath)
def GetTablebyBS(driver):
    bs = BeautifulSoup(driver.page_source, 'html.parser')
    table = bs.find_all(id='cross_rate_markets_stocks_1')[0]
    # table = bs.find_all(id='rsdiv')[0].find_all('table')
    table_pd = pd.read_html(str(table))
    mainTable = copy.deepcopy(table_pd[0])
    if len(table_pd) == 1:
        return mainTable
    elif len(table_pd) > 1:
        firstColumnData = mainTable[mainTable.columns[0]].tolist()
        locInsert = []
        for _idxData,_data in enumerate(firstColumnData):
            floatData = re.findall("\d+", _data)
            if floatData:
                locInsert.append(_idxData)
        mainTable.drop(locInsert, inplace=True)
        for _data in table_pd[1:]:
            _data.columns = mainTable.columns
            mainTable = mainTable.append(_data,ignore_index=True)
        return mainTable
def MainForStockName():
    selectName = '나스닥종합'  # 미국모든주식 # 나스닥종합 # 다우존스 # S&P500
    filePath = r'../Infomation\Investing\20220511\StockName'
    if not isdir(filePath): makedirs(filePath)

    print('-------------- Start to Down StockName --------------')
    sys.stdout.flush()
    # down location
    # down done.
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    # options.add_argument('window-size=1920x1080')
    # options.add_argument("disable-gpu")
    driver = webdriver.Chrome(r'../Setting\chromdriver\chromedriver.exe', chrome_options=options)

    # driver = webdriver.Chrome(r'../Setting\chromdriver\chromedriver.exe')
    driver.implicitly_wait(1)
    driver.set_window_position(-2000, 0)
    driver.maximize_window()
    url = 'https://kr.investing.com/equities/united-states'
    driver.get(url)
    # 로그인 하고
    LoginInvesting(driver)
    time.sleep(0.1)
    # down for sectorName
    selectID = GetSelectID(selectName)
    print('Stock Index : %s' % (selectName))
    sys.stdout.flush()
    # StockSection 드롭박스에서 설정.
    driver.find_element_by_id(selectID).click()
    time.sleep(5)
    # save folder 설정.
    # today = datetime.date.today().strftime('%Y-%m-%d')
    # filePath = filePath +'/' + today
    # if not isdir(filePath): makedirs(filePath)
    print('Down Location : %s' % (filePath))
    sys.stdout.flush()
    # 테이블 정보 저장.
    table = driver.find_element_by_id('cross_rate_markets_stocks_1')
    SaveTable(table, filePath + '/%s.csv'%(selectName))
    print('-------------- End to Down StockName --------------')
    sys.stdout.flush()
if __name__ == '__main__':
    # 페이지에 들어가고,
    # 로그인 하고
    # 미국의 모든주식 드롭박스에서 설정.
    # 기업이름만 모두 긁어옴.--> 데이터 저장.
    # 반복시작
    # 미국의 모든주식 드롭박스에서 설정.
    # 해당 기업을 클릭--> 데이터 크롤링
        # 기본개요 데이터
        # 과거데이터
        # 기술분석 데이터
    # 뒤로가기.
    # 반복마무리.
    startIdx = []
    startIdx.append(0)
    for iterate in range(500):
        try:
            # Main(startIdx)
            MainForStockName()
            break
        except:
            print('----------   Error occurred!!   ----------')
            if startIdx[0]!=0:
                startIdx[0]-=1
            continue