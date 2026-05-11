# Review UI

The review UI is a browser-based interface for approving, editing, and rejecting generated cards before they are exported.

Launch it by adding `--review` to any `generate` command:

```bash
ankirai generate notes.pdf --deck "Biochemistry" --review
```

A local server starts at `http://localhost:5173` and your browser opens automatically. The server shuts down as soon as you click Export.

Only **accepted** cards are included in the exported file. Rejected and still-pending cards are discarded.

---

## Navigation

The nav bar is present on every page and shows:

- A progress bar and accepted/total count
- A **theme toggle** (☀/☾) to switch dark/light mode — preference is saved in `localStorage`
- A context-aware view switcher: **Bulk view** when in card view, **Card view** when in bulk view
- An **Export** button

---

## Card View

Card view shows one card at a time: front, back (hidden for cloze cards), and tags.

### Keyboard shortcuts

| Key | Action |
|---|---|
| `1` | Accept — marks card accepted and advances to the next pending card |
| `2` | Edit — opens the inline edit form |
| `3` | Reject — marks card rejected and advances to the next pending card |
| `[` or `←` | Go to previous card |
| `]` or `→` | Go to next card |

Shortcuts are suppressed when the cursor is inside a textarea or input field.

### Inline edit

Press `2` or click **Edit** to reveal front and back textareas in place. Click **Save & accept** to save your changes, accept the card, and advance to the next pending card. Click **Cancel** to dismiss without saving.

---

## Bulk View

Bulk view shows all cards in a paginated table (50 per page).

| Column | Description |
|---|---|
| # | Global card index |
| Front | First 80 characters of the front text |
| Back | First 80 characters of the back text |
| Status | Badge showing `pending`, `accepted`, or `rejected` |
| (actions) | **View** button — opens that card in card view |

**Accept all pending** at the top approves every pending card in one click.

Use the **← Prev** / **Next →** links at the bottom to page through cards. Card indices are global, so **View** always opens the correct card regardless of which page you are on.

---

## Export

Click **Export N cards** in the nav bar (or the larger button at the bottom of bulk view) to finish. If any cards are still pending, a confirmation dialog asks whether to proceed — pending cards will be excluded from the export.

After export the server stops and the CLI writes the deck file.

---

## Cloze cards

Cloze deletion syntax (`{{c1::term}}`) is highlighted in the card front: the term inside the braces is shown with a yellow background. MathJax renders LaTeX (`\(...\)` inline, `\[...\]` block) on both card view and bulk view.
