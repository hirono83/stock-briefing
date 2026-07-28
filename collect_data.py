#!/usr/bin/env python3
"""
데이터 수집 전용 스크립트 (원격 에이전트용)
API 키 불필요 - 가격과 뉴스를 JSON으로만 저장
"""

import json
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).parent
PORTFOLIO_PATH = BASE_DIR / "portfolio.json"
DATA_PATH = BASE_DIR / "raw_data.json"


def main():
    portfolio = json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))
    stocks = portfolio.get("stocks", [])
    settings = portfolio.get("settings", {})

    if not stocks:
        print("EMPTY_PORTFOLIO")
        return

    print(f"종목 {len(stocks)}개 데이터 수집 시작...\n")

    # 가격 수집
    from stock_data import fetch_all_prices
    price_data = fetch_all_prices(stocks)

    # 뉴스 수집
    from news_fetcher import fetch_all_news
    dart_api_key = settings.get("dart_api_key", "")
    news_data = fetch_all_news(stocks, dart_api_key)

    # raw_data.json 저장 (에이전트가 읽어서 브리핑 생성)
    output = {
        "date": date.today().isoformat(),
        "stocks_count": len(stocks),
        "prices": price_data,
        "news": news_data,
    }
    DATA_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ raw_data.json 저장 완료")


if __name__ == "__main__":
    main()
