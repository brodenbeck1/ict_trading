---
name: nwog-ndog
aliases: [NWOG, NDOG, new week opening gap, new day opening gap]
category: pd-arrays
related: [consequent-encroachment, volume-imbalance, true-day-midnight-open]
parameters:
  ndog_window: "5:00 PM close -> 6:00 PM open NY time, Mon-Thu (futures maintenance break)"
  nwog_window: "Friday 5:00 PM close -> Sunday 6:00 PM open NY time"
  keep_last_n_nwogs: 5
detection: not-implemented
---

# New Week / New Day Opening Gap (NWOG / NDOG)

True gaps created by the futures market's closure windows — prices where **no trade at
all** occurred:

- **NDOG**: gap between the 5:00 PM NY close and 6:00 PM NY reopen (Mon–Thu daily
  maintenance hour).
- **NWOG**: gap between Friday's 5:00 PM close and Sunday's 6:00 PM reopen — the
  weekend gap, the strongest of the family.

Both act as institutional reference zones: price is repeatedly drawn back to trade
through them ("rebalance"), and reacts at their edges and especially at the 50% line
([consequent encroachment](consequent-encroachment.md)). ICT convention keeps the
**last 5 NWOGs** on the chart as live reference levels; they remain reactive even after
being filled.

In UTC (project data): 5 PM NY = 21:00/22:00 UTC depending on DST; reopen 22:00/23:00 UTC.

## Detection Rules

- NDOG: `gap = open(sunday_or_weekday_reopen) - close(prior_5pm_close)`; zone =
  (min, max) of the two prices; CE = midpoint.
- Detect from data by the timestamp discontinuity at the maintenance window rather
  than hardcoded clock times (robust to DST).
- Keep a rolling registry: last 5 NWOGs + current week's NDOGs; emit touch/CE-touch
  events for confluence scoring.

## Sources

- [ICT NDOG — innercircletrader.net](https://innercircletrader.net/tutorials/ict-new-day-opening-gap-ndog/)
- [ICT NWOG — innercircletrader.net](https://innercircletrader.net/tutorials/ict-new-week-opening-gap-nwog/)
- [NWOG & NDOG for trading — investingbrokers.com](https://investingbrokers.com/ict-new-week-opening-gap-nwog-and-new-day-opening-gap-ndog-for-trading/)
- [NDOG usage — tradingfinder.com](https://tradingfinder.com/education/forex/ict-new-day-opening-gap/)
