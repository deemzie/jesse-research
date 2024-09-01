import pandas as pd
import numpy as np
import json
from IPython.display import Javascript, display

def plot(candles, buys=pd.Series(), sells=pd.Series(), data=dict, config=[], dark_theme=False, width=980, height=700, chart_name='chart'):
    js = init(chart_name)
    js += inject_candles(candles, chart_name)
    js += inject(buys, chart_name, 'buys')
    js += inject(sells, chart_name, 'sells')
    js += inject(data, chart_name)
    js += inject(config, chart_name, name='config')
    js += render(width, height, dark_theme, chart_name)
    display(Javascript(js))

def plot_series(series, config, dark_theme=False, width=980, height=700, chart_name='chart'):
    js = init(chart_name)
    js += inject(series, chart_name)
    js += inject(config, chart_name, name='config')
    js += render_series(width, height, dark_theme, chart_name)
    display(Javascript(js))
    
### Internal utils
def date_to_time(date):
    return int(date.strftime('%s')) if isinstance(date, pd.Timestamp) else int(date)

# Use to process series into lw_data before using inject
def transform_series(series):
    return [{'time': date_to_time(date), 'value': float(val)} for date, val in series.iteritems()]

# Use if you want low level control over what's injected
def init(chart_name):
    return f""" if (typeof window.{chart_name}_data !== 'object') {{ window.{chart_name}_data = {{}} }}""" +  """
    if (typeof require === 'undefined') {
        console.log('Loading Require');
        var script2 = document.createElement('script');
        script2.src = 'https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.6/require.min.js';
        document.head.appendChild(script2);
    }
    else {
        console.log('Require loaded');
    }
                       
    if (typeof $ === 'undefined') {
        console.log('Loading JQuery');
        var script1 = document.createElement('script');
        script1.src = 'https://code.jquery.com/jquery-3.6.0.min.js';
        document.head.appendChild(script1);
    }
    else {
        console.log('JQuery loaded');
    }
    // Describe dependencies
    require.config({
        paths: {
            'lightweight-charts': ['//unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production']
        },
        shim: {
            'lightweight-charts': {
                exports: "LightweightCharts",
            },
        }
    });

    var darkTheme = {
    	chart: {
    		layout: {
    			background: {
    				type: 'solid',
    				color: '#2B2B43',
    			},
    			lineColor: '#2B2B43',
    			textColor: '#D9D9D9',
                attributionLogo: false, 
    		},
    		watermark: {
    			color: 'rgba(0, 0, 0, 0)',
    		},
    		crosshair: {
    			color: '#758696',
    		},
    		grid: {
    			vertLines: {
    				color: '#2B2B43',
    			},
    			horzLines: {
    				color: '#363C4E',
    			},
    		},
        	},
    };

    const lightTheme = {
    	chart: {
    		layout: {
    			background: {
    				type: 'solid',
    				color: '#FFFFFF',
    			},
    			lineColor: '#2B2B43',
    			textColor: '#191919',
                attributionLogo: false, 
    		},
    		watermark: {
    			color: 'rgba(0, 0, 0, 0)',
    		},
    		grid: {
    			vertLines: {
    				visible: false,
    			},
    			horzLines: {
    				color: '#f0f3fa',
    			},
    		},
    	},
    };

    var themesData = {
    	Dark: darkTheme,
    	Light: lightTheme,
    };"""


def inject_candles(candles, chart_name):
    candles['color'] = np.where(candles['close'] > candles['open'], 'rgba(38,166,154,0.6)', 'rgba(255,56,55,0.6)')
    return f"""window.{chart_name}_candles = {candles.to_json(orient="records")};
                  window.{chart_name}_volume = {candles.filter(["time", "volume","color"]).rename(columns={"volume":"value"}).to_json(orient="records")};"""

def inject_json(data, chart_name, json_name):
    return f"""window.{chart_name}_data["{json_name}"] = {json.dumps(data)};"""

# Use to automatically transform and inject pd.Series
def inject_series(series, chart_name, series_name=None):
    return inject_json(transform_series(series), chart_name, series.name if series_name is None else series_name)

# Use to automatically transform and inject pd.DataFrame
def inject_df(df, chart_name):
    return " ".join([inject_series(df[col], chart_name, col) for col in df])

def inject(data, chart_name, name=None):
    if isinstance(data, pd.Series):
        return inject_series(data, chart_name, name)
    elif isinstance(data, pd.DataFrame):
        return inject_df(data, chart_name, name)
    elif isinstance(data, dict):
        return " ".join([inject_series(data[name], chart_name, name) for name in data])
    else:
        return inject_json(data, chart_name, name)

def cleanup(name):
    display(Javascript(f"""window.{name}_data = undefined;"""))

def render_series(width=950, height=700, dark_theme=False, chart_name='chart'):
    return f"""
    require(['lightweight-charts'], function() {{
        // (Re-)create div to display the chart in
        $("#{chart_name}").remove();
        var container = document.createElement('div');
        const id = '{chart_name}';
        container.id = id;
        element.appendChild(container);

        var chart = LightweightCharts.createChart(id, {{width: {width}, height: {height}}})
        const theme = '{"Dark" if dark_theme == True else "Light"}';
        chart.applyOptions(themesData[theme].chart);

        {chart_name}_data.config.forEach(it => {{
            const params = {{'title': it['name'], ...it['style']}};
            const data = {chart_name}_data[it['name']];
            if (it['attach']) {{
                chart[it['fn']](params).setData(data);
                chart.timeScale().fitContent();
            }} else {{
                var chart_serie = LightweightCharts.createChart(id, {{width: {width}, height: it['height']}});
                const theme = '{"Dark" if dark_theme == True else "Light"}';
                chart_serie.applyOptions(themesData[theme].chart);
                all_charts.push(chart_serie)
                
                const serie = chart_serie[it['fn']](params);
                serie.setData(data);
                all_series.push(serie)

                chart_serie.priceScale('right').applyOptions({{  minimumWidth: 100, }});

                const visibleRange = chart.timeScale().getVisibleRange();
                chart_serie.timeScale().setVisibleRange(chart.timeScale().getVisibleRange());

            }}
        }})
    }})
    """


def render(width=950, height=700, dark_theme=False, chart_name='chart'):
    return f"""
    require(['lightweight-charts'], function() {{
        // (Re-)create div to display the chart in
        $("#{chart_name}").remove();
        var container = document.createElement('div');
        const id = '{chart_name}';
        container.id = id;
        element.appendChild(container);

        var chart = LightweightCharts.createChart(id, {{width: {width}, height: {height}}})
        const theme = '{"Dark" if dark_theme == True else "Light"}';
        chart.applyOptions(themesData[theme].chart);

        // Adding candles
        var candleSeries = chart.addCandlestickSeries();
        candleSeries.setData({chart_name}_candles)

        function findNearestCandle(time) {{
            time = Math.floor(time / 60) * 60;
            while (chart.timeScale().timeToCoordinate(time) == null) {{ time = time + 60; }} ;
            return chart.timeScale().timeToCoordinate(time);
        }}
        
        // Adding volume
        var volumeSeries = chart.addHistogramSeries({{
            color: '#26a69a',
            priceFormat: {{
                type: 'volume',
            }},
            priceScaleId: '',
            scaleMargins: {{
                top: 0.8,
                bottom: 0,
            }},
        }});
        volumeSeries.priceScale().applyOptions({{
            scaleMargins: {{
                top: 0.8,
                bottom: 0,
            }},
        }});
        volumeSeries.setData({chart_name}_volume)
        
        // Crosshair moves
        function getCrosshairDataPoint(series, param) {{
            if (!param.time) {{
                return null;
            }}
            const dataPoint = param.seriesData.get(series);
            return dataPoint || null;
        }}
        
        function syncCrosshair(chart, series, dataPoint) {{
            if (dataPoint) {{
                chart.setCrosshairPosition(dataPoint.value, dataPoint.time, series);
                return;
            }}
            chart.clearCrosshairPosition();
        }}
        
        // Adding indicators data
        // config and chart data should be injected in advance by calling any inject_* function
        var all_charts = [chart];
        var all_series = [candleSeries];
        chart.priceScale('right').applyOptions({{  minimumWidth: 100, }});

        {chart_name}_data.config.forEach(it => {{
            const params = {{'title': it['name'], ...it['style']}};
            const data = {chart_name}_data[it['name']];
            if (it['attach']) {{
                chart[it['fn']](params).setData(data);
            }} else {{
                var chart_serie = LightweightCharts.createChart(id, {{width: {width}, height: it['height']}});
                const theme = '{"Dark" if dark_theme == True else "Light"}';
                chart_serie.applyOptions(themesData[theme].chart);
                all_charts.push(chart_serie)
                
                const serie = chart_serie[it['fn']](params);
                serie.setData(data);
                all_series.push(serie)

                chart_serie.priceScale('right').applyOptions({{  minimumWidth: 100, }});

                const visibleRange = chart.timeScale().getVisibleRange();
                chart_serie.timeScale().setVisibleRange(chart.timeScale().getVisibleRange());

            }}
        }})

        // Synchronisation of charts time axis
        function handle(timeRange) {{ 
            all_charts.forEach(e => {{ e.timeScale().setVisibleLogicalRange(timeRange); }} ) 
        }}
        function subscribeRangeChange() {{
            all_charts.forEach((it,i) => {{
                it.timeScale().subscribeVisibleLogicalRangeChange(handle)
            }})
        }}
        // This function used for scrolling does not work and idk why
        function unsubscribeRangeChange() {{
            all_charts.forEach((it,i) => {{
                it.timeScale().unsubscribeVisibleLogicalRangeChange(handle)

            }})
            console.log(handle);
        }}
        subscribeRangeChange();
        
        all_charts.forEach((c, i) => {{
            c.subscribeCrosshairMove(param => {{
                all_charts.forEach((d, j) => {{
                    if (d != c) {{ const dataPoint = getCrosshairDataPoint(all_series[i], param); syncCrosshair(d, all_series[j], dataPoint); }}
                }})
            }})
        }})

        // Adding buy orders
        var buySeries = chart.addLineSeries({{
            color: '#30ff30',
        }});
        buySeries.setData({chart_name}_data.buys)
        buySeries.applyOptions({{
            priceLineVisible: false,
            lineVisible: false,
            pointMarkersVisible: true,
            pointMarkersRadius: 4,
        }});

        // Adding sell orders
        var sellSeries = chart.addLineSeries({{ color: '#ff0000' }});
        sellSeries.setData({chart_name}_data.sells)
        sellSeries.applyOptions({{
            priceLineVisible: false,
            lineVisible: false,
            pointMarkersVisible: true,
            pointMarkersRadius: 4,
        }});
        
        // Apply Option settings
        chart.applyOptions({{
            priceScale: {{
                autoscale: true
            }},
            timeScale: {{
                timeVisible: true,
                secondsVisible: true,
                rightOffset: 5
            }},
        }});

        // Make prices fully visible
        container.style["left"] = "-30px";
        // Make legend fully visible
        // document.querySelector("#chart > div > table > tr:nth-child(1) > td:nth-child(2) > div").style["left"] = "-30px"; 

        // Click on order or trade and move to date
        function move_to_date(dateString) {{ 
            const date = new Date(dateString);
            const time = date.getTime()/1000;

            const range = chart.timeScale().getVisibleRange();
            const d = (range.to - range.from)/2;

            chart.timeScale().setVisibleRange({{ from: time - d, to: time + d, }});
        }}

        function correct_time(time) {{
            time = Math.floor(time / 60) * 60;
            while (chart.timeScale().timeToCoordinate(time) == null) {{ time = time - 60; }} ;
            return time;
        }}
        document.querySelectorAll('.clickable-row').forEach(row => {{
            row.addEventListener('click', () => {{ 
                const dateString = row.querySelector("#date").textContent; 
                console.log(dateString);
                move_to_date(dateString); 

                const date = new Date(dateString);
                const time = date.getTime()/1000;
                if (row.querySelector("#type").textContent == 'long') {{
                    candleSeries.setMarkers( [{{
                        time: time,
                        position: 'belowBar',
                        color: '#2196F3',
                        shape: 'arrowUp',
                        text: 'Buy @ ' + row.querySelector("#entry").textContent,
                    }}])
                }} else {{
                    candleSeries.setMarkers( [{{
                        time: time,
                        position: 'aboveBar',
                        color: '#e91e63',
                        shape: 'arrowDown',
                        text: 'Sell @ ' + row.querySelector("#entry").textContent,
                    }}])
                }}
            }});
        }});

        document.querySelectorAll('#order').forEach(row => {{
            row.addEventListener('click', () => {{ 
                const dateString = row.querySelector("#date").textContent; 
                console.log(dateString);
                move_to_date(dateString);
                
                const date = new Date(dateString);
                const time = date.getTime()/1000;
                if (row.querySelector("#side").textContent == 'buy') {{
                    candleSeries.setMarkers( [{{
                        time: time,
                        position: 'belowBar',
                        color: '#2196F3',
                        shape: 'arrowUp',
                        text: 'Buy @ ' + row.querySelector("#price").textContent,
                    }}])
                }} else {{
                    candleSeries.setMarkers( [{{
                        time: time,
                        position: 'aboveBar',
                        color: '#e91e63',
                        shape: 'arrowDown',
                        text: 'Sell @ ' + row.querySelector("#price").textContent,
                    }}])
                }}
            }});
        }});

        
    }});
    """