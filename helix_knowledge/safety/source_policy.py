from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlparse

from .license_checker import LicenseChecker

_TASK_RESTRICTED_EXTENSIONS = {
    ".xsq",
    ".fseq",
    ".mp3",
    ".wav",
    ".mp4",
    ".mov",
}

_DENY_PATTERNS = [
    re.compile(r"no\s+ai\s+training", re.IGNORECASE),
    re.compile(r"no\s+scrap", re.IGNORECASE),
    re.compile(r"do\s+not\s+scrap", re.IGNORECASE),
    re.compile(r"no\s+automated\s+access", re.IGNORECASE),
    re.compile(r"members?\s+only", re.IGNORECASE),
    re.compile(r"paid\s+sequence", re.IGNORECASE),
]

_DENY_HOST_HINTS = {
    "payhip.com",
    "gumroad.com",
    "patreon.com",
}

_ALLOWED_SOURCE_TYPES = {
    "xlights_manual",
    "xlights_blog",
    "forum",
    "github_docs",
    "youtube_transcript",
    "local_file",
    "web_page",
}


@dataclass(slots=True)
class SourcePolicyDecision:
    allowed: bool
    reason: str


class SourcePolicy:
    def __init__(self, *, license_checker: LicenseChecker | None = None) -> None:
        self.license_checker = license_checker or LicenseChecker()

    def evaluate(
        self,
        *,
        source_type: str,
        url: str,
        title: str = "",
        license_hint: str = "",
        terms_notes: str = "",
        is_login_required: bool = False,
        is_user_provided: bool = False,
        via_official_api: bool = False,
    ) -> SourcePolicyDecision:
        stype = (source_type or "").strip().lower()
        if stype not in _ALLOWED_SOURCE_TYPES:
            return SourcePolicyDecision(False, f"source type '{source_type}' is not allowlisted")

        if is_login_required:
            return SourcePolicyDecision(False, "login-only material is denied")

        if self._looks_like_vendor_asset(url=url, title=title):
            return SourcePolicyDecision(False, "vendor or paid-sequence style source is denied")

        lower_terms = f"{title}\n{terms_notes}\n{license_hint}".strip().lower()
        for pattern in _DENY_PATTERNS:
            if pattern.search(lower_terms):
                return SourcePolicyDecision(False, f"source terms denied by policy ({pattern.pattern})")

        if self._has_restricted_extension(url):
            return SourcePolicyDecision(False, "sequence/media asset extension is denied for knowledge ingestion")

        if stype == "youtube_transcript" and not (is_user_provided or via_official_api):
            return SourcePolicyDecision(False, "youtube transcript requires official API access or user-provided transcript")

        if stype == "github_docs":
            allowed_license, reason = self.license_checker.is_license_compatible(license_hint)
            if not allowed_license:
                return SourcePolicyDecision(False, f"github docs license blocked: {reason}")

        return SourcePolicyDecision(True, "allowed by source policy")

    @staticmethod
    def _has_restricted_extension(url: str) -> bool:
        path = (urlparse(url).path or "").lower()
        return any(path.endswith(ext) for ext in _TASK_RESTRICTED_EXTENSIONS)

    @staticmethod
    def _looks_like_vendor_asset(*, url: str, title: str) -> bool:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        if any(hint in host for hint in _DENY_HOST_HINTS):
            return True

        text = f"{url} {title}".lower()
        denied_tokens = [
            "paid sequence",
            "vendor pack",
            "exclusive download",
            "pirated",
            "cracked",
            "premium sequence",
        ]
        return any(token in text for token in denied_tokens)
