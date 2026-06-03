#!/usr/bin/env python3
"""
브리핑 JSON → claude CLI에 전달할 전송 프롬프트 생성
main.py 실행 후 이 스크립트를 실행하여 send_prompt.txt를 만듦
"""
import json
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).parent
briefing_path = BASE_DIR / "latest_briefing.json"
prompt_path = BASE_DIR / "send_prompt.txt"

if not briefing_path.exists():
    prompt_path.write_text("포트폴리오에 종목을 추가하세요. KakaotalkChat-MemoChat MCP 툴로 '포트폴리오에 종목을 추가하세요.' 메시지를 나에게 전송해주세요.", encoding="utf-8")
else:
    data = json.loads(briefing_path.read_text(encoding="utf-8"))
    briefing = data.get("briefing", "브리핑 생성 실패")
    today = date.today().strftime("%Y년 %m월 %d일")

    prompt = f"""다음 두 가지 작업을 순서대로 실행하세요.

## 작업 1: 카카오톡 전송
KakaotalkChat-MemoChat MCP 툴을 사용하여 아래 내용을 나에게 카카오톡으로 전송하세요.

--- 전송 내용 시작 ---
{briefing}
--- 전송 내용 끝 ---

## 작업 2: Gmail 전송
create_draft MCP 툴을 사용하여 이메일 초안을 만드세요.
- 수신자: jisthex@gmail.com
- 제목: [주식 브리핑] {today}
- 본문: 위의 전송 내용과 동일하게 작성

두 작업 모두 완료되면 "전송 완료"라고만 답하세요.
"""
    prompt_path.write_text(prompt, encoding="utf-8")
    print(f"send_prompt.txt 생성 완료 ({len(prompt)}자)")
