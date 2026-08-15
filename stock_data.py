#!/usr/bin/env python3
"""주식 가격 데이터 수집
- 국내(KR): 네이버 금융 폴링 API (yfinance/pykrx 불필요)
- 해외(US 등): Yahoo Finance Chart API (requests 직접 호출)
"""

import json
import os
from datetime import date, datetime
from pathlib import Path

import requests

PORTFOLIO_PATH = Path(__file__).parent / "portfolio.json"

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
_PROXY = os.environ.get("HTTPS_PROXY", "")
_PROXIES = {"https": _PROXY, "http": _PROXY} if _PROXY else {}


def _naver_price(kr_code: str) -> dict | None:
    """네이버 금융 폴링 API로 한국 주식 실시간 시세 조회"""
    url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{kr_code}"
    headers = {"Referer": "https://finance.naver.com/"}
    try:
        r = _SESSION.get(url, headers=headers, proxies=_PROXIES, timeout=8)
        r.raise_for_status()
        areas = r.json()["result"]["areas"]
        d = areas[0]["datas"][0]
        prev_close = d.get("sv") or d.get("pcv") or d["nv"]
        change = d["nv"] - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        traded_at = d.get("localTradedAt") or ""
        price_date = traded_at[:10] if traded_at else date.today().isoformat()
        return {
            "price": d["nv"],
            "open": d.get("ov", d["nv"]),
            "high": d.get("hv", d["nv"]),
            "low": d.get("lv", d["nv"]),
            "volume": d.get("aq", 0),
            "change": change,
            "change_pct": round(change_pct, 2),
            "prev_close": prev_close,
            "currency": "KRW",
            "date": price_date,
        }
    except Exception as e:
        print(f"  네이버 API 오류 ({kr_code}): {e}")
        return None


def _yahoo_price(ticker: str) -> dict | None:
    """Yahoo Finance Chart API로 글로벌 주식 시세 조회 (requests 직접 호출)"""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=5d"
    try:
        r = _SESSION.get(url, proxies=_PROXIES, timeout=10)
        r.raise_for_status()
        result = r.json()["chart"]["result"][0]
        meta = result["meta"]
        indicators = result["indicators"]["quote"][0]

        closes = [c for c in indicators.get("close", []) if c is not None]
        opens = [o for o in indicators.get("open", []) if o is not None]
        highs = [h for h in indicators.get("high", []) if h is not None]
        lows = [l for l in indicators.get("low", []) if l is not None]
        volumes = [v for v in indicators.get("volume", []) if v is not None]
        timestamps = result.get("timestamp", [])

        if not closes:
            return None

        current = meta.get("regularMarketPrice") or closes[-1]
        prev_close = meta.get("chartPreviousClose") or (closes[-2] if len(closes) >= 2 else current)
        change = current - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        currency = meta.get("currency", "USD")

        price_date = date.today().isoformat()
        if timestamps:
            price_date = datetime.fromtimestamp(timestamps[-1]).strftime("%Y-%m-%d")

        return {
            "price": round(current, 4),
            "open": round(opens[-1], 4) if opens else current,
            "high": round(highs[-1], 4) if highs else current,
            "low": round(lows[-1], 4) if lows else current,
            "volume": volumes[-1] if volumes else 0,
            "change": round(change, 4),
            "change_pct": round(change_pct, 2),
            "prev_close": round(prev_close, 4),
            "currency": currency,
            "date": price_date,
        }
    except Exception as e:
        print(f"  Yahoo Finance 오류 ({ticker}): {e}")
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
        if market == "KR" and kr_code:
            price_data = _naver_price(kr_code)
        if price_data is None:
            price_data = _yahoo_price(ticker)

        entry = {**s}
        if price_data:
            entry.update(price_data)
            arrow = "▲" if price_data["change"] >= 0 else "▼"
            sign = "+" if price_data["change"] >= 0 else ""
            cur = price_data["currency"]
            price_str = f"{price_data['price']:,.0f}" if cur == "KRW" else f"{price_data['price']:,.2f}"
            print(f"  {name} ({ticker}): {cur} {price_str}  "
                  f"{arrow} {sign}{price_data['change_pct']:.2f}%")
        else:
            entry["error"] = "가격 조회 실패"
            print(f"  {name} ({ticker}): 조회 실패")

        results.append(entry)
    return results


def load_portfolio() -> dict:
    return json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    portfolio = load_portfolio()
    stocks = portfolio.get("stocks", [])
    if not stocks:
        print("포트폴리오가 비어 있습니다. portfolio_editor.py 로 종목을 추가하세요.")
    else:
        print(f"총 {len(stocks)}개 종목 가격 조회 중...\n")
        fetch_all_prices(stocks)
