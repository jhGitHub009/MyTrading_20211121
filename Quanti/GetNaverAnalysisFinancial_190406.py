import pandas as pd
from os import listdir,makedirs
from os.path import isfile, join, isdir
import datetime,time
from selenium import webdriver
import random
import sys
import numpy as np
import Quanti.MyLibrary_20180702 as MyLib
import logging
from selenium.webdriver.remote.remote_connection import LOGGER
LOGGER.setLevel(logging.WARNING)

def GetNaverFinancialStatement(driver,code,company_name,folder,item):
    url = 'http://companyinfo.stock.naver.com/v1/company/c1010001.aspx?cmp_cd=' + code
    driver.get(url)
    driver.find_element_by_css_selector('#header-menu > div.wrapper-menu > dl > dt:nth-child(3)').click()  # 재무분석 클릭
    if item=='포괄손익계산서':
        item_Num = '#rpt_tab1'
    elif item=='재무상태표':
        item_Num = '#rpt_tab2'
    elif item == '현금흐름표':
        item_Num = '#rpt_tab3'
    driver.find_element_by_css_selector(item_Num).click()
    # '#rpt_td2'
    col_names=[]
    time.sleep(0.5)
    wrapper = driver.find_element_by_css_selector('#wrapper')
    time.sleep(1)
    table = wrapper.find_elements_by_tag_name('table')[-1]
    for col_name in table.find_elements_by_css_selector('thead > tr > th'):
        driver.execute_script("arguments[0].style.display = 'inline';", col_name)
        data_temp = col_name.text
        data_temp = data_temp.replace('(IFRS연결)','')
        data_temp = data_temp.replace('연간컨센서스보기', '')
        data_temp = data_temp.replace('(YoY)', '').strip()
        col_names.append(data_temp)
    df_financail = pd.DataFrame(columns=col_names)
    time.sleep(0.5)
    table = table.find_elements_by_css_selector('tbody > tr')
    for row in table:
        row_data = []
        for element in row.find_elements_by_css_selector('td'):
            driver.execute_script("arguments[0].style.display = 'inline';", element)
            row_data.append(element.text)
        df_financail.loc[len(df_financail)] = row_data
    df_financail.replace('', np.nan, inplace=True)
    df_financail.replace(' ', np.nan, inplace=True)
    df_financail = df_financail.dropna(axis=1, how='all').dropna(axis=0, how='all')
    df_financail['항목']=df_financail['항목'].str.replace('펼치기', '').str.strip()
    df_financail.set_index('항목', inplace=True)
    if not isdir(folder): makedirs(folder)
    df_financail.to_csv(folder+company_name+'_'+code+'.csv',encoding='cp949')
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
        # Code = str(row_kospi['단축코드']).zfill(6)
        # Company = row_kospi['한글 종목명']
        print('%s) Code : %s  || Company : %s start......' % (idx, Code, Company), end='')
        sys.stdout.flush()
        beaktime = random.randrange(1, 4)
        time.sleep(beaktime)
        GetNaverFinancialStatement(driver, Code, Company, save_folder, item)  # 재무분석 > 재무상태표 >
        print('Done!!')
if __name__ == '__main__':
    date = '20210501'
    item = '현금흐름표'        # 포괄손익계산서, 재무상태표, 현금흐름표
    save_folder = './NaverAnalysis/%s/재무분석/%s/'%(date,item)
    kospi = pd.read_csv('./StockCode/kosdaq_20210429.csv', encoding='cp949')
    # check list
    downfiles = [f for f in listdir(save_folder) if isfile(join(save_folder, f))]
    downCodes = [file.split('_')[1].replace('.csv', '') for file in downfiles]
    missedCode = MyLib.GetMissedCode(kospi['종목코드'].tolist(),downCodes)
    kospi = kospi[kospi['종목코드'].isin(missedCode)]

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    # options.add_argument('window-size=1920x1080')
    options.add_argument("--start-maximized")
    # options.add_argument("disable-gpu")
    driver = webdriver.Chrome(r'C:\Users\user\chromedriver.exe', chrome_options=options)
    # driver = webdriver.Chrome('C:/Users/Administrator/chromedriver')
    driver.implicitly_wait(1)
    for idx_kospi, row_kospi in kospi.iterrows():
        if idx_kospi < 0:
            continue
        Code = str(row_kospi['종목코드']).zfill(6)
        Company = row_kospi['종목명']
        # Code = str(row_kospi['단축코드']).zfill(6)
        # Company = row_kospi['한글 종목명']
        print('%s) Code : %s  || Company : %s start......' % (idx_kospi, Code, Company), end='')
        sys.stdout.flush()
        beaktime = random.randrange(1, 4)
        time.sleep(beaktime)
        GetNaverFinancialStatement(driver, Code, Company, save_folder, item)  # 재무분석 > 재무상태표 >
        print('Done!!')
    driver.quit()
