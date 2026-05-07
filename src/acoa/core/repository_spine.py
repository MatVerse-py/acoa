"""Classificação de repositórios para construir o repository spine."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List


class RepoClass(str, Enum):
    """Classes canônicas de repositórios."""

    A0_CANONICAL = "A0_CANONICAL_KERNEL"
    A1_RUNTIME = "A1_RUNTIME_EXECUTION"
    A2_PROOF = "A2_PROOF_AUDIT_LEDGER"
    B_PRODUCT = "B_PRODUCT_SURFACE"
    C_ARCHIVE = "C_ARCHIVE_SATELLITE"
    REVIEW = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class RepoRecord:
    """Registro final de classificação de um repositório."""

    repo: str
    repo_class: RepoClass
    reason: str
    risk_flags: List[str]
    next_action: str


A0_TERMS = [
    "core",
    "atlas",
    "gate",
    "cassandra",
    "organismo",
    "matverse",
    "mnbs-seed",
    "mem-nano-bit",
    "svca",
    "papers",
    "docs",
]
A1_TERMS = [
    "ouroboros",
    "sovereign",
    "stack-production",
    "mcp-server",
    "u-os",
    "u-kernel",
    "u-gate",
    "u-network",
    "secure-loader",
    "core.eng",
    "acoa",
    "ia.gov",
]
A2_TERMS = [
    "verifier",
    "hub",
    "scan",
    "validator",
    "resolver",
    "bunker",
    "genesis-mirror",
    "governance-pipeline",
    "experiment-data",
    "test-results",
]
B_TERMS = [
    "page",
    "landing",
    "pwa",
    "symbiodroid",
    "csi",
    "forensic",
    "twin",
    "captals",
    "symbios-code",
    "apk-uploader",
    "symbios",
]
C_TERMS = ["superkernel", "prime", "prim", "pose", "oda-qf", "kiloman", "dev", "untitled", "delta"]
RISK_TERMS = ["superkernel", "100", "primeira", "padrão mundial", "supera", "civilização", "untitled"]


def extract_repos(text: str) -> List[str]:
    """Extrai padrões owner/repo sem duplicidade e preservando ordem."""
    pattern = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"
    matches = re.findall(pattern, text)
    seen = set()
    repos: List[str] = []
    for match in matches:
        if match not in seen:
            repos.append(match)
            seen.add(match)
    return repos


def has_any(value: str, terms: List[str]) -> bool:
    """Retorna True se o valor contiver qualquer termo."""
    lowered = value.lower()
    return any(term.lower() in lowered for term in terms)


def classify_repo(repo: str) -> RepoRecord:
    """Classifica repositório pela taxonomia A0-A2/B/C/REVIEW."""
    risk_flags: List[str] = []
    if has_any(repo, RISK_TERMS):
        risk_flags.append("neycsec01:review_overclaim_or_legacy_name")

    if has_any(repo, A0_TERMS) and not has_any(repo, C_TERMS):
        return RepoRecord(
            repo=repo,
            repo_class=RepoClass.A0_CANONICAL,
            reason="sinais de kernel, documentação, ciência, governança ou fonte canônica",
            risk_flags=risk_flags,
            next_action="auditar README, schemas, releases, testes e promover para repository_spine",
        )
    if has_any(repo, A1_TERMS):
        return RepoRecord(
            repo=repo,
            repo_class=RepoClass.A1_RUNTIME,
            reason="sinais de execução, runtime, servidor, kernel operacional ou gateway",
            risk_flags=risk_flags,
            next_action="validar build, endpoints, Docker, CI, testes e replay",
        )
    if has_any(repo, A2_TERMS):
        return RepoRecord(
            repo=repo,
            repo_class=RepoClass.A2_PROOF,
            reason="sinais de verificação, auditoria, prova, resolver, scanner ou dados experimentais",
            risk_flags=risk_flags,
            next_action="validar hashes, receipts, fixtures, Merkle root e evidência pública",
        )
    if has_any(repo, B_TERMS):
        return RepoRecord(
            repo=repo,
            repo_class=RepoClass.B_PRODUCT,
            reason="sinais de produto, interface, app, frontend, forense, mobile ou superfície pública",
            risk_flags=risk_flags,
            next_action="conectar ao kernel e exigir prova mínima para claims públicos",
        )
    if has_any(repo, C_TERMS) or risk_flags:
        return RepoRecord(
            repo=repo,
            repo_class=RepoClass.C_ARCHIVE,
            reason="parece legado, experimento, protótipo, sandbox ou linhagem histórica",
            risk_flags=risk_flags,
            next_action="preservar como archive lineage; não promover para núcleo sem prova",
        )

    return RepoRecord(
        repo=repo,
        repo_class=RepoClass.REVIEW,
        reason="classe não inferida com segurança pelo nome",
        risk_flags=risk_flags,
        next_action="abrir README e mapear função real antes de promover",
    )


def build_repository_spine(input_path: str, output_path: str = "repo_index.json") -> Dict:
    """Gera índice JSON com a classificação dos repositórios do snapshot."""
    text = Path(input_path).read_text(encoding="utf-8", errors="replace")
    repos = extract_repos(text)
    records = [classify_repo(repo) for repo in repos]
    summary: Dict[str, int] = {}
    for record in records:
        summary[record.repo_class.value] = summary.get(record.repo_class.value, 0) + 1

    result = {
        "total_repositories": len(repos),
        "summary": summary,
        "records": [asdict(record) for record in records],
    }
    Path(output_path).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result
