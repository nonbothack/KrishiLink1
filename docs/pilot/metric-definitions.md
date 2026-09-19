# Packet 16 metric definitions

All rates include an explicit denominator `n`; a missing denominator is not a result.

- **Task success:** participant completes the pre-registered task outcome without moderator coaching. A prompt/coached completion is reported separately.
- **Comprehension pass:** participant states the required facts in the task rubric (for price: amount, unit, market, report date and source, plus that it is reported information), without a leading question.
- **Time to first useful insight:** elapsed time from the first authenticated usable dashboard state to the first correct statement of one relevant crop, price, unit and source/date. Report median and range by role/segment; do not count a loading placeholder.
- **Listing success:** server-persisted lot with canonical quantity/unit and review confirmation, or an explicitly labelled offline draft when the task is the offline task. It is not a click count.
- **Meaningful actions:** deliberate participant actions from task start to publish; typing, crop choice, review and confirmation each count when required. “Three taps” is reported only if the recorded distribution supports it.
- **Buyer fill:** accepted/allocated requirement quantity divided by requested quantity, only from persisted test transactions and with units compatible. Do not infer from intent or page views.
- **FPO throughput:** stage-specific elapsed time and successful reconciliation from intake to pool to published lot to trade trace. Never reduce this to an unqualified single score.
- **Assistance rate:** sessions/tasks with PROMPT or COACHED assistance divided by attempted tasks; moderator assistance is not silently counted as success.
- **Issue frequency:** number of sessions with a coded issue divided by sessions attempting the task, with severity and segment shown.
- **Privacy/security failure:** any cross-account exposure, unauthorized action or fabricated financial/price claim is P0/P1 regardless of task completion.
- **Median:** calculate only over valid numeric observations, with count and missingness shown.

Do not publish statistical significance, population generalization, causal uplift, satisfaction claims or “representative farmers” language from a small convenience panel. Unknown remains unknown.

