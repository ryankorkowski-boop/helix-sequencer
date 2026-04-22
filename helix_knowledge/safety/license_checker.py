from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PERMISSIVE_LICENSES = {
    "mit",
    "apache-2.0",
    "bsd-2-clause",
    "bsd-3-clause",
    "isc",
    "mpl-2.0",
    "cc0-1.0",
    "unlicense",
    "cc-by-4.0",
}

COPyleft_ALLOWED_BY_FLAG = {
    "gpl-3.0",
    "gpl-2.0",
    "lgpl-3.0",
    "lgpl-2.1",
    "agpl-3.0",
}


@dataclass(slots=True)
class LicenseDecision:
    allowed: bool
    reason: str


class LicenseChecker:
    def __init__(self, *, include_copyleft: bool = False) -> None:
        self.include_copyleft = include_copyleft

    def is_license_compatible(self, license_hint: str) -> tuple[bool, str]:
        hint = (license_hint or "").strip().lower()
        if not hint:
            return False, "missing license hint"
        if hint in PERMISSIVE_LICENSES:
            return True, "permissive or public-domain style license"
        if hint in COPyleft_ALLOWED_BY_FLAG:
            if self.include_copyleft:
                return True, "copyleft allowed by configuration"
            return False, "copyleft license requires explicit opt-in"
        if "all rights reserved" in hint:
            return False, "all-rights-reserved content is incompatible"
        return False, f"license not in allowlist ({hint})"

    def github_license_from_metadata(self, repo_metadata: dict[str, Any]) -> str:
        license_obj = repo_metadata.get("license")
        if not isinstance(license_obj, dict):
            return ""
        return str(license_obj.get("spdx_id") or "").strip().lower()
