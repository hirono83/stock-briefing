# 매일 아침 주식 브리핑 자동화

다음 단계를 순서대로 실행하세요:

## 1단계: 브리핑 생성
```bash
cd "/Users/kwanz/Desktop/KwanZ's Data/stock_briefing"
python main.py
```

## 2단계: 결과 읽기
생성된 `/Users/kwanz/Desktop/KwanZ's Data/stock_briefing/latest_briefing.json` 파일을 읽어서 briefing 텍스트를 가져오세요.

## 3단계: 카카오톡 전송
KakaotalkChat-MemoChat MCP 툴을 사용하여 브리핑 내용을 나에게 전송하세요.

## 4단계: Gmail 전송
Gmail MCP 툴(create_draft)을 사용하여 이메일 초안을 만들고 전송하세요.
- 수신자: jisthex@gmail.com
- 제목: [주식 브리핑] YYYY년 MM월 DD일
- 본문: 브리핑 내용

## 웹 검색 보강
각 종목에 대해 오늘자 한국어 뉴스를 추가로 검색하여 브리핑에 반영하세요:
- "<종목명> 오늘 뉴스" 검색
- "<종목명> site:kr.investing.com OR site:finance.naver.com" 검색
