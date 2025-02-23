import ccxt
import os
import time
import sys
from dotenv import load_dotenv
import pykis
import pandas as pd
from datetime import datetime, timedelta

# 한국투자증권 API 설정
# 환경 변수 로드
load_dotenv()
ACCESS_KEY = os.getenv("KIS1_KEY")
SECRET_KEY = os.getenv("KIS1_SECRET")
ACCOUNT_NUMBER = os.getenv("KIS1_ACCOUNT_NUMBER")
ACCOUNT_CODE = os.getenv("KIS1_ACCOUNT_CODE")

key_info = {
    "appkey": ACCESS_KEY,
    "appsecret": SECRET_KEY
}
account_info = {
    "account_code": ACCOUNT_NUMBER,
    "product_code": ACCOUNT_CODE
}

api = pykis.Api(key_info=key_info, account_info=account_info)

# 종목 코드 리스트 가져오기
market = 'ALL'  # 'ALL', 'KOSPI', 'KOSDAQ' 중 선택 가능
stocks_list = api.get_stock_list(market)

# 상장한지 6개월이 지난 종목 필터링
six_months_ago = datetime.now() - timedelta(days=180)
stocks_6_months_old = []
for stock in stocks_list:
    stock_info = api.get_stock_info(stock['code'])
    if stock_info['listing_date'] < six_months_ago:
        stocks_6_months_old.append(stock_info)
        

# 오늘의 주가가 과거 신고가 또는 250일 신고가에서 -5% 이상 하락한 종목 찾기
result = []
for stock in stocks_6_months_old:
    stock_code = stock['code']
    current_price = api.get_kr_current_price(stock_code)
    high_price_250d = api.get_kr_high_price(stock_code, days=250)
    
    if current_price < high_price_250d * 0.95:
        stock_info = {
            '종목코드': stock_code,
            '종목명': stock['name'],
            '현재가': current_price,
            '과거신고가': high_price_250d,
            '신고가대비현재가비율': (current_price / high_price_250d) * 100,
            '업종': stock['sector']
        }
        result.append(stock_info)

# 결과 출력
df = pd.DataFrame(result)
print(df)
