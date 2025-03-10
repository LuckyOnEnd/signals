import os


class Config:
    captcha_api = '20889fecf36a0d81df702d81119d8f03'
    username = 'cys550301200@gmail.com'
    password = 'Mm9090!@#~~~'

    trading_view_login = os.getenv("TRADING_VIEW_ID")
    trading_view_password = os.getenv("TRADING_VIEW_PASSWORD")

    chart_link = 'https://www.tradingview.com/chart/qkIZxt36/'
