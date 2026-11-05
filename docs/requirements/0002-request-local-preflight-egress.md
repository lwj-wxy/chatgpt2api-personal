# 0002: Reuse successful preflight egress within an image request

Status: pending-verification

Created: 2026-10-20. The user authorized fixes, regression tests, deployment,
and a before/after image-generation comparison.

## Problem and outcome

An image request can report direct egress after first timing out on an account's
managed proxy during preflight, then connecting to the same failed proxy again
during generation preparation. The second failed connection is missing from the
timeline. Selecting the direct default does not clear existing managed bindings.

## Scope and owners

- The external subscription manager owns managed account bindings. On a sync
  with default direct, it clears only unchanged assignments recorded as its own,
  defers busy accounts, preserves manual changes, and stops assigning new proxies.
  Default changes take effect for existing managed bindings on the next sync;
  deployment runs that sync immediately.
- `OpenAIBackendAPI` owns transport fallback for safe account reads. Only a
  successful image preflight on fallback direct returns ephemeral routing data.
- `AccountService` carries that data from the selected account to the caller,
  removes it before persistence, and discards data from rejected candidates.
- `services.protocol.conversation` owns this image's lifecycle. It reuses direct
  after preflight fallback, retains submission guards, and records pre-submission
  connection retry time without creating another generation attempt.
- `request_detail_view` owns timeline semantics. Preflight retry is a component
  of raw account time, subtracted from its segment when displayed separately.
  A separate connection-retry segment reports failed generation preparation.

## Non-goals, persistence and failure behavior

No credential, quota, full-check freshness or account-removal policy changes.
No new persistent schema, shared transport cache, frontend layout or dependency.
Manual proxy choices remain higher-priority choices. Fallback errors, explicit
auth/HTTP rejections, credential races and generation submission ambiguity retain
their previous behavior. A subsequent request re-evaluates routing independently.
Old logs without retry metrics are not assigned invented precise timings.

## Acceptance and verification

Tests cover managed binding ownership/idempotence/busy accounts, successful
preflight handoff, no persistence or cross-candidate/request leakage, a single
generation result, submission ambiguity, and additive timeline segments.
Run the full Python suite in an offline container with temporary storage and
the manager tests with fake APIs. Validate current runtime source hashes before
deployment. Preserve credentials and explicit manual bindings, inspect real
logs in the console, and compare two public API calls with the same model,
prompt, size and quality; upstream variability must be reported separately.

Automated evidence: 117 backend tests plus 22 subtests and 30 external-manager
tests pass. Deployment cleared 36 owned bindings while preserving credentials;
an immediate repeat sync did not rebind any account. Public before/after calls
returned one image each in 46.858 s and 23.069 s respectively; account selection
took 5.658 s and 1.855 s. The latter used `default_direct` without a fallback
event. This single pair is not a stable latency benchmark. Desktop management
routes and the 390-pixel log detail were inspected; user acceptance is pending.
