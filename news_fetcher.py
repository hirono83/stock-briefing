#!/usr/bin/env python3
"""뉴스 및 공시 수집 - yfinance, SEC EDGAR, DART, 웹 검색"""

import json
import re
import requests
from datetime import date, timedelta
from pathlib import Path

PORTFOLIO_PATH = Path(__file__).parent / "portfolio.json"
TODAY = date.today().strftime("%Y-%m-%d")
TODAY_YYYYMMDD = date.today().strftime("%Y%m%d")


def load_portfolio() -> dict:
    return json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))


# ── yfinance 뉴스 ─────────────────────────────────────────────────────────────

def get_yf_news(ticker: str, max_items: int = 6) -> list[dict]:
    """yfinance에서 ticker 관련 뉴스 수집"""
    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        news = t.news or []
        results = []
        for n in news[:max_items]:
            content = n.get("content", {})
            title = content.get("title") or n.get("title", "")
            summary = content.get("summary") or ""
            pub = content.get("pubDate") or n.get("providerPublishTime", "")
            provider = content.get("provider", {})
            source = provider.get("displayName") if isinstance(provider, dict) else str(provider)
            url = content.get("canonicalUrl", {})
            link = url.get("url", "") if isinstance(url, dict) else ""
            if title:
                results.append({
                    "title": title,
                    "summary": summary,
                    "source": source or "Yahoo Finance",
                    "url": link,
                    "published": str(pub),
                    "lang": "en",
                })
        return results
    except Exception as e:
        print(f"  yfinance 뉴스 오류 ({ticker}): {e}")
        return []


# ── SEC EDGAR ────────────────────────────────────────────────────────────────

def get_sec_filings(ticker: str, max_items: int = 3) -> list[dict]:
    """SEC EDGAR에서 최근 공시 조회 (10-K, 10-Q, 8-K)"""
    try:
        # CIK 조회
        search_url = f"https://efts.sec.gov/LATEST/search-index?q=%22{ticker}%22&dateRange=custom&startdt={(date.today()-timedelta(days=30)).strftime('%Y-%m-%d')}&enddt={TODAY}&forms=8-K,10-Q,10-K"
        headers = {"User-Agent": "StockBriefing/1.0 jisthex@gmail.com"}
        r = requests.get(search_url, headers=headers, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        hits = data.get("hits", {}).get("hits", [])
        results = []
        for h in hits[:max_items]:
            src = h.get("_source", {})
            results.append({
                "title": f"[SEC {src.get('form_type','')}] {src.get('display_names','')}: {src.get('file_date','')}",
                "summary": src.get("period_of_report", ""),
                "source": "SEC EDGAR",
                "url": f"https://www.sec.gov/Archives/edgar/data/{src.get('entity_id','')}/{src.get('file_date','').replace('-','')}/",
                "published": src.get("file_date", ""),
                "lang": "en",
                "type": "filing",
            })
        return results
    except Exception as e:
        print(f"  SEC EDGAR 오류 ({ticker}): {e}")
        return []


# ── DART 공시 ────────────────────────────────────────────────────────────────

def get_dart_filings(kr_code: str, dart_api_key: str, max_items: int = 3) -> list[dict]:
    """DART 오픈API로 한국 공시 조회"""
    if not dart_api_key:
        return []
    try:
        from_date = (date.today() - timedelta(days=30)).strftime("%Y%m%d")
        url = "https://opendart.fss.or.kr/api/list.json"
        params = {
            "crtfc_key": dart_api_key,
            "corp_code": "",  # 아래에서 종목코드로 corp_code 조회 필요
            "bgn_de": from_date,
            "end_de": TODAY_YYYYMMDD,
            "last_reprt_at": "N",
            "pblntf_ty": "A",  # 정기공시
            "page_count": max_items,
        }
        # 종목코드 → corp_code 변환
        corp_url = "https://opendart.fss.or.kr/api/company.json"
        corp_params = {"crtfc_key": dart_api_key, "stock_code": kr_code}
        cr = requests.get(corp_url, params=corp_params, timeout=10)
        if cr.status_code == 200:
            corp_data = cr.json()
            corp_code = corp_data.get("corp_code", "")
            if corp_code:
                params["corp_code"] = corp_code

        r = requests.get(url, params=params, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("list", [])
        results = []
        for item in items[:max_items]:
            results.append({
                "title": f"[DART] {item.get('report_nm', '')}",
                "summary": f"{item.get('flr_nm','')} | {item.get('rcept_dt','')}",
                "source": "DART",
                "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcept_no','')}",
                "published": item.get("rcept_dt", ""),
                "lang": "ko",
                "type": "filing",
            })
        return results
    except Exception as e:
        print(f"  DART 오류 ({kr_code}): {e}")
        return []


# ── 종합 뉴스 수집 ────────────────────────────────────────────────────────────

def fetch_stock_news(stock: dict, dart_api_key: str = "") -> dict:
    """
    한 종목의 뉴스 + 공시를 수집하여 반환.
    반환: {ticker, name, intl_news: [...], kr_filings: [...], sec_filings: [...]}
    """
    ticker = stock["ticker"]
    name = stock["name"]
    market = stock.get("market", "US")
    kr_code = stock.get("kr_code", "")

    print(f"  [{name}] 뉴스 수집 중...")

    # yfinance 뉴스 (영문)
    yf_news = get_yf_news(ticker, max_items=6)

    # 공시
    sec_filings = []
    dart_filings = []
    if market == "US":
        sec_filings = get_sec_filings(ticker, max_items=3)
    elif market == "KR" and kr_code:
        dart_filings = get_dart_filings(kr_code, dart_api_key, max_items=3)

    return {
        "ticker": ticker,
        "name": name,
        "market": market,
        "intl_news": yf_news[:3],          # 해외 뉴스 3개
        "sec_filings": sec_filings,
        "dart_filings": dart_filings,
    }


def fetch_all_news(stocks: list[dict], dart_api_key: str = "") -> list[dict]:
    results = []
    for s in stocks:
        result = fetch_stock_news(s, dart_api_key)
        results.append(result)
    return results


if __name__ == "__main__":
    portfolio = load_portfolio()
    stocks = portfolio.get("stocks", [])
    dart_key = portfolio.get("settings", {}).get("dart_api_key", "")
    if not stocks:
        print("포트폴리오가 비어 있습니다.")
    else:
        all_news = fetch_all_news(stocks, dart_key)
        print(json.dumps(all_news, ensure_ascii=False, indent=2))
