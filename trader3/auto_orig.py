import time
import pyupbit
import datetime as dt
import pandas as pd
from ticker import Ticker
import account

_MAX_SEEDS = 1000000   # 이 전략으로 운용하는 전체 금액
_MAX_A_BUY = 500000    # 한번의 매수 최대금액

def print_(ticker,msg)  :
    if  ticker :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'#'+ticker+'# '+msg
    else :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' '+msg
    print(ret, flush=True)

# 거래량 상위 20개 종목 선별
def best_volume_tickers() : 
    all_tickers = pyupbit.get_tickers(fiat="KRW")
    all_tickers_prices = pyupbit.get_current_price(all_tickers)
    all_tickers_value = {}

    # 각 종목의 거래대금을 조사한다.
    for k, v in all_tickers_prices.items() :
        if  v < 90000 :   # 단가가 9만원 미만인 것만...
            df = pyupbit.get_ohlcv(k, count=3, interval='minute60')  #60분봉 3개의 거래대금 합을 가져오기 위함
            time.sleep(0.2)
            if len(df.index) == 3 :
                # if  (k == 'KRW-T') or (k == 'KRW-CELO'):  #상장된지 얼마안된건 제외.에러남.
                #     continue
                all_tickers_value[k] = df['value'].sum()

    # 거래대금 top 10 에 해당하는 종목만 걸러낸다
    sorted_list = sorted(all_tickers_value.items(), key=lambda x : x[1], reverse=True)[:20]
    top_tickers = [e[0] for e in sorted_list]
    tickers = []
    for  t in  top_tickers :
        ticker = Ticker(t)
        ticker.make_df()
        ticker.get_start_time()
        if  ticker.isgood :
            tickers.append(ticker)

    # 이미 잔고가 있는 종목은 거래대금TOP10 리스트에 강제 추가 한다
    balances = account.get_balances()
    for b in balances :
        rt = True
        tmp_ticker = b['currency']
        tmp_ticker = 'KRW-' + tmp_ticker
        for t in tickers :
            if (tmp_ticker == t.name) :
                rt=False
                break
        if  rt :
            ticker = Ticker(tmp_ticker)
            ticker.bestValue()
            ticker.make_df()
            ticker.get_start_time()
            tickers.append(ticker)
    return tickers

print_('',f"Autotrader init.. ")
tickers = best_volume_tickers()
print_('',f"best_volume_tickers finished.. count={len(tickers)} tickers={tickers}")
# for t in tickers :
#     pd.set_option('display.max_columns', None)
#     print_(t.name,'------------------')
#     print(t.df.tail(3), flush=True)

loop_cnt = 0
print_loop = 20

# 자동매매 시작
while  True :
    loop_cnt +=1
    time.sleep(2)

    if loop_cnt == print_loop :
        print_('',f"current tickers={tickers}")
    try : 
        if loop_cnt > print_loop :   # 운영모드로 가면 충분히 크게 바꿀것..
            loop_cnt = 0

        if  not tickers :
            print_('',f"None tickers selected. bestVolume search again after 5 minute sleep")
            time.sleep(300)
            tickers = best_volume_tickers()
            print_('',f"best_volume search finished.. count={len(tickers)} tickers={tickers}")
            loop_cnt = 0
            # for t in tickers :
            #     pd.set_option('display.max_columns', None)
            #     print_(t.name,'------------------')
            #     print(t.df.tail(3), flush=True)
            continue

        current_time = dt.datetime.now()
        for t in  tickers :
            time.sleep(1)
            if loop_cnt == print_loop :   # 운영모드로 가면 충분히 크게 바꿀것..
                print_(t.name,f'{t.start_time:%Y-%m-%d %H:%M:%S} ~ {t.end_time:%Y-%m-%d %H:%M:%S}, target:{t.target_price:,.4f}, current:{pyupbit.get_current_price(t.name):,.4f}')

            if  current_time > t.nextday :       
                btc=account.get_balance(t.currency) 
                if  btc > 0 :
                    avg_buy_price = account.get_avg_buy_price(t.currency)
                    current_price = float(pyupbit.get_orderbook(ticker=t.name)["orderbook_units"][0]["bid_price"])
                    print_(t.name,f'force to sell current_price= {current_price:,.4f} avg_buy_price={avg_buy_price:,.4f} profit/loss={(1-(current_price/avg_buy_price))*100:,.4f}(%)')
                    account.sell_limit_order(t.name, current_price, btc )
                    # pd.set_option('display.max_columns', None)
                    # print_(t.name,'------------------')
                    # print(t.df.tail(3), flush=True)
                try :
                    print_(t.name,'removed from ticker list')
                    tickers.remove(t)
                except ValueError :
                    pass
                break

            elif  t.start_time < current_time < t.end_time :    
                btc=account.get_balance(t.currency)
                ''' 보유하고 있는 코인이 있으면 해당코인이 익절 및 손절가격에 왔는지 확인하고
                    필요시 익절 및 손절한다.'''
                if  btc > 0 :
                    current_price = float(pyupbit.get_orderbook(ticker=t.name)["orderbook_units"][0]["bid_price"])
                    avg_buy_price = account.get_avg_buy_price(t.currency)
                    if loop_cnt == print_loop :
                        print_(t.name,f'balance exist!. avg_buy_price={avg_buy_price:,.4f} ,current_price={current_price:,.4f}')
                    if  ( current_price > avg_buy_price * 1.1 ) or \
                        ( current_price < avg_buy_price * 0.9 ) :
                        print_(t.name,f'force to sell current_price= {current_price:,.4f} avg_buy_price={avg_buy_price:,.4f} profit/loss={(1-(current_price/avg_buy_price))*100:,.4f}(%)')
                        account.sell_limit_order(t.name, current_price, btc )
                        # pd.set_option('display.max_columns', None)
                        # print_(t.name,'------------------')
                        # print(t.df.tail(3), flush=True)
                        print_(t.name,'removed from ticker list')
                        tickers.remove(t)
                        break
                else :
                    current_price = float(pyupbit.get_orderbook(ticker=t.name)["orderbook_units"][0]["ask_price"]) 
                    if t.target_price > current_price:
                        buy_enable_balance =  _MAX_SEEDS - account.get_tot_buy_price()
                        krw = account.get_balance("KRW")
                        amount = min(buy_enable_balance,krw,_MAX_A_BUY) // current_price
                        print_(t.name,f'buy_get_balance(KRW): {krw:,.4f} current_price {current_price:,.4} amount :{amount:,.4f}')
                        if (krw > 5000) and (amount > 0):
                            account.buy_limit_order(t.name, current_price, amount )
                            # pd.set_option('display.max_columns', None)
                            # print_(t.name,'------------------')
                            # print(t.df.tail(3), flush=True)
    except Exception as e:
        print_('',f'{e}')
        time.sleep(1)