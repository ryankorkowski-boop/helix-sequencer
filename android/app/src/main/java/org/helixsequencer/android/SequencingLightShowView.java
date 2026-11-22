package org.helixsequencer.android;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.view.View;

/** Lightweight decorative progress animation. Never represents rendered sequence output. */
public final class SequencingLightShowView extends View {
    public enum Scene { ARCHES, TREE, COMBINED }
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private Scene scene = Scene.COMBINED;
    private boolean running = false;
    private long startNanos;
    private float progress = 0f;

    public SequencingLightShowView(Context context) { super(context); }
    public void setScene(Scene value) { scene = value == null ? Scene.COMBINED : value; invalidate(); }
    public void setProgress(float fraction) {
        progress = Math.max(0f, Math.min(1f, fraction));
        invalidate();
    }
    public void setRunning(boolean value) {
        if (running == value) return;
        running = value;
        if (value) startNanos = System.nanoTime();
        invalidate();
    }
    @Override protected void onDetachedFromWindow() {
        running = false;
        super.onDetachedFromWindow();
    }
    @Override protected void onDraw(Canvas canvas) {
        super.onDraw(canvas);
        float w = getWidth(), h = getHeight();
        if (w <= 0 || h <= 0) return;
        canvas.drawColor(Color.rgb(9, 15, 32));
        double phase = running ? (System.nanoTime() - startNanos) / 1_000_000_000.0 : 0;
        if (scene != Scene.TREE) drawArches(canvas, w, h, phase);
        if (scene != Scene.ARCHES) drawTree(canvas, w, h, phase);
        paint.setColor(Color.rgb(36, 49, 76));
        canvas.drawRoundRect(w * .08f, h * .92f, w * .92f, h * .955f, 5, 5, paint);
        paint.setColor(Color.rgb(39, 224, 239));
        canvas.drawRoundRect(w * .08f, h * .92f, w * (.08f + .84f * progress), h * .955f, 5, 5, paint);
        if (running && getWindowVisibility() == VISIBLE) postInvalidateDelayed(50);
    }
    private void drawArches(Canvas c, float w, float h, double phase) {
        int count = 5, steps = 32;
        for (int a = 0; a < count; a++) {
            float cx = w * (.12f + a * .12f), rx = w * .075f;
            for (int i = 0; i <= steps; i++) {
                double t = Math.PI * i / steps;
                float x = cx + rx * (float)Math.cos(t);
                float y = h * .78f - h * .35f * (float)Math.sin(t);
                double chase = (i / (double)steps + a * .19 - phase * .55) % 1;
                if (chase < 0) chase += 1;
                float intensity = (float)Math.max(.15, 1 - Math.abs(chase - .5) * 3);
                paint.setColor(Color.rgb((int)(60 + 175 * intensity), (int)(35 + 160 * intensity), 255));
                c.drawCircle(x, y, Math.max(1.5f, w * .004f), paint);
            }
        }
    }
    private void drawTree(Canvas c, float w, float h, double phase) {
        float center = scene == Scene.TREE ? w * .5f : w * .82f;
        float radius = scene == Scene.TREE ? w * .28f : w * .14f;
        for (int i = 0; i < 140; i++) {
            float t = i / 139f;
            double angle = t * Math.PI * 10 + phase * 1.6;
            float x = center + radius * t * (float)Math.cos(angle);
            float y = h * (.14f + .66f * t);
            float hue = (float)((t * 240 + phase * 35) % 360);
            paint.setColor(Color.HSVToColor(new float[]{hue, .85f, 1f}));
            c.drawCircle(x, y, Math.max(1.5f, w * .004f), paint);
        }
    }
}
