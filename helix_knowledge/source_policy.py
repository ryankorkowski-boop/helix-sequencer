from __future__ import annotations

from dataclasses import dataclass


ALLOWED_SOURCE_TYPES = {
    "OFFICIAL_XLIGHTS_DOCS",
    "USER_AUTHORED_NOTES",
    "USER_SUPPLIED_FILES_WITH_CONFIRMATION",
    "EXPLICIT_PERMISSION_BASED_EXAMPLES",
    "HELIX_GENERATED_EXPERIMENTS",
    "HELIX_USER_RATED_PREVIEWS",
}

BLOCKED_SOURCE_TYPES = {
    "PAID_SEQUENCES",
    "VENDOR_TUTORIAL_NO_PERMISSION",
    "PRIVATE_GROUP_CONTENT",
    "FACEBOOK_GROUP_SCRAPING",
    "DISCORD_SCRAPING",
    "LOGIN_ONLY_CONTENT",
    "UNCLEAR_RIGHTS_TRANSCRIPTS",
    "NO_AI_TRAINING_CONTENT",
    "NO_SCRAPING_CONTENT",
    "NO_PROVENANCE_CONTENT",
    "COPYRIGHTED_AUDIO_WITHOUT_RIGHTS",
}


@dataclass(frozen=True)
class SourcePolicyDecision:
    allowed: bool
    source_type: str
    reason: str
    preserve_provenance: bool = True


def evaluate_source_policy(source_type: str, provenance_note: str = "") -> SourcePolicyDecision:
    normalized = str(source_type or "").strip().upper()
    if normalized in BLOCKED_SOURCE_TYPES:
        return SourcePolicyDecision(False, normalized, "blocked_source_type")
    if normalized in ALLOWED_SOURCE_TYPES:
        if not str(provenance_note or "").strip():
            return SourcePolicyDecision(False, normalized, "missing_provenance")
        return SourcePolicyDecision(True, normalized, "allowed")
    return SourcePolicyDecision(False, normalized or "UNKNOWN", "unknown_source_type")
