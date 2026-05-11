"""
Review UI server — exposes run_review_server(cards) -> list[Card].
All FastAPI internals are contained here; the CLI treats this as a black box.
"""

from __future__ import annotations

import math
import threading
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path

import click
import uvicorn
from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..models import Card

_HERE = Path(__file__).parent
_TEMPLATES = Jinja2Templates(directory=str(_HERE / "templates"))

PAGE_SIZE = 50

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")


@dataclass
class ReviewState:
    cards: list[Card]
    statuses: list[str]  # "pending" | "accepted" | "rejected"
    done: threading.Event = field(default_factory=threading.Event)


def _next_pending(state: ReviewState, after: int) -> int | None:
    for i in range(after, len(state.statuses)):
        if state.statuses[i] == "pending":
            return i
    for i in range(0, after):
        if state.statuses[i] == "pending":
            return i
    return None


def _progress(state: ReviewState) -> dict:
    accepted = state.statuses.count("accepted")
    rejected = state.statuses.count("rejected")
    total = len(state.statuses)
    return {
        "accepted": accepted,
        "rejected": rejected,
        "total": total,
        "pending": total - accepted - rejected,
    }


# ── Routes ─────────────────────────────────────────────────────────────────


@app.get("/", response_class=RedirectResponse)
def root():
    return RedirectResponse("/review/0")


@app.get("/review/{index}", response_class=HTMLResponse)
def review_card(request: Request, index: int):
    state: ReviewState = app.state.review
    if index < 0 or index >= len(state.cards):
        return RedirectResponse("/bulk")
    progress = _progress(state)
    return _TEMPLATES.TemplateResponse(
        request,
        "review.html",
        {
            "card": state.cards[index],
            "index": index,
            "status": state.statuses[index],
            "total": len(state.cards),
            **progress,
        },
    )


@app.post("/accept/{index}", response_class=RedirectResponse)
def accept_card(index: int):
    state: ReviewState = app.state.review
    state.statuses[index] = "accepted"
    nxt = _next_pending(state, index + 1)
    return RedirectResponse(f"/review/{nxt}" if nxt is not None else "/bulk", status_code=303)


@app.post("/reject/{index}", response_class=RedirectResponse)
def reject_card(index: int):
    state: ReviewState = app.state.review
    state.statuses[index] = "rejected"
    nxt = _next_pending(state, index + 1)
    return RedirectResponse(f"/review/{nxt}" if nxt is not None else "/bulk", status_code=303)


@app.post("/edit/{index}", response_class=RedirectResponse)
def edit_card(index: int, front: str = Form(...), back: str = Form(...)):
    state: ReviewState = app.state.review
    state.cards[index].front = front
    state.cards[index].back = back
    state.statuses[index] = "accepted"
    nxt = _next_pending(state, index + 1)
    return RedirectResponse(f"/review/{nxt}" if nxt is not None else "/bulk", status_code=303)


@app.get("/bulk", response_class=HTMLResponse)
def bulk_view(request: Request, page: int = Query(0)):
    state: ReviewState = app.state.review
    progress = _progress(state)
    all_enumerated = list(enumerate(zip(state.cards, state.statuses)))
    total_pages = max(1, math.ceil(len(all_enumerated) / PAGE_SIZE))
    page = max(0, min(page, total_pages - 1))
    enumerated = all_enumerated[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]
    return _TEMPLATES.TemplateResponse(
        request,
        "bulk.html",
        {
            "enumerated": enumerated,
            "page": page,
            "total_pages": total_pages,
            "is_bulk": True,
            **progress,
        },
    )


@app.post("/bulk/accept-all", response_class=RedirectResponse)
def bulk_accept_all():
    state: ReviewState = app.state.review
    for i, s in enumerate(state.statuses):
        if s == "pending":
            state.statuses[i] = "accepted"
    return RedirectResponse("/bulk", status_code=303)


@app.post("/bulk/toggle/{index}", response_class=RedirectResponse)
def bulk_toggle(index: int):
    state: ReviewState = app.state.review
    current = state.statuses[index]
    state.statuses[index] = "rejected" if current == "accepted" else "accepted"
    return RedirectResponse("/bulk", status_code=303)


@app.post("/export", response_class=HTMLResponse)
def export(request: Request):
    state: ReviewState = app.state.review
    state.done.set()
    accepted = state.statuses.count("accepted")
    return _TEMPLATES.TemplateResponse(
        request,
        "exporting.html",
        {
            "accepted": accepted,
        },
    )


# ── Public lifecycle ────────────────────────────────────────────────────────


def run_review_server(cards: list[Card]) -> list[Card]:
    """Start the review UI, block until the user exports, return accepted cards."""
    state = ReviewState(cards=list(cards), statuses=["pending"] * len(cards))
    app.state.review = state

    config = uvicorn.Config(app, host="127.0.0.1", port=5173, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Give server a moment to bind before opening browser
    import time

    time.sleep(0.5)

    click.echo("  Opening review UI at http://localhost:5173")
    click.echo("  Waiting for review to complete...")
    webbrowser.open("http://localhost:5173")

    state.done.wait()
    server.should_exit = True
    thread.join(timeout=5)

    return [c for c, s in zip(state.cards, state.statuses) if s == "accepted"]
