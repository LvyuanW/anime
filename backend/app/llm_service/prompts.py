from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Prompt:
    name: str
    content: str
    sha256: str


def load_prompt(prompt_filename: str) -> Prompt:
    repo_root = Path(__file__).resolve().parents[3]
    prompt_path = repo_root / "documnts" / "01-资产抽取" / "提示词" / prompt_filename
    content = prompt_path.read_text(encoding="utf-8")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return Prompt(name=prompt_filename, content=content, sha256=digest)

