import uuid
from pathlib import Path

from app.models import Crop, DataSourceRegistry, District, Market, State, Subdistrict
from app.modules.crops.service import create_unclassified_crop, resolve_crop
from app.modules.markets.import_apmc import in_india_bounds, ingest_apmc_csv


def test_unknown_geography_stays_unknown_and_exact_lgd_hierarchy_resolves(client, db_session):
    unknown = client.get("/api/v1/geo/resolve", params={"state": "No Such State", "district": "Nowhere"})
    assert unknown.status_code == 200
    assert unknown.json()["data"] == {
        "resolved": False,
        "state": None,
        "district": None,
        "subdistrict": None,
        "confidence": 0.0,
        "provenance": "unresolved",
    }

    suffix = uuid.uuid4().hex[:8]
    state = State(lgd_code=f"S-{suffix}", name=f"Test State {suffix}", source_ref="lgd:test")
    db_session.add(state)
    db_session.flush()
    district = District(
        state_id=state.id, lgd_code=f"D-{suffix}", name=f"Test District {suffix}", source_ref="lgd:test"
    )
    db_session.add(district)
    db_session.flush()
    subdistrict = Subdistrict(
        district_id=district.id, lgd_code=f"T-{suffix}", name=f"Test Taluka {suffix}", source_ref="lgd:test"
    )
    db_session.add(subdistrict)
    db_session.commit()

    resolved = client.get(
        "/api/v1/geo/resolve",
        params={"state": state.name, "district": district.name, "subdistrict": subdistrict.name},
    ).json()["data"]
    assert resolved["resolved"] is True
    assert resolved["state"]["lgd_code"] == state.lgd_code
    assert resolved["district"]["lgd_code"] == district.lgd_code
    assert resolved["subdistrict"]["lgd_code"] == subdistrict.lgd_code
    assert resolved["confidence"] == 1.0
    assert resolved["provenance"] == "lgd"


def test_crop_registry_exposes_multilingual_fields_and_aliases(client, db_session):
    crop = db_session.query(Crop).filter(Crop.name == "Onion").first()
    crop.aliases = ["Pyaaz", "Kanda"]
    crop.name_hindi = crop.name_hindi or "प्याज़"
    crop.name_marathi = crop.name_marathi or "कांदा"
    db_session.commit()

    resolved = client.get("/api/v1/crops/resolve/Pyaaz")
    assert resolved.status_code == 200
    assert resolved.json()["data"]["id"] == str(crop.id)
    assert resolved.json()["data"]["name_hindi"]
    assert resolved.json()["data"]["name_marathi"]
    assert "quintal" in resolved.json()["data"]["valid_units"]
    assert resolved.json()["data"]["is_tradable"] is True


def test_unknown_price_commodity_is_retained_but_not_publicly_tradable(db_session, client):
    name = f"Unclassified {uuid.uuid4().hex[:8]}"
    crop = create_unclassified_crop(db_session, name)
    db_session.commit()
    assert resolve_crop(db_session, name) is not None
    assert crop.is_active is False
    assert crop.is_tradable is False
    listed = client.get("/api/v1/crops").json()["data"]["items"]
    assert all(item["name"] != name for item in listed)
    assert client.get(f"/api/v1/crops/{crop.id}").status_code == 404


def test_apmc_import_requires_approved_source_and_is_idempotent(tmp_path: Path, db_session):
    suffix = uuid.uuid4().hex[:8]
    path = tmp_path / "markets.csv"
    path.write_text(
        "market_name,district,state,apmc_code,latitude,longitude,outlet_type\n"
        f"Example Yard {suffix},Example District,Example State,APMC-{suffix},19.1,73.1,apmc_principal\n"
        f"Example Yard {suffix},Example District,Example State,APMC-{suffix}-DUP,19.1,73.1,apmc_principal\n"
        f"Outside {suffix},Example District,Example State,APMC-OUT-{suffix},50,120,apmc_sub\n",
        encoding="utf-8",
    )
    source = DataSourceRegistry(
        source_key=f"test-apmc-{suffix}", name="Approved test source", license_status="approved",
        license_name="Test license", parser_version="test-v1", is_active=True,
    )
    db_session.add(source)
    db_session.commit()

    report = ingest_apmc_csv(db_session, path, source.source_key)
    assert report["fetched"] == 3
    assert report["inserted"] == 2
    assert report["review"] == 2
    imported = db_session.query(Market).filter_by(source_registry_id=source.id).all()
    assert all(row.coordinate_confidence is None and row.source_confidence is None for row in imported)
    state = State(lgd_code=f"S-{suffix}", name=f"Test State {suffix}", source_ref="lgd:test")
    db_session.add(state)
    db_session.flush()
    district = District(
        state_id=state.id, lgd_code=f"D-{suffix}", name="Example District", source_ref="lgd:test"
    )
    db_session.add(district)
    db_session.commit()
    mismatched = tmp_path / "mismatched.csv"
    mismatched.write_text(
        "market_name,district,state,apmc_code,state_lgd_code,district_lgd_code\n"
        f"Wrong Label,Example District,Other State,APMC-X,{state.lgd_code},{district.lgd_code}\n",
        encoding="utf-8",
    )
    mismatch_report = ingest_apmc_csv(db_session, mismatched, source.source_key)
    assert mismatch_report["rejected"] == 1
    assert "does not match" in mismatch_report["issues"][0]["reason"]
    assert report["rejected"] == 1
    first = ingest_apmc_csv(db_session, path, source.source_key)
    assert first["inserted"] == 0
    assert first["duplicates"] == 2
    candidates = db_session.query(Market).filter(Market.source_registry_id == source.id).all()
    assert len(candidates) == 2
    assert all(item.verification_status == "needs_review" and not item.is_active for item in candidates)


def test_apmc_import_refuses_unknown_license_and_invalid_encoding(tmp_path: Path, db_session):
    suffix = uuid.uuid4().hex[:8]
    source = DataSourceRegistry(
        source_key=f"unknown-license-{suffix}", name="Unknown terms", license_status="unknown",
        parser_version="test-v1", is_active=True,
    )
    db_session.add(source)
    db_session.commit()
    path = tmp_path / "unknown.csv"
    path.write_text("name,district,state\nTest,Test,Test\n", encoding="utf-8")
    try:
        ingest_apmc_csv(db_session, path, source.source_key)
        raise AssertionError("unapproved source unexpectedly imported")
    except ValueError as exc:
        assert "not approved" in str(exc)

    approved = DataSourceRegistry(
        source_key=f"approved-encoding-{suffix}", name="Encoding test", license_status="approved",
        license_name="Test license", parser_version="test-v1", is_active=True,
    )
    db_session.add(approved)
    db_session.commit()
    invalid_path = tmp_path / "broken.csv"
    invalid_path.write_bytes(b"\xff\xfe\x80")
    try:
        ingest_apmc_csv(db_session, invalid_path, approved.source_key)
        raise AssertionError("invalid encoding unexpectedly imported")
    except ValueError as exc:
        assert "encoding" in str(exc)

    assert in_india_bounds(19.1, 73.1)
    assert not in_india_bounds(50, 120)


def test_market_list_hides_candidates_and_nearby_distance_uses_only_verified_coordinates(client, db_session):
    suffix = uuid.uuid4().hex[:8]
    source = DataSourceRegistry(
        source_key=f"verified-source-{suffix}", name="Verified source", license_status="approved",
        license_name="Open dataset license", parser_version="test-v1", is_active=True,
    )
    db_session.add(source)
    candidate = Market(
        name=f"Candidate {suffix}", district="Nashik", state="Maharashtra", outlet_type="apmc_principal",
        verification_status="needs_review", is_active=False,
    )
    nearby = Market(
        name=f"Reviewed {suffix}", district="Nashik", state="Maharashtra", latitude=19.9975, longitude=73.7898,
        outlet_type="apmc_principal", verification_status="verified", is_active=True,
        coordinate_source="manual_review", coordinate_confidence=0.95, source_confidence=0.95,
    )
    far = Market(
        name=f"Far {suffix}", district="Pune", state="Maharashtra", latitude=18.52, longitude=73.85,
        outlet_type="apmc_principal", verification_status="verified", is_active=True,
        coordinate_source="manual_review", coordinate_confidence=0.95, source_confidence=0.95,
    )
    db_session.add_all([candidate, nearby, far])
    db_session.commit()

    public = client.get("/api/v1/markets", params={"search": suffix}).json()["data"]["items"]
    assert {row["name"] for row in public} == {nearby.name, far.name}
    nearby_result = client.get(
        "/api/v1/markets", params={"search": suffix, "near_lat": 19.9975, "near_lng": 73.7898, "radius_km": 5}
    ).json()["data"]["items"]
    assert [row["name"] for row in nearby_result] == [nearby.name]
    assert nearby_result[0]["distance_km"] == 0
    assert client.get("/api/v1/markets", params={"near_lat": 19.9}).status_code == 422


def test_outlet_review_queue_is_role_gated_and_verification_requires_evidence(
    client, db_session, admin_auth_headers, auth_headers
):
    suffix = uuid.uuid4().hex[:8]
    candidate = Market(
        name=f"Review candidate {suffix}", district="Unknown district", state="Unknown state",
        outlet_type="apmc_principal", verification_status="needs_review", is_active=False,
        latitude=19.1, longitude=73.1, coordinate_source="dataset_import", coordinate_confidence=0.65,
    )
    db_session.add(candidate)
    db_session.commit()
    assert client.get("/api/v1/markets/review", headers=auth_headers).status_code == 403
    queued = client.get("/api/v1/markets/review", headers=admin_auth_headers)
    assert queued.status_code == 200
    assert any(row["id"] == str(candidate.id) for row in queued.json()["data"]["items"])
    response = client.post(
        f"/api/v1/markets/{candidate.id}/review",
        headers=admin_auth_headers,
        json={
            "status": "verified", "verification_method": "reviewed source row", "outlet_type": "apmc_principal",
            "coordinate_source": "manual_review", "coordinate_confidence": 0.95, "source_confidence": 0.95,
        },
    )
    assert response.status_code == 409
