import pandas as pd
from os import listdir,makedirs
from os.path import isfile, join, isdir
import datetime,time
from selenium import webdriver
import numpy as np
import random
import sys
import Quanti.MyLibrary_20180702 as MyLib

def GetNaverFinancialInfo(driver,code,company_name,save_folder):
    url = 'http://companyinfo.stock.naver.com/v1/company/c1010001.aspx?cmp_cd=' + code
    driver.get(url)
    time.sleep(0.5)
    driver.find_element_by_css_selector('#header-menu > div.wrapper-menu > dl > dt:nth-child(7)').click()   # 섹터분석 클릭

    charts = driver.find_element_by_css_selector('#wrapper').find_elements_by_class_name("half")
    for idx,chart in enumerate(charts):
        col_names = []
        time.sleep(0.5)
        title = chart.text.split()[0]
        table = chart.find_element_by_class_name('list').find_element_by_tag_name('table')
        for col_row in table.find_elements_by_css_selector('thead > tr > th'):  # 첫행
            driver.execute_script("arguments[0].style.display = 'inline';", col_row)
            data_temp = col_row.text
            # if data_temp != '':
            #     col_names.append(data_temp)
            col_names.append(data_temp)
        dfTable = pd.DataFrame(columns=col_names)
        time.sleep(0.5)
        for row_data in table.find_elements_by_css_selector('tbody > tr'):
            driver.execute_script("arguments[0].style.display = 'inline';", row_data)
            data = []
            for element in row_data.find_elements_by_css_selector('td'):
                driver.execute_script("arguments[0].style.display = 'inline';", element)
                data_temp = element.text
                data.append(data_temp.strip())
            if data:
                dfTable.loc[len(dfTable)] = data
        thisSaveFolder = save_folder + '%s/'%(title)
        if not isdir(thisSaveFolder): makedirs(thisSaveFolder)
        dfTable.to_csv(thisSaveFolder + company_name + '_' + code + '.csv', encoding='cp949')
def main(driver, dfCompanyInfo, save_folder, item):
    # check list
    if not isdir(save_folder):
        makedirs(save_folder)
    else:
        folderlist = [f for f in listdir(save_folder) if isdir(join(save_folder, f))]
        if len(folderlist)==8:
            downfiles = [f for f in listdir(save_folder+'매출총이익률') if isfile(join(save_folder+'매출총이익률', f))]
            downCodes = [file.split('_')[1].replace('.csv', '') for file in downfiles]
            missedCode = MyLib.GetMissedCode(dfCompanyInfo['종목코드'].tolist(), downCodes)
            dfCompanyInfo = dfCompanyInfo[dfCompanyInfo['종목코드'].isin(missedCode)]
    for idx, data in dfCompanyInfo.iterrows():
        Code = str(data['종목코드']).zfill(6)
        Company = data['종목명']
        print('%s) Code : %s  || Company : %s start......' % (idx, Code, Company), end='')
        sys.stdout.flush()
        beaktime = random.randrange(1, 10)
        time.sleep(beaktime)
        GetNaverFinancialInfo(driver, Code, Company, save_folder)
        print('Done!!')
if __name__ == '__main__':
    date = '20210501'
    save_folder = './NaverAnalysis/%s/Sector/'%(date)
    kospi = pd.read_csv('./StockCode/kosdaq_20210429.csv', encoding='cp949')
    # check list
    downfiles = [f for f in listdir(save_folder) if isfile(join(save_folder, f))]
    downCodes = [file.split('_')[1].replace('.csv', '') for file in downfiles]
    missedCode = MyLib.GetMissedCode(kospi['종목코드'].tolist(), downCodes)
    kospi = kospi[kospi['종목코드'].isin(missedCode)]

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    # # options.add_argument('window-size=1920x1080')
    options.add_argument("--start-maximized")
    # options.add_argument("disable-gpu")
    driver = webdriver.Chrome('C:/Users/user/chromedriver.exe', chrome_options=options)
    # driver = webdriver.Chrome('C:/Users/Administrator/chromedriver')
    driver.implicitly_wait(1)
    for idx_kospi, row_kospi in kospi.iterrows():
        if idx_kospi<367:
            continue
        Code = str(row_kospi['종목코드']).zfill(6)
        Company = row_kospi['종목명']

        print('%s) Code : %s  || Company : %s start......' % (idx_kospi, Code, Company), end='')
        sys.stdout.flush()
        beaktime = random.randrange(1, 10)
        time.sleep(beaktime)
        GetNaverFinancialInfo(driver, Code, Company, save_folder)
        print('Done!!')
    driver.quit()
