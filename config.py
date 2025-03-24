import os


class Config:
    captcha_api = '20889fecf36a0d81df702d81119d8f03'
    username = 'viacheslavmw861@gmail.com'
    password = 'AdminTestUser123@'

    trading_view_login = os.getenv("TRADING_VIEW_ID")
    trading_view_password = os.getenv("TRADING_VIEW_PASSWORD")

    chart_link = 'https://www.tradingview.com/chart/qkIZxt36/'
