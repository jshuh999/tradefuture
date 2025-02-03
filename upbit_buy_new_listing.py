import ccxt
import os
import time
import argparse
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

# 업비트 API 연결
exchange = ccxt.upbit({
    'apiKey': ACCESS_KEY,
    'secret': SECRET_KEY,
    'options': {
        'createMarketBuyOrderRequiresPrice': False  # 시장가 매수 시 가격 없이 주문 가능하도록 설정
    }
})

def get_markets():
    """업비트에서 지원하는 모든 마켓 목록 조회 (최신 데이터)"""
    try:
        markets = exchange.load_markets(reload=True)  # 최신 데이터 불러오기
        market_list = list(markets.keys())  
        
        # 전체 마켓 목록 출력
        #print(f"📌 현재 업비트 지원 마켓 목록 ({len(market_list)}개):")
        #for market in market_list:
        #    print(market)  # 모든 마켓 출력

        return market_list
    except Exception as e:
        print(f"❌ 마켓 정보 조회 실패: {e}")
        return []

def buy_market_order(market, amount_krw):
    """지정된 코인을 시장가 매수 (원화 기준)"""
    try:
        order = exchange.create_market_buy_order(market, None, params={'cost': amount_krw})
        print(f"✅ {market} 시장가 매수 성공! 주문 정보:")
        print(order)
    except Exception as e:
        print(f"❌ 주문 실패: {e}")

def wait_for_listing(target_coin, max_amount):
    """지정된 코인이 업비트에 상장될 때까지 대기 후 매수"""
    print(f"🔍 {target_coin} 상장 여부 확인 중...")

    while True:
        markets = get_markets()
        normalized_markets = [m.lower() for m in markets]  # 소문자로 변환하여 비교

        if target_coin.lower() in normalized_markets:
            print(f"✅ {target_coin} 상장 확인! 시장가 매수 진행.")
            buy_market_order(target_coin, max_amount)
            break

        else:
            print(f"⏳ {target_coin} 아직 상장되지 않음. 10초 후 다시 확인...")
        time.sleep(10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="업비트 코인 상장 확인 후 자동 매수 프로그램 (CCXT 사용)")
    parser.add_argument("coin", type=str, help="매수할 코인의 마켓 코드 (예: KRW-NEWCOIN)")
    parser.add_argument("amount", type=float, help="매수할 금액 (KRW)")

    args = parser.parse_args()
    wait_for_listing(args.coin, args.amount)

