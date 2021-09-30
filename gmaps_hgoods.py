from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import pyodbc
import time
import re
import random
import urllib
import os
from bs4 import BeautifulSoup


# %%
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("window-size=5760,3240")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument('--disable-gpu')
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)
bot = webdriver.Chrome(options=chrome_options)

# %%

def scrape_locations(cursor): 
    count = 0
    while True:
        
        names, urls, lats, lons = [], [], [], []
        time.sleep(random.randint(114, 180) / 100)
        try:
            WebDriverWait(bot, 5).until(EC.presence_of_all_elements_located((By.XPATH, '//a[contains(@href, "/maps/place/")]')))

        except TimeoutException:
            print('ToutException occured!')
       
            break

        soup = BeautifulSoup(bot.page_source, 'html.parser')
        places = soup.select('a[href*="/maps/place/"]')
        #places = soup.find_all(re.compile("\d"))
        
        for i in places:
            count += 1
                        
            name = i.get('aria-label')
            print(count)
            href = i.get('href')
            print(name)
            #cursor.execute(f"SELECT * FROM hgoods_raw WHERE href LIKE (?)", href)
            #fetched_query = cursor.fetchone()
            #cursor.commit()
            #print(count)
            #if fetched_query:
                #continue

            
            lat = re.compile(r'!3d(.+?)!4d(.+?)\?').findall(href)[0][0]
            lon = re.compile(r'!3d(.+?)!4d(.+?)\?').findall(href)[0][1]
            lats.append(lat)
            lons.append(lon)
            names.append(name)
            urls.append(href)
              

        cursor.executemany('INSERT INTO [hgoods_raw] (name, href, lat, lon) VALUES (?, ?, ?, ?)', zip(names, urls, lats, lons))
        cursor.commit()

        time.sleep(random.randint(10, 155) / 100)
        next_page = bot.find_element_by_xpath('//button[@aria-label=" Next page "]')

        disabled = next_page.get_attribute('disabled')
        if disabled == 'true':
            break

        try:  
            next_page.click()
        except:
            print('Click Exception')

    
# %%
def main_func(city,town,cursor,keyword = 'home goods stores'):


    query_str = urllib.parse.quote_plus(f'{keyword} in {town} {city}')
    url = f'https://www.google.com/maps/search/{query_str}'
    bot.get(url)
    scrape_locations(cursor) 

if __name__ == '__main__':

    server = os.getenv('SERVER')
    database = os.getenv('DATABASE')
    username = os.getenv('USERNAME')
    password = os.getenv('PASSWORD')

    print('USERNAME: ',username, 'DB: ', database)


    cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database +';UID=' + username + ';PWD=' + password)
    cursor = cnxn.cursor()

    bot.get('https://www.google.com/maps/search/homegoods+stores+in+fatih+istanbul')
    time.sleep(0.5)
    try:
        bot.find_element_by_xpath("//*[contains(text(),'I agree')]").click()
        time.sleep(5)
    except:
        print('I agree click error')
    while True:

        # SELECTs all stores whose 'Checked' column is NULL and whose 'GROUP_ID' value equals to the mod division of ID number to GROUP_NUMBER value
        # so that when the script is distributed into 5 platforms, these scripts will not step in each other's chunk of stores  
        cursor.execute(f"SELECT * FROM city_table WHERE [CHECKED] = '0'")

        # Gets one store in the queried list of stores    
        row = cursor.fetchone()
        cursor.commit()

        if not row:
            print('List finished')
            break
        
        ID, city, town, checked = row
        print('Row: ', row)

        main_func(city, town, cursor)
        cursor.execute(fr"UPDATE city_table set CHECKED = '1' WHERE ID = {ID}")
        cursor.commit()

# %%
