import time
import pyupbit
import pandas as pd
import datetime as dt
import pyupbit
import matplotlib.pyplot as plt
# import mpl_finance import candlestick2_ohlc


def print_(ticker,msg)  :
    if  ticker :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+'#'+ticker+'# '+msg
    else :
        ret = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' '+msg
    print(ret, flush=True)


class Ticker :
    def __init__(self, name) -> None:
        self.name =  name
        self.currency = name[name.find('-')+1:]
        self.fee = 0.0005   #업비트 거래소 매매거래 수수료
        self.isgood = True
        self.base = self.get_max_base()
        self.k = self.get_max_k(self.base)

    def __repr__(self):
        return f"<Ticker {self.name}>"

    def __str__(self):
        return f"<Ticker {self.name}>"

    def get_ohlcv_custom(self,_base) :
        df = pyupbit.get_ohlcv(self.name, count=300, interval='minute60')
        df.index = df.index - dt.timedelta(hours=_base)
        df_daily = pd.DataFrame()
        df_daily['open'] =  df.open.resample('1D').first()
        df_daily['close'] =  df.close.resample('1D').last()
        df_daily['low'] =  df.low.resample('1D').min()
        df_daily['high'] =  df.high.resample('1D').max()
        df_daily['volume'] =  df.volume.resample('1D').sum()
        df_daily['value'] =  df.value.resample('1D').sum()
        df_daily['ma5'] = df_daily['close'].rolling(5).mean()
        df_daily['ma5_acd'] = df_daily['ma5'] - df_daily['ma5'].shift(1)

        df_daily=df_daily.dropna()
        return df_daily

    def get_max_base(self) :
        basedict = {}
        maxBase =  0
        for b in range(1,24,1) :
            df = self.get_ohlcv_custom(b) 
            if len(df.index) <= 2 :
                continue
            d = ( df['close'][-2] - df['open'][-2] ) / df['open'][-2]
            basedict[str(round(d,4))] = str(b)
        if len(basedict) > 0 :
            maxkey = max(basedict.keys(), key=(lambda k : float(k)))
            maxBase = int(basedict[maxkey])
        # print(basedict)
        # print(f'maxBase={maxBase}')
        return maxBase

    def get_max_k(self,base) :
        df = self.get_ohlcv_custom(base)
        if len(df.index) <= 2 :
            return 0 
        df['adjust'] = ( df['close'].shift(1) - df['low'] ) / df['close'].shift(1)
        df = df[df['close'].shift(1)-df['open'].shift(1) > 0]
        mean = df['adjust'].mean()
        # print(df.tail(20))
        # print(mean)
        return mean

    def make_df(self) :
        try :
            df = self.get_ohlcv_custom(self.base)
            if len(df.index) <= 2 :
                self.isgood = False
                return
            df['asc_ratio'] = ( df['close'] - df['open'] ) / df['open']
            df['target'] = df['open'].shift(1) + ( ( df['close'].shift(1) - df['open'].shift(1) ) * (1-self.k) )
            self.df = df.copy()
            self.target_price = df.iloc[-1]['target'] 

            print_(self.name,'------------------')
            print_(self.name, f"k, base, target_price : {self.k:,.4f}, {self.base}, {self.target_price:,.4f}" )
            print_(self.name, f"idx-1:ma5_acd > 0 : {df.iloc[-1]['ma5_acd']:,.4f} > 0" )
            print_(self.name, f"idx-1:low > target_price : {df.iloc[-1]['low']:,.4f} > {self.target_price:,.4f}" )
            print_(self.name, f"idx-2:asc_ratio > 0.04 : {df.iloc[-2]['asc_ratio']:,.4f} > 0.04" )

            # 일봉상 5이평선이 우상향
            self.isgood = True if df.iloc[-1]['ma5_acd'] > 0 else False
            # 이미 목표가에 도달했었던 적있는 경우는 제외
            self.isgood = self.isgood and ( True if df.iloc[-1]['low'] > self.target_price else False )
            # 직전봉 4%이상 상승봉
            self.isgood = self.isgood and ( True if df.iloc[-2]['asc_ratio'] > 0.04 else False )
            print_(self.name, f"isgood : {self.isgood}" )
            pd.set_option('display.max_columns', None)
            print(self.df.tail(3), flush=True)
            print_(self.name,'------------------')
        except Exception :
            pass

    def get_start_time(self) :
        basetime = dt.datetime.now()

        start_time = basetime.replace(hour=self.base,minute=0,second=0)
        if start_time > basetime :
            nextday = start_time
            end_time = start_time - dt.timedelta(minutes=10)
            start_time = start_time - dt.timedelta(days=1)
            
        else :
            nextday = start_time + dt.timedelta(days=1)
            end_time = start_time + dt.timedelta(days=1) - dt.timedelta(minutes=10)

        self.start_time = start_time
        self.end_time = end_time
        self.nextday = nextday

if __name__ == "__main__":
    # print('KRW-T'['KRW-T'.find('-')+1:])

    t  = Ticker('KRW-XRP')
    maxbase = t.get_max_base()
    maxk = t.get_max_k(maxbase)
    print(f'maxbase = {maxbase}')
    print(f'maxk = {maxk}')
    t.make_df()
    print(t.df.tail(3))

    # plt.figure(figsize=(9,5))
    # plt.plot(t.df.index, t.df['close'], label="close")
    # plt.plot(t.df.index, t.df['ma5'], label="ma5")
    # plt.legend(loc='best')
    # plt.grid()
    # plt.show()