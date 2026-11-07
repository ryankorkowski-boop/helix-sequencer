package org.helixsequencer.android;

import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.widget.*;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;

@RunWith(AndroidJUnit4.class)
public class InfoAndBandUiTest {
    @Test public void instructionsSwitchAndRotationKeepTheRightPageAndScroll() throws Exception {
        Instrumentation instrumentation = InstrumentationRegistry.getInstrumentation();
        Context context = instrumentation.getTargetContext();
        try (ActivityScenario<InfoActivity> scenario = ActivityScenario.launch(new Intent(context, InfoActivity.class))) {
            instrumentation.waitForIdleSync();
            scenario.onActivity(activity -> {
                TextView text = activity.findViewById(R.id.help_content);
                assertTrue(text.getText().toString().startsWith("Your first Helix show"));
                ScrollView scroll = activity.findViewById(R.id.help_scroll);
                assertTrue(scroll.getHeight() > 0);
                scroll.scrollTo(0, 120);
            });
            instrumentation.waitForIdleSync();
            final int[] originalScroll = new int[1];
            scenario.onActivity(activity -> {
                originalScroll[0] = ((ScrollView)activity.findViewById(R.id.help_scroll)).getScrollY();
                assertTrue(originalScroll[0] > 0);
                activity.findViewById(R.id.help_legal).performClick();
            });
            instrumentation.waitForIdleSync();
            scenario.recreate(); instrumentation.waitForIdleSync();
            scenario.onActivity(activity -> {
                assertTrue(activity.findViewById(R.id.help_legal).isSelected());
                assertFalse(((TextView)activity.findViewById(R.id.help_content)).getText().toString().startsWith("Your first Helix show"));
                activity.findViewById(R.id.help_instructions).performClick();
            });
            instrumentation.waitForIdleSync();
            scenario.onActivity(activity -> {
                assertEquals(originalScroll[0], ((ScrollView)activity.findViewById(R.id.help_scroll)).getScrollY());
                assertTrue(((TextView)activity.findViewById(R.id.help_content)).getText().toString().contains("Band performers"));
            });
            android.graphics.Bitmap image = instrumentation.getUiAutomation().takeScreenshot();
            assertNotNull(image); java.io.ByteArrayOutputStream bytes = new java.io.ByteArrayOutputStream();
            image.compress(android.graphics.Bitmap.CompressFormat.PNG, 100, bytes); image.recycle();
            OfflineEngineTest.publishProof(context, "screen-instructions.png", bytes.toByteArray(), "image/png");
        }
    }

    @Test public void bandSwitchSurvivesActivityRecreation() throws Exception {
        Instrumentation instrumentation = InstrumentationRegistry.getInstrumentation();
        Context context = instrumentation.getTargetContext();
        android.content.SharedPreferences preferences = context.getSharedPreferences("MainActivity", 0);
        boolean previous = preferences.getBoolean("band_enabled", true);
        preferences.edit().putBoolean("walkthrough_seen", true).putBoolean("band_enabled", true).commit();
        try (ActivityScenario<MainActivity> scenario = ActivityScenario.launch(new Intent(context, MainActivity.class))) {
            scenario.onActivity(activity -> {
                CheckBox band = activity.findViewById(R.id.include_band);
                assertTrue(band.isChecked()); band.setChecked(false);
            });
            scenario.recreate(); instrumentation.waitForIdleSync();
            scenario.onActivity(activity -> assertFalse(((CheckBox)activity.findViewById(R.id.include_band)).isChecked()));
        } finally { preferences.edit().putBoolean("band_enabled", previous).commit(); }
        OfflineEngineTest.publishProof(context, "instructions-band-ui.json",
            "{\"instructions_scroll_and_recreation\":true,\"band_switch_persisted\":true}".getBytes("UTF-8"), "application/json");
    }
}
