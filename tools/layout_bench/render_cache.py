"""Validate resumable bench outputs against their inputs and published bytes."""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from core.output_provenance import sha256


def receipt_path(output: Path) -> Path:
    return output.with_suffix(output.suffix + ".receipt.json")


def cached_render(output: Path, inputs: dict) -> dict | None:
    try:
        receipt = json.loads(receipt_path(output).read_text(encoding="utf-8"))
        if (isinstance(receipt, dict) and receipt.get("inputs") == inputs
                and output.is_file() and receipt.get("sha256") == sha256(output)):
            return receipt
    except (OSError, ValueError):
        pass
    return None


def publish_render(staged: Path, output: Path, inputs: dict, **metadata) -> None:
    if staged.stat().st_size == 0:
        raise ValueError(f"Empty render: {staged}")
    receipt = dict(inputs=inputs, sha256=sha256(staged), **metadata)
    output.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, delete=False) as handle:
        temp = Path(handle.name)
        try:
            json.dump(receipt, handle, indent=2)
            handle.write("\n")
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        staged.replace(output)
        temp.replace(receipt_path(output))
    finally:
        temp.unlink(missing_ok=True)
