# Foreman protocol

The helper prints one JSON object to stdout.

Important fields:

- `run_id` — Agent Foreman run identifier.
- `caller` — identity supplied by the current lead.
- `parent_run_id` — parent Foreman run for recursive delegation, if any.
- `delegation_depth` — propagated depth metadata.
- `provider` — `agy-staff` or `direct-agy`.
- `persona` — selected worker role.
- `agy_job_id` — background agy-staff job ID when applicable.
- `worktree_path` — isolated checkout used by the worker.
- `baseline_commit` — snapshot before worker changes.
- `changed_files` — authoritative file list generated from Git.
- `patch_path` — binary-capable Git patch against the baseline.
- `result` — worker response text/structured result.
- `review.status` — `pending_review`, `accepted`, `needs_fix`, `rejected`, `applied`, or `not_required`.

For code, the actual diff and tests are authoritative; worker prose is evidence, not acceptance.
