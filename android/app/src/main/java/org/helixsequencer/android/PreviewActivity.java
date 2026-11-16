package org.helixsequencer.android;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.widget.*;
import java.io.File;
import java.util.ArrayList;
import java.util.Locale;

/** One VideoView and audio stream for both variant review and sequential playback. */
public class PreviewActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private VideoView video;
    private SeekBar seek;
    private TextView title, time;
    private Button play, previous, next;
    private ArrayList<String> paths, titles;
    private boolean advance, seeking, prepared, wantsPlayback = true, resumed;
    private int index, position;
    private final Runnable tick = new Runnable() {
        @Override public void run() {
            updateClock();
            play.setText(video.isPlaying() ? "Pause" : "Play");
            handler.postDelayed(this, 250);
        }
    };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        paths = getIntent().getStringArrayListExtra("paths");
        titles = getIntent().getStringArrayListExtra("titles");
        if (paths == null || paths.isEmpty()) {
            String path = getIntent().getStringExtra("path");
            if (path == null) {
                finish();
                return;
            }
            paths = new ArrayList<>();
            paths.add(path);
        }
        advance = getIntent().getBooleanExtra("advance", false);
        index = getIntent().getIntExtra("index", 0);
        if (state != null) {
            index = state.getInt("index", index);
            position = state.getInt("position");
            wantsPlayback = state.getBoolean("playing", true);
        }
        index = Math.max(0, Math.min(index, paths.size() - 1));
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.BLACK);
        root.setOnApplyWindowInsetsListener((v, i) -> {
            v.setPadding(i.getSystemWindowInsetLeft(), i.getSystemWindowInsetTop(),
                i.getSystemWindowInsetRight(), i.getSystemWindowInsetBottom());
            return i;
        });
        title = caption(root);
        FrameLayout picture = new FrameLayout(this);
        root.addView(picture, new LinearLayout.LayoutParams(-1, 0, 1));
        video = new VideoView(this);
        picture.addView(video, new FrameLayout.LayoutParams(-1, -1, Gravity.CENTER));
        time = caption(root);
        seek = new SeekBar(this);
        seek.setContentDescription("Preview position");
        root.addView(seek);
        LinearLayout controls = new LinearLayout(this);
        root.addView(controls, new LinearLayout.LayoutParams(-1, -2));
        previous = button(controls, "Previous", () -> changeTrack(-1));
        play = button(controls, "Play", this::togglePlay);
        next = button(controls, "Next", () -> changeTrack(1));
        button(controls, "Close", this::finish);
        setContentView(root);
        seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onStartTrackingTouch(SeekBar view) { seeking = true; }
            @Override public void onProgressChanged(SeekBar view, int progress, boolean fromUser) {
                if (fromUser && prepared) {
                    position = progress;
                    video.seekTo(progress);
                    time.setText(clock(progress, video.getDuration()));
                }
            }
            @Override public void onStopTrackingTouch(SeekBar view) { seeking = false; }
        });
        video.setOnPreparedListener(player -> {
            prepared = true;
            play.setEnabled(true);
            seek.setEnabled(true);
            seek.setMax(video.getDuration());
            video.seekTo(position);
            if (resumed && wantsPlayback) video.start();
        });
        video.setOnCompletionListener(player -> {
            if (advance && index + 1 < paths.size()) changeTrack(1);
            else {
                wantsPlayback = false;
                position = video.getDuration();
                play.setText("Replay");
            }
        });
        video.setOnErrorListener((player, what, extra) -> {
            wantsPlayback = false;
            new AlertDialog.Builder(this).setMessage("Preview playback failed (" + what + ", " + extra + ").")
                .setPositiveButton("Close", (dialog, index) -> finish()).show();
            return true;
        });
        loadTrack();
    }

    private TextView caption(LinearLayout root) {
        TextView view = new TextView(this);
        view.setTextColor(Color.WHITE);
        view.setGravity(Gravity.CENTER);
        root.addView(view, new LinearLayout.LayoutParams(-1, -2));
        return view;
    }

    private Button button(LinearLayout controls, String text, Runnable action) {
        Button button = new Button(this);
        button.setAllCaps(false);
        button.setText(text);
        controls.addView(button, new LinearLayout.LayoutParams(0, -2, 1));
        button.setOnClickListener(view -> action.run());
        return button;
    }

    private void loadTrack() {
        prepared = false;
        play.setEnabled(false);
        seek.setEnabled(false);
        seek.setProgress(0);
        previous.setEnabled(index > 0);
        next.setEnabled(index + 1 < paths.size());
        String name = titles != null && index < titles.size() ? titles.get(index) : new File(paths.get(index)).getName();
        title.setText((index + 1) + " of " + paths.size() + " · " + name);
        time.setText(clock(0, 0));
        video.setVideoURI(Uri.fromFile(new File(paths.get(index))));
    }

    private void changeTrack(int delta) {
        int target = index + delta;
        if (target < 0 || target >= paths.size()) return;
        video.stopPlayback();
        index = target;
        position = 0;
        wantsPlayback = true;
        loadTrack();
    }

    private void togglePlay() {
        if (video.isPlaying()) {
            wantsPlayback = false;
            video.pause();
        } else {
            wantsPlayback = true;
            if (position >= video.getDuration()) {
                position = 0;
                video.seekTo(0);
            }
            video.start();
        }
    }

    private void updateClock() {
        if (!prepared || seeking) return;
        int duration = video.getDuration();
        if (position < duration || video.isPlaying()) position = video.getCurrentPosition();
        seek.setProgress(position);
        time.setText(clock(position, duration));
    }

    private static String clock(int elapsed, int duration) {
        int a = Math.max(elapsed, 0) / 1000, b = Math.max(duration, 0) / 1000;
        return String.format(Locale.ROOT, "%02d:%02d / %02d:%02d", a / 60, a % 60, b / 60, b % 60);
    }

    @Override protected void onResume() {
        super.onResume();
        resumed = true;
        handler.removeCallbacks(tick);
        handler.post(tick);
        if (prepared && wantsPlayback) video.start();
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        updateClock();
        state.putInt("index", index);
        state.putInt("position", position);
        state.putBoolean("playing", wantsPlayback);
        super.onSaveInstanceState(state);
    }

    @Override protected void onPause() {
        resumed = false;
        if (video != null) {
            updateClock();
            video.pause();
        }
        handler.removeCallbacks(tick);
        super.onPause();
    }

    @Override protected void onDestroy() {
        if (video != null) video.stopPlayback();
        super.onDestroy();
    }
}
