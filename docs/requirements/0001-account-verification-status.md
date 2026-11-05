# 0001: Separate unverified accounts from normal accounts

Status: pending-verification

- Owner: Account management
- Created: 2026-10-19
- Related ADR: [Backend owns control-panel semantics](../adr/0001-backend-owns-control-panel-semantics.md)

## Problem and user outcome

The account list reports a failed remote check in its diagnostic text while
showing a green normal status. Dashboard totals also count that account as
normal. Users need a visible, filterable `待验证` management category and a
separate Dashboard count.

## Scope and ownership

`services/account_view.py` owns the effective category shared by rows, details,
API filters, selection previews and `AccountService.get_stats`. The new
`unverified` category covers remote check results `error` and `pending`.
Disabled accounts and confirmed unusable credentials retain their higher
priority. Successful verification restores the category projected from the
current account record. Unknown plan/quota metadata alone does not create
this category.

The API and TypeScript contracts transport that projection. Accounts owns the
filter draft and selection UI; Dashboard renders a separate warning card.
Both desktop and narrow layouts retain their existing scroll owners.

## Non-goals and persistence

No new persisted status or data migration, scheduling changes, account
deletions, token revocation rules, retry changes or proxy configuration.
The existing Account Repository retains ownership. The projection must not
modify credentials, stored account status or bindings. Diagnostics remain
sanitized. A failed check cannot itself establish credential invalidity.
No new ADR is needed because existing semantic ownership is preserved.

## Interfaces

- Account rows/details: `status_category=unverified`, `status_label=待验证`,
  warning tone and the existing remote-check reason.
- List and selection filters: `unverified` or `待验证`.
- Dashboard accounts: additive integer `unverified`; `active` and normal
  quota totals exclude that category. Categories partition the account total.
- Deployment updates the backend and built console together; backup and
  rollback retain the previous source and assets.

## Acceptance and verification

| Criterion | Verification | Status |
| --- | --- | --- |
| Failed/pending checks display `待验证`; invalid and disabled remain distinct | Projection regression and live row inspection | automated + agent browser checks passed |
| Accounts filter and selection preview match the same records | HTTP integration and browser filter interaction | automated + agent browser checks passed |
| Dashboard counts unverified separately and excludes them from normal | Contract/integration and browser card inspection | automated + agent browser checks passed |
| Successful recheck clears the derived category without data migration | Regression fixture transition | automated check passed |
| Desktop/mobile rendering, existing image and proxy behavior remain intact | Console build, regression suite and browser checks | scoped automated + agent browser checks passed |

Automated validation and agent browser checks do not imply user acceptance.
The deployed snapshot contains 38 accounts: 37 normal and 1 unverified.
Backend regression passed 111 tests and 22 subtests; five scoped console
runtime checks and the production build passed. The original full console
runtime command could not run because its ignored
`web-vue/tests/local-icons-runtime.mjs` entry file is absent in this checkout.
Agent browser checks covered desktop and 390px mobile Accounts/Dashboard,
plus loading of the other six main routes; no relevant console errors were
observed. User acceptance remains pending.

## Documentation impact

Update `CONTEXT.md`, the critical flows map, the requirements index and
`CHANGELOG.md` for the management category. Deployment verification evidence
stays outside committed source.
