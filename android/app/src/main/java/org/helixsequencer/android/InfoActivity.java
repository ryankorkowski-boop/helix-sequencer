package org.helixsequencer.android;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.widget.*;
import java.nio.charset.StandardCharsets;

/** Stable, inset-aware Instructions/Legal reader with independent scroll positions. */
public class InfoActivity extends Activity {
    private final int[] scrollPositions = new int[2];
    private final Button[] tabs = new Button[2];
    private final String[] pages = new String[2];
    private ScrollView scroll;
    private TextView content;
    private int selected;
    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }

    private String load(String name) {
        try (java.io.InputStream in = getAssets().open(name)) {
            java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
            byte[] bytes = new byte[4096]; int count;
            while ((count = in.read(bytes)) != -1) out.write(bytes, 0, count);
            return new String(out.toByteArray(), StandardCharsets.UTF_8);
        } catch (Exception e) {
            return "This page could not be loaded. See the included Helix documentation.";
        }
    }

    private void select(int index, boolean rememberScroll) {
        if (rememberScroll) scrollPositions[selected] = scroll.getScrollY();
        selected = index;
        content.setText(pages[index]);
        for (int i = 0; i < tabs.length; i++) {
            tabs[i].setSelected(i == index);
            tabs[i].setTextColor(i == index ? Color.rgb(86, 230, 197) : Color.WHITE);
        }
        scroll.post(() -> { if (selected == index) scroll.scrollTo(0, scrollPositions[index]); });
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        pages[0] = load("helix_instructions.txt");
        pages[1] = load("helix_legal.txt");
        selected = state == null ? (getIntent().getBooleanExtra("legal", false) ? 1 : 0)
                                 : state.getInt("selected_page", 0);
        if (state != null) {
            scrollPositions[0] = state.getInt("instructions_scroll", 0);
            scrollPositions[1] = state.getInt("legal_scroll", 0);
        }
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(16, 24, 36));
        root.setPadding(dp(16), dp(12), dp(16), dp(16));
        root.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(dp(16) + insets.getSystemWindowInsetLeft(),
                dp(12) + insets.getSystemWindowInsetTop(),
                dp(16) + insets.getSystemWindowInsetRight(),
                dp(16) + insets.getSystemWindowInsetBottom());
            return insets;
        });
        TextView title = new TextView(this);
        title.setText("HELIX\nAudio in. Lights out.");
        title.setTextSize(23); title.setTextColor(Color.WHITE);
        title.setPadding(0, 0, 0, dp(12)); root.addView(title);
        LinearLayout tabRow = new LinearLayout(this);
        String[] names = {"Instructions", "Legal"};
        for (int i = 0; i < tabs.length; i++) {
            final int index = i;
            Button tab = new Button(this); tabs[i] = tab;
            tab.setId(i == 0 ? R.id.help_instructions : R.id.help_legal);
            tab.setText(names[i]); tab.setAllCaps(false); tab.setMinHeight(dp(48));
            tab.setOnClickListener(view -> select(index, true));
            tabRow.addView(tab, new LinearLayout.LayoutParams(0, -2, 1));
        }
        root.addView(tabRow);
        scroll = new ScrollView(this); scroll.setId(R.id.help_scroll);
        scroll.setFillViewport(true);
        content = new TextView(this); content.setId(R.id.help_content);
        content.setTextSize(16); content.setTextColor(Color.WHITE);
        content.setLineSpacing(dp(3), 1); content.setPadding(dp(4), dp(16), dp(4), dp(24));
        scroll.addView(content, new ScrollView.LayoutParams(-1, -2));
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root); root.requestApplyInsets(); select(selected, false);
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        scrollPositions[selected] = scroll.getScrollY();
        state.putInt("selected_page", selected);
        state.putInt("instructions_scroll", scrollPositions[0]);
        state.putInt("legal_scroll", scrollPositions[1]);
        super.onSaveInstanceState(state);
    }
}
