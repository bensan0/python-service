import concurrent.futures
import dataclasses
import os
import queue
import socket
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import app


@dataclass
class TX:
    name: str
    date: int
    today_closing: str
    yesterday_closing: str
    gap: str
    gap_percent: str
    opening: str
    highest: str
    lowest: str
    today_trading_volume: str

@dataclass
class Stock:
    stock_id: str
    stock_name: str
    market: str
    date: int
    today_closing_price: Decimal
    yesterday_closing_price: Optional[Decimal]
    price_gap: Optional[Decimal]
    price_gap_percent: Optional[Decimal]
    opening_price: Decimal
    highest_price: Decimal
    lowest_price: Decimal
    today_trading_volume_piece: int
    today_trading_volume_money: Optional[Decimal]

@dataclass
class Index:
    index_name: Optional[str] = None
    date: Optional[int] = None
    today_closing: Optional[Decimal] = None
    yesterday_closing: Optional[Decimal] = None
    gap: Optional[Decimal] = None
    gap_percent: Optional[Decimal] = None
    opening: Optional[Decimal] = None
    highest: Optional[Decimal] = None
    lowest: Optional[Decimal] = None
    today_trading_volume: Optional[int] = None
    today_trading_amount: Optional[Decimal] = None

'''
台指期 日盤 8:45~13:45, 夜盤 15:00~5:00
'''
def crawl_tx():
    options = webdriver.FirefoxOptions()
    driver = webdriver.Remote(
        os.getenv("BROWSER_SERVICE_PATH", "127.0.0.1/wd/hub"),
        options=options
    )
    try:
        driver.get("https://tw.stock.yahoo.com/future/charts.html?sid=WTX%26&sname=臺指期近一&mid=01&type=1")

        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='main-1-FutureChart-Proxy']/div/iframe"))
        )

        driver.switch_to.frame(iframe)

        chart_show = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "chart-show"))
        )

        future_chart = chart_show.find_element(By.XPATH, ".//div[@id='FutureChart']")
        dt = datetime.now()
        if 15 >= dt.hour <= 6:
            name = "台指期日盤"
            date_str = (dt - timedelta(days=1)).strftime("%Y%m%d")
        else:
            name = "台指期夜盤"
            date_str = dt.strftime("%Y%m%d")

        opening = future_chart.find_element(By.XPATH, ".//*[name()='svg']/*[name()='g'][31]/*[name()='text']").text
        now_closing = future_chart.find_element(By.XPATH, ".//*[name()='svg']/*[name()='g'][34]/*[name()='text']").text
        trading_volume = future_chart.find_element(By.XPATH, ".//*[name()='svg']/*[name()='g'][36]/*[name()='text']").text
        yesterday_closing = future_chart.find_element(By.XPATH, ".//*[name()='svg']/*[name()='g'][47]/*[name()='text']").text
        gap_percent_str = future_chart.find_element(By.XPATH, ".//*[name()='svg']/*[name()='g'][41]/*[name()='text']").text
        gap_str = future_chart.find_element(By.XPATH, ".//*[name()='svg']/*[name()='g'][44]/*[name()='text']").text
        highest = future_chart.find_element(By.XPATH, ".//*[name()='svg']/*[name()='g'][42]/*[name()='text']").text
        lowest = future_chart.find_element(By.XPATH, ".//*[name()='svg']/*[name()='g'][43]/*[name()='text']").text

        data = TX(name, int(date_str), now_closing, yesterday_closing, gap_str, gap_percent_str.replace("%", ""), opening, highest, lowest, trading_volume)

        return data
    finally:
        driver.quit()
'''
美股指數
'''
def crawl_america_tx():
    options = webdriver.FirefoxOptions()
    driver = webdriver.Remote(
        os.getenv("BROWSER_SERVICE_PATH", "127.0.0.1:4444/wd/hub"),
        options=options
    )
    try:
        driver.get("https://tw.stock.yahoo.com/world-indices/")

        market = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='hero-0-MarketTable-Proxy']"))
        )

        lis = market.find_elements(By.XPATH, ".//div[@class='table-body-wrapper']/ul/li[position() <= 4]")

        results = []
        dt = datetime.now()
        for li in lis:
            name = li.find_element(By.XPATH, "./div/div[1]/div[2]/div/div/span").text
            now_closing = li.find_element(By.XPATH, "./div/div[2]/span").text.replace(",", "")
            gap_str = li.find_element(By.XPATH, "./div/div[3]/span").text
            gap_percent_str = li.find_element(By.XPATH, "./div/div[4]/span").text
            opening = li.find_element(By.XPATH, "./div/div[7]/span").text.replace(",", "")
            yesterday_closing = li.find_element(By.XPATH, "./div/div[8]/span").text.replace(",", "")
            if float(now_closing) < float(yesterday_closing):
                gap_str = "-" + gap_str
                gap_percent_str = "-" + gap_percent_str
            highest = li.find_element(By.XPATH, "./div/div[9]/span").text.replace(",", "")
            lowest = li.find_element(By.XPATH, "./div/div[10]/span").text.replace(",", "")
            if 23 <= dt.hour:
                date_str = dt.strftime("%Y%m%d")
            else:
                date_str = (dt - timedelta(days=1)).strftime("%Y%m%d")

            data = TX(name, int(date_str), now_closing, yesterday_closing, gap_str, gap_percent_str.replace("%", ""), opening, highest, lowest, "")
            print(f"data = {data}")
            results.append(data)

        return results
    finally:
        driver.quit()

'''
yahoo 台股即時
'''
def craw_yahoo_realtime():
    max_threads = 2
    results = []

    def scroll_page(driver: WebDriver, scroll_pause_sec: float = 0.2, max_attempts: int = 5):
        last_height = driver.execute_script("return document.body.scrollHeight")
        attempts = 0

        while attempts < max_attempts:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(scroll_pause_sec)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            attempts += 1

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def worker(driver: WebDriver, q: queue.Queue):
        try:
            while True:
                try:
                    url = q.get_nowait()
                    app.app.logger.info(f"{driver.session_id} 開始爬蟲 {url}")
                    driver.get(url)
                    _ = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@class='table-body-wrapper']"))
                    )

                    scroll_page(driver)
                    now_date = datetime.now().strftime("%Y%m%d")
                    page_date = driver.find_element(By.XPATH, "//time/span[2]").text.replace("/", "")
                    if now_date != page_date:
                        time.sleep(2)
                        continue

                    market = "市" if "exchange=TAI" in url else "櫃"
                    rows = driver.find_elements(By.XPATH, "//div[@class='table-body-wrapper']/ul/li")
                    for row in rows:
                        '''
                        個股代號
                        '''
                        stock_id = row.find_element(By.XPATH, ".//span[@class='Fz(14px) C(#979ba7) Ell']").text.strip().replace(
                            ".TWO", "").replace(".TW", "")

                        if len(stock_id) > 4 or not stock_id.isnumeric():
                            continue

                        '''
                        個股名稱
                        '''
                        stock_name = row.find_element(By.XPATH, ".//div[@class='Lh(20px) Fw(600) Fz(16px) Ell']").text.strip()

                        p_nodes = row.find_elements(By.XPATH,
                            ".//div[@class='Fxg(1) Fxs(1) Fxb(0%) Ta(end) Mend($m-table-cell-space) Mend(0):lc Miw(68px)']")
                        ud_nodes = row.find_elements(By.XPATH,
                                                     ".//div[@class='Fxg(1) Fxs(1) Fxb(0%) Ta(end) Mend($m-table-cell-space) Mend(0):lc Miw(74px)']")

                        '''
                        成交價
                        '''
                        today_closing = p_nodes[0].text.strip().replace(",", "")
                        if not _is_number(today_closing):
                            continue

                        '''
                        昨日收盤價
                        '''
                        yesterday_closing = p_nodes[2].text.strip().replace(",", "")
                        if not _is_number(yesterday_closing):
                            yesterday_closing = today_closing

                        '''
                        價差
                        '''
                        gap = ud_nodes[0].find_element(By.XPATH, ".//span").text.strip()
                        if _is_number(gap) and float(today_closing) < float(yesterday_closing):
                            gap = "-" + gap
                        else:
                            gap = str(Decimal(today_closing) - Decimal(yesterday_closing))

                        '''
                        價差%
                        '''
                        gap_p = ud_nodes[-1].find_element(By.XPATH, ".//span").text.strip().replace("%", "")
                        if _is_number(gap_p):
                            if "-" in gap:
                                gap_p = "-" + gap_p
                        else:
                            gap_p = str(Decimal(gap)/Decimal(yesterday_closing))
                            if "-" in gap:
                                gap_p = "-" + gap_p

                        '''
                        開盤
                        '''
                        op = p_nodes[1].text.strip().replace(",", "")
                        if not _is_number(op):
                            op = yesterday_closing

                        '''
                        最高
                        '''
                        high = p_nodes[3].text.strip().replace(",", "")
                        if not _is_number(high):
                            high = today_closing

                        '''
                        最低
                        '''
                        low = p_nodes[4].text.strip().replace(",", "")
                        if not _is_number(low):
                            low = today_closing

                        '''
                        交易量
                        '''
                        vol = row.find_element(By.XPATH,
                            ".//div[@class='Fxg(1) Fxs(1) Fxb(0%) Miw($w-table-cell-min-width) Ta(end) Mend($m-table-cell-space) Mend(0):lc']/span").text.strip().replace(
                            ",", "")
                        if "M" in vol:
                            vol = int(vol.replace("M", "")) * 1000000

                        stock = Stock(stock_id, stock_name, market, int(page_date), Decimal(today_closing), Decimal(yesterday_closing),
                                      Decimal(gap), Decimal(gap_p), Decimal(op), Decimal(high), Decimal(low), vol, None)

                        results.append(dataclasses.asdict(stock))
                    app.app.logger.info(f"{driver.session_id} 結束爬蟲 {url}")
                    time.sleep(2)
                except queue.Empty:
                    break
        finally:
            driver.quit()

    q = queue.Queue()
    listed_ids = [1, 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 19, 20, 21, 22, 24, 25, 30, 37, 38, 40, 41, 42, 43, 44, 45, 46, 47, 49, 93, 94, 95, 96]
    otc_ids = [97, 98, 121, 122, 123, 124, 125, 126, 130, 138, 139, 140, 141, 142, 145, 151, 153, 154, 155, 156, 157, 158, 159, 160, 161, 169, 170, 171]

    for id in listed_ids:
        q.put(f"https://tw.stock.yahoo.com/class-quote?sectorId={id}&exchange=TAI")

    for id in otc_ids:
        q.put(f"https://tw.stock.yahoo.com/class-quote?sectorId={id}&exchange=TWO")

    drivers = [_get_driver() for _ in range(max_threads)]

    for driver in drivers:
        if driver is None:
            app.app.logger.error("爬蟲yahoo即時無法獲取driver")
            return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(worker, driver, q) for driver in drivers]
        concurrent.futures.wait(futures)

    return results

'''
證交所
'''
def crawl_twse():
    app.app.logger.info("爬蟲twse開始")
    driver = _get_driver()
    if driver is None:
        app.app.logger.error("爬蟲twse錯誤, 無法取得driver")
        return None

    try:
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y%m%d")
        twse_url = f"https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date={now_str}&type=ALLBUT0999&response=html"
        driver.get(twse_url)
        tables = driver.find_elements(By.XPATH, "//table")
        results = []
        target_table = None
        for table in tables:
            if "每日收盤行情(全部(不含權證、牛熊證))" in table.find_element(By.XPATH, ".//thead/tr/th/div").text:
                target_table = table

        if target_table is None:
            return results

        try:
            rows = target_table.find_elements(By.XPATH, ".//tbody/tr")
        except Exception:
            return results

        for row in rows:
            stock_id = row.find_element(By.XPATH, "./td[1]").text.strip()
            if len(stock_id) > 4 or not _is_number(stock_id):
                continue

            stock_name = row.find_element(By.XPATH, "./td[2]").text.strip()

            closing = row.find_element(By.XPATH, "./td[9]").text.strip().replace(",", "")
            if not _is_number(closing):
                continue

            trading_vol = row.find_element(By.XPATH, "./td[3]").text.strip().replace(",", "")
            trading_vol = int(int(trading_vol) / 1000)

            trading_amount = row.find_element(By.XPATH, "./td[5]").text.strip().replace(",", "")

            op = row.find_element(By.XPATH, "./td[6]").text.strip().replace(",", "")

            highest = row.find_element(By.XPATH, "./td[7]").text.strip().replace(",", "")

            lowest = row.find_element(By.XPATH, "./td[8]").text.strip().replace(",", "")

            stock = Stock(stock_id, stock_name, "市", int(now_str), Decimal(closing), None, None, None, Decimal(op), Decimal(highest), Decimal(lowest), trading_vol, Decimal(trading_amount))

            results.append(dataclasses.asdict(stock))
    finally:
        driver.quit()

    app.app.logger.info(f"爬蟲twse結束, 共{len(results)}筆")
    return results

'''
櫃買中心
'''
def crawl_tpex():
    app.app.logger.info(f"爬蟲tpex開始")
    driver = _get_driver()
    if driver is None:
        app.app.logger.error("爬蟲twse錯誤, 無法取得driver")
        return None

    try:
        now_dt = datetime.now()
        now_str = now_dt.strftime("%Y%m%d")
        tpex_url = (
            f"https://www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php?l=zh-tw&o=htm&d="
            f"{now_dt.year - 1911}/{now_dt.month if now_dt.month > 9 else '0' + str(now_dt.month)}/{now_dt.day if now_dt.day > 9 else '0' + str(now_dt.day)}&se=AL&s=0,asc,0")

        driver.get(tpex_url)
        rows = driver.find_elements(By.XPATH, "/html/body/table/tbody/tr")
        results = []
        if len(rows) == 0:
            return results

        for row in rows:
            stock_id = row.find_element(By.XPATH, "./td[1]").text.strip()
            if len(stock_id) > 4 or not _is_number(stock_id):
                continue

            stock_name = row.find_element(By.XPATH, "./td[2]").text.strip()
            closing = row.find_element(By.XPATH, "./td[3]").text.strip().replace(",", "")
            if not _is_number(closing):
                continue

            trading_vol = row.find_element(By.XPATH, "./td[8]").text.strip().replace(",", "")
            trading_vol = int(int(trading_vol) / 1000)

            trading_amount = row.find_element(By.XPATH, "./td[9]").text.strip().replace(",", "")

            op = row.find_element(By.XPATH, "./td[5]").text.strip().replace(",", "")

            highest = row.find_element(By.XPATH, "./td[6]").text.strip().replace(",", "")

            lowest = row.find_element(By.XPATH, "./td[7]").text.strip().replace(",", "")

            stock = Stock(stock_id, stock_name, "櫃", int(now_str), Decimal(closing), None, None, None, Decimal(op), Decimal(highest), Decimal(lowest), trading_vol, Decimal(trading_amount))

            results.append(dataclasses.asdict(stock))
    finally:
        driver.quit()

    app.app.logger.info(f"爬蟲tpex結束, 共{len(results)}筆")
    return results

def crawl_index():
    urls = ["https://tw.stock.yahoo.com/quote/%5ETWII", "https://tw.stock.yahoo.com/quote/%5ETWOII"]
    driver = _get_driver()
    results = []
    now_str = datetime.now().strftime("%Y%m%d")
    try:
        for url in urls:
            driver.get(url)
            _ = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((
                                By.XPATH,
                                "//*[@id='qsp-overview-realtime-info']//div[@class='Fx(n) W(316px) Bxz(bb) Pstart(16px) Pt(12px)']/div[@class='Pos(r)']/ul"
                            )))

            page_date = driver.find_element(By.XPATH, "//time/span[2]").text.strip().split()[0].replace("/", "")
            if now_str != page_date:
                continue

            result = Index()
            result.date = int(now_str)
            index_name = driver.find_element(By.XPATH, "//h1[@class='C($c-link-text) Fw(b) Fz(24px) Mend(8px)']").text
            result.index_name = index_name
            rows = driver.find_elements(By.XPATH, "//*[@id='qsp-overview-realtime-info']//div[@class='Fx(n) W(316px) Bxz(bb) Pstart(16px) Pt(12px)']/div[@class='Pos(r)']/ul/li")
            get_val = lambda r: Decimal(r.find_element(By.XPATH, "./span[2]").text.replace(",", ""))

            for row in rows:
                row_name = row.find_element(By.XPATH, "./span[1]").text
                if row_name == "成交":
                    result.today_closing = get_val(row)
                elif row_name == "開盤":
                    result.opening =  get_val(row)
                elif row_name == "最高":
                    result.highest = get_val(row)
                elif row_name == "最低":
                    result.lowest = get_val(row)
                elif row_name == "昨收":
                    result.yesterday_closing = get_val(row)
                elif row_name == "漲跌幅":
                    result.gap_percent = Decimal(row.find_element(By.XPATH, "./span[2]").text.replace("%", ""))
                elif row_name == "漲跌":
                    result.gap = Decimal(row.find_element(By.XPATH, "./span[2]").text)
                elif row_name == "總量":
                    result.today_trading_volume = get_val(row)
                elif row_name == "成交金額(億)":
                    result.today_trading_amount = get_val(row) * 100000000

            if result.today_closing < result.yesterday_closing:
                result.gap = 0 - result.gap
                result.gap_percent = 0 - result.gap_percent

            results.append(dataclasses.asdict(result))
    except Exception as e:
        app.app.logger.error(f"爬蟲大盤錯誤, {repr(e)}")
        print(traceback.format_exc())
        return None
    finally:
        driver.quit()

    return results

def _is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def _get_driver():
    options = webdriver.FirefoxOptions()
    options.add_argument('--headless')
    options.set_preference('permissions.default.image', 2)
    try:
        driver =  webdriver.Remote(
            os.getenv("BROWSER_SERVICE_PATH", "127.0.0.1:4444/wd/hub"),
            options=options
        )

        return driver
    except socket.timeout:
        app.app.logger.error("獲取driver超時")
        return None
    except Exception as e:
        app.app.logger.error(f"獲取driver錯誤 {repr(e)}")
        return None

if __name__ == '__main__':
    crawl_tpex()