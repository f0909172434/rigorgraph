"""Exercise real tool handoffs; preserve negative evidence without promoting claims."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args: list[str], cwd: Path, expected: int = 0) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=120)
    require(result.returncode == expected, f"Command failed: {args[0]}\n{result.stderr}")
    return result.stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--honest-cli", type=Path, required=True)
    parser.add_argument("--finite-root", type=Path, required=True)
    parser.add_argument("--proofweave-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="A new, empty output directory")
    args = parser.parse_args()
    cli = args.honest_cli.resolve()
    finite = args.finite_root.resolve()
    proof = args.proofweave_root.resolve() / "docs/walkthroughs/simple-ring"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    project = output / "project"

    def rg(*values: str, expected: int = 0) -> str:
        return command([sys.executable, "-m", "rigorgraph", *values], output, expected)

    rg("init", str(project), "--name", "Inspectable tool handoffs")
    receipt: dict[str, object] = {"scope": "Tool integration; all claims remain DRAFT"}
    for label, count in [("pass", 1), ("zero-tests", 0)]:
        case = output / label
        case.mkdir()
        (case / "honest-ci.yml").write_text(
            "version: 1\nreports:\n  - name: unit\n    paths: [reports/junit.xml]\n"
            "    format: junit\n    min_tests: 1\n    max_drop_percent: null\n"
            "    max_skipped_percent: null\nbaseline:\n"
            "  file: .honest-ci/baseline.json\n  source: default-branch\n"
            "workflows:\n  paths: [.github/workflows/*.yml]\n", encoding="utf-8",
        )
        # Synthetic report fixtures test the handoff, not application correctness.
        (case / "fixture.mjs").write_text(
            "import {mkdirSync,writeFileSync} from 'node:fs';\n"
            "mkdirSync('reports',{recursive:true});\n"
            f"writeFileSync('reports/junit.xml', '<testsuite tests=\"{count}\" "
            'failures="0" errors="0" skipped="0">'
            + ('<testcase name="fixture" classname="handoff"/>' if count else "")
            + "</testsuite>');\n", encoding="utf-8",
        )
        stdout = command([
            "node", str(cli), "run", "--format", "json", "--evidence-output", "bundle.json",
            "--", "node", "fixture.mjs",
        ], case, 0 if count else 1)
        (case / "check-result.json").write_text(stdout, encoding="utf-8")
        bundle = case / "bundle.json"
        result = json.loads(bundle.read_text(encoding="utf-8"))["result"]
        require(result["status"] == ("passed" if count else "failed"), "Wrong CI status")
        require(result["totals"]["tests"] == count, "Wrong observed test count")
        claim_id, evidence_id = f"CLM-{label}", f"EV-{label}"
        claim = output / f"{claim_id}.json"
        write_json(claim, {
            "id": claim_id, "statement": f"Synthetic {label} report handoff for inspection.",
            "type": "empirical", "authors": ["Toolchain example"], "status": "DRAFT",
        })
        rg("claim", "add", str(claim), "--path", str(project))
        for _ in range(2):
            rg("evidence", "import", str(bundle), "--id", evidence_id,
               "--claim", claim_id, "--path", str(project))
        stored = project / ".rigorgraph/artifacts" / f"{evidence_id}.json"
        require(stored.read_bytes() == bundle.read_bytes(), "Bundle bytes changed")
        receipt[label] = {"result": result["status"], "tests": count, "sha256": digest(stored)}

    evidence_dir = project / "evidence"
    evidence_dir.mkdir()

    def add_file(source: Path, name: str, kind: str, scope: str, producer: str) -> str:
        destination = evidence_dir / name
        shutil.copyfile(source, destination)
        identifier = f"EV-{name.replace('.', '-')}"
        record = output / f"{identifier}.json"
        write_json(record, {
            "id": identifier, "type": kind, "title": name, "producer": producer,
            "path": f"evidence/{name}", "sha256": digest(destination), "scope": scope,
        })
        rg("evidence", "add", str(record), "--path", str(project))
        return identifier

    certificate = finite / "examples/c4-certificate.json"
    checker_result = output / "finite-check.json"
    checker_result.write_text(command([
        sys.executable, str(finite / "tools/verify_certificate.py"),
        str(certificate), "--replay-search",
    ], output), encoding="utf-8")
    finite_result = json.loads(checker_result.read_text(encoding="utf-8"))
    require(finite_result["first_in_declared_order"] == "VERIFIED", "Finite replay failed")
    finite_scope = "C4 finite counterexample and declared search prefix; no general proof."
    finite_ids = [
        add_file(certificate, "c4-certificate.json", "computation", finite_scope, "Finite Witness"),
        add_file(checker_result, "finite-check.json", "computation", finite_scope,
                 "Python checker"),
    ]

    proof_ids = []
    for line in (proof / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        expected_hash, name = line.split()
        require(Path(name).name == name, "Unexpected proof artifact path")
        source = proof / name
        require(digest(source) == expected_hash, f"Frozen proof artifact changed: {name}")
        proof_ids.append(add_file(
            source, f"proofweave-{name}", "proof" if name == "certificate.lean" else "computation",
            "Historical simple-ring run: CERTIFIED; semantic alignment UNCONFIRMED. "
            "This handoff checks published hashes; it does not rerun Lean.", "ProofWeave snapshot",
        ))
    for label, ids, statement, kind in [
        ("finite", finite_ids, "C4 falsifies the configured triangle conjecture.", "empirical"),
        ("ring", proof_ids, "The recorded Lean ring identity has a historical certificate; "
         "alignment to the source claim remains unconfirmed.", "formal"),
    ]:
        record = output / f"claim-{label}.json"
        write_json(record, {"id": f"CLM-{label}", "statement": statement, "type": kind,
                            "authors": ["Toolchain example"], "evidence_ids": ids})
        rg("claim", "add", str(record), "--path", str(project))
    audit = json.loads(rg("audit", str(project), "--json"))
    require(audit["status"] == "PASS", "Intact project must pass")
    claims = [json.loads(line) for line in
              (project / ".rigorgraph/claims.jsonl").read_text(encoding="utf-8").splitlines()]
    require(all(c["status"] == "DRAFT" for c in claims), "Unexpected claim promotion")
    require(audit["evidence"] == 9, "Imports must be idempotent")
    rg("report", str(project), "--output", str(output / "report.html"))
    tampered = output / "tampered-project"
    shutil.copytree(project, tampered)
    with (tampered / ".rigorgraph/artifacts/EV-pass.json").open("ab") as stream:
        stream.write(b"\n")
    negative = json.loads(rg("audit", str(tampered), "--json", expected=1))
    require(any(issue["code"] == "RG_HASH_MISMATCH" for issue in negative["issues"]),
            "Tampering was not detected")
    receipt.update({"audit": audit, "tampered_audit": negative,
                    "finite": finite_result, "claim_statuses": [c["status"] for c in claims],
                    "proofweave": "Published SHA256SUMS checked; Lean not rerun"})
    write_json(output / "receipt.json", receipt)
    print("PASS: real HonestCI pass/fail, idempotent imports, finite replay, frozen proof hashes, "
          "DRAFT preservation, HTML report, and tamper rejection")


if __name__ == "__main__":
    main()
