#!/usr/bin/env python3
"""Generate the MAOP v1 parity record from the pinned CAOP v0.2 baseline.

Writes two files:

    tests/parity.json       machine-readable parity record  (subcommand: json)
    docs/maop-v1-parity.md  human-readable parity document  (subcommand: md)

Usage (from any directory; paths resolve from the repository root):

    python tests/parity_gen.py all              # regenerate both files in place
    python tests/parity_gen.py json             # only tests/parity.json
    python tests/parity_gen.py md               # only docs/maop-v1-parity.md
                                                # (rendered from tests/parity.json)
    python tests/parity_gen.py all --out DIR    # write DIR/tests/parity.json and
                                                # DIR/docs/maop-v1-parity.md instead

Every CAOP baseline file is read from git at the pinned commit BASE, not from
the working tree, so later edits (for example a status banner in SPEC.md)
cannot shift line numbers. The git history must contain BASE; a fresh clone
of the repository does. The MAOP contracts (schema/maop-v1.schema.json and
openapi/maop-v1.openapi.yaml) are read from the working tree and compared
structurally with the baseline:

    kept     the structure is identical (descriptions, titles and examples
             are ignored);
    refined  the change is additive only: new optional properties, new enum
             values, new oneOf/anyOf branches, new response codes or optional
             parameters, or annotation-only keywords;
    CHECK    anything else (a removed property, a new required property, a
             new constraint keyword, a changed value); a reviewer must look.

The output is deterministic: no timestamps, sorted sets, stable key order.
tests/validate.py check 10 (parity-reproducible) regenerates both files into
a temporary directory and requires them to be byte-identical to the
committed ones.

Dependencies: the standard library, jsonschema (>= 4.18), pyyaml and git.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

import jsonschema
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TAIL = os.path.join(HERE, "parity_tail.md")
PARITY_JSON = "tests/parity.json"
PARITY_MD = "docs/maop-v1-parity.md"
COMMAND = "python tests/parity_gen.py all"

BASE = "8c7bd07939171efc2d39079bd018904175ea8db2"
PROTECTED = [
    "openapi/caop-v0.1.2.openapi.json", "openapi/caop-v0.1.2.openapi.yaml",
    "openapi/caop-v0.1.openapi.json", "openapi/caop-v0.1.openapi.yaml",
    "openapi/caop-v0.2.openapi.json", "openapi/caop-v0.2.openapi.yaml",
    "schema/caop-v0.1.2.schema.json", "schema/caop-v0.1.schema.json",
    "schema/caop-v0.2.schema.json",
]
EXPECTED_SHA = {
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
EXPECTED_COUNTS = (17, 95, 71)  # operations, definitions, examples


class GenError(Exception):
    pass


# ---------------------------------------------------------------- git / io

def git_show(path: str) -> bytes:
    proc = subprocess.run(["git", "-C", REPO, "show", f"{BASE}:{path}"], capture_output=True)
    if proc.returncode != 0:
        raise GenError(f"git show {BASE[:7]}:{path} failed (is the baseline commit in the "
                       f"history? try 'git fetch --unshallow'): {proc.stderr.decode().strip()}")
    return proc.stdout


def git_ls(prefix: str) -> list:
    proc = subprocess.run(["git", "-C", REPO, "ls-tree", "--name-only", BASE, prefix],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise GenError(f"git ls-tree {BASE[:7]} {prefix} failed: {proc.stderr.strip()}")
    return sorted(proc.stdout.split())


class _NoDatesLoader(yaml.SafeLoader):
    """SafeLoader that keeps timestamps as strings (JSON has no date type)."""


_NoDatesLoader.yaml_implicit_resolvers = {
    key: [r for r in resolvers if r[0] != "tag:yaml.org,2002:timestamp"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def load_yaml(data):
    return yaml.load(data, Loader=_NoDatesLoader)


def write_text(out_dir: str, rel: str, text: str) -> str:
    full = os.path.join(out_dir, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return full


# ---------------------------------------------------------------- comparison

REF = re.compile(r"schemas/(\w+)|\$defs/(\w+)")

# Keywords that only annotate; adding one never rejects a valid instance.
ANNOTATION_KEYS = {"description", "title", "examples", "$comment", "default", "deprecated",
                   "readOnly", "writeOnly", "$id", "$anchor"}
# Lists whose growth only admits more instances.
WIDENING_LISTS = {"oneOf", "anyOf", "type"}


def refs(x) -> list:
    return sorted({a or b for a, b in REF.findall(json.dumps(x))})


def strip_text(x):
    """Drop description/title/examples so only structure is compared."""
    if isinstance(x, dict):
        return {k: strip_text(v) for k, v in x.items()
                if k not in ("description", "title", "examples", "$comment")}
    if isinstance(x, list):
        return [strip_text(v) for v in x]
    if isinstance(x, str):
        return re.sub(r"#/components/schemas/|#/\$defs/", "#/", x)
    return x


def additive_diff(old, new, path=""):
    """Compare schema structure old -> new. Return (additions, violations).

    An addition keeps every instance that was valid against `old` valid
    against `new`, and is the kind of change the parity rule allows (new
    optional properties, new enum values, new oneOf/anyOf branches, new
    annotation keywords). A violation is any other change.
    """
    adds, bad = [], []
    if isinstance(old, dict) and isinstance(new, dict):
        for k in old:
            if k not in new:
                bad.append(f"{path}/{k} removed")
                continue
            o, n = old[k], new[k]
            if k == "required" and isinstance(o, list) and isinstance(n, list):
                if set(n) - set(o):
                    bad.append(f"{path}/required gained {sorted(set(n) - set(o))}")
                if set(o) - set(n):
                    bad.append(f"{path}/required lost {sorted(set(o) - set(n))}")
            elif k == "enum" and isinstance(o, list) and isinstance(n, list):
                lost = [v for v in o if v not in n]
                gained = [v for v in n if v not in o]
                if lost:
                    bad.append(f"{path}/enum lost {sorted(map(str, lost))}")
                if gained:
                    adds.append(f"{path}/enum +{sorted(map(str, gained))}")
            elif k in ("properties", "$defs", "patternProperties") and isinstance(o, dict) \
                    and isinstance(n, dict):
                for name in o:
                    if name not in n:
                        bad.append(f"{path}/{k}/{name} removed")
                    else:
                        a, b = additive_diff(o[name], n[name], f"{path}/{k}/{name}")
                        adds += a
                        bad += b
                extra = sorted(set(n) - set(o))
                if extra:
                    (adds if k != "patternProperties" else bad).append(f"{path}/{k} +{extra}")
            elif k in WIDENING_LISTS and isinstance(o, list) and isinstance(n, list):
                if len(n) < len(o):
                    bad.append(f"{path}/{k} length {len(o)}->{len(n)}")
                elif k == "type":
                    if not set(o) <= set(n):
                        bad.append(f"{path}/type changed")
                    elif set(n) - set(o):
                        adds.append(f"{path}/type +{sorted(set(n) - set(o))}")
                else:
                    for i, (a0, b0) in enumerate(zip(o, n)):
                        a, b = additive_diff(a0, b0, f"{path}/{k}/{i}")
                        adds += a
                        bad += b
                    if len(n) > len(o):
                        adds.append(f"{path}/{k} +{len(n) - len(o)} branch(es)")
            else:
                a, b = additive_diff(o, n, f"{path}/{k}")
                adds += a
                bad += b
        for k in new:
            if k in old:
                continue
            if k in ANNOTATION_KEYS or k.startswith("x-"):
                adds.append(f"{path}/{k} added")
            elif k == "properties" and isinstance(new[k], dict):
                adds.append(f"{path}/properties +{sorted(new[k])}")
            else:
                bad.append(f"{path}/{k} constraint added")
    elif isinstance(old, list) and isinstance(new, list):
        if len(old) != len(new):
            bad.append(f"{path} length {len(old)}->{len(new)}")
        for i, (a0, b0) in enumerate(zip(old, new)):
            a, b = additive_diff(a0, b0, f"{path}/{i}")
            adds += a
            bad += b
    elif old != new:
        bad.append(f"{path} changed")
    return adds, bad


# ---------------------------------------------------------------- hand-written judgements

LINE_TOPIC = {80: "Two-phase verification and approval steering", 91: "Receipts and evidence",
              92: "Receipts and evidence", 538: "Two-phase verification and approval steering"}

# SPEC section prefix -> docs/maop-v1.md topic (first match wins, so longer prefixes first).
SECTION_TOPIC = [
    ("14.2", "State: epistemic status, freshness and causal invalidation"),
    ("14.3", "Guards: policy and pre-commit hooks (durable guards)"),
    ("14.4", "Capabilities: registration and lazy discovery"),
    ("14.5.2", "Act: dispatch and host execution"),
    ("14.5.3", "Leases and fencing"),
    ("14.5.4", "Receipts and evidence"),
    ("14.5.5", "Event-driven re-evaluation: pulse and triggers"),
    ("14.5", "Act: dispatch and host execution"),
    ("14.6", "Bindings: compact tools and REST"),
    ("14.7", "Bindings: host operating prompt"),
    ("14.8", "Compatibility and migration"),
    ("14.1", "Conformance levels"),
    ("15.1", "Two-phase verification and approval steering"),
    ("15.2", "Sub-agent isolation, compaction and lazy discovery"),
    ("15", "Two-phase verification and approval steering"),
    ("12.4", "Two-phase verification and approval steering"),
    ("12.2", "Authority"),
    ("12", "Authority"),
    ("13", "Bindings: compact tools and REST"),
    ("11", "Overview and vendor neutrality"),
    ("10", "Bindings: compact tools and REST"),
    ("9", "Conformance levels"),
    ("8", "Event-driven re-evaluation: pulse and triggers"),
    ("7", "Authority"),
    ("6", "Capabilities: registration and lazy discovery"),
    ("5", "Child lifecycle (execution state machine)"),
    ("4", "Outer supervision lifecycle"),
    ("3", "Outer supervision lifecycle"),
    ("2", "Core abstractions"),
    ("1", "Overview and vendor neutrality"),
]

# Per-line judgement for the upper-case normative statements (by baseline SPEC.md line number).
G_JUDGE = {
    789: ("kept", "Same three adoption states and separate freshness value (EpistemicStatus, Freshness)."),
    845: ("refined", "Obligation unchanged; subject reworded from 'the Creasura kernel' to 'the runtime' "
                     "(vendor-neutral). MAOP also treats each invalidation as a trigger for supervision.evaluate "
                     "(event-driven re-evaluation of durable guards)."),
    850: ("kept", "Same max_invalidation_subgraph limit and CAOP_413_INVALIDATION_SUBGRAPH_TOO_LARGE error code."),
    895: ("kept", "Same CAOP_422_PRECOMMIT_UNKNOWN_FACT_ID rejection; MAOP models it as an evidence Guard."),
    925: ("kept", "Same CapabilityRegistration obligations; agents.register advertises capabilities lazily."),
    955: ("kept", "Same Stage-1 continuation envelope (DispatchDirective)."),
    996: ("refined", "Same one-open-lease rule and CAOP_409_UNSETTLED_EXECUTION_LEASE; MAOP adds fenced leases "
                     "(Lease.fencing_token, monotonic) and leases.renew, so a stale holder cannot settle."),
    1252: ("refined", "Normative block kept verbatim; the obligation is generalised from two named vendor hosts to "
                      "any conversational host (vendor names become informative examples)."),
    1386: ("kept", "Same steering rule; MAOP states it as an authority Guard (a delta can only narrow an AuthorityGrant)."),
    1398: ("refined", "Same provenance-pointer rule; MAOP adds Delegation (isolation policy, budget, authority subset) "
                      "and Receipt.causal_parents so pruned traces stay traceable."),
}
EDITORIAL_REF = {1494: 1252, 1502: 789, 1511: 845, 1513: 895, 1541: 1386, 1543: 1398}

ADD_OPS = [
    ("POST", "/maop/v1/agents", "agents.register",
     "CAOP has principals but no agent identity: roles and capabilities could not be declared per agent, so "
     "separation of duties (implementer != reviewer != approver) could not be checked. Capabilities are "
     "advertised as stubs and hydrated lazily, preserving v0.2 lazy discovery."),
    ("POST", "/maop/v1/delegations", "delegations.create",
     "v0.2 isolates child work (parent_work_id, isolation_policy) but only through stage_work. A first-class "
     "delegation lets a supervisor hand work to another agent with an isolation policy, a budget and an "
     "authority subset that can only narrow the parent's authority (Act->Coordinate edge)."),
    ("GET", "/maop/v1/delegations/{delegation_id}", "delegations.get",
     "Read model for a delegation and its child lifecycle state, so a supervisor can re-evaluate without "
     "polling executions one by one."),
    ("POST", "/maop/v1/leases/{lease_id}/renew", "leases.renew",
     "v0.2 leases have a timeout but no renewal or fencing. Renewal with a monotonic fencing_token prevents a "
     "holder whose lease expired from settling a receipt after another holder took over (split-brain)."),
    ("GET", "/maop/v1/receipts/{receipt_id}", "receipts.get",
     "Receipts were only returned inline by settle_receipt. A stable read path with idempotency_key, outcome "
     "(including outcome_unknown) and causal_parents makes recovery and audit possible after a crash."),
    ("POST", "/maop/v1/supervision/{work_id}/evaluate", "supervision.evaluate",
     "CAOP re-evaluates only on pulse. Event-driven re-evaluation of durable guards returns the next outer "
     "transition (including Act->Decide, Act->Coordinate, Verify->Act and any->Recover) with the guards that "
     "passed and failed."),
]
ADD_DEFS = [
    ("AgentIdentity", "Stable identity of an agent (who acts), distinct from PrincipalRef (who is accountable)."),
    ("AgentRole", "Enum supervisor, planner, implementer, reviewer, verifier, approver, observer: needed for separation-of-duties guards."),
    ("AgentRegistration", "Request/response body of agents.register: identity, roles and lazily advertised capability stubs."),
    ("Delegation", "First-class supervisor-to-child work record: isolation policy, budget, authority subset, child lifecycle state."),
    ("DelegationCreate", "Request body of delegations.create."),
    ("AuthorityGrant", "Explicit, expiring, scoped authority with trust_level (T0_relayed, T1_attested); delegation and steering can only narrow it."),
    ("Lease", "Fenced execution lease (lease_id, holder, fencing_token, expires_at); generalises OpenLease."),
    ("LeaseRenewal", "Request body of leases.renew; the runtime rejects a stale fencing_token."),
    ("Receipt", "Durable action receipt (idempotency_key, outcome incl. outcome_unknown, evidence_refs, causal_parents) for audit and recovery."),
    ("SupervisionStage", "Enum of outer-lifecycle stages observe ... closed, including recover, so transitions are machine-checkable."),
    ("ChildLifecycleState", "Enum of child-work states proposed ... expired, mapping delegated work onto the inner lifecycle."),
    ("Guard", "Durable guard (authority, policy, evidence, freshness, lease, separation_of_duties, budget) re-evaluated on events, not only at commit."),
    ("SupervisionEvaluation", "Request/response body of supervision.evaluate."),
    ("TransitionDecision", "Result of evaluation: from_stage, to_stage, trigger, guards_passed, guards_failed, next_action."),
    ("CausalEvidence", "Evidence item with digest, derived_from and bitemporal times, linking receipts, facts and guards causally."),
]

VENDOR = re.compile(r"Creasura|\bOS\b|operating system", re.I)
KW = re.compile(r"\b(MUST NOT|MUST|SHALL NOT|SHALL|SHOULD NOT|SHOULD|REQUIRED)\b")
KW_LC = re.compile(r"\b(must not|must|should not|should|shall)\b")


def topic_for(h):
    m = re.match(r"#+\s+(\d+(?:\.\d+)*)", h or "")
    if not m:
        return "Overview and vendor neutrality"
    num = m.group(1)
    for pre, t in SECTION_TOPIC:
        if num == pre or num.startswith(pre + "."):
            return t
    return "Overview and vendor neutrality"


def tally(items):
    t = {"kept": 0, "refined": 0, "replaced": 0, "removed": 0}
    for it in items:
        t[it] = t.get(it, 0) + 1
    return t


# ---------------------------------------------------------------- json

def build_parity() -> dict:
    # Baseline pin.
    pin = []
    for p in PROTECTED:
        base_sha = hashlib.sha256(git_show(p)).hexdigest()
        if base_sha != EXPECTED_SHA[p]:
            raise GenError(f"baseline sha256 mismatch for {p} at {BASE[:7]}")
        wt = os.path.join(REPO, p)
        wt_sha = None
        if os.path.exists(wt):
            with open(wt, "rb") as fh:
                wt_sha = hashlib.sha256(fh.read()).hexdigest()
        pin.append({"path": p, "sha256": base_sha, "unchanged_in_working_tree": wt_sha == base_sha})

    schema = json.loads(git_show("schema/caop-v0.2.schema.json"))
    defs = schema["$defs"]
    d1 = json.loads(git_show("schema/caop-v0.1.schema.json"))
    d1 = d1.get("$defs", d1.get("definitions", {}))
    d12 = json.loads(git_show("schema/caop-v0.1.2.schema.json"))
    d12 = d12.get("$defs", d12.get("definitions", {}))
    oapi = load_yaml(git_show("openapi/caop-v0.2.openapi.yaml"))
    spec_lines = git_show("SPEC.md").decode("utf-8").splitlines()

    # MAOP contracts from the working tree (optional).
    maop_schema_path = os.path.join(REPO, "schema/maop-v1.schema.json")
    maop_oapi_path = os.path.join(REPO, "openapi/maop-v1.openapi.yaml")
    maop_defs = maop_oapi = None
    if os.path.exists(maop_schema_path):
        with open(maop_schema_path, encoding="utf-8") as fh:
            maop_defs = json.load(fh)["$defs"]
    if os.path.exists(maop_oapi_path):
        with open(maop_oapi_path, encoding="utf-8") as fh:
            maop_oapi = load_yaml(fh)

    # Operations.
    ops, op_by_def = {}, {}
    for p, item in oapi["paths"].items():
        for m, op in item.items():
            if not isinstance(op, dict) or "operationId" not in op:
                continue
            oid = op["operationId"]
            req = refs(op.get("requestBody", {}))
            resp = {c: refs(r) for c, r in op.get("responses", {}).items()}
            for d in req + [x for v in resp.values() for x in v]:
                op_by_def.setdefault(d, set()).add(oid)
            mpath = "/maop" + p
            status, note = "kept", ("Same operationId, method, sub-path, request and response "
                                    "definitions and semantics under the /maop/v1 prefix.")
            if maop_oapi is not None:
                mop = (maop_oapi.get("paths", {}).get(mpath) or {}).get(m)
                if not mop or mop.get("operationId") != oid:
                    status, note = "CHECK", f"Not found in openapi/maop-v1.openapi.yaml at {m.upper()} {mpath}."
                else:
                    mreq = refs(mop.get("requestBody", {}))
                    mresp = {c: refs(r) for c, r in mop.get("responses", {}).items()}
                    lost = [c for c in resp if c not in mresp]
                    if req != mreq or lost or any(resp[c] != mresp.get(c) for c in resp):
                        status, note = "CHECK", "Request/response definitions differ from CAOP v0.2."
                    else:
                        extra = sorted(set(mresp) - set(resp))
                        pname = lambda q: q.get("name", q.get("$ref", ""))  # noqa: E731
                        extra_params = sorted({pname(q) for q in mop.get("parameters", [])}
                                              - {pname(q) for q in op.get("parameters", [])})
                        if extra or extra_params:
                            status = "refined"
                            note += (" Additive only:"
                                     + (f" new response codes {extra};" if extra else "")
                                     + (f" new optional parameters {extra_params};" if extra_params else ""))
            ops[oid] = {
                "caop": {"method": m.upper(), "path": p},
                "maop": {"method": m.upper(), "path": mpath, "operationId": oid},
                "status": status,
                "summary": op.get("summary"),
                "request": req,
                "responses": resp,
                "note": note,
            }

    # Definitions.
    example_files = [os.path.basename(f) for f in git_ls("examples/") if f.endswith(".json")]
    example_names = {f[:-5] for f in example_files}
    definitions = {}
    for name, d in defs.items():
        intro = "v0.1" if name in d1 else "v0.1.2" if name in d12 else "v0.2"
        used = sorted(op_by_def.get(name, []))
        desc = d.get("description", "")
        status = "kept"
        parts = [f"Introduced in CAOP {intro}."]
        if used:
            parts.append(f"Used directly by {', '.join(used)}.")
        if name in example_names:
            parts.append(f"Example: examples/{name}.json.")
        if maop_defs is not None:
            if name not in maop_defs:
                status = "CHECK"
                parts.append("MISSING from schema/maop-v1.schema.json.")
            else:
                adds, bad = additive_diff(strip_text(d), strip_text(maop_defs[name]))
                if bad:
                    status = "CHECK"
                    parts.append("Non-additive change: " + "; ".join(bad[:5]))
                elif adds:
                    status = "refined"
                    parts.append("Additive refinement: " + "; ".join(sorted(set(adds))[:5]) + ".")
                else:
                    parts.append("Structure identical in schema/maop-v1.schema.json.")
                if not bad and maop_defs[name].get("description", "") != desc:
                    parts.append("Description reworded (vendor-neutral)"
                                 + (", no structural change." if not adds else "."))
        else:
            parts.append("Copied unchanged under the same name (contract parity rule).")
        if VENDOR.search(desc) and status == "kept" and maop_defs is None:
            parts.append("Baseline description uses vendor/OS wording; MAOP text is vendor-neutral.")
        definitions[name] = {"maop_name": name, "status": status, "introduced_in": intro,
                             "note": " ".join(parts)}

    # Examples.
    validator_cls = jsonschema.validators.validator_for(schema)
    examples = {}
    for f in example_files:
        name = f[:-5]
        inst = json.loads(git_show("examples/" + f))
        sub = {"$schema": schema["$schema"], "$defs": defs, "$ref": f"#/$defs/{name}"}
        errs = sorted(validator_cls(sub).iter_errors(inst), key=str)
        examples[f] = {
            "definition": name,
            "definition_exists": name in defs,
            "valid_against_caop_v0.2": not errs,
            "maop_status": "kept" if not errs else "CHECK",
            "note": (f"Validates against #/$defs/{name} in CAOP v0.2 and therefore against the same-named "
                     f"MAOP v1 definition (kept or additively refined). File stays at examples/{f}, unchanged."
                     if not errs else f"Does not validate: {errs[0].message[:120]}"),
        }

    # Guarantees.
    heading = num_h = cur_h = None
    in_code = False
    guarantees, supplementary = [], []
    editorial_start = next(i for i, l in enumerate(spec_lines) if l.startswith("## Editorial history"))
    for i, line in enumerate(spec_lines):
        ln = i + 1
        s = line.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if line.startswith("#") and not in_code:
            heading = line.lstrip("#").strip()
            if re.match(r"#+\s+\d", line):
                num_h = line
            cur_h = num_h if num_h else line
            continue
        if KW.search(line):
            g = {"id": None, "spec_line": ln, "spec_section": heading,
                 "keywords": sorted(set(KW.findall(line))), "text": s}
            if i >= editorial_start:
                ref = EDITORIAL_REF.get(ln)
                g.update(kind="editorial_record", status="kept",
                         maop_section="Compatibility and migration (CAOP history is frozen)",
                         note=(f"Editorial-history entry recording the change that produced SPEC.md line {ref}; "
                               "kept as frozen history. Its normative content is tracked by that line's guarantee."),
                         records_line=ref)
            else:
                st, note = G_JUDGE.get(ln, ("CHECK", "No judgement recorded."))
                g.update(kind="normative", status=st, maop_section=LINE_TOPIC.get(ln, topic_for(cur_h)),
                         note=note, spec_numbered_section=(cur_h or "").lstrip("#").strip())
            guarantees.append(g)
        elif KW_LC.search(line) and not in_code and i < editorial_start and not s.startswith("|"):
            vend = bool(VENDOR.search(line))
            supplementary.append({
                "id": None, "spec_line": ln, "spec_section": heading, "text": s,
                "maop_section": LINE_TOPIC.get(ln, topic_for(cur_h)),
                "spec_numbered_section": (cur_h or "").lstrip("#").strip(),
                "status": "refined" if vend else "kept",
                "note": ("Kept; wording made vendor-neutral (no vendor or operating-system subject)." if vend
                         else "Kept unchanged in meaning."),
            })

    normative = [g for g in guarantees if g["kind"] == "normative"]
    by_line = {}
    for n, g in enumerate(guarantees, 1):
        g["id"] = f"G-{n:03d}"
        by_line[g["spec_line"]] = g["id"]
    for g in guarantees:
        if g["kind"] == "editorial_record":
            g["records_guarantee"] = by_line.get(g.pop("records_line"))
    for n, g in enumerate(supplementary, 1):
        g["id"] = f"S-{n:03d}"

    additions = {
        "operations": [{"method": m, "path": p, "operationId": o, "justification": j,
                        "present_in_maop_openapi": (None if maop_oapi is None else
                                                    bool((maop_oapi.get("paths", {}).get(p) or {})
                                                         .get(m.lower(), {}).get("operationId") == o))}
                       for m, p, o, j in ADD_OPS],
        "definitions": [{"name": n, "justification": j,
                         "present_in_maop_schema": None if maop_defs is None else n in maop_defs}
                        for n, j in ADD_DEFS],
    }

    out = {
        "title": "MAOP v1 parity with CAOP v0.2",
        "maop_version": "1.0.0-draft.1",
        "generated_by": f"tests/parity_gen.py (regenerate with: {COMMAND}); "
                        f"baseline read from git at {BASE}; output is deterministic and "
                        "checked by tests/validate.py check 10 (parity-reproducible)",
        "baseline": {"repository_commit": BASE, "spec": "SPEC.md (CAOP v0.2)", "files": pin},
        "maop_contracts_compared": {
            "schema/maop-v1.schema.json": maop_defs is not None,
            "openapi/maop-v1.openapi.yaml": maop_oapi is not None,
        },
        "counts": {
            "operations": len(ops), "definitions": len(definitions), "examples": len(examples),
            "guarantees": len(guarantees), "guarantees_normative": len(normative),
            "guarantees_editorial_record": len(guarantees) - len(normative),
            "supplementary_requirements": len(supplementary),
            "additions_operations": len(ADD_OPS), "additions_definitions": len(ADD_DEFS),
            "maop_operations_total": len(ops) + len(ADD_OPS),
            "maop_definitions_total": len(definitions) + len(ADD_DEFS),
        },
        "status_summary": {
            "operations": tally(v["status"] for v in ops.values()),
            "definitions": tally(v["status"] for v in definitions.values()),
            "examples": tally(v["maop_status"] for v in examples.values()),
            "guarantees": tally(g["status"] for g in guarantees),
            "supplementary_requirements": tally(g["status"] for g in supplementary),
        },
        "operations": ops,
        "definitions": definitions,
        "examples": examples,
        "guarantees": guarantees,
        "supplementary_requirements": supplementary,
        "additions": additions,
    }
    if (len(ops), len(definitions), len(examples)) != EXPECTED_COUNTS:
        raise GenError(f"baseline counts {out['counts']} differ from {EXPECTED_COUNTS}")
    return out


def render_json(parity: dict) -> str:
    return json.dumps(parity, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------- markdown

def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def _names(items):
    return ", ".join(f"`{n}`" for n in items)


def generation_note(d: dict) -> str:
    cmp = d["maop_contracts_compared"]
    if not all(cmp.values()):
        missing = [k for k, v in cmp.items() if not v]
        return ("> **Generation note.** When this file was generated, " + ", ".join(f"`{m}`" for m in missing)
                + " did not exist yet, so operation and definition statuses follow the parity rule above. "
                f"Re-running `{COMMAND}` after those files land compares them structurally with CAOP v0.2: "
                "an identical structure stays `kept`, an additive change becomes `refined`, and anything "
                "else is flagged `CHECK` for review.")
    ops, defs = d["operations"], d["definitions"]
    n_ops, n_defs = len(ops), len(defs)
    parts = ["> **Generation note.** Statuses were derived by structurally comparing `schema/maop-v1.schema.json` "
             "and `openapi/maop-v1.openapi.yaml` with CAOP v0.2, ignoring descriptions."]
    op_ref = [k for k, v in ops.items() if v["status"] == "refined"]
    op_chk = [k for k, v in ops.items() if v["status"] not in ("kept", "refined")]
    if not op_ref and not op_chk:
        parts.append(f"All {n_ops} operations have the same method, sub-path, request body and response "
                     "codes and bodies.")
    else:
        parts.append(f"{n_ops - len(op_ref) - len(op_chk)} of {n_ops} operations have the same method, sub-path, "
                     "request body and response codes and bodies.")
        if op_ref:
            parts.append(f"{len(op_ref)} are refined additively ({_names(op_ref)}).")
        if op_chk:
            parts.append(f"{len(op_chk)} need review ({_names(op_chk)}).")
    def_ref = [k for k, v in defs.items() if v["status"] == "refined"]
    def_chk = [k for k, v in defs.items() if v["status"] not in ("kept", "refined")]
    rew = [k for k, v in defs.items() if v["status"] == "kept" and "reworded" in v["note"]]
    if not def_ref and not def_chk:
        parts.append(f"All {n_defs} definitions are structurally identical, so none needed an additive "
                     "refinement.")
    else:
        parts.append(f"{n_defs - len(def_ref) - len(def_chk)} of {n_defs} definitions are structurally "
                     "identical.")
        if def_ref:
            parts.append(f"{len(def_ref)} are refined additively (new optional properties or enum values only; "
                         f"see the Note column): {_names(def_ref)}.")
        if def_chk:
            parts.append(f"{len(def_chk)} have a non-additive change and need review: {_names(def_chk)}.")
    if rew:
        parts.append(f"{len(rew)} kept definitions have reworded, vendor-neutral descriptions only "
                     f"({_names(rew)}), and their status stays `kept`.")
    parts.append(f"Re-run `{COMMAND}` after any contract change; an additive change shows as `refined`, "
                 "and any other change is flagged `CHECK`.")
    return " ".join(parts)


def render_md(d: dict) -> str:
    with open(TAIL, encoding="utf-8") as fh:
        tail = fh.read()
    c, ss = d["counts"], d["status_summary"]
    L = []
    w = L.append
    w("# MAOP v1 parity with CAOP v0.2")
    w("")
    w("**Status:** DRAFT · **MAOP version:** 1.0.0-draft.1 · **Baseline:** CAOP v0.2 at commit "
      f"`{d['baseline']['repository_commit']}`")
    w("")
    w("This document shows that MAOP v1 (Multi-Agent Orchestration Protocol) covers every operation, schema "
      "definition, example and normative guarantee of CAOP v0.2, and lists what MAOP adds. The machine-readable "
      "version is [`tests/parity.json`](../tests/parity.json). Both are generated from the files at the pinned "
      "baseline commit, not typed by hand: the generator, [`tests/parity_gen.py`](../tests/parity_gen.py), reads "
      "`SPEC.md`, `schema/caop-v0.2.schema.json`, `openapi/caop-v0.2.openapi.yaml` and `examples/*.json` from "
      "git at that commit, validates every example, and extracts every line of `SPEC.md` that contains MUST, "
      "MUST NOT, SHALL, SHOULD or REQUIRED. Line numbers refer to `SPEC.md` at the baseline commit. Regenerate "
      f"both files with `{COMMAND}`; see [Regenerating](#regenerating).")
    w("")
    w("The specification itself is [`docs/maop-v1.md`](maop-v1.md); migration and compatibility are in "
      "[`docs/maop-v1-migration.md`](maop-v1-migration.md).")
    w("")
    w("## Parity rule")
    w("")
    w("MAOP v1 keeps all 17 CAOP v0.2 operations with the same operationIds, methods, sub-paths, request and "
      "response bodies and semantics, under the path prefix `/maop/v1` instead of `/v1`. It keeps all 95 CAOP v0.2 "
      "definitions under the same names; a definition may only be refined additively (new optional properties, new "
      "enum values, vendor-neutral descriptions), never weakened. Every CAOP v0.2 example is therefore a valid "
      "instance of the same-named MAOP definition. Parity holds by construction; the improvements are additive.")
    w("")
    w("## Baseline pin")
    w("")
    w(f"Commit: `{d['baseline']['repository_commit']}` (branch `main` when MAOP work started).")
    w("")
    w("These nine historical contract files are frozen. The sha256 values were computed from the files at the "
      "baseline commit, and the working tree was checked against them when this file was generated.")
    w("")
    w("| File | sha256 | Unchanged in working tree |")
    w("|---|---|---|")
    for f in d["baseline"]["files"]:
        w(f"| `{f['path']}` | `{f['sha256']}` | {'yes' if f['unchanged_in_working_tree'] else 'NO'} |")
    w("")
    w("## Summary")
    w("")
    w("| Category | CAOP v0.2 count | Kept | Refined | Replaced | Removed |")
    w("|---|---|---|---|---|---|")
    rows = [("Operations", c["operations"], ss["operations"]),
            ("Schema definitions", c["definitions"], ss["definitions"]),
            ("Examples", c["examples"], ss["examples"]),
            ("Normative guarantees (MUST/SHALL/SHOULD/REQUIRED lines)", c["guarantees"], ss["guarantees"]),
            ("Supplementary lower-case requirements (informative check)", c["supplementary_requirements"],
             ss["supplementary_requirements"])]
    for name, n, t in rows:
        w(f"| {name} | {n} | {t['kept']} | {t['refined']} | {t['replaced']} | {t['removed']} |")
    checks = sum(t.get("CHECK", 0) for t in ss.values())
    w("")
    w(f"Nothing is removed or replaced, so no removal needs a justification. Of the {c['guarantees']} guarantee "
      f"lines, {c['guarantees_normative']} are normative statements and {c['guarantees_editorial_record']} are "
      "entries in SPEC.md's editorial history that quote those statements; the history entries are tracked so "
      "the count matches a plain keyword search, and each points at the guarantee it records."
      + (f" **{checks} entries are flagged `CHECK` and need review.**" if checks else ""))
    w("")
    w(f"MAOP v1 adds {c['additions_operations']} operations and {c['additions_definitions']} definitions, for "
      f"{c['maop_operations_total']} operations and {c['maop_definitions_total']} definitions in total.")
    w("")
    w(generation_note(d))
    w("")
    w("## Operations")
    w("")
    w("| # | operationId | CAOP v0.2 | MAOP v1 | Request | Success response | Status |")
    w("|---|---|---|---|---|---|---|")
    for i, (oid, o) in enumerate(d["operations"].items(), 1):
        ok = [f"{k}: {', '.join(v)}" for k, v in o["responses"].items() if k.startswith("2")]
        w(f"| {i} | `{oid}` | `{o['caop']['method']} {o['caop']['path']}` | `{o['maop']['method']} {o['maop']['path']}` "
          f"| {', '.join(o['request']) or 'none'} | {'; '.join(ok)} | {o['status']} |")
    w("")
    w("Every operation keeps its error responses (Error envelope, same codes). Note for all rows: "
      + d["operations"]["observations.ingest"]["note"])
    w("")
    w("## Schema definitions")
    w("")
    w("| # | Definition | MAOP name | Introduced | Status | Note |")
    w("|---|---|---|---|---|---|")
    for i, (n, v) in enumerate(d["definitions"].items(), 1):
        w(f"| {i} | `{n}` | `{v['maop_name']}` | {v['introduced_in']} | {v['status']} | {esc(v['note'])} |")
    w("")
    w("## Examples")
    w("")
    w("Each example file is matched by filename to the definition of the same name and validated against "
      "CAOP v0.2 (JSON Schema 2020-12) during generation. "
      f"{sum(1 for e in d['examples'].values() if e['valid_against_caop_v0.2'])} of {c['examples']} validate.")
    w("")
    w("| # | File | Definition | Valid (v0.2) | MAOP status |")
    w("|---|---|---|---|---|")
    for i, (f, e) in enumerate(d["examples"].items(), 1):
        w(f"| {i} | `examples/{f}` | `{e['definition']}` | {'yes' if e['valid_against_caop_v0.2'] else 'NO'} "
          f"| {e['maop_status']} |")
    w("")
    w("The files stay in `examples/` unchanged. New MAOP examples live in `examples/maop-v1/`.")
    w("")
    w("## Normative guarantees")
    w("")
    w("MAOP section names refer to topics in [`docs/maop-v1.md`](maop-v1.md).")
    w("")
    for g in d["guarantees"]:
        w(f"### {g['id']} · SPEC.md line {g['spec_line']} · {g['status']}")
        w("")
        sec = g.get("spec_numbered_section") or g["spec_section"]
        under = (f" (under “{esc(g['spec_section'])}”)"
                 if g.get("spec_numbered_section") and g["spec_section"] != g["spec_numbered_section"] else "")
        w(f"- **CAOP section:** {esc(sec)}{under}")
        w(f"- **Kind:** {g['kind'].replace('_', ' ')}; keywords: {', '.join(g['keywords'])}")
        w(f"- **MAOP mapping:** {g['maop_section']}")
        w(f"- **Note:** {g['note']}" + (f" (see {g['records_guarantee']})" if g.get("records_guarantee") else ""))
        w("")
        w("> " + g["text"])
        w("")
    w("## Supplementary lower-case requirements")
    w("")
    w("Not counted as guarantees (the keyword rule is upper case), but checked so that no lower-case "
      "obligation in the normative text is lost. Lines in code blocks and in the editorial history are skipped.")
    w("")
    w("| ID | Line | CAOP section | Text | MAOP mapping | Status |")
    w("|---|---|---|---|---|---|")
    for g in d["supplementary_requirements"]:
        w(f"| {g['id']} | {g['spec_line']} | {esc(g['spec_numbered_section'])} | {esc(g['text'])} "
          f"| {g['maop_section']} | {g['status']} |")
    w("")
    w("## Additions")
    w("")
    w("### New operations")
    w("")
    w("| operationId | Method and path | Justification |")
    w("|---|---|---|")
    for a in d["additions"]["operations"]:
        w(f"| `{a['operationId']}` | `{a['method']} {a['path']}` | {esc(a['justification'])} |")
    w("")
    w("### New definitions")
    w("")
    w("| Definition | Justification |")
    w("|---|---|")
    for a in d["additions"]["definitions"]:
        w(f"| `{a['name']}` | {esc(a['justification'])} |")
    w("")
    return "\n".join(L) + "\n" + tail


# ---------------------------------------------------------------- cli

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Generate tests/parity.json and docs/maop-v1-parity.md "
                                             "from the pinned CAOP v0.2 baseline.")
    ap.add_argument("target", choices=("json", "md", "all"),
                    help="json: tests/parity.json; md: docs/maop-v1-parity.md (rendered from "
                         "<out>/tests/parity.json); all: both")
    ap.add_argument("--out", default=REPO, metavar="DIR",
                    help="output root (default: the repository root, i.e. regenerate in place)")
    args = ap.parse_args(argv)
    try:
        if args.target in ("json", "all"):
            parity = build_parity()
            print("wrote " + write_text(args.out, PARITY_JSON, render_json(parity)))
        else:
            with open(os.path.join(args.out, PARITY_JSON), encoding="utf-8") as fh:
                parity = json.load(fh)
        if args.target in ("md", "all"):
            print("wrote " + write_text(args.out, PARITY_MD, render_md(parity)))
    except GenError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 1
    print(json.dumps(parity["status_summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
