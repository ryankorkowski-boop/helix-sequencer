package org.helixsequencer.android;

import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/** Native, offline launcher. No server, browser, account or storage permission. */
public class MainActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private final ExecutorService files = Executors.newSingleThreadExecutor();
    private final Map<String, Uri> inputs = new HashMap<>();
    private final Map<String, Button> selectors = new HashMap<>();
    private LinearLayout body;
    private Spinner mode, palette;
    private EditText variants, duration;
    private CheckBox polish, matrix, birdsong, spatial, ac, preview;
    private TextView status, log;
    private ProgressBar progress;
    private Button run, cancel, save, watch, movie;
    private String picking, exporting;
    private String bundlePath = "", previewPath = "";
    private File currentJob;
    private boolean busy;
    private String lastState = "";

    private int dp(int value) { return (int)(value*getResources().getDisplayMetrics().density); }
    private TextView text(String s, int size, int color) {
        TextView t = new TextView(this); t.setText(s); t.setTextSize(size); t.setTextColor(color);
        t.setPadding(0, dp(5), 0, dp(5)); body.addView(t); return t;
    }
    private Button button(String label, Runnable action) {
        Button b = new Button(this); b.setText(label); b.setAllCaps(false);
        body.addView(b, new LinearLayout.LayoutParams(-1, dp(52))); b.setOnClickListener(v -> action.run()); return b;
    }
    private CheckBox check(String label, boolean value) {
        CheckBox c = new CheckBox(this); c.setText(label); c.setChecked(value); body.addView(c); return c;
    }
    private EditText number(String label, String value) {
        text(label, 13, Color.LTGRAY); EditText e = new EditText(this);
        e.setInputType(2); e.setText(value); e.setSingleLine(); body.addView(e); return e;
    }
    private Spinner spinner(String[] values) {
        Spinner s = new Spinner(this); s.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, values));
        body.addView(s, new LinearLayout.LayoutParams(-1, dp(48))); return s;
    }
    private void select(String key, String label) {
        Button b = button(label, () -> {
            picking = key;
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType(key.equals("audio") ? "audio/*" : "*/*")
                .addCategory(Intent.CATEGORY_OPENABLE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(intent, 100);
        }); selectors.put(key, b);
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        ScrollView scroll = new ScrollView(this); body = new LinearLayout(this); body.setOrientation(1);
        body.setPadding(dp(20), dp(18), dp(20), dp(28)); scroll.addView(body); setContentView(scroll);
        body.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(dp(20), dp(18)+insets.getSystemWindowInsetTop(), dp(20), dp(28)+insets.getSystemWindowInsetBottom()); return insets;
        });
        text("HELIX", 34, Color.rgb(86,230,197));
        text("Your music. Your lights. On your phone.", 17, Color.WHITE);
        text("Offline beta • Sequences and simulated previews run on this device. Keep Helix open for best performance.", 13, Color.LTGRAY);
        SupportLinks.add(this, body);
        button("Control desktop Helix", () -> startActivity(new Intent(this, RemoteActivity.class)));
        text("Sequence mode", 14, Color.rgb(101,169,255)); mode = spinner(new String[]{"xLights · XSQ", "Light-O-Rama · LMS"});
        select("audio", "Choose song"); select("layout", "Choose xLights layout (or use bundled 256-channel)");
        select("template", "Choose XSQ template (or use bundled)"); select("lor", "Choose LOR channel layout · .lms");
        select("networks", "Optional xLights controller configuration"); select("routing", "Optional model routing · JSON");
        button("Reset selected files", () -> { inputs.clear(); getPreferences(0).edit().clear().apply(); recreate(); });
        text("Performance", 20, Color.rgb(101,169,255));
        variants = number("Variants · 1–8 (one is faster on a phone)", "1");
        palette = spinner(new String[]{"Default colors", "Musical neon palettes"});
        polish = check("Polish the sequence", true); matrix = check("Matrix intelligence", true);
        birdsong = check("Birdsong · confidence-gated canopy profile", true); spatial = check("RGB chorus chase", false);
        ac = check("AC-compatible effects", false); preview = check("Generate MP4 preview with audio", true);
        duration = number("Preview duration · 1–120 seconds", "30");
        text("LOR preserves addresses from your LMS. Native .loredit, neural stem separation and Whisper are unavailable in this beta. Preview geometry is simulated; xLights/controller playback needs separate verification.", 12, Color.LTGRAY);
        run = button("Build sequence on this phone", this::startJob);
        cancel = button("Cancel build", () -> {
            startService(new Intent(this, EngineService.class).setAction("cancel"));
        }); cancel.setEnabled(false);
        progress = new ProgressBar(this); body.addView(progress); progress.setVisibility(View.GONE);
        status = text("Ready", 17, Color.rgb(86,230,197));
        watch = button("Play preview", () -> startActivity(new Intent(this, PreviewActivity.class).putExtra("path", previewPath))); watch.setEnabled(false);
        movie = button("Save MP4…", () -> export(previewPath, "video/mp4", "Helix-preview.mp4")); movie.setEnabled(false);
        save = button("Save show ZIP…", () -> export(bundlePath, "application/zip", "Helix-show.zip")); save.setEnabled(false);
        text("Run log", 19, Color.rgb(101,169,255)); log = text("", 12, Color.LTGRAY); log.setTextIsSelectable(true);
        mode.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            public void onItemSelected(AdapterView<?> p, View v, int n, long id) { updateMode(); }
            public void onNothingSelected(AdapterView<?> p) {}
        }); ac.setOnCheckedChangeListener((b,v) -> updateMode());
        if (state != null) { picking=state.getString("picking"); exporting=state.getString("exporting"); }
        for (String key : selectors.keySet()) {
            String value=getPreferences(0).getString("uri_"+key, "");
            if (!value.isEmpty()) { Uri uri=Uri.parse(value); inputs.put(key, uri); selectors.get(key).setText(key+" · "+name(uri)); }
        }
        String job = getPreferences(0).getString("job", ""); if (!job.isEmpty()) currentJob = new File(job);
        if (Build.VERSION.SDK_INT >= 33) requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"}, 1);
    }
    private void updateMode() {
        boolean lor=mode.getSelectedItemPosition()==1, rgb=!lor && !ac.isChecked();
        for (String key : new String[]{"layout", "template", "routing", "networks"}) selectors.get(key).setVisibility(lor?View.GONE:View.VISIBLE);
        selectors.get("lor").setVisibility(lor?View.VISIBLE:View.GONE);
        for (View v : new View[]{palette,matrix,birdsong,spatial}) v.setEnabled(rgb && !busy);
        ac.setEnabled(!lor && !busy);
    }
    private String name(Uri uri) {
        try (android.database.Cursor c=getContentResolver().query(uri, new String[]{OpenableColumns.DISPLAY_NAME}, null,null,null)) {
            if (c!=null && c.moveToFirst()) return c.getString(0);
        } catch (Exception ignored) {} return "selected file";
    }
    private void startJob() {
        if (busy) return;
        try {
            if(android.system.Os.sysconf(android.system.OsConstants._SC_PAGESIZE)!=4096)
                throw new IllegalArgumentException("This offline beta needs a 4 KB-page device. Its numerical libraries must be rebuilt for this phone's memory page size.");
            if (!inputs.containsKey("audio")) throw new IllegalArgumentException("Choose a song first.");
            if (mode.getSelectedItemPosition()==1 && !inputs.containsKey("lor")) throw new IllegalArgumentException("Choose your existing LOR LMS first.");
            int n=Integer.parseInt(variants.getText().toString()), sec=Integer.parseInt(duration.getText().toString());
            if(n<1||n>8||sec<1||sec>120) throw new IllegalArgumentException("Use 1–8 variants and a 1–120 second preview.");
            JSONObject r=new JSONObject(); r.put("mode", mode.getSelectedItemPosition()==1?"lor":"xlights");
            r.put("variants",n); r.put("preview_seconds",sec); r.put("preview",preview.isChecked()); r.put("polish",polish.isChecked());
            r.put("palette",palette.getSelectedItemPosition()==1?"neon":"default"); r.put("matrix",matrix.isChecked());
            r.put("birdsong",birdsong.isChecked()); r.put("spatial",spatial.isChecked()); r.put("ac_compatible",ac.isChecked());
            JSONObject uris=new JSONObject(); for(Map.Entry<String,Uri> e:inputs.entrySet()) uris.put(e.getKey(),e.getValue().toString()); r.put("inputs",uris);
            currentJob=new File(getFilesDir(),"jobs/"+UUID.randomUUID());
            getPreferences(0).edit().putString("job",currentJob.getAbsolutePath()).apply();
            busy=true; run.setEnabled(false); lastState=""; status.setText("Starting local engine…");
            startForegroundService(new Intent(this,EngineService.class).putExtra("job",currentJob.getAbsolutePath()).putExtra("request",r.toString()));
        } catch(Exception e) { alert(e.getMessage()); }
    }
    private void poll() {
        if(currentJob==null) return;
        File state=new File(currentJob,"state.json");
        if(!state.isFile()) return;
        try {
            String raw=new String(java.nio.file.Files.readAllBytes(state.toPath()),StandardCharsets.UTF_8);
            if(raw.equals(lastState)) return; lastState=raw; JSONObject s=new JSONObject(raw);
            String phase=s.getString("phase"); busy=phase.equals("running");
            if(busy && System.currentTimeMillis()-s.optLong("updated_ms",System.currentTimeMillis())>15000){
                java.util.List<ActivityManager.RunningAppProcessInfo> processes=getSystemService(ActivityManager.class).getRunningAppProcesses();
                if(processes!=null && processes.stream().noneMatch(p->p.processName.equals(getPackageName()+":engine"))){
                    busy=false;s.put("message","Android stopped the previous build. You can start a fresh job.");
                }
            }
            run.setEnabled(!busy); cancel.setEnabled(busy); progress.setVisibility(busy?View.VISIBLE:View.GONE);
            status.setText(s.optString("message",phase));
            log.setText(s.optString("log")); updateMode();
            bundlePath=s.optString("bundle"); previewPath=s.optString("preview");
            save.setEnabled(!bundlePath.isEmpty() && new File(bundlePath).isFile());
            watch.setEnabled(!previewPath.isEmpty() && new File(previewPath).isFile()); movie.setEnabled(watch.isEnabled());
        } catch(Exception ignored) { /* atomic writer may not have finished yet */ }
    }
    private final Runnable ticker=new Runnable(){ public void run(){ poll(); handler.postDelayed(this,1000); }};
    @Override protected void onResume(){super.onResume();handler.post(ticker);}
    @Override protected void onPause(){handler.removeCallbacks(ticker);super.onPause();}
    @Override protected void onSaveInstanceState(Bundle s){s.putString("picking",picking);s.putString("exporting",exporting);super.onSaveInstanceState(s);}
    private void export(String path,String mime,String filename){ exporting=path; startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).setType(mime).addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE,filename),200); }
    @Override protected void onActivityResult(int code,int result,Intent data){
        super.onActivityResult(code,result,data); if(result!=RESULT_OK||data==null||data.getData()==null) return;
        Uri uri=data.getData();
        if(code==100&&picking!=null){
            try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(SecurityException ignored){}
            inputs.put(picking,uri);getPreferences(0).edit().putString("uri_"+picking,uri.toString()).apply();selectors.get(picking).setText(picking+" · "+name(uri));
        } else if(code==200&&exporting!=null){
            String source=exporting; files.submit(()->{
                try(InputStream in=new FileInputStream(source);OutputStream out=getContentResolver().openOutputStream(uri,"wt")){
                    if(out==null)throw new IOException("Cannot open destination");EngineService.copy(in,out);runOnUiThread(()->alert("Saved successfully."));
                }catch(Exception e){runOnUiThread(()->alert("Save failed: "+e.getMessage()));}
            });
        }
    }
    private void alert(String s){new AlertDialog.Builder(this).setMessage(s==null?"Unable to continue":s).setPositiveButton("OK",null).show();}
}
