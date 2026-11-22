#!/usr/bin/env python3
"""MAOP v1 conformance checker.

Runs a fixed set of checks against this repository and prints one PASS or
FAIL line per check (with indented detail lines under a FAIL). Exits 0 only
if every selected check passes.

Usage:
    python tests/validate.py                 # run every check
    python tests/validate.py --only schema   # run one check (name or number)
    python tests/validate.py --only 1,3 --only parity
    python tests/validate.py --list          # list check names

Dependencies: the Python standard library plus jsonschema (>= 4.18) and
pyyaml. See tests/README.md for what each check means.
"""

from __future__ import annotations

import argparse
import copy
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

try:
    import jsonschema
    from jsonschema import Draft202012Validator
    import yaml
except ImportError as exc:  # pragma: no cover - exercised manually
    missing = getattr(exc, "name", None) or str(exc)
    print(
        "FAIL dependencies: missing Python module %r. This checker needs "
        "jsonschema (>= 4.18) and pyyaml: pip install jsonschema pyyaml"
        % missing
    )
    sys.exit(2)

try:
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
except ImportError:  # jsonschema < 4.18
    Registry = None


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Constants from the binding MAOP v1 shared contract
# ---------------------------------------------------------------------------

PROTECTED_SHA256 = {
    "openapi/caop-v0.1.2.openapi.json": "6b727a0fa60efc1f487fe154d3eb3fe63c3f1e7121a89962a553116b04b005a8",
    "openapi/caop-v0.1.2.openapi.yaml": "05dd1dfbe6449cc5447420023f336aa48c7221d229219cbd17396da4bf9be8b4",
    "openapi/caop-v0.1.openapi.json": "076a128385a1bc7d4841d1447cf3b2a4eedfc612ad393c3b14d0714f9857a4eb",
    "openapi/caop-v0.1.openapi.yaml": "272fd7face00997359c9d185851995d9397281846ce6166d25a32e98f16a622f",
    "openapi/caop-v0.2.openapi.json": "699fc607a7b0473d8b2c08bac3d1f59b11687f2f6670cb391d86ec4b1aa7fcd6",
    "openapi/caop-v0.2.openapi.yaml": "aaf1ae25400fd3db9483c737b787e36a31976415434d9bb615ca3481ec790e42",
    "schema/caop-v0.1.2.schema.json": "3a72213ecf506df646cfb8c455b564349e2eae819bf3b6b9686f6868cfdbf000",
    "schema/caop-v0.1.schema.json": "4cc2cda6f49926efa8521aa5dabd66803b23691ce8a7488c51f0477798005ded",
    "schema/caop-v0.2.schema.json": "7a4e7ce9fdd5328d10a93595fe0269e63ba9a8fb9bce21b300dd6c7020a45f75",
}

CAOP_SCHEMA = "schema/caop-v0.2.schema.json"
CAOP_OPENAPI = "openapi/caop-v0.2.openapi.json"
MAOP_SCHEMA = "schema/maop-v1.schema.json"
MAOP_OPENAPI_YAML = "openapi/maop-v1.openapi.yaml"
MAOP_OPENAPI_JSON = "openapi/maop-v1.openapi.json"
MAOP_DOC = "docs/maop-v1.md"
MAOP_EXAMPLES_DIR = "examples/maop-v1"
PARITY_JSON = "tests/parity.json"

META_2020_12 = "https://json-schema.org/draft/2020-12/schema"

CAOP_OPERATION_COUNT = 17
CAOP_DEFINITION_COUNT = 95
CAOP_EXAMPLE_COUNT = 71
MAOP_OPERATION_COUNT = 23
MAOP_DEFINITION_COUNT = 110

# (method, path, operationId)
NEW_OPERATIONS = [
    ("post", "/maop/v1/agents", "agents.register"),
    ("post", "/maop/v1/delegations", "delegations.create"),
    ("get", "/maop/v1/delegations/{delegation_id}", "delegations.get"),
    ("post", "/maop/v1/leases/{lease_id}/renew", "leases.renew"),
    ("get", "/maop/v1/receipts/{receipt_id}", "receipts.get"),
    ("post", "/maop/v1/supervision/{work_id}/evaluate", "supervision.evaluate"),
]

NEW_DEFINITIONS = [
    "AgentIdentity", "AgentRole", "AgentRegistration", "Delegation",
    "DelegationCreate", "AuthorityGrant", "Lease", "LeaseRenewal", "Receipt",
    "SupervisionStage", "ChildLifecycleState", "Guard",
    "SupervisionEvaluation", "TransitionDecision", "CausalEvidence",
]

# (definition, property or None for the definition itself) -> exact enum values
NEW_ENUMS = {
    ("AgentRole", None): ["supervisor", "planner", "implementer", "reviewer",
                          "verifier", "approver", "observer"],
    ("AuthorityGrant", "trust_level"): ["T0_relayed", "T1_attested"],
    ("Receipt", "outcome"): ["succeeded", "failed", "outcome_unknown"],
    ("SupervisionStage", None): ["observe", "decide", "plan", "coordinate",
                                 "act", "verify", "review", "approve",
                                 "record", "recover", "closed"],
    ("ChildLifecycleState", None): ["proposed", "delegated", "leased",
                                    "executing", "submitted", "verifying",
                                    "accepted", "rejected", "cancelled",
                                    "expired"],
    ("Guard", "kind"): ["authority", "policy", "evidence", "freshness",
                        "lease", "separation_of_duties", "budget"],
}

# Properties the contract names for the new definitions.
NEW_PROPERTIES = {
    "AuthorityGrant": ["trust_level", "scope", "expires_at"],
    "Lease": ["lease_id", "holder", "fencing_token", "expires_at"],
    "Receipt": ["receipt_id", "action", "actor", "idempotency_key", "outcome",
                "evidence_refs", "causal_parents"],
    "Guard": ["guard_id", "kind", "expression", "durable"],
    "TransitionDecision": ["from_stage", "to_stage", "trigger",
                           "guards_passed", "guards_failed", "next_action"],
    "CausalEvidence": ["evidence_id", "kind", "digest", "derived_from",
                       "observed_at", "valid_time"],
}

HTTP_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class CheckFailed(Exception):
    """Raised for a fatal problem that stops a check early."""


def path(rel: str) -> str:
    return os.path.join(ROOT, rel)


def require_file(rel: str) -> str:
    full = path(rel)
    if not os.path.isfile(full):
        raise CheckFailed("missing file: %s" % rel)
    return full


def load_json(rel: str):
    full = require_file(rel)
    try:
        with open(full, encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        raise CheckFailed("%s is not valid JSON: %s" % (rel, exc))


class _NoDatesLoader(yaml.SafeLoader):
    """SafeLoader that keeps timestamps as strings (JSON has no date type)."""


_NoDatesLoader.yaml_implicit_resolvers = {
    key: [r for r in resolvers if r[0] != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml(rel: str):
    full = require_file(rel)
    try:
        with open(full, encoding="utf-8") as fh:
            return yaml.load(fh, Loader=_NoDatesLoader)
    except yaml.YAMLError as exc:
        raise CheckFailed("%s is not valid YAML: %s" % (rel, exc))


def git(*args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True)
    except FileNotFoundError:
        raise CheckFailed("git is not installed or not on PATH")


def json_pointer(doc, pointer: str):
    """Resolve a JSON Pointer fragment ('' or '/a/b'). Raises KeyError."""
    if pointer in ("", "/"):
        return doc
    if not pointer.startswith("/"):
        raise KeyError(pointer)
    node = doc
    for raw in pointer[1:].split("/"):
        token = raw.replace("~1", "/").replace("~0", "~")
        token = re.sub(r"%([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), token)
        if isinstance(node, list):
            node = node[int(token)]
        elif isinstance(node, dict):
            node = node[token]
        else:
            raise KeyError(pointer)
    return node


def iter_refs(node, where="#"):
    """Yield (location, $ref value) for every $ref in a JSON document."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                yield where, value
            else:
                yield from iter_refs(value, "%s/%s" % (where, key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from iter_refs(value, "%s/%d" % (where, i))


def operations(openapi: dict):
    """Return {operationId: (method, path)} and a list of all operations."""
    by_id, all_ops = {}, []
    for p, item in (openapi.get("paths") or {}).items():
        if not isinstance(item, dict):
            continue
        for method in HTTP_METHODS:
            op = item.get(method)
            if isinstance(op, dict):
                op_id = op.get("operationId")
                all_ops.append((method, p, op_id))
                if op_id:
                    by_id[op_id] = (method, p)
    return by_id, all_ops


def def_validator(root: dict, name: str) -> Draft202012Validator:
    """A validator for root['$defs'][name] that resolves refs within root."""
    wrapper = {"$schema": META_2020_12, "$defs": root.get("$defs", {}),
               "$ref": "#/$defs/%s" % name}
    kwargs = {"format_checker": Draft202012Validator.FORMAT_CHECKER}
    if Registry is not None:
        resource = Resource.from_contents(root, default_specification=DRAFT202012)
        registry = Registry()
        for uri in {root.get("$id"), os.path.basename(MAOP_SCHEMA),
                    os.path.basename(CAOP_SCHEMA)}:
            if uri:
                registry = registry.with_resource(uri, resource)
        kwargs["registry"] = registry
    return Draft202012Validator(wrapper, **kwargs)


def first_errors(validator, instance, limit=3):
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    out = []
    for err in errors[:limit]:
        loc = "/".join(str(p) for p in err.absolute_path) or "(root)"
        out.append("at %s: %s" % (loc, err.message[:200]))
    return out, len(errors)


def find_enum(root: dict, node, seen=None):
    """Follow $ref/allOf/anyOf/oneOf to find an enum (or const) list."""
    seen = seen or set()
    if not isinstance(node, dict):
        return None
    if "enum" in node:
        return list(node["enum"])
    if "const" in node:
        return [node["const"]]
    ref = node.get("$ref")
    if isinstance(ref, str):
        frag = ref.split("#", 1)[1] if "#" in ref else ""
        if ref not in seen:
            seen.add(ref)
            try:
                return find_enum(root, json_pointer(root, frag), seen)
            except (KeyError, IndexError, ValueError):
                return None
    for comb in ("allOf", "anyOf", "oneOf"):
        for sub in node.get(comb, []) or []:
            found = find_enum(root, sub, seen)
            if found is not None:
                return found
    return None


def collect_properties(root: dict, node, seen=None) -> dict:
    """Merge 'properties' through $ref and allOf."""
    seen = seen or set()
    props = {}
    if not isinstance(node, dict):
        return props
    props.update(node.get("properties") or {})
    ref = node.get("$ref")
    if isinstance(ref, str) and ref not in seen:
        seen.add(ref)
        frag = ref.split("#", 1)[1] if "#" in ref else ""
        try:
            props.update(collect_properties(root, json_pointer(root, frag), seen))
        except (KeyError, IndexError, ValueError):
            pass
    for sub in node.get("allOf", []) or []:
        props.update(collect_properties(root, sub, seen))
    return props


# ---------------------------------------------------------------------------
# Checks. Each returns a list of failure details (empty list == PASS) plus
# optional info lines; raising CheckFailed is a FAIL with that message.
# ---------------------------------------------------------------------------

def check_protected_hashes():
    fails, info = [], []
    for rel, expected in sorted(PROTECTED_SHA256.items()):
        full = path(rel)
        if not os.path.isfile(full):
            fails.append("missing protected file: %s" % rel)
            continue
        with open(full, "rb") as fh:
            actual = hashlib.sha256(fh.read()).hexdigest()
        if actual != expected:
            fails.append("%s sha256 %s, expected %s" % (rel, actual, expected))
    info.append("%d protected files checked" % len(PROTECTED_SHA256))
    return fails, info


def check_protected_git():
    fails, info = [], []
    if git("rev-parse", "--verify", "HEAD").returncode != 0:
        raise CheckFailed("not a git repository with a HEAD commit: %s" % ROOT)

    unchanged = ["LICENSE", ".gitattributes", "examples/README.md"]
    tracked = git("ls-files", "--", "examples/*.json").stdout.split()
    tracked = [t for t in tracked if t.count("/") == 1]  # top-level only
    for rel in unchanged + tracked:
        res = git("diff", "--quiet", "HEAD", "--", rel)
        if res.returncode == 1:
            fails.append("changed versus HEAD: %s" % rel)
        elif res.returncode != 0:
            fails.append("git diff failed for %s: %s" % (rel, res.stderr.strip()))
        elif not os.path.exists(path(rel)):
            fails.append("deleted: %s" % rel)
    untracked = git("ls-files", "--others", "--exclude-standard", "--",
                    "examples/").stdout.split()
    for rel in untracked:
        if rel.count("/") == 1 and rel.endswith(".json"):
            fails.append("new file in protected examples/ directory: %s "
                         "(MAOP examples belong in examples/maop-v1/)" % rel)
    info.append("%d tracked CAOP examples unchanged" % len(tracked)
                if not fails else "%d tracked CAOP examples checked" % len(tracked))

    # SPEC.md: only added lines, only at the top, at most 10.
    res = git("diff", "--unified=0", "--no-color", "HEAD", "--", "SPEC.md")
    if res.returncode != 0:
        fails.append("git diff failed for SPEC.md: %s" % res.stderr.strip())
        return fails, info
    added = 0
    for line in res.stdout.splitlines():
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
        if m:
            old_count = int(m.group(2)) if m.group(2) is not None else 1
            new_start = int(m.group(3))
            if old_count != 0:
                fails.append("SPEC.md: existing lines modified or removed (%s)" % line)
            elif new_start != 1:
                fails.append("SPEC.md: lines added below the top (%s)" % line)
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            fails.append("SPEC.md: removed line: %s" % line[:120])
        elif line.startswith("\\ No newline"):
            fails.append("SPEC.md: end-of-file newline changed")
    if added > 10:
        fails.append("SPEC.md: %d lines added at the top (at most 10 allowed)" % added)
    info.append("SPEC.md: %d line(s) added at the top" % added)
    return fails, info


def check_schema():
    fails, info = [], []
    maop = load_json(MAOP_SCHEMA)
    caop = load_json(CAOP_SCHEMA)
    if maop.get("$schema") != META_2020_12:
        fails.append("$schema is %r, expected %r" % (maop.get("$schema"), META_2020_12))
    try:
        Draft202012Validator.check_schema(maop)
    except jsonschema.exceptions.SchemaError as exc:
        fails.append("not a valid 2020-12 schema: %s (at %s)" % (
            exc.message[:200], "/".join(str(p) for p in exc.absolute_path)))
    defs = maop.get("$defs")
    if not isinstance(defs, dict):
        raise CheckFailed("%s has no $defs object" % MAOP_SCHEMA)
    if len(defs) != MAOP_DEFINITION_COUNT:
        fails.append("$defs has %d definitions, expected %d"
                     % (len(defs), MAOP_DEFINITION_COUNT))
    caop_names = list(caop["$defs"])
    if len(caop_names) != CAOP_DEFINITION_COUNT:
        fails.append("CAOP schema has %d definitions, expected %d"
                     % (len(caop_names), CAOP_DEFINITION_COUNT))
    missing = [n for n in caop_names if n not in defs]
    if missing:
        fails.append("missing CAOP definitions: %s" % ", ".join(missing))
    missing_new = [n for n in NEW_DEFINITIONS if n not in defs]
    if missing_new:
        fails.append("missing new definitions: %s" % ", ".join(missing_new))
    extra = sorted(set(defs) - set(caop_names) - set(NEW_DEFINITIONS))
    if extra:
        fails.append("definitions not in the contract: %s" % ", ".join(extra))

    for (name, prop), expected in NEW_ENUMS.items():
        if name not in defs:
            continue
        node = defs[name]
        label = name if prop is None else "%s.%s" % (name, prop)
        if prop is not None:
            node = collect_properties(maop, node).get(prop)
            if node is None:
                fails.append("%s: property missing" % label)
                continue
        values = find_enum(maop, node)
        if values is None:
            fails.append("%s: no enum found" % label)
        elif sorted(map(str, values)) != sorted(expected) or len(values) != len(set(map(str, values))):
            fails.append("%s: enum %s, expected exactly %s" % (label, values, expected))

    for name, props in NEW_PROPERTIES.items():
        if name not in defs:
            continue
        have = collect_properties(maop, defs[name])
        absent = [p for p in props if p not in have]
        if absent:
            fails.append("%s: missing properties %s" % (name, ", ".join(absent)))
    if "Guard" in defs:
        durable = collect_properties(maop, defs["Guard"]).get("durable")
        if isinstance(durable, dict) and find_enum(maop, durable) != [True]:
            fails.append("Guard.durable must be fixed to true (const: true)")

    for where, ref in iter_refs(maop):
        if ref.startswith("#"):
            try:
                json_pointer(maop, ref[1:])
            except (KeyError, IndexError, ValueError):
                fails.append("unresolved $ref %s at %s" % (ref, where))
    info.append("%d definitions (%d CAOP + %d new)" % (
        len(defs), len([n for n in caop_names if n in defs]),
        len([n for n in NEW_DEFINITIONS if n in defs])))
    return fails, info


def check_openapi():
    fails, info = [], []
    doc_json = load_json(MAOP_OPENAPI_JSON)
    doc_yaml = load_yaml(MAOP_OPENAPI_YAML)
    if doc_json != doc_yaml:
        diffs = []
        for key in sorted(set(doc_json) | set(doc_yaml or {})):
            if doc_json.get(key) != (doc_yaml or {}).get(key):
                diffs.append(key)
        fails.append("yaml and json differ when parsed (top-level keys: %s)"
                     % ", ".join(diffs))
    version = str(doc_json.get("openapi", ""))
    if not version.startswith("3.1"):
        fails.append("openapi version is %r, expected 3.1.x" % version)

    by_id, all_ops = operations(doc_json)
    if len(all_ops) != MAOP_OPERATION_COUNT:
        fails.append("%d operations, expected %d" % (len(all_ops), MAOP_OPERATION_COUNT))
    no_id = [(m, p) for m, p, i in all_ops if not i]
    if no_id:
        fails.append("operations without operationId: %s" % no_id)
    ids = [i for _, _, i in all_ops if i]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        fails.append("duplicate operationIds: %s" % ", ".join(dupes))

    caop_by_id, caop_ops = operations(load_json(CAOP_OPENAPI))
    if len(caop_ops) != CAOP_OPERATION_COUNT:
        fails.append("CAOP v0.2 has %d operations, expected %d"
                     % (len(caop_ops), CAOP_OPERATION_COUNT))
    for op_id, (method, p) in sorted(caop_by_id.items()):
        expected = "/maop" + p if p.startswith("/v1/") else "/maop/v1" + p
        got = by_id.get(op_id)
        if got is None:
            fails.append("missing CAOP operation %s" % op_id)
        elif got != (method, expected):
            fails.append("%s is %s %s, expected %s %s" % (
                op_id, got[0].upper(), got[1], method.upper(), expected))
    for method, p, op_id in NEW_OPERATIONS:
        got = by_id.get(op_id)
        if got is None:
            fails.append("missing new operation %s" % op_id)
        elif got != (method, p):
            fails.append("%s is %s %s, expected %s %s" % (
                op_id, got[0].upper(), got[1], method.upper(), p))
    components = (doc_json.get("components") or {}).get("schemas") or {}
    try:
        maop_defs = set(load_json(MAOP_SCHEMA).get("$defs") or {})
    except CheckFailed:
        maop_defs = None
    if len(components) != MAOP_DEFINITION_COUNT:
        fails.append("components.schemas has %d entries, expected %d"
                     % (len(components), MAOP_DEFINITION_COUNT))
    if maop_defs is not None and set(components) != maop_defs:
        fails.append("components.schemas names differ from schema $defs: %s"
                     % ", ".join(sorted(set(components) ^ maop_defs)))
    stray = [p for _, p, _ in all_ops if not p.startswith("/maop/v1/")]
    if stray:
        fails.append("paths outside /maop/v1: %s" % ", ".join(sorted(set(stray))))

    # $ref resolution: internal, and to external files relative to openapi/.
    external_cache = {}
    n_refs = 0
    for where, ref in iter_refs(doc_json):
        n_refs += 1
        target, _, frag = ref.partition("#")
        if not target:
            doc = doc_json
        else:
            if re.match(r"^[a-z]+://", target):
                fails.append("absolute $ref not checked offline: %s at %s" % (ref, where))
                continue
            full = os.path.normpath(os.path.join(path("openapi"), target))
            if not os.path.isfile(full):
                alt = path(os.path.join("schema", os.path.basename(target)))
                full = alt if os.path.isfile(alt) else full
            if full not in external_cache:
                try:
                    with open(full, encoding="utf-8") as fh:
                        external_cache[full] = (json.load(fh) if full.endswith(".json")
                                                else yaml.load(fh, Loader=_NoDatesLoader))
                except (OSError, ValueError, yaml.YAMLError) as exc:
                    external_cache[full] = None
                    fails.append("cannot load $ref target %s: %s" % (target, exc))
            doc = external_cache[full]
            if doc is None:
                continue
        try:
            json_pointer(doc, frag)
        except (KeyError, IndexError, ValueError):
            fails.append("unresolved $ref %s at %s" % (ref, where))
    info.append("%d operations, %d $refs checked" % (len(all_ops), n_refs))
    return fails, info


def check_caop_examples():
    fails, info = [], []
    maop = load_json(MAOP_SCHEMA)
    defs = maop.get("$defs") or {}
    files = sorted(glob.glob(path("examples/*.json")))
    if len(files) != CAOP_EXAMPLE_COUNT:
        fails.append("%d CAOP examples, expected %d" % (len(files), CAOP_EXAMPLE_COUNT))
    ok = 0
    for full in files:
        stem = os.path.basename(full)[:-5]
        if stem not in defs:
            fails.append("%s.json: definition %s not kept in MAOP schema" % (stem, stem))
            continue
        with open(full, encoding="utf-8") as fh:
            instance = json.load(fh)
        errs, n = first_errors(def_validator(maop, stem), instance)
        if n:
            fails.append("%s.json no longer validates against MAOP %s (%d error(s)): %s"
                         % (stem, stem, n, "; ".join(errs)))
        else:
            ok += 1
    info.append("%d/%d CAOP v0.2 examples validate against MAOP v1" % (ok, len(files)))
    return fails, info


def maop_example_mapping(defs: dict):
    """Map examples/maop-v1/README.md filenames to definition names."""
    mapping = {}
    readme = path(os.path.join(MAOP_EXAMPLES_DIR, "README.md"))
    if not os.path.isfile(readme):
        return mapping
    with open(readme, encoding="utf-8") as fh:
        for line in fh:
            names = re.findall(r"([\w.\-]+\.json)", line)
            if re.search(r"path param", line, re.I):
                op = re.search(r"`([a-z_]+\.[a-z_]+)`", line)
                for name in names:
                    if op and not name.endswith("schema.json"):
                        mapping.setdefault(os.path.basename(name),
                                           ("path-parameters", op.group(1)))
                continue
            target = re.search(r"#/\$defs/(\w+)", line)
            if not target:
                # fall back to any backticked definition name on the line
                for cand in re.findall(r"`(\w+)`", line):
                    if cand in defs:
                        target = cand
                        break
            else:
                target = target.group(1)
            for name in names:
                base = os.path.basename(name)
                if target and base not in mapping and not name.endswith("schema.json"):
                    mapping[base] = target
    return mapping


def path_parameter_validator(maop: dict, openapi: dict, op_id: str):
    """Validator for an object holding an operation's path parameters."""
    for p, item in (openapi.get("paths") or {}).items():
        for method in HTTP_METHODS:
            op = (item or {}).get(method)
            if isinstance(op, dict) and op.get("operationId") == op_id:
                params = list(item.get("parameters") or []) + list(op.get("parameters") or [])
                props, required = {}, []
                for prm in params:
                    if "$ref" in prm:
                        prm = json_pointer(openapi, prm["$ref"].split("#", 1)[1])
                    if prm.get("in") != "path":
                        continue
                    sub = json.loads(json.dumps(prm.get("schema") or {}).replace(
                        "#/components/schemas/", "#/$defs/"))
                    props[prm["name"]] = {"allOf": [sub, {"type": "string", "minLength": 1}]}
                    required.append(prm["name"])
                schema = {"$schema": META_2020_12, "$defs": maop.get("$defs", {}),
                          "type": "object", "properties": props, "required": required,
                          "additionalProperties": False}
                return Draft202012Validator(schema), "path parameters of %s" % op_id
    raise CheckFailed("operation %s not found in %s" % (op_id, MAOP_OPENAPI_JSON))


def check_maop_examples():
    fails, info = [], []
    maop = load_json(MAOP_SCHEMA)
    defs = maop.get("$defs") or {}
    if not os.path.isdir(path(MAOP_EXAMPLES_DIR)):
        raise CheckFailed("missing directory: %s" % MAOP_EXAMPLES_DIR)
    files = sorted(glob.glob(path(os.path.join(MAOP_EXAMPLES_DIR, "*.json"))))
    if not files:
        raise CheckFailed("no examples in %s" % MAOP_EXAMPLES_DIR)
    readme_map = maop_example_mapping(defs)
    covered, ok = set(), 0
    for full in files:
        base = os.path.basename(full)
        stem = base[:-5]
        try:
            with open(full, encoding="utf-8") as fh:
                instance = json.load(fh)
        except json.JSONDecodeError as exc:
            fails.append("%s: invalid JSON: %s" % (base, exc))
            continue
        target, how = None, None
        if isinstance(instance, dict) and isinstance(instance.get("$schema_def"), str):
            target, how = instance["$schema_def"].split("/")[-1], "$schema_def"
            instance = {k: v for k, v in instance.items() if k != "$schema_def"}
        elif stem in defs:
            target, how = stem, "filename"
        elif isinstance(readme_map.get(base), tuple):
            try:
                validator, label = path_parameter_validator(
                    maop, load_json(MAOP_OPENAPI_JSON), readme_map[base][1])
            except CheckFailed as exc:
                fails.append("%s: %s" % (base, exc))
                continue
            errs, n = first_errors(validator, instance)
            if n:
                fails.append("%s does not validate against %s (%d error(s)): %s"
                             % (base, label, n, "; ".join(errs)))
            else:
                ok += 1
            continue
        elif base in readme_map:
            target, how = readme_map[base], "README"
        elif stem.split(".")[0] in defs:
            target, how = stem.split(".")[0], "filename prefix"
        if target is None:
            fails.append("%s: cannot tell which definition it instantiates "
                         "(no matching filename, $schema_def key or README entry)" % base)
            continue
        if target not in defs:
            fails.append("%s: definition %s (by %s) not in MAOP schema" % (base, target, how))
            continue
        errs, n = first_errors(def_validator(maop, target), instance)
        if n:
            fails.append("%s does not validate against %s (%d error(s)): %s"
                         % (base, target, n, "; ".join(errs)))
        else:
            ok += 1
            covered.add(target)
    uncovered = [n for n in NEW_DEFINITIONS if n not in covered]
    if uncovered:
        fails.append("new definitions without a valid example: %s" % ", ".join(uncovered))
    info.append("%d/%d MAOP examples validate; %d/%d new definitions covered"
                % (ok, len(files), len(NEW_DEFINITIONS) - len(uncovered), len(NEW_DEFINITIONS)))
    return fails, info


_COUNT_KEYS = {
    "operations": ("operations", "operation_count", "operations_count", "ops"),
    "definitions": ("definitions", "definition_count", "definitions_count", "defs",
                    "schemas", "schema_definitions"),
    "examples": ("examples", "example_count", "examples_count"),
}


def _walk(node, trail=()):
    yield trail, node
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, trail + (str(k),))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, trail + (str(i),))


def _strings(node):
    for _, value in _walk(node):
        if isinstance(value, str):
            yield value
        if isinstance(value, dict):
            yield from (k for k in value)


def check_parity():
    fails, info = [], []
    parity = load_json(PARITY_JSON)
    expected = {"operations": CAOP_OPERATION_COUNT,
                "definitions": CAOP_DEFINITION_COUNT,
                "examples": CAOP_EXAMPLE_COUNT}

    # Counts: any dict with integer values for all three kinds.
    count_sets = []
    for trail, node in _walk(parity):
        if not isinstance(node, dict):
            continue
        found = {}
        for kind, keys in _COUNT_KEYS.items():
            for key in keys:
                if isinstance(node.get(key), int) and not isinstance(node.get(key), bool):
                    found[kind] = node[key]
                    break
        if len(found) == 3:
            count_sets.append(("/".join(trail) or "(root)", found))
    if not count_sets:
        # Fall back to list lengths: {"operations": [...], ...}
        lists = {k: parity.get(k) for k in expected if isinstance(parity.get(k), list)}
        if len(lists) == 3:
            count_sets.append(("(list lengths)", {k: len(v) for k, v in lists.items()}))
    if not count_sets:
        fails.append("no counts found (expected an object with operations=17, "
                     "definitions=95, examples=71)")
    else:
        exact = [t for t, c in count_sets if c == expected]
        caopish = [(t, c) for t, c in count_sets
                   if re.search(r"caop|baseline|v0\.?2|source|counts", t, re.I) or t == "(root)"]
        if not exact:
            fails.append("counts %s, expected %s" % (count_sets[0][1], expected))
        for t, c in caopish:
            if c != expected:
                fails.append("counts at %s are %s, expected %s" % (t, c, expected))
        if exact:
            info.append("counts 17/95/71 found at %s" % exact[0])

    strings = set(_strings(parity))
    caop_by_id, _ = operations(load_json(CAOP_OPENAPI))
    missing_ops = sorted(i for i in caop_by_id if i not in strings)
    if missing_ops:
        fails.append("operationIds not covered: %s" % ", ".join(missing_ops))
    caop_defs = list(load_json(CAOP_SCHEMA)["$defs"])
    def_hits = {s.rsplit("/", 1)[-1] for s in strings}
    missing_defs = [d for d in caop_defs if d not in def_hits]
    if missing_defs:
        fails.append("definitions not covered: %s" % ", ".join(missing_defs))
    example_files = sorted(os.path.basename(f) for f in glob.glob(path("examples/*.json")))
    missing_ex = [e for e in example_files
                  if not any(s == e or s.endswith("/" + e) for s in strings)]
    if missing_ex:
        fails.append("example files not covered (by filename): %s" % ", ".join(missing_ex))

    removed = 0
    for trail, node in _walk(parity):
        if not isinstance(node, dict):
            continue
        status_vals = [str(v).lower() for k, v in node.items()
                       if k.lower() in ("status", "disposition", "parity", "verdict",
                                        "change", "maop", "maop_status", "outcome")
                       and isinstance(v, str)]
        if "removed" in status_vals:
            removed += 1
            just = (node.get("justification") or node.get("rationale")
                    or node.get("reason"))
            if not (isinstance(just, str) and just.strip()):
                fails.append("removed entry without justification at %s"
                             % ("/".join(trail) or "(root)"))
    info.append("%d removed entr%s" % (removed, "y" if removed == 1 else "ies"))
    return fails, info


NEUTRALITY_ALLOW = re.compile(r"reference implementation|generator", re.I)

# Exact CAOP v0.2 wire tokens that backward compatibility requires MAOP to
# keep, exempted only in the listed files. CREASURA_VAULT is a kept value of
# the AuthCustodian enum (coordinator decision, 2026-11-22).
NEUTRALITY_LEGACY_TOKENS = {
    "CREASURA_VAULT": (MAOP_SCHEMA, MAOP_OPENAPI_YAML, MAOP_OPENAPI_JSON),
}


def check_neutrality():
    fails, info = [], []
    targets = [MAOP_DOC, MAOP_SCHEMA, MAOP_OPENAPI_YAML, MAOP_OPENAPI_JSON]
    missing = [t for t in targets if not os.path.isfile(path(t))]
    ex_dir = path(MAOP_EXAMPLES_DIR)
    if os.path.isdir(ex_dir):
        for name in sorted(os.listdir(ex_dir)):
            if os.path.isfile(os.path.join(ex_dir, name)):
                targets.append(os.path.join(MAOP_EXAMPLES_DIR, name))
    else:
        missing.append(MAOP_EXAMPLES_DIR + "/")
    for m in missing:
        fails.append("missing: %s" % m)
    allowed = []
    for rel in targets:
        full = path(rel)
        if not os.path.isfile(full):
            continue
        with open(full, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        heading = ""
        for n, line in enumerate(lines, 1):
            if rel == MAOP_DOC and re.match(r"^#{1,6}\s", line):
                heading = line
            if re.search(r"operating system", line, re.I):
                fails.append("%s:%d: 'operating system': %s" % (rel, n, line.strip()[:120]))
            scan = line
            for token, files in NEUTRALITY_LEGACY_TOKENS.items():
                if rel in files and token in scan:
                    allowed.append("%s:%d: legacy token %s" % (rel, n, token))
                    scan = scan.replace(token, "")
            if re.search(r"creasura", scan, re.I):
                if rel == MAOP_DOC and (NEUTRALITY_ALLOW.search(line)
                                        or NEUTRALITY_ALLOW.search(heading)):
                    allowed.append("%s:%d: %s" % (rel, n, line.strip()[:120]))
                else:
                    fails.append("%s:%d: 'Creasura': %s" % (rel, n, line.strip()[:120]))
    info.append("%d file(s) scanned; %d allowed 'Creasura' mention(s)"
                % (sum(os.path.isfile(path(t)) for t in targets), len(allowed)))
    info.extend("  allowed " + a for a in allowed)
    return fails, info


TOPICS = [
    ("Act->Decide back-edge", r"\bAct\s*(?:→|->|⟶|to)\s*Decide\b"),
    ("Act->Coordinate back-edge", r"\bAct\s*(?:→|->|⟶|to)\s*Coordinate\b"),
    ("two-phase verification", r"two[- ]phase verification"),
    ("approval steering", r"approval steering"),
    ("isolation", r"\bisolation\b"),
    ("compaction", r"\bcompaction\b"),
    ("lazy discovery", r"\blazy(?:ily)?\b[\w\s-]{0,30}?\b(?:discovery|discover|advertis\w*|hydrat\w*)"),
    ("receipts", r"\breceipts?\b"),
    ("leases", r"\bleases?\b"),
    ("authority", r"\bauthority\b"),
    ("recovery", r"\brecover(?:y|s|ed|ing)?\b"),
]


def check_topics():
    fails, info = [], []
    full = require_file(MAOP_DOC)
    with open(full, encoding="utf-8") as fh:
        text = fh.read()
    for label, pattern in TOPICS:
        if not re.search(pattern, text, re.I):
            fails.append("topic not found: %s (pattern %s)" % (label, pattern))
    if not re.search(r"north\s*star", text, re.I):
        fails.append("topic not found: Northstar")
    # Northstar table rows A..K: markdown table rows whose first cell is the letter.
    rows = set(re.findall(r"^\s*\|\s*\**\s*([A-K])\b[^|]*\|", text, re.M))
    missing_rows = [c for c in "ABCDEFGHIJK" if c not in rows]
    if missing_rows:
        fails.append("Northstar table rows missing: %s" % ", ".join(missing_rows))
    info.append("%d topics + Northstar rows A-K checked" % len(TOPICS))
    return fails, info


CHECKS = [
    ("protected-hashes", "protected CAOP files match contract sha256", check_protected_hashes),
    ("protected-git", "other protected files unchanged versus HEAD", check_protected_git),
    ("schema", "MAOP schema is 2020-12, 110 defs, contract enums", check_schema),
    ("openapi", "MAOP OpenAPI 3.1, 23 ops, parity paths, refs resolve", check_openapi),
    ("caop-examples", "CAOP v0.2 examples validate against MAOP (backward compat)", check_caop_examples),
    ("maop-examples", "MAOP v1 examples validate", check_maop_examples),
    ("parity", "tests/parity.json counts and coverage", check_parity),
    ("neutrality", "vendor neutrality of MAOP files", check_neutrality),
    ("topics", "docs/maop-v1.md required topics", check_topics),
]


def select(only):
    if not only:
        return CHECKS
    wanted = []
    for item in only:
        for token in item.split(","):
            token = token.strip()
            if not token:
                continue
            match = None
            if token.isdigit() and 1 <= int(token) <= len(CHECKS):
                match = CHECKS[int(token) - 1]
            else:
                match = next((c for c in CHECKS if c[0] == token), None)
            if match is None:
                raise SystemExit("unknown check %r; use --list to see the names" % token)
            if match not in wanted:
                wanted.append(match)
    return wanted


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="MAOP v1 conformance checker")
    parser.add_argument("--only", action="append", metavar="CHECK",
                        help="run only these checks (name or 1-based number; "
                             "repeatable or comma-separated)")
    parser.add_argument("--list", action="store_true", help="list the checks and exit")
    args = parser.parse_args(argv)

    if args.list:
        for i, (name, desc, _) in enumerate(CHECKS, 1):
            print("%d. %-16s %s" % (i, name, desc))
        return 0

    failed = 0
    selected = select(args.only)
    for name, desc, func in selected:
        number = CHECKS.index((name, desc, func)) + 1
        try:
            fails, info = func()
        except CheckFailed as exc:
            fails, info = [str(exc)], []
        except Exception as exc:  # a bug or malformed input: report, do not crash
            fails, info = ["unexpected error: %s: %s" % (type(exc).__name__, exc)], []
        status = "FAIL" if fails else "PASS"
        summary = info[0] if info else ""
        print("%s %d %s: %s%s" % (status, number, name, desc,
                                  (" (%s)" % summary) if summary and not fails else ""))
        if fails:
            failed += 1
            for line in fails:
                print("      - " + line)
        for line in (info if fails else info[1:]):
            print("      " + line)
    print("%d/%d checks passed" % (len(selected) - failed, len(selected)))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
