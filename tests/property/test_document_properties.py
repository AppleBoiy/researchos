"""Property-based tests for Document endpoints."""
import io

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st


VALID_FILE_TYPES = ["pdf", "latex", "dataset", "other"]

# Strategies
file_content_st = st.binary(min_size=0, max_size=10_000)
title_st = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
    min_size=1,
    max_size=100,
).map(str.strip).filter(lambda s: len(s) > 0)
file_type_st = st.sampled_from(VALID_FILE_TYPES)
description_st = st.one_of(st.none(), st.text(max_size=200))
category_st = st.one_of(st.none(), st.text(max_size=50))


# Feature: research-os, Property 4: Document creation round-trip with file size
@given(
    file_content=file_content_st,
    title=title_st,
    file_type=file_type_st,
    description=description_st,
    category=category_st,
)
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_document_creation_round_trip_file_size(
    app, client, auth_headers, tmp_path, file_content, title, file_type, description, category
):
    """Validates: Requirements 2.1, 2.5

    For any valid file and metadata combination, creating a document via
    POST /documents should return HTTP 201 with a Document ID, and the
    stored file_size should equal the actual byte size of the uploaded file.
    """
    app.config["STORAGE_PATH"] = str(tmp_path)

    data = {
        "title": title,
        "file_type": file_type,
        "file": (io.BytesIO(file_content), "test_file.bin"),
    }
    if description is not None:
        data["description"] = description
    if category is not None:
        data["category"] = category

    # POST /documents — should return 201
    post_resp = client.post(
        "/documents",
        data=data,
        content_type="multipart/form-data",
        headers={"Accept": "application/json", **auth_headers},
    )
    assert post_resp.status_code == 201, (
        f"Expected 201, got {post_resp.status_code}: {post_resp.get_json()}"
    )

    doc_id = post_resp.get_json()["id"]
    assert doc_id is not None

    # GET /documents/<id> — fetch stored metadata
    get_resp = client.get(
        f"/documents/{doc_id}",
        headers={"Accept": "application/json", **auth_headers},
    )
    assert get_resp.status_code == 200, (
        f"Expected 200, got {get_resp.status_code}: {get_resp.get_json()}"
    )

    doc_data = get_resp.get_json()
    assert doc_data["file_size"] == len(file_content), (
        f"file_size mismatch: stored={doc_data['file_size']}, actual={len(file_content)}"
    )
