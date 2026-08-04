#!/usr/bin/env python3
"""
Gmail SMTP로 브리핑 메일을 직접 발송합니다.
필요 환경변수:
  GMAIL_APP_PASSWORD  - Gmail 앱 비밀번호 (16자리)
  GMAIL_FROM          - 발신 주소 (기본값: CLAUDE_CODE_USER_EMAIL)
"""

import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date


def send_briefing_email(subject: str, body: str, to: str = None) -> bool:
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    from_addr = os.environ.get("GMAIL_FROM") or os.environ.get("CLAUDE_CODE_USER_EMAIL", "")
    to_addr = to or from_addr  # 기본: 자신에게 발송

    if not app_password:
        print("❌ GMAIL_APP_PASSWORD 환경변수가 설정되지 않았습니다.")
        print("   설정 방법: Claude Code 환경변수에 GMAIL_APP_PASSWORD 추가")
        return False

    if not from_addr:
        print("❌ 발신 주소를 확인할 수 없습니다.")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(from_addr, app_password)
            server.sendmail(from_addr, to_addr, msg.as_string())
        print(f"✅ 메일 발송 완료: {to_addr}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ Gmail 인증 실패. 앱 비밀번호를 확인하세요.")
        print("   https://myaccount.google.com/apppasswords")
        return False
    except Exception as e:
        print(f"❌ 메일 발송 실패: {e}")
        return False


if __name__ == "__main__":
    # 테스트 발송
    today = date.today().strftime("%Y년 %m월 %d일")
    ok = send_briefing_email(
        subject=f"[테스트] 주식 브리핑 발송 확인 - {today}",
        body=f"이 메일은 주식 브리핑 자동 발송 테스트입니다.\n날짜: {today}\n\n정상적으로 수신되면 자동 발송이 설정된 것입니다.",
    )
    sys.exit(0 if ok else 1)
