---
name: spendly-ui-designer
description: Generates production-ready UI (Jinja templates + CSS) for Spendly, a personal expense-tracker Flask app, matching its existing warm editorial fintech design system (forest green + gold on cream, DM Serif Display headings, card-based layout). Use this whenever the user asks to design, create, build, redesign, or improve any page or component for Spendly — e.g. "design the add expense page", "create UI for the dashboard", "build the expense list", "redesign the profile page", "improve the expense form" — even if they don't say "UI" or name a specific page explicitly (any Spendly-related screen, form, card, table, or nav element qualifies). Also use it if the user pastes a screenshot of a Spendly page and asks for a redesign or a new page to match it.
---

# Spendly UI designer

Spendly is a personal expense tracker built as a plain Flask + Jinja2 app —
server-rendered, no npm, no build step, no JS framework. It already has a real
design system (colors, fonts, spacing, reusable CSS classes) sitting in
`static/css/style.css`, established across its landing/auth/legal pages. Six
pages are built; four expense-related routes (`profile`, `add_expense`,
`edit_expense`, `delete_expense`) are still stubs. Most of what this skill will
be asked to design is genuinely new — there's no existing template to copy for
a dashboard, an expense list, or an add/edit expense form, so "match the
existing design" means matching the *system* (tokens, class conventions, page
structure), not copying a page that doesn't exist yet.

**Read `references/design-system.md` before writing anything.** It has the
exact design tokens, every reusable CSS class already defined, the full
`base.html` shell, a worked example template (`login.html`), the route
pattern in `app.py`, and the icon convention — all snapshotted directly from
the real repo, not reconstructed from memory. Working from that file instead
of guessing is what makes a new page look like it was built by the same person
who built the rest of the app, rather than a generic template dropped on top.

If a connected folder or local checkout of the actual Spendly repo is
available, prefer reading the live `style.css` / `base.html` / a sibling
template over the snapshot when they might have diverged (the app is actively
being built out) — the reference file is a fast, offline-safe default, not the
only source of truth. If the user mentions the design has changed recently,
say so and check the live files rather than trusting the snapshot silently.

## Before designing: place the page in the app

A few questions determine more about the output than any styling choice does.
Answer them from context where possible; ask the user only what you can't
infer:

- **What data does this page show or collect?** An expense list needs to know
  what fields an expense has (amount, category, date, note) — check
  `database/db.py` / the schema if unsure rather than guessing field names.
- **Is this a logged-in page?** Every real app page (dashboard, expenses,
  profile) sits behind login, unlike the landing/auth/legal pages the design
  system was mostly built from. That has one concrete consequence worth
  flagging: `base.html`'s navbar currently has no in-app links (dashboard,
  expenses, profile) for a logged-in user — just "Logout". If you're designing
  the first real in-app page, say so and either propose the minimal navbar
  addition needed to reach it, or note clearly that the page will be
  unreachable from the nav until that's added.
- **What's the empty/zero state?** A brand-new user has no expenses yet. A
  list or dashboard design that only shows the populated state isn't really
  finished — sketch the empty state too, even briefly.

## What to produce

Structure the response in two parts.

### 1. UI structure (brief)

A short, plain-language walkthrough, not a spec document: the overall layout,
the key sections and why they're arranged that way, and any UX decision worth
calling out (e.g. "amount input is right-aligned and uses a large numeral
since it's the field the user scans for first"). Include what data the
template expects to receive from its route (e.g. "expects `expenses`, a list
of dicts with `amount`, `category`, `date`, `note`") — this is documentation
of the contract, not an implementation of it (see Scope, below).

Keep this to a few sentences or a short paragraph plus a couple of bullets if
there are distinct sections to name — it's orientation for the person reading
the code next, not a design doc to review on its own.

### 2. Code

- A complete Jinja template (`{% extends "base.html" %}`, following the
  structure/indentation conventions in `login.html`), using existing classes
  from `style.css` wherever the existing system already covers the need.
- Any *new* CSS the page needs, clearly presented as an addition to
  `static/css/style.css` (a diff-shaped block or a clearly labeled new section
  comment, matching the file's existing `/* --- Section --- */` divider
  style) — not a full rewrite of the stylesheet, and not a new inline
  `<style>` block or separate CSS file.
- New class names follow the existing kebab-case, page-scoped-prefix
  convention (`expense-*` for an expense list page, `dash-*` for a dashboard —
  see "Naming" in the reference doc).
- Where a page repeats a chunk of markup (an expense row, a stat card, a
  category badge), prefer a Jinja `{% macro %}` (or at minimum a clearly
  isolated, copy-pasteable block) over hand-duplicating the HTML three or four
  times — that's what "modular" means in a Jinja codebase, since there's no
  component framework to lean on.
- Icons as inline SVG from `assets/icons/` (see reference doc for the full
  bundled list and the convention for anything not already bundled). Every
  icon should be doing a job — labeling an action, marking a category, showing
  a state — not decorating for its own sake.

### Scope: template + CSS, not the route

Design the page, not the backend. It's fine — expected, even — to name what
route/view logic the page assumes (mentioned in the UI structure section
above), but don't write or modify `app.py` or `database/db.py` as part of this
skill. If the route is still a placeholder stub, say so explicitly so the user
knows the template won't render correctly until the view function catches up.

## Design quality bar

Spendly's existing identity is a **warm editorial fintech** look — cream
paper tones, forest green and warm gold accents, a serif display font for
headings over a clean sans body, soft borders and subtle shadows rather than
heavy drop shadows or saturated gradients. That's a deliberate, specific
aesthetic, not a placeholder — resist the pull toward generic "modern SaaS
blue" defaults (blue-purple gradients, Inter-everywhere, harsh card shadows)
just because that's a common look elsewhere. The bar is: does this look like
the same designer who built the landing and auth pages made it, not does it
look like a generic dashboard template.

Concretely, that means: card-based grouping for related content (a white
surface, 1px border, radius token — see `.feature-card`/`.auth-card` in the
reference), a clear type hierarchy (serif display for the page/section title,
sans body for everything else, muted ink for secondary text), generous
spacing from the existing scale rather than cramped defaults, and icons used
functionally rather than as filler.

## Avoid

- Inventing new colors, fonts, or radius values instead of using the tokens
  that already exist — the design system is small on purpose; lean on it.
- A generic dashboard-template look that could belong to any app — every
  choice should trace back to something already established in Spendly.
- Dumping an unstructured wall of HTML/CSS with no explanation of layout or
  decisions — the brief structure section is part of the deliverable, not
  optional preamble.
- Reconstructing Lucide icon SVG paths from memory — read them from
  `assets/icons/`, or fetch fresh from the source named in the reference doc.
- Silently designing a logged-in page as if the navbar already links to it.