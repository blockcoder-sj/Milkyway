# 미국장 하루 페이퍼 준비 및 후보 비교 · 2026-10-02

## 비교 방법

- 기존 8개 저장 전략에서 실행 설정 중복을 제외한 6개 후보. AI API 호출 0회.
- 최초 결과 확인 전에 전체 1년 샤프지수를 우선하고 하위 구간/낙폭을 확인하기로 정했다.
- 동일 기간 2025-10-01~2026-10-01, 초기자금 $100,000, 편도 비용 0.1%. 원본의 종목·위험설정은 유지했다.
- 편도 0.3%인 C2/C3만 비교용 복사본을 생성했다. 원본은 변경하지 않았다.
- 전반기 2025-10-01~2026-03-31, 후반기 2026-04-01~2026-10-01은 각각 현금에서 새로 시작한 독립 실행이다. 반기 수익률을 단순 연결하면 전체 1년 결과와 다를 수 있다.
- 총 18개 앱 백테스트 작업 완료. 데이터 fingerprint: `2b94e4422026c4eed80ffb00b19c3664c31ea7a5c58b9c9ca695e8f78ec9527b`.
- 선택 기준 및 전 기간을 이미 확인한 탐색이다. 후반기를 한 번도 보지 않은 최종 검증 구간으로 주장하지 않는다.

|후보|구성|투자비중|주기(달력일)|손절|1년 수익률|샤프|최대낙폭|전반기 수익률|후반기 수익률|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|C1|60일 모멘텀 Top 5|80%|7|-8%|+19.37%|0.862|-23.71%|-13.31%|+37.44%|
|C2|60일 모멘텀 Top 5|80%|7|-5%|+16.46%|0.768|-22.97%|-15.03%|+34.38%|
|C3|60일 모멘텀 Top 5|100%|30|-5%|+20.63%|0.853|-21.09%|-13.14%|+43.80%|
|C4|60일 모멘텀 + 20일 저변동성 Top 3|45%|10|-5%|+5.81%|0.655|-8.21%|-0.58%|+5.15%|
|C5|60일 모멘텀 + 20일 저변동성 Top 3|60%|7|-5%|+10.96%|0.874|-11.45%|-1.60%|+8.53%|
|C6|60일 모멘텀 + 20일 저변동성 Top 3|50%|10|-5%|+6.42%|0.655|-9.08%|-0.66%|+5.70%|

## 오늘의 후보

C5 `9ac37176f4bc4feea965f6f065957ad3` — Tech Momentum LowVol Top3. 전체 샤프가 가장 높고 C1/C3보다 낙폭이 작았다. C1과 샤프 차이는 약 0.012에 불과하여 통계적 우월성이나 향후 수익 보장은 아니다. 전반기 손실도 함께 공개한다.

- 유니버스: AAPL, MSFT, NVDA, AMZN, GOOGL, META.
- 60일 모멘텀 0.6 + 20일 저변동성 0.4; 상위 3개.
- $100,000 가상자금, 총 60% 투자, 3개 선택 시 각각 총자산의 20%, 현금 약 40% (체결비용 반영 시 달라짐).
- 최대 종목당 25%, 7달력일마다 동일비중 조정, 취득단가 대비 -5% 손절, 편도 비용 0.1%.
- 현재 일봉에 기반한 주간 전략이며 하루 단타 전략으로 바꾸지 않는다. 오늘 종가에 강제매도하지 않고 운용을 중지한다.

## 유니버스의 한계

현재 전략 가격 데이터는 사용자가 지금 선택한 총 11개 미국 종목의 Yahoo 일봉이다. 시장 백과의 대규모 기업 목록과 전략 백테스트 유니버스는 다르다. 과거 시점별 전체 상장·편입·퇴출 목록과 상장폐지 수익률을 갖춘 인증 PIT 자료가 없다. 모든 비교 결과는 `exploratory`, `certification_eligible=false`다.

최근 6~12개월로 좁히면 편입·퇴출 사건 수가 줄어들 가능성은 있지만, 현재 성공한 기업들을 선택한 편향은 남는다. 구간을 줄여 편향이 얼마나 줄었는지는 현재 자료로 측정할 수 없다. 표본 감소·특정 장세 집중도 커진다. 정식 검증에는 당시 구성 종목, 변경 이력, 안정적인 기업 식별자, 상장폐지/합병 처리, 기업행사와 해당 시점에 알 수 있었던 자료가 필요하다. 오늘부터 고정한 전략과 종목의 전진 페이퍼 기록은 앞으로의 검증 자료가 되지만 하루만으로 수익성을 판정할 수 없다.

근거: [QuantConnect Research Guide](https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/research-guide), [CRSP 미국 주식 데이터의 active/inactive 포함 범위](https://www.crsp.org/research__trashed/crsp-us-stock-databases/).

## 실행 계약

- NYSE 2026-10-02 정규장: 13:30~20:00 UTC = 한국시간 10월 2일 22:30~10월 3일 05:00. 첫 리밸런싱 허용은 개장 5분 뒤다. [NYSE 공식 일정](https://www.nyse.com/trade/hours-calendars).
- 지정 거래일의 개장 전/마감 이후 가상 매수·손절 체결을 차단한다. 마감 시 첫 worker tick에서 중지 상태와 마지막 확인 평가/체결 요약을 저장한다.
- 종료 처리를 데이터/시세 요청보다 먼저 별도 커밋한다. 종료 직전 시작한 요청이 늦게 끝나도 체결 직전에 시간을 재확인한다.
- PC 재시작·다음 거래일 복귀 시 이미 끝난 하루 계좌를 재개하지 않는다. 놓친 하루는 체결 0건으로 기록한다.
- 거래일/시간/요약은 로컬 SQLite의 personal_paper_sessions에 원장과 함께 보존한다. 계좌 생성과 일정은 같은 트랜잭션이다.
- 종료 시 강제청산, 가짜 종가, 백테스트 가격을 실제 시세처럼 사용하는 대체 체결은 없다. 마지막 완전한 평가의 실제 시각과 공식 종가 미확인을 표시한다.
- 연속 운용 계좌의 기존 동작은 유지한다. 지정 날짜는 오늘부터 7일 이내 거래일만 받으며 종료 계좌의 재개 요청은 거부한다.

## 실제 시세 사전 확인

2026-10-02 11:37 UTC, 기존 로컬 암호화 자격증명을 사용하는 시세 전용 provider에서 AAPL/MSFT/NVDA/AMZN/GOOGL/META 6개 시세를 5.855초에 수신했다. 공급자 시각 11:37:07~11:37:15 UTC. 이 확인은 장전 수신 확인이며 정규장 체결 성공으로 해석하지 않는다. 당일 기업행사 게이트는 개장 후 Yahoo 오늘 행 확인이 필요하며 기존 재시도/차단을 유지한다.

## 검증 및 배포

- Local full suite: 517 tests / 70.232s, OK (16 Node-dependent tests skipped in Python image). Host frontend/boundary suite: 18 tests / 12.038s, OK, including scheduled-account display and disabled resume.
- First full run: 516 tests / 92.398s, 1 existing provider warmup timeout (10-second deadline). Rebuilt with the final frontend regression; repeated with the same 1 CPU / 768 MiB limits while company-data and market-details were temporarily stopped: all passed. Both collectors were restored. This shows startup sensitivity under local concurrent load; no timing threshold was loosened or unconditional performance claim made.
- Direct code/security review: dates bounded and validated against exchange calendar, owner strategy/account checks and CSRF retained, local-only table, atomic account+schedule creation, expired resume denial, per-fill time guard, expiry durable before failing data I/O, UI escaping. No new dependencies, provider endpoints, credential storage, or real-order path.
- Tests cover DST/early close, invalid/holiday/expired dates, owner isolation, cloud rejection, rollback, early/late BUY and SELL, missed session/restart with zero fills, expiry despite later worker failure, immutable last-observed summary, unscheduled accounts. Python AST, node --check and git diff --check passed.
- Deployed runtime image: `sha256:097f64ade4b15072d52754d4f2293ceb8dceb9724bf0a635ed97bb6312d4927d`. All 8 services recreated with existing runtime/backup volumes retained.
- 11:44 UTC: created account `b1042a427dec4e1991be17f24f8becc8`, active and `market_closed`, zero positions/fills, $100,000 cash. Session stored: 2026-10-02 13:30–20:00 UTC. Actual day execution is still in the future, not completed.
- Today’s corporate-action gate remains pending before the opening print. The worker refreshes selected daily data every 60 seconds; missing/stale broker quotes or unverified corporate actions block fills and automatically retry. No bypass was introduced.
- Five live account reads after deploy: 25.275 / 19.296 / 12.818 / 116.611 / 58.249 ms (median 25.275 ms). Small local sample, not a load test.
- Bounded macOS idle-sleep inhibition via caffeinate until 2026-10-03 05:10 KST. This does not prevent a lid close, manual sleep, Docker shutdown, power loss or internet outage. The worker must be running for real-time fills; a late restart expires the session without backfilling fake trades.
- No additional AI calls, no real brokerage orders, no new permanent containers. Paid data not used. This is a focused local patch review, not a full public deployment security audit.
- Browser observation found the user working in unrelated Google Docs tabs; those tabs were left unchanged. Existing Node behavior tests verify the added account display. Open the local portfolio view to inspect the armed account.
- Git push / exact CI result: record after commit; do not substitute previous commit CI.
