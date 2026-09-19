# KrishiLink 4.0 — Astra 6 Work Packet 14: Government/enterprise readiness

> **Source of truth:** `KrishiLink_4.0_Multi_Stakeholder_Production_Procurement_Master_Astra6.md`. Do not treat this packet as permission to override the master specification. Read the sections explicitly referenced below from the master before coding.

# PART 20A — ASTRA 6 MODULAR EXECUTION CONTRACT

> Do NOT paste the entire master specification into a coding loop and tell the agent to “build everything.” The master specification is the source of truth; execution happens through bounded work packets below.

## 20A.1 Rules for every Astra work packet

For each packet Astra must:

1. read the master sections explicitly referenced by that packet;
2. inspect existing implementation before proposing replacement;
3. write `docs/work/<packet-id>-plan.md` with current state, intended changes, files/tables/endpoints affected, migration risk and tests;
4. make the smallest coherent implementation that satisfies the packet;
5. run the packet's tests plus impacted regression tests;
6. write `docs/work/<packet-id>-result.md` with commands/results, unresolved issues, screenshots/evidence where useful and exact next dependencies;
7. create a clean git checkpoint/commit if the environment allows;
8. STOP the packet if a blocker requires external credentials/legal approval/data rather than inventing success;
9. never silently expand scope into a later packet;
10. never rewrite a working subsystem solely for style.

### Required completion status

Every packet ends in exactly one of:

- `PASS` — acceptance criteria evidenced;
- `PASS_WITH_EXTERNAL_DEPENDENCY` — software/interface complete, activation waits on named external dependency;
- `BLOCKED` — cannot safely continue; document exact blocker;
- `FAIL` — implementation attempted but acceptance criteria not met; revert or isolate before next packet.

Only `PASS` and explicitly approved `PASS_WITH_EXTERNAL_DEPENDENCY` advance.

---

## 20A.16 Packet 14 — Government/enterprise readiness

**Read:** Part 19C and Tier 4.

Deliver compliance matrix, procurement pack, GIGW evidence, security-audit readiness, export/exit plan, department MIS, hosting/DR options, training/UAT materials and contract configuration boundaries. Do not claim certification before an external certifier issues it.

## Required final response from Astra 6

Return: status (`PASS` / `PASS_WITH_EXTERNAL_DEPENDENCY` / `BLOCKED` / `FAIL`), files changed, migrations/endpoints changed, commands/tests run and results, measurable acceptance evidence, known risks, external dependencies, rollback instructions, and the exact recommended next packet. Do not begin that next packet in the same run.
