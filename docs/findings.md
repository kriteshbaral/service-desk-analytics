# Service Desk Performance Review: Findings and Recommendations

**Organisation:** Harbourline Regional Services (fictional)
**Period:** October 2025 to September 2026
**Prepared by:** Kritesh Baral
**Audience:** IT Service Manager

## Summary

The service desk handled **4,752 tickets** in 12 months. Overall it performs reasonably: **88.2%** of tickets were resolved within SLA (goal 90%) and **94.4%** received a first response in time (goal 95%). Average satisfaction is **4.05 out of 5**.

The averages hide three problems: **hardware repairs at remote sites**, **new starter setup**, and **a large volume of password resets** that a self-service tool could remove. Fixing these would lift SLA performance above target and free about a quarter of the desk's ticket load.

## 1. Password and account resets are 23% of all tickets

- 1,090 tickets were password resets, account lockouts or MFA resets.
- 764 of them (70%) came in by phone, which ties up an L1 analyst each time.
- They are quick to fix (under an hour on average), but the volume is large.

**Recommendation:** Roll out self-service password reset (for example Microsoft Entra SSPR) and promote it on the lock screen and intranet. Even a 60% take-up would remove around 650 tickets a year.

## 2. Remote sites wait much longer for hardware fixes

| Site | Hardware tickets | Average resolution | SLA met |
|---|---|---|---|
| Alice Springs | 110 | 60.2 h | 28.4% |
| Katherine | 132 | 52.7 h | 33.1% |
| Palmerston | 192 | 31.2 h | 56.4% |
| Darwin CBD | 375 | 30.3 h | 66.7% |

Hardware is the biggest SLA problem overall (53.6% met), and it is worst where a technician has to travel.

**Recommendation:** Keep a small pool of pre-built spare laptops and docks at Katherine and Alice Springs so a faulty device can be swapped the same day, with repairs done afterwards.

## 3. Onboarding misses its target two times out of three

- 166 new starter and leaver tickets; only **33.3%** met the 24-hour target.
- Average time to complete: **47.4 hours**.

**Recommendation:** Require managers to log new starters at least five business days before the start date, and script the account and device setup (for example with PowerShell and Intune) so it is the same every time.

## 4. Printing faults in Katherine keep coming back

- 13 of 66 printing tickets in Katherine (**19.7%**) were re-opened, four times the desk average of 4.6%.
- Network and Wi-Fi tickets also re-open more often (7.1%), especially in Palmerston.

**Recommendation:** Raise an ITIL problem record for the Katherine printers to find the root cause (device age, driver, or network) instead of fixing each incident on its own.

## 5. Monday demand is about 70% higher than Friday

- Monday averages 24.5 tickets a day; Friday averages 14.5.
- First response is slowest on Monday (99 minutes on average).
- February is the busiest month (494 tickets), driven by new starters.

**Recommendation:** Move non-urgent admin and project time off Mondays and plan extra cover in February.

## Why this matters

Satisfaction drops sharply when SLAs are missed: **4.20** when the SLA is met against **2.83** when it is breached. Each fix above improves both performance and how staff feel about IT.

## Method

1. Ticket data loaded into SQLite (`sql/schema.sql`), with a view that calculates resolution hours, response minutes and SLA results.
2. Eleven SQL queries (`sql/analysis.sql`) produce the figures in this report.
3. Headline figures were cross-checked with an independent calculation in pandas.
4. Data is synthetic and generated with a fixed seed, so results can be reproduced exactly.
