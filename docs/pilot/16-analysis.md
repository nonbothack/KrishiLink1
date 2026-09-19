# Packet 16 analysis protocol

The analysis is intentionally conservative. `scripts/analyze_pilot_sessions.py` accepts only anonymized records matching `data/session-schema.json`, calculates descriptive task outcomes/timings/assistance/comprehension and reports denominators. It does not invent participants, fill missing values, infer adoption or calculate causal price realization.

With an absent, empty or invalid export it returns `NO PILOT DATA` (and a non-zero exit for operational visibility). A valid export returns `ANALYZED` and includes participant/task counts plus segment caveats. Any claim must be traceable to session IDs and the pre-registered metric definitions.

No analysis was run on real sessions in Packet 16 because none were supplied.

