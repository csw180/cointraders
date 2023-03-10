import time
import pyupbit
import pandas as pd
import datetime as dt
from ticker import Ticker
import account
# upbit 실계좌를 활용할경우
# import upbit_account 로 대체

_MAX_SEEDS = 2000000   # 이 전략으로 운용하는 전체 금액
_MAX_A_BUY = 1000000    # 한번의 매수 최대금액

def print_(ticker,msg)  :
    if  ticker :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'#'+ticker+'# '+msg
    else :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' '+msg
    print(ret, flush=True)

# 거래량 상위 10개 종목 선별
def best_volume_tickers() : 
    all_tickers = pyupbit.get_tickers(fiat="KRW")
    all_tickers_prices = pyupbit.get_current_price(all_tickers)
    all_tickers_value = {}

    # 각 종목의 거래대금을 조사한다.
    for k, v in all_tickers_prices.items() :
        if  v < 90000 :   # 단가가 9만원 미만인 것만...
            df = pyupbit.get_ohlcv(k, count=10, interval='minute60')  #60분봉 3개의 거래대금
            df['ma5'] = df['close'].rolling(window=5).mean()
            time.sleep(0.5)
            if (len(df.index) > 0) and (df.iloc[-1]['close'] < df.iloc[-1]['ma5']) :
                print_(k,f"idx-1:close < idx-1:ma5: {df.iloc[-1]['close']} < {df.iloc[-1]['ma5']} ")
                all_tickers_value[k] = df['value'].sum()

    # 거래대금 top 10 에 해당하는 종목만 걸러낸다
    sorted_list = sorted(all_tickers_value.items(), key=lambda x : x[1], reverse=True)[:10]
    top_tickers = [e[0] for e in sorted_list]
    tickers = []
    for  t in  top_tickers :
        tickers.append(Ticker(t))
    return tickers

print_('',f"Autotrader(Ntype) init.. ")
tickers = best_volume_tickers()
print_('',f"best_volume_tickers finished.. count={len(tickers)} tickers={tickers}")

current_time = dt.datetime.now()
next_time = current_time + dt.timedelta(hours=2)

loop_cnt = 0
print_loop = 20
# 자동매매 시작
while  True :
    loop_cnt +=1
    try : 
        if  loop_cnt > print_loop :
            loop_cnt = 0

        current_time = dt.datetime.now()
        balances = account.get_balances()
        if  (len(balances)==0) and  (current_time > next_time) :  # 주기적으로 거래량top10 종목들 재갱신
            next_time = current_time + dt.timedelta(hours=2)
            tickers = best_volume_tickers()
            print_('',f"best_volume_tickers finished.. count={len(tickers)} tickers={tickers}")
            continue

        for t in  tickers :  
            # 이미 잔고가 있는 종목은 목표가에 왔는지 확인하고 즉시 매도 처리 한다.
            btc=account.get_balance(t.currency)
            if  btc > 0 :
                current_price = float(pyupbit.get_orderbook(ticker=t.name)["orderbook_units"][0]["bid_price"])
                avg_buy_price = account.get_avg_buy_price(t.currency)
                if  loop_cnt == print_loop :
                    print_(t.name,f'avg:p-cut:l-cut = {avg_buy_price:,.4f}:{avg_buy_price*1.006:,.4f}:{max(avg_buy_price * 0.985,t.losscut_price):,.4f}, curr_price= {current_price:,.4f}')
                if  ( current_price > avg_buy_price * 1.006 ) or \
                    ( current_price < max(avg_buy_price * 0.985,t.losscut_price) ) :
                    account.sell_limit_order(t.name, current_price, btc )
                continue

            ret = t.make_df()
            if t.target_price > 0 :
                buy_enable_balance =  _MAX_SEEDS - account.get_tot_buy_price()
                krw = account.get_balance("KRW")
                print_(t.name,f'KRW : {krw}, usable : {buy_enable_balance}')
                if (buy_enable_balance > 0) and (krw > 5000):
                    trys = 60
                    while trys > 0 :
                        trys -= 1
                        current_price = float(pyupbit.get_orderbook(ticker=t.name)["orderbook_units"][0]["ask_price"]) 
                        print_(t.name,f'buy_{trys}: Target(*1.002)={t.target_price:,.4f}({t.target_price*1.002:,.4f}), curr_price={current_price:,.4f}')
                        if t.target_price * 1.002 > current_price:
                            amount = min(buy_enable_balance,krw,_MAX_A_BUY) // current_price
                            print_(t.name,f'buy_get_balance(KRW): {krw:,.2f} current_price {current_price:,.4f} amount :{amount}')
                            if amount > 0:
                                account.buy_limit_order(t.name, current_price, amount )
                                break
                        time.sleep(1)                    
            else :
                if  loop_cnt == print_loop :
                    print_(t.name,f'make_df: {ret}')
            time.sleep(1)
    except Exception as e:
        print_('',f'{e}')
        time.sleep(1)