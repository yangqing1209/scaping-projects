#! encoding=utf-8
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import pyexcel
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By



class jdSpider(object):

    def __init__(self):
        option = Options()
        option.add_argument('--headless')
        self.driver = webdriver.Chrome(executable_path="chromedriver.exe",
                                       chrome_options=option)
        self.url = 'https://www.jd.com'
        self.keyword = '小米笔记本'
        self.has_next = True
        self.rows = []

    def get_args(self):
        if sys.argv and len(sys.argv) > 1:
            self.keyword = sys.argv[1]

    def get_page(self):
        self.driver.get(self.url)
        time.sleep(5)
        kw = self.driver.find_element_by_id('key')
        self.get_args()
        kw.send_keys(self.keyword)
        kw.send_keys(Keys.RETURN)
        sort_btn = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, './/div[@class="f-sort"]/a[2]')))
        sort_btn.click()

    def parse_page(self):
        time.sleep(3)
        cur_page = self.driver.find_element_by_xpath(
            '//div[@id="J_bottomPage"]//a[@class="curr"]').text
        print('----------------------current page is %s----------------------------' % cur_page)
        goods_list = self.driver.find_element_by_id("J_goodsList")
        y = goods_list.rect['y'] + goods_list.rect['height']
        self.driver.execute_script('window.scrollTo(0, %s)' % y)
        time.sleep(5)
        products = self.driver.find_elements_by_class_name('gl-item')
        for p in products:
            row = {}
            sku = p.get_attribute('data-sku')
            row['price'] = p.find_element_by_css_selector('strong.J_%s' % sku).text
            row['name'] = p.find_element_by_css_selector('div.p-name>a>em').text
            row['comments'] = p.find_element_by_id('J_comment_%s' % sku).text
            try:
                row['shop'] = p.find_element_by_css_selector('div.p-shop>span>a').text
            except Exception:
                row['shop'] = '无'
            self.rows.append(row)
        next_page = self.driver.find_element_by_css_selector('a.pn-next')
        if 'disabled' in next_page.get_attribute('class'):
            self.has_next = False
        else:
            next_page.click()

    def save_data(self):
        pyexcel.save_as(records=self.rows, dest_file_name='%s.xls' % self.keyword)

    def main(self):
        try:
            self.get_page()
            while self.has_next:
                self.parse_page()
            self.save_data()
        except Exception as e:
            print(e)
        finally:
            self.driver.quit()



if __name__ == '__main__':
    spider = jdSpider()
    spider.main()
