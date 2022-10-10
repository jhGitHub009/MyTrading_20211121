import pandas as pd
from os import listdir,makedirs
from os.path import isfile, join, isdir
import datetime,time
from selenium import webdriver
import random
import sys
import numpy as np
import Quanti.MyLibrary_20180702 as MyLib

def GetNaverFSQCrawl(filename):
    date = '20210501'
    save_folder = './NaverAnalysis/%s/기업현황/'%(date)
    df_code = pd.read_csv('./StockCode/'+filename, encoding='cp949')
    # check list
    downfiles = [f for f in listdir(save_folder) if isfile(join(save_folder, f))]
    downCodes = [file.split('_')[1].replace('.csv', '') for file in downfiles]
    missedCode = MyLib.GetMissedCode(df_code['종목코드'].tolist(), downCodes)
    df_code = df_code[df_code['종목코드'].isin(missedCode)]

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    # options.add_argument('window-size=1920x1080')
    # options.add_argument("disable-gpu")
    driver = webdriver.Chrome('C:/Users/user/chromedriver.exe', chrome_options=options)
    # driver = webdriver.Chrome('C:/Users/user/chromedriver')
    driver.implicitly_wait(1)
    for idx_df_code, row_df_code in df_code.iterrows():
        # if idx_df_code < 224:
        #     continue
        Code = str(row_df_code['종목코드']).zfill(6)
        Company = row_df_code['종목명']
        print('%s) Code : %s  || Company : %s start......' % (idx_df_code, Code, Company), end='')
        sys.stdout.flush()
        beaktime = random.randrange(1, 4)
        time.sleep(beaktime)
        GetNaverFinancialSummeryQuater(driver, Code, Company, save_folder)  # 기업현황 > financial_summery
        print('Done!!')
    driver.quit()
def GetNaverFinancialSummeryQuater(driver,code,company_name,folder):
    url = 'http://companyinfo.stock.naver.com/v1/company/c1010001.aspx?cmp_cd=' + code
    driver.get(url)
    col_names=[]
    time.sleep(0.5)
    period_selector={}
    for selector in driver.find_elements_by_css_selector('#cTB00 > tbody > tr > td'):
        if selector.text!='':
            period_selector[selector.text]=selector
    period_selector['연간'].click()   # click 분기.
    tables = driver.find_elements_by_class_name('gHead01')
    table = [table for table in tables if '주요재무정보' in table.text][0]
    col_names.append(table.find_element_by_css_selector('thead > tr:nth-child(1) > th').text)
    for col_name in table.find_elements_by_css_selector('thead > tr:nth-child(2) > th'):
        data_temp = col_name.text
        col_names.append(data_temp)
    df_financail = pd.DataFrame(columns=col_names)
    time.sleep(0.5)
    table_body = table.find_elements_by_css_selector('tbody > tr')
    for row in table_body:
        row_data = []
        for element in row.find_elements_by_css_selector('th'):
            row_data.append(element.text)
        for element in row.find_elements_by_css_selector('td'):
            row_data.append(element.text)
        df_financail.loc[len(df_financail)] = row_data
    df_financail.replace('', np.nan, inplace=True)
    df_financail.replace(' ', np.nan, inplace=True)
    df_financail = df_financail.dropna(axis=1, how='all').dropna(axis=0, how='all')
    this_folder = folder
    if not isdir(this_folder): makedirs(this_folder)
    df_financail.to_csv(this_folder+company_name+'_'+code+'.csv',encoding='cp949',index=False)
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
        print('%s) Code : %s  || Company : %s start......' % (idx, Code, Company), end='')
        sys.stdout.flush()
        beaktime = random.randrange(1, 4)
        time.sleep(beaktime)
        GetNaverFinancialSummeryQuater(driver, Code, Company, save_folder)  # 기업현황 > financial_summery
        print('Done!!')
if __name__ == '__main__':
    filename = 'kosdaq_20210429.csv'
    GetNaverFSQCrawl(filename)