"""Preview lifecycle labels shared by the phone checkpoint and desktop review log."""
from pathlib import Path

from core.preview_status import (
    COMPLETED,
    FAILED,
    PENDING,
    RUNNING,
    UNAVAILABLE,
    align_preview_paths,
    classify_review_log,
    failed_preview_line,
    preview_stage,
    preview_states,
    select_preview_candidates,
)

ROOT = Path(__file__).resolve().parents[1]
MOBILE = ROOT / "android/app/src/main/python/helix_mobile.py"
ENGINE = ROOT / "android/app/src/main/java/org/helixsequencer/android/EngineService.java"
ACTIVITY = ROOT / "android/app/src/main/java/org/helixsequencer/android/MainActivity.java"
MANIFEST = ROOT / "android/app/src/main/AndroidManifest.xml"


def test_candidate_order_and_states_stay_aligned_with_sequences():
    primary = Path("/job/outputs/show.xsq")
    second = Path("/job/outputs/show.alt1.xsq")
    third = Path("/job/outputs/show.alt2.xsq")
    extra = Path("/job/outputs/show.alt3.xsq")
    valid = [second, primary, extra, third]
    candidates, limit = select_preview_candidates(valid, primary, 3)
    assert limit == 3
    assert candidates == [primary, second, extra]

    outcomes = {str(primary): "/job/outputs/show.mp4", str(second): ""}
    assert preview_states(valid, candidates, outcomes, active=extra) == [
        FAILED, COMPLETED, RUNNING, UNAVAILABLE,
    ]
    assert align_preview_paths(valid, outcomes) == [
        "", "/job/outputs/show.mp4", "", "",
    ]
    running = preview_stage(candidates, outcomes, limit, running=True)
    assert running["status"] == RUNNING
    assert running["rendered"] == 1
    assert running["pending_variants"] == ["show.alt3.xsq"]
    assert running["failed_variants"] == ["show.alt1.xsq"]
    finished = preview_stage(
        candidates, {**outcomes, str(extra): "/job/outputs/show.alt2.mp4"}, limit, running=False,
    )
    assert finished["status"] == "partial"
    assert finished["rendered"] == 2
    assert finished["requested"] == 3
    assert finished["missing_candidates"] == 0


def test_requested_cap_and_all_success_accounting():
    valid = [Path(f"/job/{name}.xsq") for name in ("a", "b")]
    candidates, limit = select_preview_candidates(valid, valid[0], 99)
    assert limit == 8
    assert candidates == valid
    outcomes = {str(item): str(item.with_suffix(".mp4")) for item in candidates}
    stage = preview_stage(candidates, outcomes, limit, running=False)
    assert stage["status"] == "partial"
    assert stage["missing_candidates"] == 6
    assert stage["pending_variants"] == []
    eight = [Path(f"/job/{index}.xsq") for index in range(8)]
    chosen, capped = select_preview_candidates(eight, eight[3], 8)
    assert capped == 8
    assert chosen[0] == eight[3]
    assert len(chosen) == 8
    done = {str(item): "movie.mp4" for item in chosen}
    assert preview_stage(chosen, done, capped, running=False)["status"] == "success"


def test_failed_desktop_log_line_is_distinct_from_a_ready_preview():
    ready = classify_review_log(
        "preview_mp4: /tmp/show.mp4 (simulated, not native rendering)")
    failed = classify_review_log(failed_preview_line("Verse Lights.xsq"))
    assert ready == ("ready", "/tmp/show.mp4")
    assert failed == (FAILED, "Verse Lights.xsq")
    assert classify_review_log("Preview review: 1/2 requested (simulated)") is None


def test_phone_sources_publish_and_honor_preview_states():
    mobile = MOBILE.read_text(encoding="utf-8")
    engine = ENGINE.read_text(encoding="utf-8")
    activity = ACTIVITY.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "intensities.shape[1], frame_start=start" in mobile
    assert "frame_colors=colors[:, offset, :]" in mobile
    assert "frame_limit=" in mobile
    assert "preview_states" in mobile
    assert '"preview_states"' in engine
    assert "PreviewStatus.canPlay" in activity
    assert "pending_variants" in activity
    assert 'android:largeHeap="true"' in manifest


def test_phone_variant_export_uses_selected_sequence_filename():
    activity = ACTIVITY.read_text(encoding="utf-8")
    assert 'movie=button("Save selected variant MP4' in activity
    assert 'new File(sequencePath).getName()' in activity
    assert 'export(previewPath,"video/mp4",name+"-preview.mp4")' in activity
    assert 'Variant "+(index+1)+" of "+count' in activity
    assert 'if(index<0&&count>0)' in activity


def test_phone_preview_activity_handles_missing_variant_movie():
    source = (ROOT / "android/app/src/main/java/org/helixsequencer/android/PreviewActivity.java").read_text(encoding="utf-8")
    assert 'path==null||path.isEmpty()||!new java.io.File(path).isFile()' in source
    assert 'Return to Results and choose a completed preview.' in source


def test_preview_candidate_selection_ignores_stale_primary_and_duplicates():
    valid = [Path("/job/a.xsq"), Path("/job/b.xsq"), Path("/job/a.xsq")]
    selected = Path("/job/removed.xsq")
    candidates, limit = select_preview_candidates(valid, selected, 8)
    assert limit == 8
    assert candidates == [Path("/job/a.xsq"), Path("/job/b.xsq")]
    assert selected not in candidates
    assert preview_stage(candidates, {}, limit, running=False)["missing_candidates"] == 6


def test_band_preview_rejection_is_per_variant_not_global():
    mobile = MOBILE.read_text(encoding="utf-8")
    start = mobile.index("preview_candidates, preview_limit = select_preview_candidates(")
    end = mobile.index("for index, variant in enumerate(preview_candidates):", start)
    assert "band_stage_preview_error(" not in mobile[start:end]
    variant = mobile[end:mobile.index("publish(running=index + 1 < len(preview_candidates))", end)]
    assert "variant_band_error = band_stage_preview_error(inspect_band_stage(variant_layout))" in variant
    assert "outcomes[str(variant)] = ''" in variant
    assert "callback.log('Variant %d preview failed:" in variant


def test_android_results_passes_completed_variant_playlist_to_player():
    activity = (ROOT / "android/app/src/main/java/org/helixsequencer/android/MainActivity.java").read_text(encoding="utf-8")
    assert 'putStringArrayListExtra("playlist",playable)' in activity
    assert 'putExtra("playlist_index",playable.indexOf(previewPath))' in activity
    assert 'PreviewStatus.canPlay(previewStateFor(candidate),available(moviePath))' in activity


def test_android_preview_player_supports_next_previous_and_rotation():
    source = (ROOT / "android/app/src/main/java/org/helixsequencer/android/PreviewActivity.java").read_text(encoding="utf-8")
    assert 'previous.setOnClickListener(v->selectVariant(playlistIndex-1))' in source
    assert 'next.setOnClickListener(v->selectVariant(playlistIndex+1))' in source
    assert 'state.putInt("playlist_index",playlistIndex)' in source
    assert 'state.getInt("playlist_index",playlistIndex)' in source
    assert 'if(!restoring){position=0;resumePlayback=true;}' in source
    assert 'selectVariant(playlistIndex, state!=null)' in source
    assert 'prepared?video.getCurrentPosition():position' in source
    assert 'if(prepared){resumePlayback=video.isPlaying();position=video.getCurrentPosition();video.pause();}' in source


def test_android_player_can_auto_play_all_completed_variants():
    source = (ROOT / "android/app/src/main/java/org/helixsequencer/android/PreviewActivity.java").read_text(encoding="utf-8")
    assert 'playAll.setText("Play all completed variants automatically")' in source
    assert 'if(playAll.isChecked()&&playlistIndex+1<playlist.size())selectVariant(playlistIndex+1)' in source
    assert 'state.putBoolean("play_all",playAll.isChecked())' in source
    assert 'state.getBoolean("play_all",true)' in source
