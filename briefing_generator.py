#!/usr/bin/env python3
"""Claude API로 주식 브리핑 생성 (번역 + 요약 + 전문가 의견)"""

import os
import json
from datetime import date

TODAY_STR = date.today().strftime("%Y년 %m월 %d일")


def format_price_line(stock: dict) -> str:
    name = stock["name"]
    ticker = stock["ticker"]
    if "error" in stock:
        return f"• {name} ({ticker}): 가격 조회 실패"
    price = stock.get("price", 0)
    currency = stock.get("currency", "")
    change_pct = stock.get("change_pct", 0)
    change = stock.get("change", 0)
    arrow = "▲" if change >= 0 else "▼"
    sign = "+" if change >= 0 else ""
    cur_symbol = {"KRW": "₩", "USD": "$", "JPY": "¥", "EUR": "€", "GBP": "£", "HKD": "HK$"}.get(currency, currency)
    fmt_price = f"{price:,.0f}" if currency == "KRW" else f"{price:,.2f}"
    return f"• {name} ({ticker}): {cur_symbol}{fmt_price}  {arrow} {sign}{change_pct:.2f}%"


def build_prompt(price_data: list[dict], news_data: list[dict]) -> str:
    """Claude에게 전달할 브리핑 생성 프롬프트"""

    price_section = "\n".join(format_price_line(s) for s in price_data)

    news_section_parts = []
    for n in news_data:
        name = n["name"]
        ticker = n["ticker"]
        intl = n.get("intl_news", [])
        sec = n.get("sec_filings", [])
        dart = n.get("dart_filings", [])

        part = f"=== {name} ({ticker}) ===\n"

        if intl:
            part += "【해외 뉴스】\n"
            for item in intl:
                part += f"- [{item.get('source','')}] {item['title']}\n"
                if item.get("summary"):
                    part += f"  요약: {item['summary'][:200]}\n"

        if sec:
            part += "【SEC 공시】\n"
            for item in sec:
                part += f"- {item['title']}\n"

        if dart:
            part += "【DART 공시】\n"
            for item in dart:
                part += f"- {item['title']} ({item.get('summary','')})\n"

        if not intl and not sec and not dart:
            part += "(뉴스 없음)\n"

        news_section_parts.append(part)

    news_section = "\n\n".join(news_section_parts)

    prompt = f"""당신은 전문 주식 분석가입니다. 아래 데이터를 바탕으로 {TODAY_STR} 아침 주식 브리핑을 한국어로 작성해 주세요.

## 📊 오늘의 주가 현황
{price_section}

## 📰 종목별 뉴스 및 공시 원문
{news_section}

## 작성 지침
1. 영어/외국어 뉴스는 모두 한국어로 번역하여 작성하세요.
2. 각 종목별로 섹션을 나누어 정리하세요.
3. 뉴스가 있으면 국내 뉴스/해외 뉴스 구분하여 각 3개씩 요약하세요.
4. 주요 공시(SEC/DART)가 있으면 별도로 강조하세요.
5. 전문가 의견이나 애널리스트 코멘트가 뉴스에 있으면 함께 정리하세요.
6. 전체 포트폴리오 시황 요약을 첫 단락에 작성하세요.
7. 이모지를 활용해 가독성 있게 작성하세요.
8. 마지막에 오늘의 투자 포인트 1-2가지를 정리하세요.

카카오톡 메시지로 전송할 형식으로 작성하되, 전체 길이는 2000자 이내로 유지하세요."""

    return prompt


def generate_briefing(price_data: list[dict], news_data: list[dict]) -> str:
    """Claude API로 브리핑 생성"""
    import anthropic

    prompt = build_prompt(price_data, news_data)

    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


if __name__ == "__main__":
    import sys
    # 테스트용
    sample_prices = [
        {"name": "삼성전자", "ticker": "005930.KS", "price": 74000, "currency": "KRW",
         "change": 1000, "change_pct": 1.37},
        {"name": "Apple", "ticker": "AAPL", "price": 195.5, "currency": "USD",
         "change": -2.3, "change_pct": -1.16},
    ]
    sample_news = [
        {"name": "삼성전자", "ticker": "005930.KS", "market": "KR",
         "intl_news": [{"title": "Samsung beats earnings", "summary": "Q2 earnings beat expectations",
                        "source": "Reuters", "lang": "en"}],
         "sec_filings": [], "dart_filings": []},
    ]
    print(generate_briefing(sample_prices, sample_news))
