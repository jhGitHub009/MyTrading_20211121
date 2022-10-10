import pandas as pd
from os import listdir,makedirs
from os.path import isfile, join, isdir
import datetime,time
from selenium import webdriver
import random
import sys
import numpy as np
import Quanti.MyLibrary_20180702 as MyLib
def GetNaverStatementIndex(driver,code,company_name,folder='',item=''):
    url = 'http://companyinfo.stock.naver.com/v1/company/c1010001.aspx?cmp_cd=' + code
    driver.get(url)
    driver.find_element_by_css_selector('#header-menu > div.wrapper-menu > dl > dt:nth-child(4)').click()  # 재무분석 클릭
    if item != '가치분석':
        driver.find_element_by_link_text(item).click()
    # driver.find_element_by_css_selector('#rpt_tab2').click()
    # '#rpt_td2'
    col_names=[]
    time.sleep(0.5)
    table = driver.find_element_by_id('wrapper')
    time.sleep(1)
    table = table.find_elements_by_css_selector('div>table')
    if item == '가치분석':
        itemSearchWord = 'EPS'
    elif item == '수익성':
        itemSearchWord = '매출총이익률'
    elif item == '성장성':
        itemSearchWord = '매출액증가율'
    elif item == '안정성':
        itemSearchWord = '부채비율'
    elif item == '활동성':
        itemSearchWord = '총자산회전율'
    idxTable = [idx for idx,data in enumerate(table) if itemSearchWord in data.text][0]
    table = table[idxTable]
    for col_name in table.find_elements_by_css_selector('thead > tr > th'):
        driver.execute_script("arguments[0].style.display = 'inline';", col_name)
        data_temp = col_name.text
        data_temp = data_temp.replace('(IFRS연결)', '')
        data_temp = data_temp.replace('연간컨센서스보기', '')
        data_temp = data_temp.replace('(YoY)', '').strip()
        col_names.append(data_temp)
    df_StatementIndex = pd.DataFrame(columns=col_names)
    time.sleep(0.5)
    for row in table.find_elements_by_css_selector('tbody > tr'):
        row_data = []
        driver.execute_script("arguments[0].style.display = 'inline';", row)
        for element in row.find_elements_by_css_selector('td'):
            driver.execute_script("arguments[0].style.display = 'inline';", element)
            row_data.append(element.text)
        df_StatementIndex.loc[len(df_StatementIndex)] = row_data
    df_StatementIndex.set_index('항목', inplace=True)
    if folder=='':
        return df_StatementIndex
    if not isdir(folder): makedirs(folder)
    df_StatementIndex.to_csv(folder + company_name + '_' + code + '.csv', encoding='cp949')
def main(driver, dfCompanyInfo, save_folder, item):
    # check list
    if not isdir(save_folder):
        makedirs(save_folder)
    else:
        downfiles = [f for f in listdir(save_folder) if isfile(join(save_folder, f))]
        downCodes = [file.split('_')[1].replace('.csv', '') for file in downfiles]
        missedCode = MyLib.GetMissedCode(dfCompanyInfo['종목코드'].tolist(), downCodes)
        dfCompanyInfo = dfCompanyInfo[dfCompanyInfo['종목코드'].isin(missedCode)]

    for idx, data in dfCompanyInfo.iterrows():
        Code = str(data['종목코드']).zfill(6)
        Company = data['종목명']
        if Code=='412930':
            continue
        print('%s) Code : %s  || Company : %s start......' % (idx, Code, Company), end='')
        sys.stdout.flush()
        beaktime = random.randrange(1, 4)
        time.sleep(beaktime)
        GetNaverStatementIndex(driver, Code, Company, save_folder, item)  # 투자지표 > 수익성 > 가치분석라인
        print('Done!!')
if __name__ == '__main__':
    date = '20210501'
    item = '가치분석'    # 가치분석, 수익성, 성장성, 안정성, 활동성
    save_folder = './NaverAnalysis/%s/투자지표/%s/'%(date,item)
    kospi200 = pd.read_csv('./StockCode/kosdaq_20210429.csv', encoding='cp949')
    # check list
    downfiles = [f for f in listdir(save_folder) if isfile(join(save_folder, f))]
    downCodes = [file.split('_')[1].replace('.csv', '') for file in downfiles]
    missedCode = MyLib.GetMissedCode(kospi200['종목코드'].tolist(), downCodes)
    kospi200 = kospi200[kospi200['종목코드'].isin(missedCode)]

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    # options.add_argument('window-size=1920x1080')
    options.add_argument("--start-maximized")
    # options.add_argument("disable-gpu")
    driver = webdriver.Chrome('C:/Users/user/chromedriver.exe', chrome_options=options)
    # driver = webdriver.Chrome('C:/Users/Administrator/chromedriver')
    driver.implicitly_wait(1)
    for idx_kospi200, row_kospi200 in kospi200.iterrows():
        if idx_kospi200<0:
            continue
        # Code = str(kospi200.loc[idx_kospi200]['Code']).zfill(6)
        # Company = kospi200.loc[idx_kospi200]['Company']
        Code = str(kospi200.loc[idx_kospi200]['종목코드']).zfill(6)
        Company = kospi200.loc[idx_kospi200]['종목명']
        print('%s) Code : %s  || Company : %s start......' % (idx_kospi200, Code, Company), end='')
        sys.stdout.flush()
        beaktime = random.randrange(1, 4)
        time.sleep(beaktime)
        GetNaverStatementIndex(driver, Code, Company, save_folder,item)      # 투자지표 > 수익성 > 가치분석라인
        print('Done!!')
    driver.quit()
