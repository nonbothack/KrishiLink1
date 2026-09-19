import json
from pathlib import Path

from app.modules.fpo.router import _csv_safe


ROOT = Path(__file__).resolve().parents[2]


def test_fpo_export_csv_escapes_formula_values():
    for value in ("=SUM(A1)", "+123", "-123", "@cmd"):
        assert _csv_safe(value).startswith("'")
    assert _csv_safe("ordinary") == "ordinary"


def test_readiness_manifest_has_evidence_and_no_certification_claim():
    manifest = json.loads((ROOT / "docs/readiness/readiness-manifest.json").read_text(encoding="utf-8"))
    assert manifest["certification_claim"] is False
    for control in manifest["controls"]:
        evidence = ROOT / control["evidence"]
        assert evidence.exists(), control["id"]
        if control["status"] == "IMPLEMENTED_AND_TESTED":
            assert evidence.is_file()


def test_export_route_is_owner_scoped_and_not_admin_public_surface():
    source = (ROOT / "backend/app/modules/fpo/router.py").read_text(encoding="utf-8")
    assert 'user: User = Depends(require_role("fpo"))' in source
    assert 'pattern="^(json|csv)$"' in source
    assert "CSV export requires one domain" in source


def test_fpo_export_endpoint_returns_manifest_and_denies_buyer(client, fpo_auth_headers, buyer_auth_headers):
    response = client.get("/api/v1/fpo/export", headers=fpo_auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["manifest"]["secrets_included"] is False
    assert payload["manifest"]["owner_scope"]["fpo_id"]
    assert client.get("/api/v1/fpo/export", headers=buyer_auth_headers).status_code == 403
