# Worker protocol

The CLI writes a single JSON object to stdout. Diagnostics are kept out of stdout when possible.

Important fields for implementation runs:

- `success`: whether the wrapper completed successfully;
- `run_id`: stable local run identifier;
- `conversation_id`: Antigravity conversation identifier, when available;
- `worktree_path`: isolated worktree containing the external agent's edits;
- `patch_path`: Git binary patch from the baseline snapshot to the worker result;
- `changed_files`: files changed by the worker relative to the snapshot;
- `result`: structured Gemini output;
- `usage`: Antigravity token usage;
- `review.status`: `pending_review`, `accepted`, `needs_fix`, `rejected`, or `applied`.

The worker's structured result uses these fields when available:

- `summary`
- `findings[]`
- `changes[]`
- `tests[]`
- `risks[]`
- `questions[]`
- `confidence`

The actual Git diff is authoritative for code changes; `changes[]` is only the worker's description.

State and patches are stored under `${CODEX_HOME}/cheap-agent-runs` when `CODEX_HOME` is set, otherwise under the user's `.codex/cheap-agent-runs` directory. Worktrees are stored alongside that state under `.codex/cheap-agent-worktrees`.
