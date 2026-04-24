from __future__ import annotations


def sample_proxy_model(proxy_name: str, real_props: list[str]) -> dict[str, object]:
    return {
        "proxy": proxy_name,
        "sampled_targets": real_props[:8],
        "sample_strategy": "ordered_mapping",
    }
