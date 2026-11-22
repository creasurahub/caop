#!/usr/bin/env python3
"""Compact, machine-readable diff of the MAOP v1 contracts between two git commits.

Usage (from anywhere inside the repository):

    python tests/contract_diff.py BASE HEAD            # JSON to stdout
    python tests/contract_diff.py BASE HEAD --out FILE

It reads schema/maop-v1.schema.json and openapi/maop-v1.openapi.{json,yaml} at both
commits with `git show` (the working tree is never read), and reports:

- definitions added, removed and changed, each changed one with its exact JSON before and
  after (descriptions included, so nothing is hidden);
- for every enum that grew or shrank, the values added and removed;
- whether, at HEAD, OpenAPI components.schemas equals the schema $defs (after rewriting
  $ref prefixes) and whether the YAML and JSON OpenAPI files parse identical;
- the sha256 of each contract file at both commits.

The output is deterministic (sorted keys, no timestamps). Dependencies: pyyaml and git.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "schema/maop-v1.schema.json"
OAS_JSON = "openapi/maop-v1.openapi.json"
OAS_YAML = "openapi/maop-v1.openapi.yaml"


def show(commit, path):
    return subprocess.run(["git", "-C", ROOT, "show", f"{commit}:{path}"],
                          check=True, capture_output=True).stdout


def rev(commit):
    return subprocess.run(["git", "-C", ROOT, "rev-parse", commit], check=True,
                          capture_output=True, text=True).stdout.strip()


def enums(node, path=""):
    out = {}
    if isinstance(node, dict):
        if isinstance(node.get("enum"), list):
            out[path or "/"] = node["enum"]
        for k, v in node.items():
            out.update(enums(v, f"{path}/{k}"))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.update(enums(v, f"{path}/{i}"))
    return out


def rewrite_refs(node):
    if isinstance(node, dict):
        return {k: (v.replace("#/components/schemas/", "#/$defs/") if k == "$ref" and isinstance(v, str)
                    else rewrite_refs(v)) for k, v in node.items()}
    if isinstance(node, list):
        return [rewrite_refs(v) for v in node]
    return node


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("head")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    base, head = rev(a.base), rev(a.head)
    b = json.loads(show(base, SCHEMA))["$defs"]
    h = json.loads(show(head, SCHEMA))["$defs"]
    changed = {}
    for name in sorted(set(b) & set(h)):
        if b[name] != h[name]:
            eb, eh = enums(b[name]), enums(h[name])
            enum_changes = {}
            for p in sorted(set(eb) | set(eh)):
                added = [v for v in eh.get(p, []) if v not in eb.get(p, [])]
                removed = [v for v in eb.get(p, []) if v not in eh.get(p, [])]
                if added or removed:
                    enum_changes[p] = {"added": added, "removed": removed}
            changed[name] = {"enum_changes": enum_changes, "before": b[name], "after": h[name]}
    oas_json = json.loads(show(head, OAS_JSON))
    oas_yaml = yaml.safe_load(show(head, OAS_YAML))
    comps = rewrite_refs(oas_json["components"]["schemas"])
    report = {
        "base": base,
        "head": head,
        "files": {p: {"base_sha256": hashlib.sha256(show(base, p)).hexdigest(),
                      "head_sha256": hashlib.sha256(show(head, p)).hexdigest()}
                  for p in (SCHEMA, OAS_JSON, OAS_YAML)},
        "definitions": {"base_count": len(b), "head_count": len(h),
                        "added": sorted(set(h) - set(b)), "removed": sorted(set(b) - set(h)),
                        "changed": changed},
        "head_consistency": {
            "openapi_components_equal_schema_defs": comps == h,
            "openapi_yaml_equals_json": oas_yaml == oas_json,
            "operation_count": sum(1 for p in oas_json["paths"].values() for m in p
                                   if m in ("get", "post", "put", "patch", "delete")),
        },
    }
    text = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
