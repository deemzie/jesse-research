# jesse-research
Analyze Jesse backtest results and indicators with clean TradingView charts in jupyter.

This project is a continuation of these two projects:
Lightweight Charts for Jesse : https://github.com/Gabri/jupyterlab-lightweight-charts-jesse
and Jesse Trades Info : https://github.com/nick-dolan/jesse-trades-info

It leverages the power of lightweight charts TradingView library imported to jupyter to visualize indicators and backtest results in a straightforward and modulable way for improved research.

Main Features:
1. Print costumizable candle and indicator series in TV clean charts.
2. Feed candles series from jesse database and calculate indicators directly within jupyter or import indicator seris from .json file.
3. Read backtest json files and displays an interactive table of trades that expands to display orders table and show them on chart.

Installation process:
1. Copy this repo into the root of your Jesse directory in your server.
2. Run Jesse and Jypyter Lab.
3. Import candles
4. Edit your strategy file like the example to select the indicators you want to save in the before method and dump the json files in the terminate method.
5. Run your backtest
6. Go to jupyter, open the notebook and select your backtest by editing the name file ; select the timeframe you want to look at ; warmup candles and initial balance.
7. Select and customize your indicators to plot on the chart in the last notebook cell.
8. Run the notebook.

Known issues:
1. "Javascript: require is not defined" may pop, just rerun the notebook.
2. Candlestick markers on orders may have an offset when using different timeframes than the backtest. 

![equity](https://github.com/user-attachments/assets/c8c5f4d3-2777-424f-a34a-987262a60a29)
![chart](https://github.com/user-attachments/assets/c502bca6-3ead-4a2f-8118-15ebd24e3103)
