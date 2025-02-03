import ccxt
from dhooks import Webhook, Embed
import urllib.request
import json
from datetime import datetime, timedelta
import os
import time

url = "https://quotation-api-cdn.dunamu.com/v1/forex/recent?codes=FRX.KRWUSD"


def get_usdkrw():
    try:
        response = urllib.request.urlopen(url)
        data = response.read().decode("utf-8")
        json_data = json.loads(data)

        result = json_data[0]
        return result["basePrice"]

    except Exception as e:
        print(e)


#####################
#      초기설정      #
######################################################
API_KEY = "API키를 입력하세요"
SECRET_KEY = "SECRET키를 입력하세요"
DISCORD_WEBHOOK_URL = "디스코드 웹훅 URL을 입력하세요"

김프기준 = 0

보낼금액 = 6000
보낼코인 = "출금할 코인코드 입력하세요"
주소 = "출금할 주소를 입력하세요"
주소2 = ""

#######################################################

##### 선택사항 ######
김프_모니터링_코인 = "BTC"

#######################################################

upbit = ccxt.upbit({"apiKey": API_KEY, "secret": SECRET_KEY})
hook = Webhook(DISCORD_WEBHOOK_URL.replace("discordapp", "discord"))


def get_kimp():
    upbit_ticker = ccxt.upbit().fetch_ticker(f"{김프_모니터링_코인.upper()}/KRW")
    binance_ticker = ccxt.binance().fetch_ticker(f"{김프_모니터링_코인.upper()}/USDT")
    usdkrw = get_usdkrw()

    upbit_price = upbit_ticker["last"]
    binance_price = binance_ticker["last"]

    return (upbit_price / (binance_price * usdkrw) - 1) * 100


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


def check_last_execution():
    if os.path.exists("last_run.txt"):
        with open("last_run.txt", "r") as f:
            last_exec_time_str = f.read()
            last_exec_time = datetime.fromisoformat(last_exec_time_str)

            if datetime.now() - last_exec_time < timedelta(hours=24):
                m = f"{last_exec_time.strftime('%Y-%m-%d %H:%M:%S')}에 출금 시도한 이후로 24시간이 지나지 않았습니다."
                print(m)

                return False
    return True


kimp = get_kimp()
data = {"result": "", "message": ""}

print(f"현재 김프: {kimp:.2f}% , 출금 김프기준 : {김프기준}%")
if kimp <= float(김프기준):
    보낼코인 = 보낼코인.upper()
    if check_last_execution():
        try:
            if 보낼금액 < 6000:
                raise Exception("보낼금액은 최소 6000원 이상이어야 합니다.")

            result = upbit.create_market_order(f"{보낼코인}/KRW", "buy", 보낼금액, 1)
            order_id = result["id"]

            retries = 0
            while retries < 10:
                order_result = upbit.fetch_order(order_id)

                print(order_result["status"], order_result["filled"], order_result["remaining"])
                if order_result["status"] in ["closed", "canceled"]:
                    break

                time.sleep(0.5)

                retries += 1

            amount = order_result["filled"]
            amount = float(f"{amount:.4f}")
            message = withdraw(보낼코인, amount, 주소, 주소2)

        except Exception as e:
            data["result"] = "시도 실패"
            data["message"] = str(e)
            embed = Embed(
                description=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 출금{data['result']}",
                color=0xFF2D00,
            )
            embed.add_field(name="코인", value=보낼코인, inline=False)
            embed.add_field(name="금액", value=f"{보낼금액}원", inline=False)
            embed.add_field(name="주소", value=주소, inline=False)
            if 주소2:
                embed.add_field(name="주소2", value=주소2, inline=False)
            embed.add_field(name="메시지", value=data["message"])
            hook.send(embed=embed)

        else:
            data["result"] = "시도 성공"
            data["message"] = message
            embed = Embed(
                description=f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 출금{data['result']} (김프기준: {김프기준:.2f}%)",
                color=0x34FF00,
            )
            embed.add_field(name="코인", value=보낼코인, inline=False)
            embed.add_field(name="금액", value=f"{보낼금액}원", inline=False)
            embed.add_field(name="주소", value=주소, inline=False)
            if 주소2:
                embed.add_field(name="주소2", value=주소2, inline=False)

            hook.send(embed=embed)

        finally:
            with open("last_run.txt", "w") as f:
                f.write(datetime.now().isoformat())
