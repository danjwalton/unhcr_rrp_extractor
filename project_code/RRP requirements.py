from time import sleep
import json, os, datetime, re, sys, requests, random
from urllib.request import urlopen
import urllib.parse as urlparse
from lxml import etree, html
from subprocess import check_output
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

###
#Setup
###

script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

chromedriver_dir = script_dir + '/project_data/chromedriver.exe'
chrome_dir = script_dir + '/project_data/bin/chrome.exe'

chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = chrome_dir
chrome_options.add_argument("window-size=1920,1080")
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--profile-directory=Default')
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--disable-plugins-discovery");
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
prefs = {"directory_upgrade": True, "extensions_to_open": "", "profile.default_content_settings.popups": 0, "download.prompt_for_download": False, 'useAutomationExtension': False, "excludeSwitches": ['enable-automation']}
chrome_options.add_experimental_option("prefs", prefs)

browser = webdriver.Chrome(chromedriver_dir, options=chrome_options)
browser.implicitly_wait(30)
wait = WebDriverWait(browser, 10)
action = webdriver.ActionChains(browser)

####
#Functions
###

def get_home_rrps():
    global home_rrps_dropdown
    global home_rrps_search
    home_rrps_search = browser.find_elements_by_xpath("//*[text()='Search']")[1].find_element_by_xpath('..')
    home_rrps_dropdown = browser.find_element_by_xpath("//*[contains(@aria-label, 'Inter-Agency Regional Plan,')]")
    home_rrps_dropdown.click()
    home_rrps = browser.find_elements_by_xpath("//span[@class='slicerText' and contains(@title, 'RP')]")
    home_rrps_dropdown.click()
    return home_rrps

def next_country(previous_country):
    global more_countries
    global rrp_countries
    global rrp_countries_dropdown
    rrp_countries_dropdown = browser.find_elements_by_xpath("//*[@class='slicer-dropdown-menu']")[0]
    rrp_countries_dropdown.click()
    sleep(0.2)
    rrp_countries = browser.find_elements_by_xpath("//*[@class='slicer-dropdown-popup visual']//*[@class='slicerText']")
    
    if previous_country:
        rrp_countries = rrp_countries[rrp_countries.index(previous_country)+1:]
        rrp_country = rrp_countries[0]
    else:
        rrp_country = rrp_countries[0]

    if rrp_country == rrp_countries[len(rrp_countries)-1]:
        more_countries = False
       
    sleep(0.2)
    browser.execute_script("arguments[0].scrollIntoView(true);", rrp_country)
    rrp_country.click()
    sleep(0.2)
    rrp_countries_dropdown.click()
    return rrp_country

def get_rrp_years():
    browser.switch_to.default_content()
    browser.switch_to.frame(2)
    rrp_years = browser.find_elements_by_xpath("//*[@class='slicerItemContainer']")
    browser.switch_to.default_content()
    return(rrp_years)

def switch_year(year):
    global rrp_year
    browser.switch_to.frame(2)
    rrp_year_btn = rrp_years[year]
    rrp_year = rrp_year_btn.text
    browser.execute_script("arguments[0].click();", rrp_year_btn) #because chromedriver can't click straight sometimes
    browser.switch_to.default_content()

def switch_country(rrp_country):
    rrp_countries_dropdown.click()
    sleep(0.5)
    browser.execute_script("arguments[0].scrollIntoView(true);", rrp_country)
    rrp_country.click()
    sleep(0.5)
    rrp_countries_dropdown.click()


###
#Run
###

url = "https://app.powerbi.com/view?r=eyJrIjoiM2M2NDMyZTgtZmQ4OC00ZDE1LWEyYWMtMTAxZDY2NzMyY2QxIiwidCI6ImU1YzM3OTgxLTY2NjQtNDEzNC04YTBjLTY1NDNkMmFmODBiZSIsImMiOjh9"

browser.get(url)

output = pd.read_csv(script_dir + '/output/rrp_data.csv')

 
home_rrps = get_home_rrps()

for i in range(len(home_rrps)):
    rrp = home_rrps[i]
    rrp_text = rrp.get_attribute('title')
    print(rrp_text)
    home_rrps_dropdown.click()
    sleep(0.2)
    rrp.click()
    home_rrps_dropdown.click()
    home_rrps_search.click()

    sleep(3)
    rrp_years = get_rrp_years()

    for j in range(len(rrp_years)):
        switch_year(j)
        sleep(1)
        title = browser.find_elements_by_xpath("//*[@class='card']")[0].text
        title_year = title[len(title)-4:len(title)]
        print(title_year)
        more_countries = True
        previous_country = None
        while more_countries == True:
            rrp_country = next_country(previous_country)
            country = rrp_country.get_attribute('title')
            print(country)
            sleep(0.2)
            data = browser.find_elements_by_xpath("//*[@class='card']")[1].text

            cols = ['RRP', 'Year', 'Country'] + data.split('\n')[1::2]
            cells = [rrp_text, title_year, country] + data.split('\n')[::2]

            cells = pd.DataFrame(cells).transpose()
            cells.columns = cols

            output = output.append(cells, ignore_index = True)

            previous_country = rrp_country

        switch_country(previous_country) #Remove last country selection
        rrp_years = get_rrp_years()
            
    browser.get(url)
    sleep(3)
    home_rrps = get_home_rrps()

output.to_csv(script_dir + '/output/rrp_data.csv', index=False)
browser.quit()
