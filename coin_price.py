import ccxt
from dhooks import Webhook
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# Upbit에서 코인 가격을 가져오는 함수
def get_coin_price(symbol='BTC/USDT'):
    exchange = ccxt.upbit()
    ticker = exchange.fetch_ticker(symbol)
    return ticker['last']  # 가장 최근의 거래 가격

# 디스코드 웹훅을 통해 메시지를 전송하는 함수
def send_to_discord(price, webhook_url):
    hook = Webhook(webhook_url)
    hook.send(f"현재 BTC 가격은 {price}입니다.")

# 메인 함수
if __name__ == "__main__":
    # .env 파일에서 DISCORD_WEBHOOK_URL 읽어오기
    discord_webhook_url = os.getenv('DISCORD_WEBHOOK_URL')

    if not discord_webhook_url:
        print("디스코드 웹훅 URL이 .env 파일에 없습니다!")
        exit(1)

    coin_price = get_coin_price('BTC/KRW')  # 원하는 코인의 가격을 가져옵니다.
    send_to_discord(coin_price, discord_webhook_url)
