"""Tests for the review server routes (no browser, no threading)."""

import threading

import pytest
from fastapi.testclient import TestClient

from ankirai.models import Card
from ankirai.review.server import ReviewState, app


def _make_cards(n: int = 3) -> list[Card]:
    return [
        Card(front=f"Q{i}", back=f"A{i}", tags=[], source_file="test.md", source_chunk=i)
        for i in range(n)
    ]


def _setup(cards: list[Card] | None = None) -> ReviewState:
    cards = cards or _make_cards()
    state = ReviewState(cards=cards, statuses=["pending"] * len(cards))
    app.state.review = state
    return state


@pytest.fixture
def client():
    return TestClient(app, follow_redirects=True)


# ── Route tests ─────────────────────────────────────────────────────────────

def test_accept_marks_card_accepted(client):
    state = _setup()
    client.post("/accept/0")
    assert state.statuses[0] == "accepted"


def test_reject_marks_card_rejected(client):
    state = _setup()
    client.post("/reject/0")
    assert state.statuses[0] == "rejected"


def test_edit_updates_card_and_accepts(client):
    state = _setup()
    client.post("/edit/0", data={"front": "New front", "back": "New back"})
    assert state.cards[0].front == "New front"
    assert state.cards[0].back == "New back"
    assert state.statuses[0] == "accepted"


def test_bulk_accept_all(client):
    state = _setup(_make_cards(4))
    state.statuses[1] = "rejected"  # one already rejected — should stay rejected
    client.post("/bulk/accept-all")
    assert state.statuses[0] == "accepted"
    assert state.statuses[1] == "rejected"  # unchanged
    assert state.statuses[2] == "accepted"
    assert state.statuses[3] == "accepted"


def test_export_sets_done_event(client):
    state = _setup()
    state.statuses[0] = "accepted"
    client.post("/export")
    assert state.done.is_set()


def test_bulk_toggle_accept_to_reject(client):
    state = _setup()
    state.statuses[0] = "accepted"
    client.post("/bulk/toggle/0")
    assert state.statuses[0] == "rejected"


def test_bulk_toggle_rejected_to_accepted(client):
    state = _setup()
    state.statuses[0] = "rejected"
    client.post("/bulk/toggle/0")
    assert state.statuses[0] == "accepted"


def test_review_page_renders(client):
    _setup()
    resp = client.get("/review/0")
    assert resp.status_code == 200
    assert "Q0" in resp.text


def test_bulk_page_renders(client):
    _setup()
    resp = client.get("/bulk")
    assert resp.status_code == 200
    assert "All cards" in resp.text
