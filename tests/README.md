# MAOP v1 conformance checks

`tests/validate.py` is a standalone checker for this repository. It confirms that the MAOP v1 draft is complete and consistent, and that it stays backward compatible with CAOP v0.2.

## Running it

```bash
pip install jsonschema pyyaml          # jsonschema >= 4.18
python tests/validate.py               # run all checks
python tests/validate.py --list        # list check numbers and names
python tests/validate.py --only schema           # one check, by name
python tests/validate.py --only 3,5 --only parity  # several, by number or name
```

The checker prints one `PASS` or `FAIL` line per check. Under a `FAIL`, indented lines give the details. The last line reads `N/M checks passed`.

Exit codes:

- `0`: every selected check passed.
- `1`: at least one check failed.
- `2`: `jsonschema` or `pyyaml` is not installed. The checker prints the missing module and how to install it.

The checker needs only the standard library, `jsonschema`, `pyyaml` and `git`. It works offline and resolves paths from the repository root, so you can run it from any directory. A missing file is reported as a `FAIL` that names the file. It never crashes.

## The checks

| # | Name | What it proves |
|---|------|----------------|
| 1 | `protected-hashes` | The 9 CAOP schema and OpenAPI files (v0.1, v0.1.2 and v0.2) match the sha256 values in the MAOP shared contract, which are hard-coded. |
| 2 | `protected-git` | `LICENSE`, `.gitattributes`, `examples/README.md` and every tracked `examples/*.json` are unchanged versus `git HEAD`, checked with `git diff --quiet HEAD -- <path>`. No new JSON file was added at the top level of `examples/`. In `SPEC.md`, the only allowed change versus HEAD is at most 10 lines added at the very top. No line may be modified, removed or added further down. |
| 3 | `schema` | `schema/maop-v1.schema.json` declares and passes the JSON Schema 2020-12 meta-schema. It has exactly 110 `$defs`: all 95 CAOP v0.2 names plus the 15 new names from the contract, and nothing else. The new enums have exactly the contract values: `AgentRole`, `AuthorityGrant.trust_level`, `Receipt.outcome`, `SupervisionStage`, `ChildLifecycleState` and `Guard.kind`. The properties the contract names are present, `Guard.durable` is fixed to `true`, and every internal `$ref` resolves. |
| 4 | `openapi` | `openapi/maop-v1.openapi.yaml` and `.json` are identical when parsed. YAML timestamps are kept as strings, as in JSON. The document is OpenAPI 3.1 with exactly 23 operations and unique operationIds, all under `/maop/v1/`. The 17 CAOP v0.2 operationIds keep the same method and sub-path: `/v1/X` becomes `/maop/v1/X`. The 6 new operations have the contract's method, path and id. `components.schemas` has the same 110 names as the schema's `$defs`. Every `$ref` resolves, internal or into a file relative to `openapi/`. |
| 5 | `caop-examples` | **Backward-compatibility proof.** Each of the 71 CAOP v0.2 examples (`examples/<Name>.json`) still validates against the MAOP definition with the same name, so MAOP can only have refined the kept definitions additively. |
| 6 | `maop-examples` | Every `examples/maop-v1/*.json` validates. See "How MAOP examples are matched" below. Each of the 15 new definitions must have at least one valid example. |
| 7 | `parity` | `tests/parity.json` records the CAOP baseline counts as exactly 17 operations, 95 definitions and 71 examples. It mentions every CAOP operationId, definition name and example filename. Every entry with status `removed` has a non-empty `justification`, `rationale` or `reason`. |
| 8 | `neutrality` | `docs/maop-v1.md`, the MAOP schema, both MAOP OpenAPI files and every file in `examples/maop-v1/` contain neither "Creasura" nor "operating system" (case-insensitive). See "Neutrality exceptions" below. Allowed occurrences are listed in the output. |
| 9 | `topics` | `docs/maop-v1.md` covers each required topic, found by keyword or heading: Act→Decide, Act→Coordinate, Northstar with table rows A to K, two-phase verification, approval steering, isolation, compaction, lazy discovery, receipts, leases, authority and recovery. The back-edges may be written `→`, `->` or `to`. A Northstar row is a Markdown table row whose first cell is the letter. |
| 10 | `parity-reproducible` | Runs `tests/parity_gen.py all --out <tmp>` and requires `tests/parity.json` and `docs/maop-v1-parity.md` to be byte-identical to the committed files. To regenerate after a schema or OpenAPI change: `python tests/parity_gen.py all`. |

### How MAOP examples are matched (check 6)

The checker tries these rules in order:

1. A `"$schema_def"` key, such as `"#/$defs/Delegation"`, names the definition. The key is removed before validation.
2. The filename stem is a definition name, as in `Receipt.json`.
3. An entry in `examples/maop-v1/README.md` maps the file. A line holding the filename and `#/$defs/<Name>` maps it to that definition. A line holding the filename, an operationId in backticks and the words "path parameters" means the file is a GET request. It must be an object with exactly that operation's path parameters, each a non-empty string that matches the parameter's schema.
4. The part of the stem before the first dot is a definition name.

A file that matches none of these rules fails.

### Neutrality exceptions (check 8)

- In `docs/maop-v1.md`, "Creasura" may appear on a line that contains "reference implementation" or "generator". It may also appear under a heading that contains either phrase.
- The CAOP v0.2 wire value `CREASURA_VAULT`, from the `AuthCustodian` enum, is allowed in the MAOP schema and OpenAPI files. It is a kept constraint: removing it would break CAOP v0.2 clients. The exemption is listed in `NEUTRALITY_LEGACY_TOKENS` and covers only those files.
- "CAOP" is allowed as a name, as are MCP tool names such as `caop_pulse`.
- "operating system" has no exceptions.

## Where the constants come from

The hashes, counts, operation paths, definition names and enum values come from the binding MAOP v1 shared contract. They sit at the top of `validate.py`, and the CAOP baselines are also read from `schema/caop-v0.2.schema.json` and `openapi/caop-v0.2.openapi.json`. If the contract changes, update those constants in the same change.
