import pandas as pd
from os import listdir,makedirs
from os.path import isfile, join, isdir
import datetime,time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import random
import sys
import numpy as np
import os.path
import shutil
from bs4 import BeautifulSoup
import copy
import re
import glob
import os

def LoginInvesting(driver):
    timeDelta = 0.3
    # popupWindow = driver.find_element_by_id('PromoteSignUpPopUp')
    # popupWindow.find_element_by_class_name('popupCloseIcon largeBannerCloser')
    # popupWindow.find_element_by_css_selector('div.right > i').click()
    print('Login Start...', end='')
    sys.stdout.flush()
    time.sleep(1.0 * timeDelta)
    print('*..', end='')
    login = driver.find_element_by_id('userAccount')
    login.find_element_by_link_text('로그인').click()
    time.sleep(1.0 * timeDelta)
    print('*..', end='')
    loginPopup = driver.find_element_by_id('loginPopup')
    loginEmail = loginPopup.find_element_by_id('loginFormUser_email')
    time.sleep(1.0 * timeDelta)
    print('*..', end='')
    loginEmail.click()
    loginEmail.clear()
    time.sleep(1.0 * timeDelta)
    print('*..', end='')
    loginEmail.send_keys('jhmail009@gmail.com')
    loginPW = loginPopup.find_element_by_id('loginForm_password')
    time.sleep(1.0 * timeDelta)
    print('*..', end='')
    loginPW.click()
    loginPW.clear()
    time.sleep(1.0 * timeDelta)
    print('*..', end='')
    loginPW.send_keys('**gs10728')
    loginPopup.find_element_by_link_text('로그인').click()
    print('...Complete!!')
    sys.stdout.flush()
def SearchByCode(driver, code, company):
    # driver.find_elements_by_xpath("//*[contains(text(), '시세')]")
    search = driver.find_element_by_xpath("//input[@placeholder='웹사이트 검색']")
    search.send_keys(code)
    search.send_keys(Keys.RETURN)
    driver.find_element_by_xpath("//*[contains(text(), '%s')]" % (company)).click()
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
def GetTable2(table):
    # 미국주식 메인페이지.--> 데이터 저장.
    # tHeads = table.find_elements_by_tag_name('tbody')[0]
    tHeads = table.find_elements_by_css_selector('#header_row > th')
    listHead = []
    for tHead in tHeads:
        text = tHead.text
        # if text == ' ' or text == '': continue
        listHead.append(text)
    dfCompanyInfo = pd.DataFrame(columns=listHead)
    # tRows = table.find_elements_by_tag_name('tbody > tr')
    # for row in tRows:
    #     tDatas = row.find_elements_by_tag_name('td')
    #     rowData = []
    #     for tData in tDatas:
    #         text = tData.text
    #         # if text == ' ' or text == '': continue
    #         rowData.append(text)
    #     dfCompanyInfo.loc[len(dfCompanyInfo)] = rowData
    return dfCompanyInfo
def SaveTable(table,fileFullPath):
    dfCompanyInfo = GetTable(table)
    dfCompanyInfo.replace('', np.nan, inplace=True)
    dfCompanyInfo.replace(' ', np.nan, inplace=True)
    dfCompanyInfo = dfCompanyInfo.dropna(axis=1, how='all').dropna(axis=0, how='all')
    dfCompanyInfo.to_csv(fileFullPath, encoding='cp949', index=False)
def DownHistoricalData(driver,startIdx,startDate,endDate,downFolder,dst,indexData,selectName):
    mode = 2
    if mode == 1:
        # 테이블 상 나와있는 text 획득.
        table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
        # 테이블상 종목 으로 테이블상 index획듯.
        companyNames = [table_row.text for table_row in table_rows]
        idxCompanyNames = [companyNames.index(comName) for comName in indexData['종목'].tolist()]
        indexData['테이블상 위치'] = idxCompanyNames
        # 매핑 하여 indexData에 저장.
    for idx_data, row_data in indexData.iterrows():
        if idx_data < startIdx[0]:
            continue
        if mode == 0:
            table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
            thisRow = [row for row in table_rows if row.text == row_data['종목']]  # 시간 많이 걸림.
            if not thisRow:
                continue
            thisRow = thisRow[0]
        elif mode == 1:
            time.sleep(5)
            table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
            thisRow = table_rows[row_data['테이블상 위치']]
        elif mode == 2:
            table_rows = driver.find_elements_by_link_text(row_data['종목'])
            if table_rows:
                thisRow = table_rows[0]
            else:
                table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
                thisRow = [row for row in table_rows if row.text == row_data['종목']]  # 시간 많이 걸림.
                if not thisRow:
                    continue
                thisRow = thisRow[0]

        elif mode == 3:
            time.sleep(5)
            table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
            # thisRow = table_rows[idx_data]
            thisRow = table_rows[row_data['테이블상 위치']]
        companyName = thisRow.text
        if row_data['종목'] != companyName:
            # print('%s - %s) Downloading Stock Data...%s Fail!!' % (len(indexData), idx_data, companyName))
            # sys.stdout.flush()
            # continue
            table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
            thisRow = [row for row in table_rows if row.text == row_data['종목']]  # 시간 많이 걸림.
            if not thisRow:
                continue
            thisRow = thisRow[0]
        thisRow.click()
        time.sleep(1.5)

        headTxt = [item for item in driver.find_elements_by_tag_name('h1') if '(' in item.text]
        if headTxt:
            headTxt = headTxt[0].text
        else:
            headTxt = companyName
        fullName = headTxt.split('(')[0].strip()
        abbreviations = headTxt.split('(')[1].replace(')', '').strip()
        print('%s - %s) Downloading Stock Data...%s' % (len(indexData), idx_data, headTxt), end='')
        sys.stdout.flush()

        # 과거 데이터 클릭
        subRow = driver.find_elements_by_link_text('과거 데이터')
        if not subRow:
            continue
        # subRow = driver.find_elements_by_css_selector('#__next > div > div > div.grid-container.grid-container--fixed-desktop.general-layout_main__3tg3t > main > div > div:nth-child(3) > nav > ul > li')
        # driver.find_elements_by_xpath('//*[@id="__next"]/div/div/div[2]/main/div/div[4]/nav/ul/li')
        # subRow[2].click()  # 과거 데이터
        subRow[0].click()  # 과거 데이터
        # 날짜 설정.
        time.sleep(3)
        # 다운버튼 클릭.
        driver.find_element_by_css_selector(
            '#column-content > div.float_lang_base_2.downloadDataWrap > div > a').click()
        time.sleep(2.0)
        # back 버튼 두번 --> 메인페이지.
        driver.back()
        time.sleep(2.0)
        driver.back()
        time.sleep(1.0)
        print('..2', end='')
        sys.stdout.flush()
        # 파일 무빙.
        files = listdir(downFolder)
        downFile = [file for file in files if abbreviations in file]
        if not downFile:
            list_of_files = glob.glob(downFolder + '/*.csv')
            latest_file = max(list_of_files, key=os.path.getctime)
            downFile.append(latest_file.split('\\')[-1])
        if os.path.exists(downFolder + '/' + downFile[0]):
            # shutil.move(downFolder + '/' + downFile[0], dst + '/%s_%s.csv' % (fullName, abbreviations))
            shutil.move(downFolder + '/' + downFile[0], dst + '/%s.csv' % (companyName.replace('/','')))
        print('...Done!!')
        sys.stdout.flush()
        driver.execute_script("window.scrollTo(0, 10)")
        selectID = GetSelectID('미국모든주식')
        driver.find_element_by_id(selectID).click()
        # time.sleep(2.0)
        for i in range(10):
            listOfCompany = driver.find_elements_by_xpath('//*[@id="cross_rate_markets_stocks_1"]/tbody/tr')
            if listOfCompany:
                time.sleep(1.0)
                break
            else:
                time.sleep(1.0)
        selectID = GetSelectID(selectName)
        driver.find_element_by_id(selectID).click()
        for i in range(10):
            listOfCompany = driver.find_elements_by_xpath('//*[@id="cross_rate_markets_stocks_1"]/tbody/tr')
            if listOfCompany:
                time.sleep(1.0)
                break
            else:
                time.sleep(1.0)
        popUpBtnActivate = driver.find_elements_by_xpath('/html/body/div[6]/div/div[4]/button[2]')
        if popUpBtnActivate:
            popUpBtnActivate[0].click()  # 활성화 버튼 클릭.
        startIdx[0] += 1
    driver.quit()
def GetTableHead(table):
    tHeads = table.find_elements_by_tag_name('thead > tr > th')
    listHead = []
    for tHead in tHeads:
        text = tHead.text
        listHead.append(text)
    df = pd.DataFrame(columns=listHead)
    return df
def GetTableHeadfromTbody(table):
    tHeads = table.find_elements_by_tag_name('tbody > tr')[0]
    tHeads = tHeads.find_elements_by_tag_name('th')
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
        if tDatas[0].text in df[df.columns[0]].tolist():
            continue
        rowData = []
        for tData in tDatas:
            text = tData.text
            rowData.append(text)
        df.loc[len(df)] = rowData
    return df
def GetTableBodyfromTbody(df, table, startRow):
    tRows = table.find_elements_by_tag_name('tr')
    time.sleep(1)
    for idx,row in enumerate(tRows):
        if idx < startRow : continue
        if row.find_elements_by_tag_name('table'):
            GetTableBody(df, row.find_elements_by_tag_name('table')[0], 0)
            continue
        tDatas = row.find_elements_by_tag_name('td')
        if tDatas[0].text in df[df.columns[0]].tolist():
            continue
        rowData = []
        for tData in tDatas:
            text = tData.text
            rowData.append(text)
        df.loc[len(df)] = rowData
    return df
def GetRatioData(driver, startIdx, filePath, sectionName):
    time.sleep(2)
    table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
    for idx, row in enumerate(table_rows):
        if idx < startIdx[0]:
            continue
        time.sleep(1)
        row = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')[idx]
        companyName = row.text
        row.click()
        time.sleep(2)

        headTxt = [item for item in driver.find_elements_by_tag_name('h1') if '(' in item.text]
        if headTxt:
            headTxt = headTxt[0].text
        else:
            headTxt = companyName
        print('%s - %s) Downloading Stock Data...%s' % (len(table_rows), idx, headTxt), end='')
        sys.stdout.flush()
        print('..1', end='')
        sys.stdout.flush()
        # 과거 데이터 클릭
        mainRows = driver.find_elements_by_class_name('navbar_navbar-item__1Z2Tn')
        # mainRows = driver.find_elements_by_css_selector('#pairSublinksLevel1>li')
        financialStatusIdx = [idxmainRow for idxmainRow,mainRow in enumerate(mainRows) if mainRow.text=='재정 상황'][0]
        mainRows[financialStatusIdx].find_element_by_tag_name('a').click()  # 과거 데이터
        subRows = driver.find_elements_by_css_selector('#pairSublinksLevel2>li')
        ratioIdx = [idxSubRows for idxSubRows, subRows in enumerate(subRows) if subRows.text == sectionName][0]
        subRows[ratioIdx].find_element_by_tag_name('a').click()  # 과거 데이터
        hrefs = driver.find_elements_by_tag_name('a')
        print('..2', end='')
        sys.stdout.flush()
        #연간 클릭.
        [href for href in hrefs if href.text=='연간'][0].click()
        # table
        tables = driver.find_element_by_id('rrtable')
        tables = tables.find_elements_by_tag_name('table>tbody')
        dfCompanyInfo = GetTableHeadfromTbody(tables[0])
        GetTableBodyfromTbody(dfCompanyInfo, tables[1], 0)
        print('..3', end='')
        sys.stdout.flush()
        # Save
        dfCompanyInfo.replace('', np.nan, inplace=True)
        dfCompanyInfo.replace(' ', np.nan, inplace=True)
        dfCompanyInfo = dfCompanyInfo.dropna(axis=1, how='all').dropna(axis=0, how='all')
        # dfCompanyInfo.to_csv(filePath+'/%s_%s.csv'%(fullName,abbreviations), encoding='cp949', index=False)
        dfCompanyInfo.to_csv(filePath + '/%s.csv' % (companyName.replace('/','')), encoding='cp949', index=False)
        print('..4', end='')
        sys.stdout.flush()

        driver.back()
        time.sleep(0.5)
        driver.back()
        time.sleep(0.5)
        driver.back()
        time.sleep(0.5)
        print('...Done!!')
        sys.stdout.flush()
        startIdx[0] += 1
def GetRatioData2(driver, startIdx, filePath, indexData, sectionName):
    mode = 1
    if mode==1:
        # 테이블 상 나와있는 text 획득.
        table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
        # 테이블상 종목 으로 테이블상 index획듯.
        companyNames = [table_row.text for table_row in table_rows]
        idxCompanyNames = [companyNames.index(comName) for comName in indexData['종목'].tolist()]
        indexData['테이블상 위치'] = idxCompanyNames
        # 매핑 하여 indexData에 저장.
    for idx_data, row_data in indexData.iterrows():
        if idx_data < startIdx[0]:
            continue
        if mode == 0:
            table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
            thisRow = [row for row in table_rows if row.text == row_data['종목']]  # 시간 많이 걸림.
            if not thisRow:
                continue
            thisRow = thisRow[0]
        elif mode == 1:
            time.sleep(2.5)
            table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
            thisRow = table_rows[row_data['테이블상 위치']]
        companyName = thisRow.text
        if row_data['종목'] != companyName:
            print('%s - %s) Downloading Stock Data...%s Fail!!' % (len(indexData), idx_data, companyName))
            sys.stdout.flush()
            continue
        thisRow.click()
        time.sleep(1.5)

        # headTxt = companyName
        headTxt = [item for item in driver.find_elements_by_tag_name('h1') if '(' in item.text]
        if headTxt:
            headTxt = headTxt[0].text
        else:
            headTxt = companyName
        print('%s - %s) Downloading Stock Data...%s' % (len(indexData), idx_data, headTxt), end='')
        sys.stdout.flush()
        # 과거 데이터 클릭
        mainRows = driver.find_elements_by_class_name('navbar_navbar-item__1Z2Tn')
        # mainRows = driver.find_elements_by_css_selector('#pairSublinksLevel1>li')
        financialStatusIdx = [idxmainRow for idxmainRow, mainRow in enumerate(mainRows) if mainRow.text == '재정 상황'][0]
        mainRows[financialStatusIdx].find_element_by_tag_name('a').click()  # 과거 데이터
        subRows = driver.find_elements_by_css_selector('#pairSublinksLevel2>li')
        ratioIdx = [idxSubRows for idxSubRows, subRows in enumerate(subRows) if subRows.text == sectionName][0]
        time.sleep(1)
        print('..0', end='')
        sys.stdout.flush()
        subRows[ratioIdx].find_element_by_tag_name('a').click()  # 과거 데이터
        time.sleep(3)
        # 연간 클릭.
        print('..1', end='')
        sys.stdout.flush()
        hrefs = driver.find_elements_by_tag_name('a')
        [href for href in hrefs if href.text == '연간'][0].click()
        time.sleep(2)
        print('..2', end='')
        sys.stdout.flush()
        # table
        tables = driver.find_element_by_id('rrtable')
        tables = tables.find_elements_by_tag_name('table>tbody')
        dfCompanyInfo = GetTableHeadfromTbody(tables[0])
        GetTableBodyfromTbody(dfCompanyInfo, tables[1], 0)      # 에러 많이 남.
        print('..3', end='')
        sys.stdout.flush()
        # Save
        dfCompanyInfo.replace('', np.nan, inplace=True)
        dfCompanyInfo.replace(' ', np.nan, inplace=True)
        dfCompanyInfo = dfCompanyInfo.dropna(axis=1, how='all').dropna(axis=0, how='all')
        # dfCompanyInfo.to_csv(filePath + '/%s_%s.csv' % (fullName, abbreviations), encoding='cp949', index=False)
        dfCompanyInfo.to_csv(filePath + '/%s.csv' % (companyName.replace('/','')), encoding='cp949', index=False)
        driver.back()
        time.sleep(0.5)
        driver.back()
        time.sleep(0.5)
        driver.back()
        time.sleep(0.5)
        print('...Done!!')
        sys.stdout.flush()
        startIdx[0] += 1
def GetGernalData(driver, startIdx, filePath, indexData, sectionName, selectName):
    mode = 2
    if mode==1:
        # 테이블 상 나와있는 text 획득.
        table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
        # 테이블상 종목 으로 테이블상 index획듯.
        companyNames = [table_row.text for table_row in table_rows]
        idxCompanyNames = [companyNames.index(comName) for comName in indexData['종목'].tolist()]
        indexData['테이블상 위치'] = idxCompanyNames
        # 매핑 하여 indexData에 저장.
    for idx_data, row_data in indexData.iterrows():
        if idx_data < startIdx[0]:
            continue
        if mode == 0:
            table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
            thisRow = [row for row in table_rows if row.text == row_data['종목']]  # 시간 많이 걸림.
            if not thisRow:
                continue
            thisRow = thisRow[0]
        elif mode == 1:
            time.sleep(2.5)
            table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
            thisRow = table_rows[row_data['테이블상 위치']]
        elif mode == 2:
            table_rows = driver.find_elements_by_link_text(row_data['종목'])
            if table_rows:  # 찾았으면,
                thisRow = table_rows[0]
            else:   #못찾으면,
                table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
                thisRow = [row for row in table_rows if row.text == row_data['종목']]  # 시간 많이 걸림.
                if not thisRow:
                    continue
                thisRow = thisRow[0]
        companyName = thisRow.text
        if row_data['종목'] != companyName:
            print('%s - %s) Downloading Stock Data...%s Fail!!' % (len(indexData), idx_data, companyName))
            sys.stdout.flush()
            continue
        thisRow.click()
        time.sleep(1.5)

        headTxt = [item for item in driver.find_elements_by_tag_name('h1') if '(' in item.text]
        if headTxt:
            headTxt = headTxt[0].text
        else:
            headTxt = companyName
        print('%s - %s) Downloading Stock Data...%s' % (len(indexData), idx_data, headTxt), end='')
        sys.stdout.flush()
        mainRows = driver.find_elements_by_link_text(sectionName.split()[0])
        if mainRows:
            mainRows.click()
        subRows = driver.find_elements_by_link_text(sectionName.split()[1])
        if subRows:
            subRows[0].click()
        time.sleep(3)
        # 연간 클릭.
        print('..1', end='')
        sys.stdout.flush()
        # table
        tableDatas = driver.find_elements_by_tag_name('dl')[0]
        tableDatas = tableDatas.find_elements_by_xpath("./div")
        # tableDatas = driver.find_element_by_css_selector('#leftColumn > div.clear.overviewDataTable.overviewDataTableWithTooltip')
        # tableDatas = tableDatas.find_elements_by_tag_name('div')
        dfCompanyInfo = pd.DataFrame(columns=['Key','Data'])
        for tableData in tableDatas:
            key = tableData.find_element_by_tag_name('dt').text
            data = tableData.find_element_by_tag_name('dd').text
            dfCompanyInfo.loc[len(dfCompanyInfo)] = [key, data]
        print('..2', end='')
        sys.stdout.flush()
        # Save
        dfCompanyInfo.replace('', np.nan, inplace=True)
        dfCompanyInfo.replace(' ', np.nan, inplace=True)
        dfCompanyInfo = dfCompanyInfo.dropna(axis=1, how='all').dropna(axis=0, how='all')
        dfCompanyInfo.to_csv(filePath + '/%s.csv' % (companyName.replace('/','')), encoding='cp949', index=False)
        driver.back()
        time.sleep(0.5)
        print('...Done!!')
        sys.stdout.flush()
        selectID = GetSelectID('미국모든주식')
        driver.find_element_by_id(selectID).click()
        time.sleep(2.0)
        selectID = GetSelectID(selectName)
        driver.find_element_by_id(selectID).click()
        for i in range(10):
            listOfCompany = driver.find_elements_by_xpath('//*[@id="cross_rate_markets_stocks_1"]/tbody/tr')
            if listOfCompany:
                time.sleep(1.0)
                break
            else:
                time.sleep(1.0)
        popUpBtnActivate = driver.find_elements_by_xpath('/html/body/div[6]/div/div[4]/button[2]')
        if popUpBtnActivate:
            popUpBtnActivate[0].click()  # 활성화 버튼 클릭.
        startIdx[0] += 1
def SetfinancialSectionEn(financialSection):
    # financialSection = '일반 개요'  # 손익 계산서'Income Statement'/ 대차 대조표 'Balance sheet'/
    # 현금흐름 'Cash flow statement' / 일반 개요 'General Summary' / 일반 프로필 'General Profile' /  재정 상황'Financial situation' /
    # 재무 정보 요약 'Financial information summary'
    if financialSection=='손익 계산서':
        enName = 'Income Statement'
    elif financialSection=='대차 대조표':
        enName = 'Balance sheet'
    elif financialSection=='현금흐름':
        enName = 'Cash flow statement'
    elif financialSection=='일반 개요':
        enName = 'General Summary'
    elif financialSection == '일반 프로필':
        enName = 'General Profile'
    elif financialSection == '재무 정보 요약':
        enName = 'Financial information summary'
    return enName
def Main(startIdx):
    selectName = 'S&P500'  # 미국모든주식 # 나스닥종합 # 다우존스 # S&P500
    financialSection = '손익 계산서'  # 손익 계산서'Income Statement'/ 대차 대조표 'Balance sheet'/ 현금흐름 'Cash flow statement'
    driver =  r'../Infomation\Investing\20220511\StockName\%s.csv'%(selectName)
    filePathforSaving = r'../Infomation\Investing\20220511\StockData_USA'
    # today = '2021-03-29'
    today = datetime.date.today().strftime('%Y-%m-%d')
    print('-------------- Start Main Function %s--------------'%(financialSection))
    sys.stdout.flush()
    print('-------------- Start to Down Financial info --------------')
    sys.stdout.flush()
    # 페이지에 들어가고,
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    # options.add_argument('window-size=1920x1080')
    # options.add_argument("disable-gpu")
    driver = webdriver.Chrome(r'../Setting\chromdriver\chromedriver.exe', chrome_options=options)
    # driver = webdriver.Chrome('C:/Users/user/chromedriver')
    driver.implicitly_wait(1)
    driver.set_window_position(-2000, 0)
    # driver.set_window_position(2000, 0)
    driver.maximize_window()
    url = 'https://kr.investing.com/equities/united-states'
    driver.get(url)
    # 로그인 하고
    LoginInvesting(driver)
    time.sleep(0.1)
    selectID = GetSelectID(selectName)
    print('Stock Index : %s' % (selectName))
    sys.stdout.flush()
    # 미국의 모든주식 드롭박스에서 설정.
    driver.find_element_by_id(selectID).click()
    time.sleep(5)
    # save folder 설정.

    enName = SetfinancialSectionEn(financialSection)
    filePathforSaving = filePathforSaving + '/' + enName + '/' + selectName
    # filePathforSaving = filePathforSaving + '/' + today
    if not isdir(filePathforSaving): makedirs(filePathforSaving)
    print('Down Location : %s' % (filePathforSaving))
    sys.stdout.flush()
    GetRatioData(driver, startIdx, filePathforSaving,financialSection)
    # indexData = pd.read_csv(filePathforIndex, encoding='cp949', engine='python')
    # GetRatioData2(driver, startIdx, filePathforSaving, indexData, financialSection)

    # 테이블 정보 저장.
    # table = driver.find_element_by_id('cross_rate_markets_stocks_1')
    # table_rows = table.find_elements_by_tag_name('a')

    # startDate = '2010/01/01'
    # endDate = datetime.date.today().strftime('%Y/%m/%d')
    # downFolder = r'C:\Users\user\Downloads'
    # dst = r'G:\PycharmProjects_20171228\stock\Kiwoom_stock_20180529\StockData_USA\Historical_Data\Daily'
    #
    # DownHistoricalData(driver, startIdx, startDate, endDate, downFolder, dst)

    # SaveTable(table, folder + '/%s.csv'%(selectName))
def MainforCheck(startIdx):
    selectName = 'S&P500'  # 미국모든주식 # 나스닥종합 # 다우존스 # S&P500
    financialSection = '손익 계산서'  # 손익 계산서'Income Statement'/ 대차 대조표 'Balance sheet'/ 현금흐름 'Cash flow statement'
    filePathforIndex = r'../Infomation\Investing\20220511\StockName\%s.csv' % (selectName)
    filePathforSaving = r'../Infomation\Investing\20220511\StockData_USA'
    # today = '2022-05-11'

    print('-------------- Start to Check Financial info --------------')
    sys.stdout.flush()
    enName = SetfinancialSectionEn(financialSection)
    filePathforSaving = filePathforSaving + '/' + enName + '/' + selectName
    # filePathforSaving = filePathforSaving + '/' + today
    if not isdir(filePathforSaving): makedirs(filePathforSaving)
    print('Down Location : %s' % (filePathforSaving))
    sys.stdout.flush()
    # index파일리딩.
    indexData = pd.read_csv(filePathforIndex, encoding='cp949', engine='python')
    # 폴더 파일 리스트
    downFiles = [f for f in listdir(filePathforSaving) if isfile(join(filePathforSaving, f))]  # folder내 파일name list
    downFilesfront = [f.replace('.csv','') for f in downFiles]
    # 있는 것은 지우기.
    listforErase = []
    for idx_indexData, rowindexData in indexData.iterrows():
        if rowindexData['종목'] in downFilesfront:
            listforErase.append(idx_indexData)
    indexData.drop(indexData.index[listforErase],inplace=True)
    indexData.reset_index(drop=True, inplace=True)
    print(indexData)
    # 없는 index 파일 포함하여 넘기고 추가로 받기.
    if indexData.empty:
        return True
    # 페이지에 들어가고,
    options = webdriver.ChromeOptions()
    # options.add_argument('headless')
    # options.add_argument('window-size=1920x1080')
    # options.add_argument("disable-gpu")
    driver = webdriver.Chrome(r'../Setting\chromdriver\chromedriver.exe', chrome_options=options)
    # driver = webdriver.Chrome('C:/Users/user/chromedriver.exe', chrome_options=options)
    # driver = webdriver.Chrome('C:/Users/user/chromedriver')
    driver.implicitly_wait(1)
    driver.set_window_position(-2000, 0)
    driver.maximize_window()
    url = 'https://kr.investing.com/equities/united-states'
    driver.get(url)
    # 로그인 하고
    LoginInvesting(driver)
    time.sleep(0.1)
    selectID = GetSelectID(selectName)
    print('Stock Index : %s' % (selectName))
    sys.stdout.flush()
    # 미국의 모든주식 드롭박스에서 설정.
    driver.find_element_by_id(selectID).click()
    time.sleep(5)
    startIdx = [0]
    GetRatioData2(driver, startIdx, filePathforSaving, indexData, financialSection)
def MainforRename():
    selectName = 'S&P500'  # 미국모든주식 # 나스닥종합 # 다우존스 # S&P500
    filePathforIndex = r'../Infomation\Investing\20220511\StockName\%s.csv' % (selectName)
    filePathforCurrent = r'../Infomation\Investing\20220511\StockData_USA'
    filePathforNew = r'./StockData_USA\Historical_Data\Daily\2021-04-26'
    print('-------------- Start to Check Financial info --------------')
    sys.stdout.flush()
    # index파일리딩.
    indexData = pd.read_csv(filePathforIndex, encoding='cp949', engine='python')
    # 폴더 파일 리스트
    downFiles = [f for f in listdir(filePathforCurrent) if isfile(join(filePathforCurrent, f))]  # folder내 파일name list
    downFilesFront = [f.split('_')[0] for f in downFiles]
    downFilesBack = [f.split('_')[1].replace('.csv','') for f in downFiles]
    # 인덱싱에 있는 파일은 파일이동
    for idx_indexData, row_indexData in indexData.iterrows():
        if row_indexData['종목'] in downFilesFront:
            fileIndex = downFilesFront.index(row_indexData['종목'])
            print(row_indexData['종목'])
        elif row_indexData['종목'] in downFilesBack:
            fileIndex = downFilesBack.index(row_indexData['종목'])
            print(row_indexData['종목'])
        else:
            continue
        # 이동시 rename.
        shutil.move(filePathforCurrent + '/' + downFiles[fileIndex], filePathforNew + '/%s.csv' % (row_indexData['종목']))
    print('-------------- End to Down Financial info --------------')
def MainforGernal(startIdx, driver):
    selectName = '나스닥종합'  # 미국모든주식 # 나스닥종합 # 다우존스 # S&P500
    financialSection = '일반 개요'  # 일반 개요 'General Summary'
    filePathforIndex = r'../Infomation\Investing\20220511\StockName\%s.csv' % (selectName)
    filePathforSaving = r'../Infomation\Investing\20220511\StockData_USA'
    # today = '2021-05-09'
    print('-------------- Start MainforGernal Function %s--------------'%(financialSection))
    sys.stdout.flush()
    print('-------------- Start to Check Financial info --------------')
    sys.stdout.flush()
    enName = SetfinancialSectionEn(financialSection)
    filePathforSaving = filePathforSaving + '/' + enName + '/' + selectName
    # filePathforSaving = filePathforSaving + '/' + today
    if not isdir(filePathforSaving): makedirs(filePathforSaving)
    print('Down Location : %s' % (filePathforSaving))
    sys.stdout.flush()
    # index파일리딩.
    indexData = pd.read_csv(filePathforIndex, encoding='cp949', engine='python')
    # 폴더 파일 리스트
    downFiles = [f for f in listdir(filePathforSaving) if isfile(join(filePathforSaving, f))]  # folder내 파일name list
    downFilesfront = [f.replace('.csv','') for f in downFiles]
    # 있는 것은 지우기.
    listforErase = []
    for idx_indexData, rowindexData in indexData.iterrows():
        if rowindexData['종목'] in downFilesfront:
            listforErase.append(idx_indexData)
    indexData.drop(indexData.index[listforErase],inplace=True)
    indexData.reset_index(drop=True, inplace=True)
    print(indexData)
    # 없는 index 파일 포함하여 넘기고 추가로 받기.
    if indexData.empty:
        return True
    url = 'https://kr.investing.com/equities/united-states'
    driver.get(url)
    # 로그인 하고
    LoginInvesting(driver)
    time.sleep(0.1)
    selectID = GetSelectID(selectName)
    print('Stock Index : %s' % (selectName))
    sys.stdout.flush()
    # 미국의 모든주식 드롭박스에서 설정.
    driver.find_element_by_id(selectID).click()
    for i in range(10):
        listOfCompany = driver.find_elements_by_xpath('//*[@id="cross_rate_markets_stocks_1"]/tbody/tr')
        if listOfCompany:
            time.sleep(1.0)
            break
        else:
            time.sleep(1.0)
    startIdx = [0]
    GetGernalData(driver, startIdx, filePathforSaving, indexData, financialSection, selectName)
    # driver.quit()
def GetTablebyBS(driver):
    bs = BeautifulSoup(driver.page_source, 'html.parser')
    table = bs.find_all(id='rrtable')[0].find('table')
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
def GetFinancialSummary(driver, startIdx, filePath, indexData, sectionName,selectName):
    mode = 2
    if mode == 1:
        # 테이블 상 나와있는 text 획득.
        table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
        # 테이블상 종목 으로 테이블상 index획듯.
        companyNames = [table_row.text for table_row in table_rows]
        idxCompanyNames = [companyNames.index(comName) for comName in indexData['종목'].tolist()]
        indexData['테이블상 위치'] = idxCompanyNames
        # 매핑 하여 indexData에 저장.
    for idx_data, row_data in indexData.iterrows():
        if idx_data < startIdx[0]:
            continue
        if mode == 0:
            table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
            thisRow = [row for row in table_rows if row.text == row_data['종목']]  # 시간 많이 걸림.
            if not thisRow:
                continue
            thisRow = thisRow[0]
        elif mode == 1:
            time.sleep(2.5)
            table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
            thisRow = table_rows[row_data['테이블상 위치']]
        elif mode == 2:
            table_rows = driver.find_elements_by_link_text(row_data['종목'])
            if table_rows:
                thisRow = table_rows[0]
            else:
                table_rows = driver.find_element_by_id('cross_rate_markets_stocks_1').find_elements_by_tag_name('a')
                thisRow = [row for row in table_rows if row.text == row_data['종목']]  # 시간 많이 걸림.
                if not thisRow:
                    continue
                thisRow = thisRow[0]

        companyName = thisRow.text
        if row_data['종목'] != companyName:
            print('%s - %s) Downloading Stock Data...%s Fail!!' % (len(indexData), idx_data, companyName))
            sys.stdout.flush()
            continue
        thisRow.click()
        time.sleep(1.5)
        headTxt = [item for item in driver.find_elements_by_tag_name('h1') if '(' in item.text]
        if headTxt:
            headTxt = headTxt[0].text
        else:
            headTxt = companyName
        print('%s - %s) Downloading Stock Data...%s' % (len(indexData), idx_data, headTxt), end='')
        sys.stdout.flush()

        driver.find_element_by_link_text('재정 상황').click()
        time.sleep(1)
        if sectionName != '재무 정보 요약':
            driver.find_element_by_link_text(sectionName).click()
            time.sleep(1)
        # 연간 클릭.
        print('..1', end='')
        sys.stdout.flush()
        try:
            driver.find_element_by_link_text('연간').click()
        except:
            driver.back()
            time.sleep(0.5)
            driver.back()
            time.sleep(0.5)
            if sectionName != '재무 정보 요약':
                driver.back()
                time.sleep(0.5)
            selectID = GetSelectID('미국모든주식')
            driver.find_element_by_id(selectID).click()
            time.sleep(3.0)
            selectID = GetSelectID(selectName)
            driver.find_element_by_id(selectID).click()
            time.sleep(3.0)
            startIdx[0] += 1
            print('...Fail')
            continue
        time.sleep(2)
        print('..2', end='')
        sys.stdout.flush()
        # table
        if sectionName=='재무 정보 요약':
            tables = driver.find_element_by_id('rsdiv').find_elements_by_tag_name('table')
            dfCompanyInfo = GetTable(tables[0])
            GetTableBodyfromTbody(dfCompanyInfo, tables[1].find_element_by_tag_name('tbody'), 0)  # 에러 많이 남.
            GetTableBodyfromTbody(dfCompanyInfo, tables[2].find_element_by_tag_name('tbody'), 0)  # 에러 많이 남.
        else:
            tables = driver.find_element_by_id('rrtable').find_elements_by_tag_name('table')
            # GetTablebySele(tables)
            dfCompanyInfo = GetTablebyBS(driver)
        print('..3', end='')
        sys.stdout.flush()
        # Save
        dfCompanyInfo.replace('', np.nan, inplace=True)
        dfCompanyInfo.replace(' ', np.nan, inplace=True)
        dfCompanyInfo = dfCompanyInfo.dropna(axis=1, how='all').dropna(axis=0, how='all')
        dfCompanyInfo.to_csv(filePath + '/%s.csv' % (companyName.replace('/','')), encoding='cp949', index=False)
        driver.back()
        time.sleep(1.5)
        driver.back()
        time.sleep(0.5)
        if sectionName != '재무 정보 요약':
            driver.back()
            time.sleep(0.5)
        print('...Done!!')
        sys.stdout.flush()
        selectID = GetSelectID('미국모든주식')
        driver.find_element_by_id(selectID).click()
        time.sleep(1.0)
        selectID = GetSelectID(selectName)
        driver.find_element_by_id(selectID).click()
        for i in range(10):
            listOfCompany = driver.find_elements_by_xpath('//*[@id="cross_rate_markets_stocks_1"]/tbody/tr')
            if listOfCompany:
                time.sleep(1.0)
                break
            else:
                time.sleep(1.0)
        popUpBtnActivate = driver.find_elements_by_xpath('/html/body/div[6]/div/div[4]/button[2]')
        if popUpBtnActivate:
            popUpBtnActivate[0].click()  # 활성화 버튼 클릭.
        startIdx[0] += 1
def MainforFinancialSummary(startIdx, driver):
    selectName = '나스닥종합'  # 미국모든주식 # 나스닥종합 # 다우존스 # S&P500
    financialSection = '재무 정보 요약'
    # 재무 정보 요약 'Financial information summary' 손익 계산서'Income Statement'/ 대차 대조표 'Balance sheet'/ 현금흐름 'Cash flow statement'
    filePathforIndex = r'../Infomation\Investing\20220511\StockName\%s.csv' % (selectName)
    filePathforSaving = r'../Infomation\Investing\20220511\StockData_USA'
    # today = '2021-05-09'
    print('-------------- Calling MainforFinancialSummary Function --------------')
    sys.stdout.flush()
    print('-------------- Start to Check Financial info --------------')
    sys.stdout.flush()
    enName = SetfinancialSectionEn(financialSection)
    filePathforSaving = filePathforSaving + '/' + enName + '/' + selectName
    # filePathforSaving = filePathforSaving + '/' + today
    if not isdir(filePathforSaving): makedirs(filePathforSaving)
    print('Down Location : %s' % (filePathforSaving))
    sys.stdout.flush()
    # index파일리딩.
    indexData = pd.read_csv(filePathforIndex, encoding='cp949', engine='python')
    # 폴더 파일 리스트
    downFiles = [f for f in listdir(filePathforSaving) if isfile(join(filePathforSaving, f))]  # folder내 파일name list
    downFilesfront = [f.replace('.csv', '') for f in downFiles]
    # 있는 것은 지우기.
    listforErase = []
    for idx_indexData, rowindexData in indexData.iterrows():
        if rowindexData['종목'] in downFilesfront:
            listforErase.append(idx_indexData)
    indexData.drop(indexData.index[listforErase], inplace=True)
    indexData.reset_index(drop=True, inplace=True)
    print(indexData)
    # 없는 index 파일 포함하여 넘기고 추가로 받기.
    if indexData.empty:
        return True
    url = 'https://kr.investing.com/equities/united-states'
    driver.get(url)
    # 로그인 하고
    LoginInvesting(driver)
    time.sleep(0.1)
    selectID = GetSelectID(selectName)
    print('Stock Index : %s' % (selectName))
    sys.stdout.flush()
    # 미국의 모든주식 드롭박스에서 설정.
    driver.find_element_by_id(selectID).click()
    time.sleep(5)
    startIdx = [0]
    GetFinancialSummary(driver, startIdx, filePathforSaving, indexData, financialSection,selectName)
def MainforDownHistoricalData(startIdx, driver):
    selectName = 'S&P500'  # 미국모든주식 # 나스닥종합 # 다우존스 # S&P500
    filePathforIndex = r'../Infomation\Investing\20220511\StockName\%s.csv' % (selectName)
    # today = '2021-05-10'
    downFolder = r'C:\Users\jhmai\Downloads'
    startDate = '2010/01/01'
    endDate = datetime.date.today().strftime('%Y/%m/%d')
    filePathforSaving = r'../Infomation\Investing\20220511\StockData_USA\Historical_Data\Daily'

    print('-------------- Start to Down Historical Data --------------')
    sys.stdout.flush()
    # filePathforSaving = filePathforSaving + '/' + today
    if not isdir(filePathforSaving): makedirs(filePathforSaving)
    print('Down Location : %s' % (filePathforSaving))
    sys.stdout.flush()
    # index파일리딩.
    indexData = pd.read_csv(filePathforIndex, encoding='cp949', engine='python')
    # 폴더 파일 리스트
    downFiles = [f for f in listdir(filePathforSaving) if isfile(join(filePathforSaving, f))]  # folder내 파일name list
    downFilesfront = [f.replace('.csv', '') for f in downFiles]
    # 있는 것은 지우기.
    listforErase = []
    for idx_indexData, rowindexData in indexData.iterrows():
        if rowindexData['종목'].replace('/','') in downFilesfront:
            listforErase.append(idx_indexData)
    indexData.drop(indexData.index[listforErase], inplace=True)
    # indexData.reset_index(drop=True, inplace=True)
    indexData.reset_index(inplace=True)
    indexData.rename(columns={indexData.columns[0]: "테이블상 위치"},inplace=True)
    # indexData.reset_index(level='테이블상 위치')
    print(indexData)
    # from tabulate import tabulate
    # print(tabulate(indexData, headers='keys', tablefmt='psql'))
    print('Number of Index : %s'%(len(indexData)))
    # 없는 index 파일 포함하여 넘기고 추가로 받기.
    if indexData.empty:
        return True
    url = 'https://kr.investing.com/equities/united-states'
    driver.get(url)
    # 로그인 하고
    LoginInvesting(driver)
    time.sleep(0.1)
    selectID = GetSelectID(selectName)
    print('Stock Index : %s' % (selectName))
    sys.stdout.flush()
    # 미국의 모든주식 드롭박스에서 설정.
    driver.find_element_by_id(selectID).click()
    time.sleep(5)
    startIdx = [0]
    DownHistoricalData(driver, startIdx, startDate, endDate, downFolder, filePathforSaving,indexData,selectName)
def ChangseFormat():
    # index데이터 열고
    selectName = 'S&P500'  # 미국모든주식 # 나스닥종합 # 다우존스 # S&P500
    filePathforIndex = r'../Infomation\Investing\20220511\StockName\%s.csv' % (selectName)
    today = '2022-05-30'
    indexData = pd.read_csv(filePathforIndex, encoding='cp949', engine='python')
    filePath = r'../Infomation\Investing\20220511\StockData_USA\Historical_Data\Daily'
    print('-------------- Start to Change Historical Data --------------')
    sys.stdout.flush()
    filePathforSaving = filePath + '/' + today
    if not isdir(filePathforSaving): makedirs(filePathforSaving)
    print('Down Location : %s' % (filePathforSaving))
    sys.stdout.flush()
    # for문
    for idx_indexData, row_indexData in indexData.iterrows():
        try:
            print('(%s - %s) %s...' % (len(indexData), idx_indexData, row_indexData['종목']), end='')
            sys.stdout.flush()
            # if idx_indexData==23:
            #     print()
            # Stock data열고.
            dfData = pd.read_csv(filePath + '/%s.csv' % (row_indexData['종목']))
            # 날짜	종가	오픈	고가	저가	거래량 만남기고.
            dfData = dfData[['날짜', '오픈', '종가', '고가', '저가', '거래량']]
            # Date	Open	Close	High	Low	Volume 로 변경.
            dfData.columns = ['Date', 'Open', 'Close', 'High', 'Low', 'Volume']
            # 날짜 format을 변경.
            dfData.drop_duplicates(subset=['Date'], inplace=True)
            dfData['Date'] = pd.to_datetime(arg=dfData['Date'], format='%Y년 %m월 %d일')
            dfData.sort_values(by='Date', ascending=True, inplace=True)
            dfData['Date'] = dfData['Date'].dt.strftime('%Y-%m-%d')
            # 다시 저장.
            dfData.to_csv(filePathforSaving + '/%s.csv' % (row_indexData['종목']), encoding='cp949',index=False)
            print('...Done!!!')
            sys.stdout.flush()
        except:
            try:
                dfData = pd.read_csv(filePathforSaving + '/%s.csv' % (row_indexData['종목']),engine='python')
                dfData.columns = ['Date', 'Close', 'Open', 'High', 'Low', 'Volume', 'Change %']
                dfData = dfData[['Date', 'Open', 'Close', 'High', 'Low', 'Volume']]
                dfData['Date'] = pd.to_datetime(arg = dfData['Date'], format = '%Y�뀈 %m�썡 %d�씪')
                dfData.sort_values(by='Date', ascending=True, inplace=True)
                dfData.drop_duplicates(subset=['Date'], inplace=True)
                dfData['Date'] = dfData['Date'].dt.strftime('%Y-%m-%d')
                dfData.to_csv(filePathforSaving + '_changed/%s.csv' % (row_indexData['종목']), encoding='cp949',
                                 index=False)
                print('...Done!!!')
                continue
            except:
                # os.remove(filePathforSaving + '/%s.csv' % (row_indexData['종목']))
                # if os.path.exists(filePathforSaving + '/%s.csv' % (row_indexData['종목'])):
                #     os.remove(filePathforSaving + '/%s.csv' % (row_indexData['종목']))
                print('...Fail!!!')
                sys.stdout.flush()
                continue
    print('-------------- End to Change Historical Data --------------')
def SaveErrorScreenShot(driver, saveFolder, FileName):
    if not isdir(saveFolder): makedirs(saveFolder)
    # 파일 리스트
    files = listdir(saveFolder)
    downFile = [file for file in files if FileName.replace('.png','') in file]
    # 파일 이름 정하기.
    fileURL = saveFolder+'/'+ FileName.replace('.png','_%s.png'%(len(downFile)))
    # 저장하기.
    driver.save_screenshot(fileURL)
    print('Error ScreenShot FileName : %s'%(FileName.replace('.png','_%s.png'%(len(downFile)))))

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
            options = webdriver.ChromeOptions()
            # options.add_argument('headless')
            # # options.add_argument('window-size=1920x1080')
            # options.add_argument("disable-gpu")
            driver = webdriver.Chrome(r'../Setting\chromdriver\chromedriver.exe', options=options)
            driver.implicitly_wait(3)
            driver.set_window_position(-2000, 0)
            driver.maximize_window()

            # Main(startIdx)    # 손익 계산서'Income Statement'/ 대차 대조표 'Balance sheet'/ 현금흐름 'Cash flow statement'
            # MainforCheck(startIdx)      # Income Statement
            # MainforRename()

            # 일반 개요 'General Summary'
            # MainforGernal(startIdx, driver)

            # 재무 정보 요약 'Financial information summary' 손익 계산서'Income Statement'/ 대차 대조표 'Balance sheet'/ 현금흐름 'Cash flow statement'
            # MainforFinancialSummary(startIdx, driver)

            # MainforDownHistoricalData(startIdx, driver)
            ChangseFormat()
            driver.quit()
            break

        except Exception as e:
            SaveErrorScreenShot(driver, saveFolder=r'../Infomation\Investing\20220511\ScreenShot', FileName='Nasdaq.png')

            print(e)
            print('----------   Error occurred!!   ----------')
            if startIdx[0]!=0:
                startIdx[0]-=1
            driver.quit()
            continue