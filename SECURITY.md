# 보안 정책 — us_trading_bot

이 저장소는 실거래 API 키와 계좌 정보를 다룹니다. 보안 제보를 환영합니다.

---

## 📣 취약점 제보

### 채널 (비공개)

- **GitHub Security Advisory**: [Report a vulnerability](https://github.com/blockcoder-sj/us_trading_bot/security/advisories/new) (권장)
- 저장소 소유자에게 GitHub DM · 멘션

**공개 이슈로 올리지 말 것** — 실자금 손실로 이어질 수 있습니다.

### 제보에 포함해 주세요

1. 취약점 개요 (파일·함수·조건)
2. 재현 절차 (최소 PoC)
3. 영향도 (API 키 유출 · 주문 조작 · PIT 검증 우회 · 캐시 변조 등)
4. 제안 완화책 (선택)

---

## 🎯 스코프

### In Scope
- API 키 저장·전송·로깅 경로 (KIS, Finnhub, Telegram)
- 주문 체결·검증 로직 (Mom20d / Rev20d · SELL→BUY 순서 · 스톱 로직)
- `.env` · macOS Keychain (`keychain.py`) 접근 경로
- FULL_MVC 방어 매트릭스 (17건) 우회 가능성
- 데이터 파이프라인 (`data_cache/`, `market_calendar.py`, `spike_analysis.py` 파서)
- 텔레그램 원격 명령 (`/rebalance` 등) 권한 우회

### Out of Scope
- 사용자 실수로 `.env` · 토큰을 커밋한 경우 (Git history 정리는 본인 책임)
- KIS · yfinance · Finnhub · NASDAQ 공급자 측 취약점
- 백테스트 수치가 실전과 다르다는 사실 (구조적 한계)
- launchd / cron / watchdog 스크립트의 OS 계층 이슈 — macOS TCC 가이드는 `OPERATIONS.md`

### 클라우드 페이퍼 플랫폼

- AI가 만든 Python/shell 코드는 실행하지 않는다. `cloud_app.strategies.StrategySpec`의
  허용 목록 JSON만 저장하고 공통 엔진으로 컴파일한다.
- production은 PostgreSQL, 32자 이상 session secret, HTTPS URL, 명시적 host 목록,
  8자 이상 초대 코드가 없으면 시작하지 않는다.
- 브라우저 세션은 HttpOnly/SameSite=Strict/Secure cookie와 CSRF header를 함께 검증한다.
- KIS 시세 공유는 `MARKET_DATA_SHARING_ALLOWED=true`가 없으면 시작하지 않는다.
- PostgreSQL, worker, AI endpoint는 Docker 내부망에만 두고 Caddy 80/443만 공개한다.
- 페이퍼 체결은 `dedupe_key` unique constraint와 worker lease로 재시작/중복 worker에
  의한 이중 체결을 막는다.

---

## 🔐 권장 운영 보안

- **macOS Keychain 필수** — `keychain.py` 경로 사용, `.env` 평문 저장 금지
- `.env` 는 `.gitignore` 포함 — **절대 커밋 금지**
- KIS API 키 유출 시 즉시 [KIS Developers](https://apiportal.koreainvestment.com) 에서 재발급
- Finnhub 키 유출 시 즉시 Finnhub 대시보드에서 revoke
- 텔레그램 봇 토큰 유출 시 [@BotFather](https://t.me/BotFather) 에서 revoke
- 실전 모드 전환 전 반드시 4주 이상 `paper_realtime` 검증

---

## ⏱️ 대응 목표

| 이벤트 | 목표 시간 |
|---|---|
| 초기 확인 | 7일 이내 |
| Critical 패치 | 30일 이내 |

---

## 🏅 크레딧

수정 커밋·릴리스 노트에 제보자 크레딧 게재 (동의 시). 금전 보상은 없습니다.

---

## 🔗 관련

- [OPERATIONS.md](OPERATIONS.md) — 운영 경로
- [FULL_MVC.md](FULL_MVC.md) — 17건 방어 매트릭스
- [KNOWN_ISSUES.md](KNOWN_ISSUES.md) — 알려진 이슈와 대응
- [CONTRIBUTING.md](CONTRIBUTING.md) — 커밋·브랜치 규칙
