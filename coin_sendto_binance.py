import ccxt
import os
import argparse
from dotenv import load_dotenv
from dhooks import Webhook, Embed
from datetime import datetime
import time
import sys

url = "https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD"


# 환경 변수 로드
load_dotenv()

# 바이낸스와 업비트 API 인증 정보
binance_api_key = os.getenv("BINANCE_API_KEY")
binance_api_secret = os.getenv("BINANCE_SECRET_KEY")
upbit_api_key = os.getenv("UPBIT_ACCESS_KEY")
upbit_api_secret = os.getenv("UPBIT_SECRET_KEY")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# 거래소 객체 생성
binance = ccxt.binance({'apiKey': binance_api_key, 'secret': binance_api_secret})
upbit = ccxt.upbit({'apiKey': upbit_api_key, 'secret': upbit_api_secret})
hook = Webhook(DISCORD_WEBHOOK_URL.replace("discordapp", "discord"))


default_coin_symbol = 'USDT'
default_amount_to_buy = 5 # 거래수량
default_sell_yn = 'N'

# 매도할 코인과 수량 입력 받기
if len(sys.argv) == 1:
    # 매도할 코인과 수량 입력 받기
    coin_symbol = input(f"매도할 코인을 입력하세요 (기본값: {default_coin_symbol}): ") or default_coin_symbol  # 매도할 코인
    amount_to_buy = float(input(f"매도할 수량을 입력하세요 (기본값: {default_amount_to_buy}): ") or default_amount_to_buy)  # 매도할 수량
    sell_yn = input(f"바이낸스 시장가 매도 여부를 입력하세요 (기본값: {default_sell_yn}): ") or default_sell_yn  # 바이낸스 시장가 매도 여부
elif len(sys.argv) == 4:
    coin_symbol = sys.argv[1] if len(sys.argv) > 3 else default_coin_symbol  # 매도할 코인
    amount_to_buy = float(sys.argv[2]) if len(sys.argv) > 3 else default_amount_to_buy  # 매도할 수량
    sell_yn = sys.argv[3] if len(sys.argv) > 3 else default_sell_yn # 바이낸스 시장가 매도 여부 
else:
    print("잘못 입력하셨습니다. 사용방법을 확인해주세요. \n [사용방법] \n1. python3 ./deposit_binance.py [코인티커] [수량] [Y/N] \n2. python3 ./deposit_binance.py")
    exit(0)



# 업비트로 송금할 주소 및 태그
binance_address = 'eosbndeposit'
binance_tag = '102263705'

def get_withdraw_info():
    return upbit.fetch2(path="/withdraws/coin_addresses", api="private", method="GET")

def get_withdraw_net_type(code: str, address: str, tag: str = None):
    infos = get_withdraw_info()
    for info in infos:
        if info["currency"] == code and info["withdraw_address"] == address:
            if tag is None:
                return info["currency"]
            elif info["secondary_address"] == tag:
                return info["currency"]

def withdraw(code: str, amount: float, address: str, tag: str = None):
    code = code.upper()
    net_type = get_withdraw_net_type(code, address, tag)
    if not tag:
        return upbit.withdraw(code, amount, address, params={"net_type": net_type})
    else:
        return upbit.withdraw(code, amount, address, tag, params={"net_type": net_type})

data = {"result": "", "message": ""}

try:
    # 업비트에서 EOS/KRW 현재 시세 조회
    symbol_krw = f'{coin_symbol}/KRW'
    symbol_usdt = f'{coin_symbol}/USDT'
    ticker = upbit.fetch_ticker(symbol_krw)
    coin_price = ticker['last']  

    # 업비트에서 계정 잔고 조회
    balance = upbit.fetch_balance()
    upbit_balance = balance['total']['KRW']

    # 매수에 필요한 금액 계산
    total_cost = amount_to_buy * coin_price

    if (upbit_balance < total_cost or total_cost <= 5000):
        print(f"잔고 {upbit_balance:.1f}는 매수금액{total_cost:.1f}보다 크거나 같거나 매수금액은 5,000원 이상이어야 합니다.")
        raise Exception(f"잔고 {upbit_balance:.1f}는 매수금액{total_cost:.1f}보다 크거나 같거나 매수금액은 5,000원 이상이어야 합니다.")

    # 1. 매수 주문 생성
    upbit_order = upbit.create_market_order(symbol_krw, "buy", total_cost, 1)

    order_id = upbit_order["id"]

    retries = 0
    while retries < 10:
        order_result = upbit.fetch_order(order_id, coin_symbol)
        if order_result["status"] in ["closed", "canceled"]:
            break
        time.sleep(0.5)
        retries += 1

    amount = order_result["filled"]
    amount = float(f"{amount:.4f}")
    # 2. 바이낸스로 출금
    message = withdraw(coin_symbol, amount, binance_address, binance_tag)
    # 업비트에서 바이낸스로부터 입금된 코인 확인 후 매도 (20분 동안 확인)
    # print(message)
    if sell_yn:
        # 현재 시간 가져오기
        current_time = datetime.now()
        dots = 0
        for _ in range(60):
            # 업비트에서 바이낸스로 입금된 코인 확인
            binance_deposit = binance.fetch_deposits(coin_symbol)
            found = False
            dots += 1
            for deposit in binance_deposit:
                deposit_time = datetime.fromtimestamp(deposit['timestamp'] / 1000)  # 밀리초 단위를 초 단위로 변환 후 datetime 객체로 변환
                print("." * dots, end='\r')
                if deposit['address'] == binance_address and deposit['tag'] == binance_tag and deposit_time > current_time:
                    # 3. 입금된 코인을 매도
                    binance.create_market_sell_order(symbol_usdt, deposit['amount'])
                    found = True 
            if found: break
            # 1분 대기 후 재확인
            time.sleep(10)

except Exception as e:
    data["result"] = "시도 실패"
    data["message"] = str(e)
    embed = Embed(
        description=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 출금{data['result']}",
        color=0xFF2D00,
    )
    embed.add_field(name="코인", value=coin_symbol, inline=False)
    embed.add_field(name="주소", value=binance_address, inline=False)
    if binance_tag:
        embed.add_field(name="주소2", value=binance_tag, inline=False)
    embed.add_field(name="메시지", value=data["message"])
    hook.send(embed=embed)

else:
    data["result"] = "시도 성공"
    data["message"] = message
    embed = Embed(
        description=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 출금{data['result']})",
        color=0x34FF00,
    )
    embed.add_field(name="코인", value=coin_symbol, inline=False)
    embed.add_field(name="수량", value=f"{amount_to_buy}", inline=False)
    embed.add_field(name="주소", value=binance_address, inline=False)
    if binance_tag:
        embed.add_field(name="주소2", value=binance_tag, inline=False)

    hook.send(embed=embed)

finally:
    with open("last_run.txt", "w") as f:
        f.write(datetime.now().isoformat())
