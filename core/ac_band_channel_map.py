from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from models.helixville4_band_assets import HELIXVILLE4_BAND_ASSETS, BandModelAsset


@dataclass(frozen=True)
class AcBandChannel:
    member_id: str
    display_name: str
    model_prefix: str
    submodel: str
    channel_name: str
    channel_index: int
    controller_type: str = "ac"

    def to_dict(self) -> dict[str, Any]:
        return {
            "member_id": self.member_id,
            "display_name": self.display_name,
            "model_prefix": self.model_prefix,
            "submodel": self.submodel,
            "channel_name": self.channel_name,
            "channel_index": self.channel_index,
            "controller_type": self.controller_type,
        }


@dataclass(frozen=True)
class AcBandChannelMap:
    schema: str
    start_channel: int
    channels: tuple[AcBandChannel, ...]

    @property
    def channel_count(self) -> int:
        return len(self.channels)

    @property
    def end_channel(self) -> int:
        if not self.channels:
            return self.start_channel - 1
        return max(channel.channel_index for channel in self.channels)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "start_channel": self.start_channel,
            "end_channel": self.end_channel,
            "channel_count": self.channel_count,
            "channels": [channel.to_dict() for channel in self.channels],
        }


def normalize_channel_name(value: str) -> str:
    return "_".join(value.strip().upper().replace("-", "_").replace(" ", "_").split("_"))


def build_ac_band_channel_map(
    *,
    assets: Iterable[BandModelAsset] = HELIXVILLE4_BAND_ASSETS,
    start_channel: int = 1,
    selected_submodels: Mapping[str, Iterable[str]] | None = None,
) -> AcBandChannelMap:
    """Build one AC channel per performer submodel/position.

    This is for relay/AC-style output where each band pose, instrument zone,
    mouth state, or body part is represented by a discrete on/off channel.
    RGB pixel rendering can still use the richer outline/SVG assets.
    """

    channels: list[AcBandChannel] = []
    next_channel = start_channel

    for asset in assets:
        allowed = None
        if selected_submodels is not None:
            allowed = {normalize_channel_name(value) for value in selected_submodels.get(asset.member_id, [])}

        for submodel in asset.submodel_order:
            normalized_submodel = normalize_channel_name(submodel)
            if allowed is not None and normalized_submodel not in allowed:
                continue

            channel_name = normalize_channel_name(f"{asset.model_prefix}_{normalized_submodel}")
            channels.append(
                AcBandChannel(
                    member_id=asset.member_id,
                    display_name=asset.display_name,
                    model_prefix=asset.model_prefix,
                    submodel=normalized_submodel,
                    channel_name=channel_name,
                    channel_index=next_channel,
                )
            )
            next_channel += 1

    return AcBandChannelMap(
        schema="helix.ac_band_channel_map.v1",
        start_channel=start_channel,
        channels=tuple(channels),
    )


def ac_band_channel_lookup(channel_map: AcBandChannelMap) -> dict[tuple[str, str], AcBandChannel]:
    return {
        (channel.member_id, channel.submodel): channel
        for channel in channel_map.channels
    }


def ac_band_channel_map_payload(
    *,
    start_channel: int = 1,
    selected_submodels: Mapping[str, Iterable[str]] | None = None,
) -> dict[str, Any]:
    return build_ac_band_channel_map(
        start_channel=start_channel,
        selected_submodels=selected_submodels,
    ).to_dict()
