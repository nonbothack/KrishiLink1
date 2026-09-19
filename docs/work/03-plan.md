# Work Packet 03 — Geography, Outlet Provenance and Crop Registry Plan

**Branch:** `abdulrehman`  
**Baseline:** Packets 00, 00A, 01, and 02; backend regression target 125 passing tests, existing frontend build/tests retained.  
**Scope:** Packet 03 only. No redesign or Packet 04 work; no commits or pushes.

## Verified starting state

- `backend/app/models.py` already has `User.state` (non-null with a Maharashtra default), free-text `district`/`location`, nullable user geography, `Crop`, `CropVariety`, `Market` with nullable coordinates and PostGIS geography, and price observations tied to `Market` and `Crop`.
- `backend/app/modules/markets/import_apmc.py` does not parse the repository APMC file. It contains a hardcoded 38-entry coordinate dictionary across Maharashtra and Karnataka and writes those coordinates as though verified. Its geocoder functions use Nominatim but do not attach provenance/confidence.
- The file `List_Of_APMC.csv` begins with bytes that do not decode as UTF-8; the purported CSV has no verified publisher/license metadata in the repository. It is not safe to import or publish from the current artifact.
- `backend/app/modules/prices/sync_service.py` and `import_mandi.py` dynamically create crops and market rows from price feed labels without canonical aliases or outlet verification metadata.
- The crop API is read-only and returns only name/category/unit. The frontend still owns `CROPS` in `frontend/src/lib/produce.js`; `RateLookup.jsx` consumes it, while Sell/FPO forms already load `/api/v1/crops`.
- The public market list/map currently includes active rows without provenance/verification checks. Existing PostGIS `ST_DWithin` is used for filtering, then application Haversine calculates displayed distance for any row with coordinates. SQLite has a bounding-box approximation.
- No authoritative LGD state/district/subdistrict data or license-cleared national outlet data is present. Existing tests use SQLite; PostGIS runtime availability was previously reported as unavailable.

## Intended implementation

1. Add geography hierarchy tables (`states`, `districts`, `subdistricts`) and nullable structured location references on users and markets. Do not seed identifiers or administrative labels without an authoritative source snapshot. Remove the implicit Maharashtra user default; unknown remains unknown.
2. Extend the existing `Market` table as the canonical outlet record to preserve current price-observation foreign keys and compatibility. Add stable source registry and per-outlet source reference, type, coordinate provenance/confidence, verification/review states, normalized name and administrative references. Existing market rows are retained and moved into `needs_review`; no existing row or price observation is deleted.
3. Add a repeatable CSV ingestion function/CLI that requires declared source identity, license/terms, parser version and expected columns. It records valid rows without coordinates as review candidates; validates bounds and names; uses source identity/normalized administrative identity for deterministic matching; never fuzzy-merges; and emits row-level reject/review results. Do not run it on the unverified current CSV.
4. Add public geography hierarchy reads, verified-only outlet lookup/nearby search, and a role-protected outlet review queue/action. Nearby distances use PostGIS geography distance in PostgreSQL and are only emitted for sufficiently confident verified coordinates. An insufficient location returns an explicit unavailable result; no fallback points/distances.
5. Extend the existing crop registry with slug, aliases, valid/default units, multilingual names, AGMARKNET mapping and active/tradable flags. Backfill existing names without deleting crops or remapping historical foreign keys. Unknown ingested commodities are retained as inactive/non-tradable registry entries rather than published crops. The frontend crop selector reads `/api/v1/crops`; retain `UNIT_FACTORS` as presentation/conversion constants.
6. Add targeted backend and frontend tests for hierarchy, unknown location, provenance, verification, deterministic dedupe/review, distance confidence, crop aliases/locales/API, and frontend registry ownership. Add a reversible Alembic migration; validate it on PostgreSQL/PostGIS when available and at least test revision graph/SQLite compatibility locally.
7. Record the unusable dataset and source/license dependency. Registry coverage is reported from verified rows and never padded toward the master specification target.

## Expected files and data changes

- `backend/app/models.py`, new geography/outlet/crop service/schema modules as appropriate, markets/crops/auth routes and schemas, price ingestion normalization, APMC import script.
- New Alembic revision with additive tables/columns, safe backfill metadata, indexes/checks, and reversible downgrade; preserve all existing rows.
- Frontend crop API consumption and tests; no broad geography UI.
- `docs/DECISIONS.md`, `docs/work/03-plan.md`, `docs/work/03-result.md`, `PROGRESS_TRACKER.md`.

No live rows will be imported from an unverified source. If production migration or PostGIS runtime cannot be exercised in this environment, that limitation will be explicit in the completion status.
