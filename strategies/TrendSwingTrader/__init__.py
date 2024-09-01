from jesse.strategies import Strategy, cached
import jesse.indicators as ta
from jesse import utils

import datetime
import json
from datetime import datetime
from jesse.store import store
import jesse.helpers as jh
from jesse.config import config
import os


class TrendSwingTrader(Strategy):
    @property
    def adx(self):
        return ta.adx(self.candles)

    @property
    def trend(self):
        e1 = ta.ema(self.candles, self.hp['ema1_period'])
        e2 = ta.ema(self.candles, self.hp['ema2_period'])
        e3 = ta.ema(self.candles, self.hp['ema3_period'])
        if e3 < e2 < e1 < self.price:
            return 1
        elif e3 > e2 > e1 > self.price:
            return -1
        else:
            return 0

    def should_long(self) -> bool:
        return self.trend == 1 and self.adx > self.hp['adx_threshold']

    def go_long(self):
        entry = self.price
        stop = self.price - ta.atr(self.candles) * self.hp['stop_loss']
        qty = utils.risk_to_qty(self.available_margin, 5, entry, stop, fee_rate=self.fee_rate)
        self.buy = qty, self.price

    def should_short(self) -> bool:
        return self.trend == -1 and self.adx > self.hp['adx_threshold']

    def go_short(self):
        entry = self.price
        stop = self.price + ta.atr(self.candles) * self.hp['stop_loss']
        qty = utils.risk_to_qty(self.available_margin, 5, entry, stop, fee_rate=self.fee_rate)
        self.sell = qty, self.price

    def should_cancel_entry(self) -> bool:
        return True

    def on_open_position(self, order) -> None:
        if self.is_long:
            self.take_profit = self.position.qty, self.price + ta.atr(self.candles) * self.hp['take_profit']
            self.stop_loss = self.position.qty, self.price - ta.atr(self.candles) * self.hp['stop_loss']
        elif self.is_short:
            self.take_profit = self.position.qty, self.price - ta.atr(self.candles) * self.hp['take_profit']
            self.stop_loss = self.position.qty, self.price + ta.atr(self.candles) * self.hp['stop_loss']

    def hyperparameters(self) -> list:
        return [
            {'name': 'stop_loss', 'type': float, 'min': 1, 'max': 3, 'default': 2},
            {'name': 'take_profit', 'type': float, 'min': 2, 'max': 5, 'default': 3.5},
            {'name': 'adx_threshold', 'type': int, 'min': 10, 'max': 50, 'default': 25},
            {'name': 'ema1_period', 'type': int, 'min': 15, 'max': 30, 'default': 21},
            {'name': 'ema2_period', 'type': int, 'min': 30, 'max': 70, 'default': 50},
            {'name': 'ema3_period', 'type': int, 'min': 80, 'max': 120, 'default': 100},
        ]

    def dna(self) -> str:
        # return 'GKiY8S'
        return 'HLivH('

    # Add to jesse flow
    def __init__(self):
        super().__init__()
        self.saved_series = {}

    def before(self):
        self.save_series_value([self.adx], ['adx'])

    def terminate(self):
        self.store_json()
        self.dump_series()

    # Toolbox to save data, should be imported from a custom Strategy object in another file
    def store_json(self):
        start_date = str(datetime.fromtimestamp(store.app.starting_time / 1000))[0:10]
        finish_date = str(datetime.fromtimestamp(store.app.time / 1000))[0:10]
        exchange = 'BF' if self.exchange == 'Binance Perpetual Futures' else self.exchange
        sid = jh.get_session_id()[-4:]
        file_name = f"{self.name}_{exchange}_{self.symbol}_{self.timeframe}_{start_date}_{finish_date}_{sid}"
        trades_json = {'trades': [], 'considering_timeframes': config['app']['considering_timeframes']}
        for t in store.completed_trades.trades:
            trades_json['trades'].append(self.toJSON(t))
    
        path = f'storage/json/{file_name}.json'
    
        os.makedirs('./storage/json', exist_ok=True)
        with open(path, 'w+') as outfile:
            def set_default(obj):
                if isinstance(obj, set):
                    return list(obj)
                raise TypeError
                
            json.dump(trades_json, outfile, default=set_default)
            
            
    def save_series_value(self, values, names):
        for (name, serie) in zip(names, values): 
            if name not in self.saved_series: self.saved_series[name] = {}
            self.saved_series[name][self.time] = serie
            
    def dump_series(self):
        start_date = str(datetime.fromtimestamp(store.app.starting_time / 1000))[0:10]
        finish_date = str(datetime.fromtimestamp(store.app.time / 1000))[0:10]
        exchange = 'BF' if self.exchange == 'Binance Perpetual Futures' else self.exchange
        sid = jh.get_session_id()[-4:]
        
        file_name = f"data_{self.name}_{exchange}_{self.symbol}_{self.timeframe}_{start_date}_{finish_date}_{sid}"
        path = f'storage/data/{file_name}.json'
    
        os.makedirs('./storage/data', exist_ok=True)
        with open(path, 'w+') as outfile:
            def set_default(obj):
                if isinstance(obj, set):
                    return list(obj)
                raise TypeError
                
            json.dump(self.saved_series, outfile, default=set_default)

    @staticmethod       
    def toJSON(trade):
        orders = [o.__dict__ for o in trade.orders]
        return {
            "id": trade.id,
            "strategy_name": trade.strategy_name,
            "symbol": trade.symbol,
            "exchange": trade.exchange,
            "type": trade.type,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "qty": trade.qty,
            "fee": trade.fee,
            "size": trade.size,
            "PNL": trade.pnl,
            "PNL_percentage": trade.pnl_percentage,
            "holding_period": trade.holding_period,
            "opened_at": trade.opened_at,
            "closed_at": trade.closed_at,
            "entry_candle_timestamp": trade.opened_at,
            "exit_candle_timestamp": trade.closed_at,
            "orders": orders,
        }