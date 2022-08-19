import pandas as pd
from os import listdir,makedirs, remove
from os.path import isfile, join, isdir, exists
import datetime,time
from selenium import webdriver
import random
import sys
import numpy as np
import copy
import Quanti.BasicFomula as bf

def GetDates(driver):
    listOfDate = [elem.text for elem in driver.find_element_by_id('ft-id-4').find_elements_by_tag_name('li')]  # 체크박스 개채
    return listOfDate
def GetSelectedDates(driver):
    listOfDate = [elem.text for elem in driver.find_element_by_id('ft-id-4').find_elements_by_tag_name('li') if 'selected' in elem.find_element_by_xpath('span').get_attribute('class')]
    return listOfDate
# 왼쪽 탐색 fucn
def LeftBarSelection(driver, secNames):
    driver.switch_to.frame(driver.find_element_by_id("iframe_leftMenu"))
    time.sleep(1.5 * sleepCon)
    # 아파트 매매 실거래 평균가격
    for secName in secNames:
        leftItems = driver.find_elements_by_tag_name('span')
        item = [item for item in leftItems if secName in item.text]
        if len(item)==1:
            upTag = item[0].find_element_by_xpath('..')
            if upTag.tag_name=='a':
                upTag.click()
    # # driver.find_element_by_id('treeDown_DT_KAB_11672_S15').click()
    # driver.find_element_by_id('treeDown_DT_KAB_11672_S25').click()
    # # 미분양주택현황보고-
    # driver.find_element_by_id('I1_2').click()
    # # driver.find_element_by_link_text('미분양주택현황보고').click()
    # time.sleep(1.5 * sleepCon)
    # # driver.find_element_by_link_text('시・군・구별 미분양현황 (월 2000.12~2021.11)').click()
    # driver.find_element_by_id('treeDown_DT_MLTM_2082').click()

    driver.switch_to.default_content()
# 시점버튼
def GetPeriodInst(driver):
    for elem in driver.find_elements_by_tag_name('button'):
        if elem.text == '시점':
            return elem
# 전체해제 클릭
def ToggleAllSelectBtn(driver, selectFlag):
    btn = [item for item in driver.find_elements_by_tag_name('button') if '전체해제' in item.text or '선택해제' in item.text][0]
    if btn.text==selectFlag:
        btn.click()
    else:
        while True:
            btn.click()
            if btn.text=='선택해제':
                btn.click()
                return
# 안받은 데이터 inst가져옴 func.
def GetUnreceivedDate(driver, received):
    datesItem = [item for item in driver.find_elements_by_tag_name('li') if '2020.' in item.text][0]
    datesItem = datesItem.find_element_by_xpath('..')
    temp = datesItem.find_elements_by_tag_name('li')
    for elem in received:
        temp.remove(elem)
    return temp
# 체크박스 클릭
def CheckUnReivedDate(driver, unReceived):
    selectedDate = []
    for elem in unReceived:
        elem.click()
        time.sleep(0.5)
        numOfData = int(driver.find_element_by_id('changePopTextLi').text.split('=')[1].replace(',', ''))  # 데이터 갯수
        if numOfData < 20000:# 셀넘버확인
            selectedDate.append(elem)
            continue
        else:
            elem.click()
            return selectedDate
    return selectedDate
# 다운로드 func
def DownData(driver):
    # 적용버튼
    time.sleep(0.5 * sleepCon)
    driver.find_element_by_id('searchPopBtn').find_elements_by_tag_name('button')[0].click()
    # 다운로드 버튼
    time.sleep(7.0 * sleepCon)
    driver.find_element_by_id('ico_download').click()
    # csv 체크
    time.sleep(0.5 * sleepCon)
    # driver.find_element_by_id('pop_downgrid')
    driver.find_element_by_id('csvradio').click()
    # 다운
    time.sleep(0.5 * sleepCon)
    driver.find_element_by_link_text('다운로드').click()
    # 다운로드 닫기버튼
    time.sleep(0.5 * sleepCon)
    driver.find_element_by_link_text('X 닫기').click()

# options = webdriver.ChromeOptions()
# options.add_argument('headless')
# # options.add_argument('window-size=1920x1080')
# # options.add_argument("disable-gpu")
# driver = webdriver.Chrome('../Setting/chromedriver.exe', chrome_options=options)
# # driver = webdriver.Chrome('C:/Users/user/chromedriver')
# driver.implicitly_wait(1)
#
# sleepCon = 2
# driver = webdriver.Chrome(r'../Setting\chromdriver\chromedriver.exe')
# driver.implicitly_wait(1)
# driver.set_window_position(-2000, 0)
# driver.maximize_window()
# url = 'https://kosis.kr/statHtml/statHtml.do?orgId=408&tblId=DT_KAB_11672_S19&vw_cd=MT_ZTITLE&list_id=I1_1&scrId=&seqNo=&lang_mode=ko&obj_var_id=&itm_id=&conn_path=MT_ZTITLE&path=%252FstatisticsList%252FstatisticsListIndex.do'
# driver.get(url)
# # 왼쪽 탐색
# # secNames = ['아파트 매매 실거래 평균가격']
# # secNames = ['아파트 전세 실거래 평균가격']
# secNames = ['전국주택가격동향조사','전국주택가격동향(기준월: 2021.06)','주요지역별 전세수급동향 (월 2013.01~2022.01)']
# # secNames = ['민간아파트분양시장동향','지역별 3.3㎡당 평균 분양가격']
# # secNames = ['민간아파트분양시장동향','지역별 민간아파트 평균 초기분양률 (분기 2015 3/4~2021 3/4)']
# # secNames = ['민간아파트분양시장동향','지역별 민간아파트 평균 초기분양률 (분기 2014 3/4~2015 2/4)']
# # secNames = ['민간아파트분양시장동향','지역별 신규 분양세대수 (월 2015.10~2022.01)']
# # secNames = ['민간아파트분양시장동향','지역별 신규 분양세대수 (월 2013.12~2015.09)']
# # secNames = ['미분양주택현황보고','시・군・구별 미분양현황','시・군・구별_미분양현황']
# LeftBarSelection(driver, secNames)
# time.sleep(2)
# driver.switch_to.frame(driver.find_element_by_id("iframe_rightMenu"))
# driver.switch_to.frame(driver.find_element_by_id('iframe_centerMenu2'))
# # get 시점버튼
# periodBtn = GetPeriodInst(driver)
# # Get all date Inst
# if 'block' not in driver.find_element_by_id('pop_timeSet').get_attribute('style'):
#     periodBtn.click()
# time.sleep(0.5 * sleepCon)
#
# datesItem = [item for item in driver.find_elements_by_tag_name('li') if '.' in item.text][0]
# datesItem = datesItem.find_element_by_xpath('..')
# # if driver.find_elements_by_id('timePopListM'):
# #     listOfAllDate = driver.find_element_by_id('timePopListM').find_elements_by_tag_name('li')
# # elif driver.find_elements_by_id('timePopListQ'):
# #     listOfAllDate = driver.find_element_by_id('timePopListQ').find_elements_by_tag_name('li')
# listOfAllDate = datesItem.find_elements_by_tag_name('li')
# periodBtn.click()
# receivedData = []
# while listOfAllDate!=receivedData:
#     periodBtn.click()
#     ToggleAllSelectBtn(driver, '전체해제')
#     unReceived = GetUnreceivedDate(driver, received=receivedData)
#     selectedDate = CheckUnReivedDate(driver, unReceived)
#     receivedData = receivedData + selectedDate
#     DownData(driver)
# time.sleep(2)
# # 받은 데이터 merge
# downFolder = r'C:\Users\jhmai\Downloads'
# downfiles = [f for f in listdir(downFolder) if isfile(join(downFolder, f))]
# downFileName = secNames[-1].split('(')[0]
# downFileName = downFileName.replace(' ','_')
# downfiles = [f for f in downfiles if downFileName in f]
#
# for idx,file in enumerate(downfiles):
#     dfData = pd.read_csv(downFolder +'/'+ file,encoding='cp949',engine='python')
#     if idx==0:
#         dfMerged = copy.deepcopy(dfData)
#     else:
#         dfMerged = pd.concat([dfMerged, dfData], axis=1)
#         dfMerged = dfMerged.loc[:, ~dfMerged.columns.duplicated()]
#         newList = sorted(set(dfMerged.columns))
#         newList.insert(0, newList.pop(-1))
#         newList.insert(0, newList.pop(-1))
#         dfMerged = dfMerged[newList]
#
# saveURL = './RealEstate'
# if not isdir(saveURL): makedirs(saveURL)
# fileName = saveURL+'/' + secNames[-1].replace(' ','_')+'.csv'
# dfMerged.to_csv(fileName,encoding='cp949')
# driver.close()
#
# for idx,file in enumerate(downfiles):
#     file_path = downFolder +'/'+ file
#     if exists(file_path):
#         remove(file_path)
#
# # 시점버튼누르고, 전체해제, 안받은 데이터 조회, 체크박스 클릭, 셀넘버 확인및 비교,
# # 체크박스클릭, 셀넘버 확인및 비교
# # 체크박스클릭, 셀넘버 확인및 비교
# # 다운로드
# # 시점버튼누르고, 전체해제, 안받은 데이터 조회, 체크박스 클릭, 셀넘버 확인및 비교,
# # 체크박스클릭, 셀넘버 확인및 비교
# # 체크박스클릭, 셀넘버 확인및 비교
# # 다운로드
# # 받은 데이터 merge
# # move and save

# read data
# data = pd.read_csv(r'./RealEstate\아파트_매매_실거래_평균가격.csv',engine='python',encoding='cp949')
# # firstCol = data.columns[0]
# # secCol = data.columns[1]
# data_columns = data[data.columns[0]] +'('+ data[data.columns[1]] +')'
# data = data.transpose()
# data.columns = data_columns.tolist()
# data.drop(data.index[0:2],inplace=True)
# data.reset_index(inplace=True)
# tempIdx = (data[data["index"].str.contains('\.09')].index+1).tolist()
# data.loc[tempIdx,'index'] = data.loc[tempIdx].apply(lambda x: str(x['index']).replace('.1','.10'),axis=1)
# data.set_index(pd.to_datetime(data[data.columns[0]]),inplace=True)
# data.drop(data.columns[0],axis=1,inplace=True)
# for col in data.columns.tolist():
#     temp = data[[col]]
#     temp.to_csv(r'./RealEstate\아파트_매매_실거래_평균가격_%s.csv'%(col),encoding='cp949')

data = pd.read_csv(r'./RealEstate\아파트_매매_실거래_평균가격_서울(서울).csv',engine='python',encoding='cp949')
data.set_index(pd.to_datetime(data[data.columns[0]]),inplace=True)
data.drop(data.columns[0],axis=1,inplace=True)
data['TimeDelta'] = data.index.tolist()
# data.insert(0,'TimeDelta',data.index)
data['TimeDelta'] = data.apply(lambda x: bf.GetYear(data.index[0], x['TimeDelta']),axis=1)
# data['전국(소계)'] = pd.to_numeric(data['전국(소계)'])
listCAGR = []
for i in range(len(data)):
    listCAGR.append(bf.GetCAGR(data.iloc[0][data.columns[0]], data.iloc[i][data.columns[0]], data.iloc[i]['TimeDelta']))
# CAGR_All = GetCAGR(294.6, 413.1, years)
# Expect_All      = GetFinalAsset(_initalAsset=294.6, _cagr=CAGR_All2, _times=years)
data['CAGR'] = listCAGR
data.to_csv(r'./RealEstate\아파트_매매_실거래_평균가격_서울(서울).csv',encoding='cp949')
# cagr =
# expPrice = []
# for i in range(len(data)):
#     listCAGR.append(bf.GetFinalAsset(data.iloc[0][data.columns[0]], data.iloc[i][data.columns[0]], data.iloc[i]['TimeDelta']))
print()
