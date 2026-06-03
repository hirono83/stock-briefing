#!/bin/bash
# 주식 브리핑 실행 스크립트 (launchd에서 호출)

set -e

SCRIPT_DIR="/Users/kwanz/Desktop/KwanZ's Data/stock_briefing"
LOG_FILE="$SCRIPT_DIR/briefing.log"
PYTHON="/opt/anaconda3/bin/python3"
CLAUDE="/Users/kwanz/.local/bin/claude"

echo "=============================" >> "$LOG_FILE"
echo "실행 시각: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

cd "$SCRIPT_DIR"

# 1. 주가 + 뉴스 수집 + 브리핑 생성
echo "[1/2] 브리핑 생성 중..." >> "$LOG_FILE"
"$PYTHON" main.py >> "$LOG_FILE" 2>&1

# 전송 프롬프트 생성
"$PYTHON" generate_send_prompt.py >> "$LOG_FILE" 2>&1

# 2. Claude CLI로 전송 (MCP 툴 사용)
echo "[2/2] 카카오톡·Gmail 전송 중..." >> "$LOG_FILE"
"$CLAUDE" -p "$(cat "$SCRIPT_DIR/send_prompt.txt")" \
  --allowedTools "mcp__555c64ad-0415-4b55-a9cf-6294a41b4edf__KakaotalkChat-MemoChat,mcp__88c64956-5a26-4e25-8172-58dd014093cd__create_draft" \
  --output-format text \
  >> "$LOG_FILE" 2>&1

echo "완료: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
