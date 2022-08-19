import pandas as pd
from os import listdir,makedirs, remove
from os.path import isfile, join, isdir, exists
import datetime,time
from selenium import webdriver
import random
import sys
import numpy as np
import copy
import pyperclip
from selenium.webdriver.common.keys import Keys

userID = 'gs10728'
userPW = '**gs107283'

# open chrome
driver = webdriver.Chrome(r'../Setting\chromdriver\chromedriver.exe')
driver.implicitly_wait(1)
driver.set_window_position(-2000, 0)
driver.maximize_window()
url = 'https://cafe.naver.com/firstlesson'
driver.get(url)
print()
driver.find_element_by_link_text('로그인').click()
# driver.find_element_by_id('id').send_keys('gs10728')
elem_id = driver.find_element_by_id('id')
elem_id.click()
pyperclip.copy(userID)
elem_id.send_keys(Keys.CONTROL, 'v')
time.sleep(1)

# 4. pw 복사 붙여넣기
elem_pw = driver.find_element_by_id('pw')
elem_pw.click()
pyperclip.copy(userPW)
elem_pw.send_keys(Keys.CONTROL, 'v')
time.sleep(1)

# 5. 로그인 버튼 클릭
driver.find_element_by_id('log.login').click()
driver.find_element_by_link_text('등록안함').click()

leftMenu = driver.find_element_by_id('cafe-menu')
leftMenu.find_element_by_id('menuLink181').click()

rightMenu = driver.find_element_by_id('main-area')
cafeMain = rightMenu.find_element_by_id('cafe_main')
driver.switch_to.frame(cafeMain)

mainArea = driver.find_element_by_id('main-area')
tbRows = mainArea.find_element_by_xpath('//div[4]/table/tbody')
tbRows = tbRows.find_elements_by_class_name('td_date')
dateForScrab = '2022.03.16'
tbRows = [tbRow for tbRow in tbRows if dateForScrab in tbRow.text]
dfData = pd.DataFrame(columns=['Time','Title','Text'])
# 읽어야할 갯수를 세고, 갯수 만큼 반복문.

for idx, tr in enumerate(tbRows):
    textDate = tr.find_element_by_class_name('td_date').text
    if ':' in textDate:
        # textDate = datetime.datetime.strptime(textDate, '%H:%M')
        # textDate = textDate.replace(year=datetime.date.today().year)
        # textDate = textDate.replace(month=datetime.date.today().month)
        # textDate = textDate.replace(day=datetime.date.today().day)
        textDate = datetime.date.today()
    elif '.' in textDate:
        textDate = datetime.datetime.strptime(textDate, '%Y.%m.%d.')
        textDate = textDate.date()
    textTitle = tr.find_element_by_class_name('board-list').text
    dfData.loc[idx, 'Time'] = textDate
    dfData.loc[idx, 'Title'] = textTitle
# listIdx = dfData[dfData['Time']>=datetime.date.today()].index.tolist()
# for idx in listIdx:
#     tbRows[idx].find_element_by_tag_name('a').click()
#     contents = driver.find_element_by_class_name('article_viewer').text
#     dfData.loc[idx, 'Text'] = contents
    tr.find_element_by_tag_name('a').click()
    contents = driver.find_element_by_class_name('article_viewer').text
    dfData.loc[idx, 'Text'] = contents
    driver.back()
print()