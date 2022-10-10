from selenium import webdriver
import datetime,time
from os import listdir,makedirs
from os.path import isfile, join, isdir
import shutil
import pandas as pd
import numpy as np
import os
import Quanti.CalenderTest as CalenderTest

def DownStockCodeETF():
    today = datetime.datetime.today()
    downDate = CalenderTest.GetNearWorkingDayDate(today)
    driver = webdriver.Chrome(r'./Setting\chromdriver\chromedriver.exe')
    driver.implicitly_wait(0.1)
    url = 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201030104'
    driver.get(url)
    time.sleep(2)
    # driver.find_element_by_xpath("//img[@title='다운로드 팝업']").click()  # 다운로드 클릭.
    driver.find_element_by_class_name('CI-MDI-UNIT-DOWNLOAD').click()  # 다운로드 클릭.
    time.sleep(1)
    driver.find_element_by_link_text('CSV').click()
    time.sleep(10)
    driver.close()
def DownStockCode(field):
    if field=='total':
        field = 0
    elif field=='kospi':
        field = 1
    elif field == 'kosdaq':
        field = 2
    elif field == 'konex':
        field = 3
    driver = webdriver.Chrome(r'./Setting\chromdriver\chromedriver.exe')
    driver.implicitly_wait(0.1)
    url = 'http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201020201'
    driver.get(url)
    selectBox = driver.find_element_by_id('MDCSTAT019_FORM').find_elements_by_tag_name('label')
    #[item for item in selectBox if field==item.text]
    # selectBox = driver.find_elements_by_css_selector('#formc81e728d9d4c2f636f067f89cc14862c > dl:nth-child(1) > dd > input')
    selectBox[field].click()
    time.sleep(2)
    driver.find_element_by_id('MDCSTAT019_FORM').find_element_by_link_text('조회').click()    # 조회 클릭
    driver.find_element_by_id('MDCSTAT019_FORM').find_element_by_class_name('CI-MDI-UNIT-DOWNLOAD').click()     # 다운로드 클릭.
    driver.find_element_by_css_selector('#mdiDownloadModal0').find_element_by_link_text('CSV').click()
    time.sleep(10)
    driver.close()
def MoveFile(dst):
    src=r'C:\Users\jhmai\Downloads/'
    # stockFolder = './NaverAnalysis/'
    srcFiles = [f for f in listdir(src) if isfile(join(src, f))]  # folder내 파일name list
    srcFile = [filename for filename in srcFiles if 'data' in filename]
    for file in srcFile:
        # os.rename("path/to/current/file.foo", "path/to/new/destination/for/file.foo")
        if not os.path.isdir(dst): os.makedirs(dst)
        shutil.move(src+file, dst+'/'+file)
    return srcFile
def PostTreatStockCode(src,dst):
    #read data and change file name and save file
    if src.split('.')[-1]=='xls':
        data = pd.read_excel(src, error_bad_lines=False)
    elif src.split('.')[-1]=='csv':
        try:
            data = pd.read_csv(src, error_bad_lines=False, encoding='cp949')
        except:
            data = pd.read_csv(src,error_bad_lines=False)
    # data.dropna(subset=['종목코드'], how='all',inplace=True)
    if 'Unnamed: 0' in data.columns:
        del data['Unnamed: 0']
    data.dropna(thresh=5, inplace=True)
    # data.dropna(how='any', inplace=True)
    changeName = {'단축코드': '종목코드', '한글 종목약명': '종목명'}
    for key, value in changeName.items():
        if key in data.columns:
            data.rename(columns={key: value}, inplace=True)
    data.to_csv(dst,encoding='cp949',index=False)
def main(field, saveFolder):
    if field.upper()=='ETF':
        DownStockCodeETF()
    else:
        DownStockCode(field=field)
    srcFiles = MoveFile(dst=saveFolder)
    today = datetime.datetime.today()
    today_str = today.strftime('%Y%m%d')
    dstFile = saveFolder + '/%s_%s.csv' % (field, today_str)
    for srcFile in srcFiles:
        PostTreatStockCode(src=saveFolder + '/' + srcFile, dst=dstFile)
        # remove files
        os.remove(saveFolder + '/' + srcFile)
    print("Finish DownCode for %s" % (field))
if __name__ == '__main__':
    field = 'kospi'
    saveFolder = './Stock_data_total/'
    DownStockCode(field=field)
    MoveFile(dst=saveFolder)
    today = datetime.datetime.today()
    today_str = today.strftime('%Y%m%d')
    dstFile = saveFolder+'%s_%s.csv'%(field,today_str)
    PostTreatStockCode(src=saveFolder+'data.csv',dst=dstFile)
    #remove files
    os.remove(saveFolder+'data.csv')
    # copy files
    # src = stockFolder+'kospi_%s.csv'%(today_str)
    dst = 'G:/PycharmProjects_20171228/stock/Quanti/NaverAnalysis/'
    shutil.copy(dstFile, dst)
