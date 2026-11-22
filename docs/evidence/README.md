# Review evidence for MAOP v1

Small, reviewable files that let a reviewer check the large contract files without a
patch viewer. Each one names the exact commit it describes and how to reproduce it.

| File | What it shows | Reproduce |
|---|---|---|
| `maop-v1-contract-diff-cb615d2-05e4845.json` | Every contract change from draft v1 (`cb615d2`) to v2 (`05e4845`): definitions added, removed and changed, with exact JSON before and after; enum values added; sha256 of each contract file; and, at `05e4845`, that OpenAPI `components.schemas` equals the schema `$defs`, that the YAML and JSON OpenAPI files are identical, and that there are 23 operations. | `python tests/contract_diff.py cb615d2 05e4845` |
| `maop-v1-validate-05e4845.txt` | The full output of `tests/validate.py` (10/10 PASS, exit 0) run on a clean checkout of exactly `05e4845`, with the Python, jsonschema and pyyaml versions. | `git worktree add --detach /tmp/maop 05e4845 && cd /tmp/maop && python tests/validate.py` |
