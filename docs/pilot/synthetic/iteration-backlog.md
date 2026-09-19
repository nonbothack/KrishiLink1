# Synthetic iteration backlog

No product fixes were made in Packet 16S because the strongest findings were caused by the test deployment and unsupported origin, and the prompt requires baseline evidence before fixes. The first follow-up is a staging harness correction, not a change to origin security or price truth rules.

| Priority | Item | Decision | Owner/input needed |
|---|---|---|---|
| P1 | Provide a supported staging origin with API proxy and deterministic seeded price/no-price fixtures | TEST_MORE | engineering/test environment |
| P1 | Re-run authenticated Farmer → Sell with a supported origin and isolated fixture account | TEST_MORE | engineering + QA |
| P2 | Validate source/date/unit and non-guarantee wording with real farmers, buyers, and FPO operators | REAL_USER_VALIDATION | named research moderator |
| P2 | Test offline and payment state vocabulary with real users and accessibility review | REAL_USER_VALIDATION | pilot panel |
| P2 | Investigate home-versus-`/prices` fixture mismatch and repeat the exact task | TEST_MORE | frontend/data integration |
| P2 | Preserve selected crop through authenticated Sell navigation and repeat the exact task | TEST_MORE | frontend/auth navigation |

Stop rules remain: any credible synthetic P0/P1 about privacy, authorization, data loss, or false financial/provider truth blocks acceptance until fixed and rerun. Synthetic evidence never replaces paid, consented sessions.
