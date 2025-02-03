import ccxt
import os
import time
import argparse
from dotenv import load_dotenv

# 1. 환경 변수 로드
load_dotenv()

# 2. API 키 가져오기
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

# 3. API 연결 확인
print(f"API Key Loaded: {BINANCE_API_KEY is not None}")
print(f"Secret Key Loaded: {BINANCE_SECRET_KEY is not None}")

# 4. 바이낸스 API 연결
exchange = ccxt.binance({
    'apiKey': BINANCE_API_KEY,
    'secret': BINANCE_SECRET_KEY,
    'options': {'defaultType': 'spot'}
})

def get_markets():
    """바이낸스에서 지원하는 모든 마켓 목록 조회"""
    try:
        markets = exchange.load_markets(reload=True)
        return list(markets.keys())
    except Exception as e:
        print(f"❌ 마켓 정보 조회 실패: {e}")
        return []

def buy_market_order(market, amount_usdt):
    """지정된 코인을 시장가 매수"""
    try:
        ticker = exchange.fetch_ticker(market)
        price = ticker['last']
        amount = amount_usdt / price  # USDT 기준 수량 계산

        order = exchange.create_market_buy_order(market, amount)
        print(f"✅ {market} 시장가 매수 성공! 주문 정보:")
        print(order)
    except Exception as e:
        print(f"❌ 주문 실패: {e}")

def wait_for_listing(target_coin, max_amount):
    """지정된 코인이 바이낸스에 상장될 때까지 대기 후 매수"""
    market_symbol = f"{target_coin.upper()}/USDT"
    print(f"🔍 {market_symbol} 상장 여부 확인 중...")

    while True:
        markets = get_markets()
        normalized_markets = [m.lower() for m in markets]

        if market_symbol.lower() in normalized_markets:
            print(f"✅ {market_symbol} 상장 확인! 시장가 매수 진행.")
            buy_market_order(market_symbol, max_amount)
            break
        else:
            print(f"⏳ {market_symbol} 아직 상장되지 않음. 1초 후 다시 확인...")
        time.sleep(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="바이낸스 코인 상장 확인 후 자동 매수 프로그램")
    parser.add_argument("coin", type=str, help="매수할 코인의 코드 (예: BTC)")
    parser.add_argument("amount", type=float, help="매수할 금액 (USDT)")

    args = parser.parse_args()
    wait_for_listing(args.coin, args.amount)

