#!/usr/bin/env python3
"""주식 가격 데이터 수집 - pykrx(한국) + yfinance(글로벌)"""

import json
from datetime import date, timedelta
from pathlib import Path
import yfinance as yf

PORTFOLIO_PATH = Path(__file__).parent / "portfolio.json"


def load_portfolio() -> dict:
    return json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))


def get_kr_price(kr_code: str) -> dict | None:
    """pykrx로 한국 주식 당일 가격 조회"""
    try:
        from pykrx import stock as krx
        today = date.today().strftime("%Y%m%d")
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y%m%d")

        # 당일 데이터가 없을 수 있으므로 최근 5영업일 조회
        df = krx.get_market_ohlcv_by_date(yesterday, today, kr_code)
        if df is None or df.empty:
            # 주말/공휴일이면 더 앞으로
            from_date = (date.today() - timedelta(days=7)).strftime("%Y%m%d")
            df = krx.get_market_ohlcv_by_date(from_date, today, kr_code)

        if df is not None and not df.empty:
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) >= 2 else None
            close = float(latest["종가"])
            prev_close = float(prev["종가"]) if prev is not None else close
            change = close - prev_close
            change_pct = (change / prev_close * 100) if prev_close else 0
            return {
                "price": close,
                "open": float(latest["시가"]),
                "high": float(latest["고가"]),
                "low": float(latest["저가"]),
                "volume": int(latest["거래량"]),
                "change": change,
                "change_pct": round(change_pct, 2),
                "currency": "KRW",
                "date": df.index[-1].strftime("%Y-%m-%d"),
            }
    except Exception as e:
        print(f"  pykrx 오류 ({kr_code}): {e}")
    return None


def get_yf_price(ticker: str) -> dict | None:
    """yfinance로 글로벌 주식 가격 조회"""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="5d")
        if hist.empty:
            return None
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) >= 2 else None
        close = float(latest["Close"])
        prev_close = float(prev["Close"]) if prev is not None else close
        change = close - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0

        info = t.fast_info
        currency = getattr(info, "currency", "USD") or "USD"

        return {
            "price": close,
            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "volume": int(latest["Volume"]),
            "change": change,
            "change_pct": round(change_pct, 2),
            "currency": currency,
            "date": hist.index[-1].strftime("%Y-%m-%d"),
        }
    except Exception as e:
        print(f"  yfinance 오류 ({ticker}): {e}")
    return None


def fetch_all_prices(stocks: list[dict]) -> list[dict]:
    """포트폴리오 전체 주식의 현재가 수집"""
    results = []
    for s in stocks:
        ticker = s["ticker"]
        market = s.get("market", "US")
        kr_code = s.get("kr_code")
        name = s["name"]

        price_data = None
        # 한국 주식: pykrx 우선, 실패 시 yfinance
        if market == "KR" and kr_code:
            price_data = get_kr_price(kr_code)
        if price_data is None:
            price_data = get_yf_price(ticker)

        entry = {**s}
        if price_data:
            entry.update(price_data)
            arrow = "▲" if price_data["change"] >= 0 else "▼"
            sign = "+" if price_data["change"] >= 0 else ""
            cur = price_data["currency"]
            print(f"  {name} ({ticker}): {cur} {price_data['price']:,.2f}  "
                  f"{arrow} {sign}{price_data['change_pct']:.2f}%")
        else:
            entry["error"] = "가격 조회 실패"
            print(f"  {name} ({ticker}): 조회 실패")

        results.append(entry)
    return results


if __name__ == "__main__":
    portfolio = load_portfolio()
    stocks = portfolio.get("stocks", [])
    if not stocks:
        print("포트폴리오가 비어 있습니다. portfolio_editor.py 로 종목을 추가하세요.")
    else:
        print(f"총 {len(stocks)}개 종목 가격 조회 중...\n")
        fetch_all_prices(stocks)
