# Cognee Cloud Recall — Fix Plan

> Symptom: on Cognee Cloud, `remember()` returns OK but `recall()` returns 0 hits
> even ~30s later (not eventual consistency alone). Local self-hosted works fully.
> Currently shipping LOCAL; Cloud path wired but parked. Re-enable by uncommenting
> `COGNEE_SERVICE_URL` in `.env`.
>
> Verify all API shapes against **docs.cognee.ai** — research file says signatures
> need confirming there (`research/cognee.md` line 6). This plan is ranked
> hypotheses + probes, not a confirmed one-line fix.

## Hypotheses, ranked (test top-down)

### #1 — Background pipeline not finished (most likely)
`remember()` on Cloud = async **server-side pipeline** (add → cognify → embed).
30s often isn't enough on Cloud, and if it errors server-side it fails silently.
Local worked because the pipeline ran inline.
- **Probe:** after `remember()`, poll a pipeline/dataset status call instead of
  guessing (look for `get_pipeline_status()` / dataset-status in the Cloud API).
  Recall only after status = completed.
- **Cheap test:** `remember` → wait 3–5 min → `recall`. If hits appear, it's pure
  timing → add a status poll before recall.

### #2 — `cognee.serve()` is the wrong client mechanism
`serve()` normally *starts an API server*; it may not mean "connect to my Cloud
tenant." If misused, `remember()` might write **local**, not Cloud — which also
explains "remember works, recall empty on Cloud."
- **Probe:** check docs.cognee.ai for the real Cloud-client call. Cloud likely
  wants an SDK client pointed at the tenant URL + API key, or plain REST
  (`POST /add`, `/cognify`, `/search`) — not `serve()`. **Verify this first.**
- Code: `integrations/cognee/real.py` `_serve_if_cloud()` (line ~88).

### #3 — Dataset scoping mismatch
Write uses `dataset_name=self._dataset` (real.py ~125); read uses
`datasets=[self._dataset]` (real.py ~138). On Cloud these can resolve to
different scopes (tenant/user-namespaced).
- **Probe:** list datasets on the tenant after remember. Confirm
  `sentinel_team_memory` exists and holds nodes. Align write/read names if not.

### #4 — `only_context=True` filters everything out
real.py ~139 — `only_context=True` returns graph-context chunks only; if Cloud's
default search type doesn't populate those, result is empty.
- **Probe:** set `only_context=False`, or pass an explicit `search_type`
  (graph-completion vs chunks). Retry.

### #5 — Double cognify conflict
Seed does `remember()` (already cognifies) **then** `improve()` =
`cognify(datasets=[...])` (seed line 56). On Cloud a second cognify mid-pipeline
may reset it.
- **Probe:** skip `improve()` in Cloud mode; recall directly.

## Fastest path to root cause
Write a standalone probe `scripts/probe_cognee_cloud.py`:
`remember → list datasets → poll status → search(only_context=False)`, printing
each raw response. Surfaces which stage drops the data in one run instead of
guessing through the full app.

## Re-enable Cloud
1. Uncomment `COGNEE_SERVICE_URL=https://tenant-...aws.cognee.ai` in `.env`
   (line ~105). Blank = local self-hosted.
2. Confirm `COGNEE_API_KEY` is a live key (ROTATE the old one — it leaked in
   session logs).
3. Run the probe script; walk the hypotheses top-down.

## Track relevance
Cloud recall unblocks the **iPhone / Cognee-Cloud track**. Open-Source track ships
fine on LOCAL (already verified). Fix Cloud only if time allows before deadline.
