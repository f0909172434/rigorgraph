from __future__ import annotations

from pathlib import Path

from rigorgraph.integrity import claim_snapshot_sha256, sha256_file
from rigorgraph.models import (
    Claim,
    ClaimStatus,
    ClaimType,
    Evidence,
    EvidenceType,
    Verification,
    VerificationOutcome,
)
from rigorgraph.storage import (
    CLAIMS_FILE,
    EVIDENCE_FILE,
    STATE_DIR,
    VERIFICATIONS_FILE,
    initialize_project,
    write_records,
)


def create_demo(root: Path, scenario: str, language: str) -> None:
    name = {
        "math": "Odd-sum proof audit",
        "benchmark": "Reproducible benchmark audit",
        "invalid": "Invalid numerical-to-proof promotion",
    }[scenario]
    initialize_project(root, name, language)
    evidence_dir = root / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    if scenario in {"math", "invalid"}:
        artifact = evidence_dir / ("odd-sum-proof.md" if scenario == "math" else "numeric-scan.txt")
        if scenario == "math":
            artifact.write_text(
                "# Sum of the first n odd integers\n\n"
                "Base case: 1 = 1^2. If the sum through n is n^2, adding 2n+1 gives "
                "n^2+2n+1=(n+1)^2. Therefore the identity holds by induction.\n",
                encoding="utf-8",
            )
            item = Evidence(
                id="EV-PROOF-001",
                type=EvidenceType.PROOF,
                title="Induction proof",
                producer="Example author",
                path="evidence/odd-sum-proof.md",
                scope="The identity 1+3+...+(2n-1)=n^2 for every positive integer n.",
                sha256=sha256_file(artifact),
            )
        else:
            artifact.write_text(
                "Checked n=1 through n=100000; all values matched.\n", encoding="utf-8"
            )
            item = Evidence(
                id="EV-COMP-001",
                type=EvidenceType.COMPUTATION,
                title="Finite numerical scan",
                producer="Example script",
                path="evidence/numeric-scan.txt",
                scope="The first 100000 positive integers only; this is not a proof for all n.",
                sha256=sha256_file(artifact),
            )
        claim = Claim(
            id="CLM-ODD-001",
            statement="The sum of the first n odd positive integers is n squared.",
            type=ClaimType.FORMAL,
            status=ClaimStatus.VERIFIED,
            authors=["Example author"],
            evidence_ids=[item.id],
        )
        verification = Verification(
            id="VER-ODD-001",
            claim_id=claim.id,
            verifier="Independent reviewer",
            outcome=VerificationOutcome.ACCEPT,
            rationale=(
                "The induction proof is complete."
                if scenario == "math"
                else "The finite scan agrees, but this intentionally invalid demo overpromotes it."
            ),
            checked_evidence_ids=[item.id],
            previous_status=ClaimStatus.PROPOSED,
            resulting_status=ClaimStatus.VERIFIED,
            snapshot_sha256=claim_snapshot_sha256(claim, {item.id: item}),
        )
        evidence_records = [item]
        claims = [claim]
        verifications = [verification]
    else:
        dataset_path = evidence_dir / "benchmark-data.csv"
        run_path = evidence_dir / "benchmark-run.json"
        dataset_path.write_text("case,baseline,candidate\nA,100,80\nB,200,150\n", encoding="utf-8")
        run_path.write_text(
            '{"environment":"demo","metric":"latency_ms","mean_reduction_percent":23.33}\n',
            encoding="utf-8",
        )
        dataset = Evidence(
            id="EV-DATA-001",
            type=EvidenceType.DATASET,
            title="Benchmark measurements",
            producer="Example benchmark harness",
            path="evidence/benchmark-data.csv",
            scope="Two synthetic cases in the recorded demo environment.",
            sha256=sha256_file(dataset_path),
        )
        run = Evidence(
            id="EV-RUN-001",
            type=EvidenceType.BENCHMARK_RUN,
            title="Benchmark run manifest",
            producer="Example benchmark harness",
            path="evidence/benchmark-run.json",
            scope="Reproduction metadata for the two synthetic cases only.",
            sha256=sha256_file(run_path),
        )
        claim = Claim(
            id="CLM-BENCH-001",
            statement="The candidate reduced mean latency in the two recorded synthetic cases.",
            type=ClaimType.BENCHMARK,
            status=ClaimStatus.VERIFIED,
            authors=["Benchmark author"],
            evidence_ids=[dataset.id, run.id],
        )
        verification = Verification(
            id="VER-BENCH-001",
            claim_id=claim.id,
            verifier="Independent benchmark reviewer",
            outcome=VerificationOutcome.ACCEPT,
            rationale="The claim is restricted to the recorded cases and matches the artifacts.",
            checked_evidence_ids=[dataset.id, run.id],
            previous_status=ClaimStatus.PROPOSED,
            resulting_status=ClaimStatus.VERIFIED,
            snapshot_sha256=claim_snapshot_sha256(claim, {dataset.id: dataset, run.id: run}),
        )
        evidence_records = [dataset, run]
        claims = [claim]
        verifications = [verification]

    state = root / STATE_DIR
    write_records(state / CLAIMS_FILE, claims)
    write_records(state / EVIDENCE_FILE, evidence_records)
    write_records(state / VERIFICATIONS_FILE, verifications)
