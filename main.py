#!/usr/bin/env python3
"""
주식 브리핑 메인 실행 파일
- 포트폴리오 로드 → 가격 수집 → 뉴스 수집 → 브리핑 생성 → 결과를 JSON으로 저장
- 전송은 Claude Code MCP 툴로 처리
"""

import json
import sys
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).parent
PORTFOLIO_PATH = BASE_DIR / "portfolio.json"
OUTPUT_PATH = BASE_DIR / "latest_briefing.json"


def load_portfolio() -> dict:
    return json.loads(PORTFOLIO_PATH.read_text(encoding="utf-8"))


def run():
    print(f"\n{'='*60}")
    print(f"  📊 주식 브리핑 시작 - {date.today().strftime('%Y년 %m월 %d일')}")
    print(f"{'='*60}\n")

    portfolio = load_portfolio()
    stocks = portfolio.get("stocks", [])
    settings = portfolio.get("settings", {})
    dart_api_key = settings.get("dart_api_key", "")

    if not stocks:
        print("⚠️  포트폴리오가 비어 있습니다.")
        print("   python portfolio_editor.py 로 종목을 추가하세요.")
        return None

    print(f"📋 포트폴리오: {len(stocks)}개 종목\n")

    # 1. 주가 수집
    print("── 1단계: 주가 수집 ──────────────────────────")
    from stock_data import fetch_all_prices
    price_data = fetch_all_prices(stocks)

    # 2. 뉴스 수집
    print("\n── 2단계: 뉴스/공시 수집 ────────────────────")
    from news_fetcher import fetch_all_news
    news_data = fetch_all_news(stocks, dart_api_key)

    # 3. 브리핑 생성
    print("\n── 3단계: 브리핑 생성 (Claude API) ──────────")
    from briefing_generator import generate_briefing
    briefing_text = generate_briefing(price_data, news_data)

    print("\n" + "─" * 60)
    print(briefing_text)
    print("─" * 60)

    # 결과 저장
    output = {
        "date": date.today().isoformat(),
        "briefing": briefing_text,
        "price_data": price_data,
        "settings": settings,
    }
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ 브리핑 저장 완료: {OUTPUT_PATH}")
    return output


if __name__ == "__main__":
    result = run()
    if result:
        print("\n브리핑이 생성되었습니다. MCP 툴로 전송을 진행합니다.")
