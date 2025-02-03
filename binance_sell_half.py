import ccxt
import os
import time
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
ACCESS_KEY = os.getenv("BINANCE_ACCESS_KEY")
SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

binance = ccxt.binance({
    'apiKey': ACCESS_KEY,
    'secret': SECRET_KEY,
    'options': {'defaultType': 'spot'}
})

# 실행 시 입력값 받기
if len(sys.argv) < 2:
    print("❌ 사용법: python script.py <티커>")
    sys.exit(1)

symbol = sys.argv[1]  # 입력된 티커 (예: BTC/USDT)
target_profit = 100  # 목표 수익률 (%)

def get_balance(asset):
    """ 보유 코인 수량 조회 """
    balance = binance.fetch_balance()
    return balance['total'].get(asset, 0)

def get_avg_buy_price(symbol):
    """ 최근 매수 평균가 계산 """
    trades = binance.fetch_my_trades(symbol)  # 최근 거래 내역 조회
    buy_trades = [trade for trade in trades if trade['side'] == 'buy']  # 매수 거래만 필터링

    if not buy_trades:
        print("❌ 최근 매수 내역이 없습니다.")
        sys.exit(1)

    total_cost = sum(trade['price'] * trade['amount'] for trade in buy_trades)
    total_amount = sum(trade['amount'] for trade in buy_trades)

    return total_cost / total_amount if total_amount > 0 else 0

def sell_half(symbol, quantity):
    """ 시장가 매도 (50% 수량) """
    sell_amount = quantity / 2
    binance.create_market_sell_order(symbol, sell_amount)
    print(f"🚀 {symbol} {sell_amount}개 매도 완료!")

# 코인 이름 추출 (예: BTC/USDT → BTC)
base_asset = symbol.split("/")[0]

# 매수가 자동 조회
buy_price = get_avg_buy_price(symbol)
print(f"💰 평균 매수가: {buy_price:.2f} USDT")

while True:
    ticker = binance.fetch_ticker(symbol)
    current_price = ticker['last']

    # 수익률 계산
    profit_percentage = ((current_price - buy_price) / buy_price) * 100

    print(f"📈 현재 가격: {current_price} USDT | 수익률: {profit_percentage:.2f}% (목표: {target_profit}%)")

    if profit_percentage >= target_profit:
        balance = get_balance(base_asset)

        if balance > 0:
            print(f"💰 보유량: {balance} {base_asset} → 50% 매도 실행")
            sell_half(symbol, balance)
            break  # 매도 후 종료
        else:
            print("❌ 보유 코인이 없습니다.")

    time.sleep(10)  # 10초마다 가격 확인

