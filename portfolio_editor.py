#!/usr/bin/env python3
"""포트폴리오 편집기 - 종목명 또는 종목코드로 추가/삭제 가능"""

import json
import sys
import re
from pathlib import Path
import yfinance as yf

PORTFOLIO_PATH = Path(__file__).parent / "portfolio.json"

KR_MARKET_SUFFIXES = [".KS", ".KQ"]  # KOSPI, KOSDAQ


def load_portfolio() -> dict:
    if PORTFOLIO_PATH.exists():
        return json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))
    return {"stocks": [], "settings": {}}


def save_portfolio(data: dict):
    PORTFOLIO_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_kr_code(code: str) -> bool:
    """6자리 숫자면 한국 종목코드"""
    return bool(re.match(r"^\d{6}$", code.strip()))


def resolve_ticker(query: str) -> dict | None:
    """
    종목명 또는 종목코드를 입력받아 {ticker, name, exchange, market} 반환.
    한국 6자리 코드 → pykrx로 이름 조회
    그 외 → yfinance search
    """
    query = query.strip()

    if is_kr_code(query):
        return _resolve_kr_code(query)

    # yfinance 검색 시도
    try:
        search = yf.Search(query, max_results=5)
        quotes = search.quotes
        if quotes:
            q = quotes[0]
            ticker = q.get("symbol", "")
            name = q.get("longname") or q.get("shortname") or ticker
            exchange = q.get("exchange", "")
            market = _detect_market(ticker, exchange)
            return {"ticker": ticker, "name": name, "exchange": exchange, "market": market, "query": query}
    except Exception as e:
        print(f"  yfinance 검색 오류: {e}")

    # 직접 ticker로 시도
    try:
        t = yf.Ticker(query)
        info = t.fast_info
        name = getattr(info, "longName", None) or query
        exchange = getattr(info, "exchange", "")
        market = _detect_market(query, exchange)
        return {"ticker": query.upper(), "name": name, "exchange": exchange, "market": market, "query": query}
    except Exception:
        pass

    return None


def _resolve_kr_code(code: str) -> dict | None:
    """한국 종목코드 6자리 → KS/KQ ticker 결정"""
    try:
        from pykrx import stock as krx
        name = krx.get_market_ticker_name(code)
        if name:
            # KOSPI/KOSDAQ 구분
            try:
                kospi = krx.get_market_ticker_list(market="KOSPI")
                suffix = ".KS" if code in kospi else ".KQ"
            except Exception:
                suffix = ".KS"
            ticker = code + suffix
            return {"ticker": ticker, "name": name, "exchange": "KRX", "market": "KR", "kr_code": code, "query": code}
    except Exception as e:
        print(f"  pykrx 조회 오류: {e}")
    return None


def _detect_market(ticker: str, exchange: str) -> str:
    upper = ticker.upper()
    exch = exchange.upper()
    if upper.endswith(".KS") or upper.endswith(".KQ") or "KSC" in exch or "KOE" in exch:
        return "KR"
    if upper.endswith(".T") or "JPX" in exch:
        return "JP"
    if upper.endswith(".HK"):
        return "HK"
    if upper.endswith(".L"):
        return "UK"
    if upper.endswith(".DE") or upper.endswith(".F"):
        return "DE"
    return "US"


def list_stocks(portfolio: dict):
    stocks = portfolio.get("stocks", [])
    if not stocks:
        print("  (포트폴리오가 비어 있습니다)")
        return
    print(f"  {'#':>3}  {'종목명':<20} {'티커':<15} {'시장':<6} {'거래소'}")
    print("  " + "-" * 60)
    for i, s in enumerate(stocks, 1):
        print(f"  {i:>3}. {s['name']:<20} {s['ticker']:<15} {s['market']:<6} {s.get('exchange','')}")


def add_stock(portfolio: dict, query: str):
    result = resolve_ticker(query)
    if not result:
        print(f"  ✗ '{query}' 를 찾을 수 없습니다.")
        return
    stocks = portfolio.setdefault("stocks", [])
    # 중복 체크
    if any(s["ticker"].upper() == result["ticker"].upper() for s in stocks):
        print(f"  이미 포트폴리오에 있습니다: {result['name']} ({result['ticker']})")
        return
    stocks.append(result)
    save_portfolio(portfolio)
    print(f"  ✓ 추가됨: {result['name']} ({result['ticker']}) [{result['market']}]")


def remove_stock(portfolio: dict, query: str):
    stocks = portfolio.get("stocks", [])
    query_upper = query.upper().strip()
    removed = None
    new_stocks = []
    for s in stocks:
        if s["ticker"].upper() == query_upper or s["name"] == query.strip():
            removed = s
        else:
            new_stocks.append(s)
    if removed:
        portfolio["stocks"] = new_stocks
        save_portfolio(portfolio)
        print(f"  ✓ 삭제됨: {removed['name']} ({removed['ticker']})")
    else:
        print(f"  ✗ '{query}' 를 포트폴리오에서 찾을 수 없습니다.")


def set_setting(portfolio: dict, key: str, value: str):
    settings = portfolio.setdefault("settings", {})
    # 타입 변환
    if value.lower() in ("true", "yes", "1"):
        settings[key] = True
    elif value.lower() in ("false", "no", "0"):
        settings[key] = False
    else:
        settings[key] = value
    save_portfolio(portfolio)
    print(f"  ✓ 설정: {key} = {settings[key]}")


def interactive_menu():
    print("\n" + "=" * 60)
    print("  📊 주식 브리핑 포트폴리오 편집기")
    print("=" * 60)
    portfolio = load_portfolio()

    while True:
        print("\n  [메뉴]")
        print("  1. 포트폴리오 보기")
        print("  2. 종목 추가 (종목명 또는 종목코드)")
        print("  3. 종목 삭제")
        print("  4. 설정 변경 (DART API 키 등)")
        print("  5. 종료")
        choice = input("\n  선택 (1-5): ").strip()

        if choice == "1":
            print()
            list_stocks(portfolio)

        elif choice == "2":
            query = input("  추가할 종목명 또는 코드 입력: ").strip()
            if query:
                print("  검색 중...")
                add_stock(portfolio, query)

        elif choice == "3":
            list_stocks(portfolio)
            query = input("\n  삭제할 티커 또는 종목명 입력: ").strip()
            if query:
                remove_stock(portfolio, query)

        elif choice == "4":
            print("\n  설정 가능한 항목:")
            print("    dart_api_key   - DART 오픈API 키")
            print("    send_kakao     - 카카오톡 전송 (true/false)")
            print("    send_gmail     - Gmail 전송 (true/false)")
            print("    gmail_to       - Gmail 수신 주소")
            key = input("  설정 키: ").strip()
            val = input("  설정 값: ").strip()
            if key and val:
                set_setting(portfolio, key, val)

        elif choice == "5":
            print("  종료합니다.")
            break
        else:
            print("  잘못된 입력입니다.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        portfolio = load_portfolio()
        if cmd == "list":
            list_stocks(portfolio)
        elif cmd == "add" and len(sys.argv) > 2:
            add_stock(portfolio, " ".join(sys.argv[2:]))
        elif cmd == "remove" and len(sys.argv) > 2:
            remove_stock(portfolio, " ".join(sys.argv[2:]))
        else:
            print("사용법: portfolio_editor.py [list|add <종목>|remove <종목>]")
    else:
        interactive_menu()
