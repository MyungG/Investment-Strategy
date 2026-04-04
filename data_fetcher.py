import FinanceDataReader as fdr
import pandas as pd
from datetime import datetime, timedelta


def get_stock_list() -> pd.DataFrame:
    """코스피 + 코스닥 전체 종목 리스트 반환"""
    kospi  = fdr.StockListing("KOSPI")[["Code", "Name"]].copy()
    kosdaq = fdr.StockListing("KOSDAQ")[["Code", "Name"]].copy()
    kospi["market"]  = "KOSPI"
    kosdaq["market"] = "KOSDAQ"

    df = pd.concat([kospi, kosdaq], ignore_index=True)
    df.columns = ["ticker", "name", "market"]
    return df


def get_ohlcv(ticker: str, days: int = 250) -> pd.DataFrame:
    """종목의 최근 N 거래일 OHLCV 데이터 반환"""
    start = (datetime.today() - timedelta(days=days * 2)).strftime("%Y-%m-%d")
    try:
        df = fdr.DataReader(ticker, start)
        df = df.dropna()
        if len(df) == 0:
            return df
        return df.tail(days)
    except Exception:
        return pd.DataFrame()
