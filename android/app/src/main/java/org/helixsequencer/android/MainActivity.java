package org.helixsequencer.android;
import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import android.view.*;
import android.widget.*;
import androidx.core.content.FileProvider;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/** Guided native launcher; local jobs stay in the private engine process. */
public class MainActivity extends Activity {
    private final Handler handler=new Handler(Looper.getMainLooper());
    private final ExecutorService files=Executors.newSingleThreadExecutor();
    private final Map<String,Uri> inputs=new HashMap<>();
    private final Map<String,Button> selectors=new HashMap<>();
    private final List<View> settings=new ArrayList<>();
    private final String[] steps={"Music","Layout","Style","Advanced","Generate","Results"};
    private final LinearLayout[] pages=new LinearLayout[6];
    private LinearLayout body,expert;
    private Spinner mode,palette;
    private EditText variants,duration;
    private CheckBox polish,matrix,birdsong,spatial,ac,preview;
    private TextView status,log,stepTitle,results;
    private ProgressBar progress;
    private Button run,cancel,save,watch,movie,sequence,report,share,next,back;
    private String picking,exporting,bundlePath="",previewPath="",sequencePath="",reportPath="";
    private File currentJob;
    private boolean busy,wasBusy;
    private int page;
    private String lastState="";
    private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density);}
    private TextView text(String value,int size,int color){
        TextView v=new TextView(this);v.setText(value);v.setTextSize(size);v.setTextColor(color);
        v.setPadding(0,dp(6),0,dp(6));body.addView(v);return v;
    }
    private Button button(String label,Runnable action){
        Button v=new Button(this);v.setText(label);v.setAllCaps(false);v.setMinHeight(dp(52));
        body.addView(v,new LinearLayout.LayoutParams(-1,-2));v.setOnClickListener(b->action.run());return v;
    }
    private CheckBox check(String label,boolean value){
        CheckBox v=new CheckBox(this);v.setText(label);v.setChecked(value);body.addView(v);settings.add(v);return v;
    }
    private EditText number(String label,String value){
        text(label,14,Color.LTGRAY);EditText v=new EditText(this);v.setInputType(2);v.setText(value);
        v.setSingleLine();body.addView(v);settings.add(v);return v;
    }
    private Spinner spinner(String[] choices){
        Spinner v=new Spinner(this);v.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,choices));
        body.addView(v,new LinearLayout.LayoutParams(-1,dp(52)));settings.add(v);return v;
    }
    private void select(String key,String label){
        Button v=button(label,()->{
            picking=key;startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType(key.equals("audio")?"audio/*":"*/*")
                .addCategory(Intent.CATEGORY_OPENABLE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION),100);
        });selectors.put(key,v);settings.add(v);
    }
    private void panel(int i){body=pages[i];text(steps[i],26,Color.WHITE);}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);ScrollView scroll=new ScrollView(this);LinearLayout root=new LinearLayout(this);root.setOrientation(1);
        root.setPadding(dp(18),dp(16),dp(18),dp(24));scroll.addView(root);setContentView(scroll);body=root;
        root.setOnApplyWindowInsetsListener((v,insets)->{
            v.setPadding(dp(18),dp(16)+insets.getSystemWindowInsetTop(),dp(18),dp(24)+insets.getSystemWindowInsetBottom());return insets;
        });
        text("HELIX",32,Color.rgb(86,230,197));text("Your music. Your lights.",17,Color.WHITE);stepTitle=text("",14,Color.LTGRAY);
        HorizontalScrollView strip=new HorizontalScrollView(this);LinearLayout tabs=new LinearLayout(this);strip.addView(tabs);root.addView(strip);
        for(int i=0;i<steps.length;i++){
            final int target=i;Button tab=new Button(this);tab.setText(steps[i]);tab.setAllCaps(false);tabs.addView(tab);tab.setOnClickListener(v->showPage(target));
            pages[i]=new LinearLayout(this);pages[i].setOrientation(1);root.addView(pages[i]);
        }
        panel(0);text("Choose the song you want your lights to perform.",17,Color.WHITE);select("audio","Choose music · MP3 or WAV");
        text("Your music stays on this phone during local sequencing. The full song is sequenced even when the preview is shorter.",14,Color.LTGRAY);
        settings.add(button("Clear selected files",()->{
            inputs.clear();android.content.SharedPreferences.Editor e=getPreferences(0).edit();for(String key:selectors.keySet())e.remove("uri_"+key);e.apply();recreate();
        }));
        button("How to use Helix",this::walkthrough);button("Control desktop Helix",()->startActivity(new Intent(this, RemoteActivity.class)));

        panel(1);text("Choose the program you use for your lighting show.",17,Color.WHITE);
        mode=spinner(new String[]{"xLights · export XSQ","Light-O-Rama · export LMS"});
        select("layout","Import xLights layout · RGB effects XML");select("lor","Import LOR channels · existing LMS");
        text("xLights: use your layout, or leave it empty for the original bundled 256-channel display. Optional XSQ/controller files are in Advanced.",14,Color.LTGRAY);
        text("LOR: choose a legacy LMS with real Unit/Circuit addresses. Native .loredit and LCC import are unavailable.",14,Color.LTGRAY);

        panel(2);text("Helix follows the music automatically. Default colors come from your compatible template and layout.",17,Color.WHITE);
        palette=spinner(new String[]{"Layout/template colors (recommended)","Neon · optional RGB palette"});
        text("Neon changes RGB effect palettes to vivid colors. It does not improve detection or turn AC channels into RGB lights.",14,Color.LTGRAY);
        preview=check("Also make a preview with the soundtrack",true);
        text("A preview failure never takes away your sequence. Phone previews illustrate model-level effects; verify final playback in your lighting software.",14,Color.LTGRAY);

        panel(3);text("The defaults work without expert adjustments.",17,Color.WHITE);
        variants=number("Sequence variations · 1–8 (one uses less time and memory)","1");
        duration=number("Preview length · 1–120 seconds; full song still sequenced","30");
        spatial=check("Automatic RGB chorus/drop chase",true);
        text("An accent travels across at least three RGB models in layout order when a chorus/drop and free effect space allow it. Single-color channels are excluded.",14,Color.LTGRAY);
        ac=check("Force AC-compatible effects",false);
        text("Use this override for AC-safe On, ramps and similar effects. LOR enables it automatically.",14,Color.LTGRAY);
        select("template","Optional xLights XSQ template");select("networks","Optional xLights controllers · networks XML");select("routing","Optional model routing · JSON");
        expert=new LinearLayout(this);expert.setOrientation(1);
        button("Show / hide expert analysis controls",()->expert.setVisibility(expert.getVisibility()==View.VISIBLE?View.GONE:View.VISIBLE));
        body.addView(expert);expert.setVisibility(View.GONE);LinearLayout advanced=body;body=expert;
        polish=check("Polish · automatic finishing pass",true);matrix=check("Matrix Intelligence · supported pixel models",true);birdsong=check("Birdsong · confidence-gated canopy phrasing",true);
        text("Existing engine defaults are retained. RGB-only options are disabled in AC/LOR mode. Capability and confidence gates still apply. Neural stems and Whisper require desktop; HPSS runs locally.",13,Color.LTGRAY);body=advanced;

        panel(4);text("Generate on this phone. Keep Helix open for best performance. Cancellation affects only this job.",17,Color.WHITE);
        run=button("Generate sequence",this::startJob);cancel=button("Cancel current job",()->startService(new Intent(this,EngineService.class).setAction("cancel")));cancel.setEnabled(false);
        progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);progress.setMax(100);body.addView(progress);progress.setVisibility(View.GONE);
        status=text("Ready · choose music and layout",17,Color.rgb(86,230,197));text("Run log",18,Color.WHITE);log=text("",12,Color.LTGRAY);log.setTextIsSelectable(true);

        panel(5);results=text("Your sequence, show ZIP and preview will appear here.",16,Color.WHITE);
        sequence=button("Save sequence…",()->export(sequencePath,sequencePath.endsWith(".lms")?"application/xml":"application/octet-stream",new File(sequencePath).getName()));
        watch=button("Play preview",()->startActivity(new Intent(this,PreviewActivity.class).putExtra("path",previewPath)));
        movie=button("Save MP4…",()->export(previewPath,"video/mp4","Helix-preview.mp4"));
        save=button("Save show ZIP…",()->export(bundlePath,"application/zip","Helix-show.zip"));share=button("Share show ZIP…",this::shareShow);
        report=button("Save run report…",()->export(reportPath,"text/plain","Helix-run-report.txt"));
        for(Button v:new Button[]{sequence,watch,movie,save,share,report})v.setEnabled(false);
        text("The ZIP includes generated sequences, available layout/configuration files, soundtrack, manifest and report. A synchronized preview is included when it succeeds.",14,Color.LTGRAY);
        body=root;LinearLayout controls=new LinearLayout(this);root.addView(controls);
        back=new Button(this);back.setText("Back");controls.addView(back,new LinearLayout.LayoutParams(0,-2,1));back.setOnClickListener(v->showPage(page-1));
        next=new Button(this);next.setText("Next");controls.addView(next,new LinearLayout.LayoutParams(0,-2,1));next.setOnClickListener(v->showPage(page+1));
        SupportLinks.add(this,root);restorePreferences();
        mode.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
            public void onItemSelected(AdapterView<?> p,View v,int n,long id){updateMode();}public void onNothingSelected(AdapterView<?> p){}
        });ac.setOnCheckedChangeListener((b,v)->updateMode());
        if(state!=null){picking=state.getString("picking");exporting=state.getString("exporting");page=state.getInt("page",page);}
        showPage(page);updateMode();if(!getPreferences(0).getBoolean("walkthrough_seen",false))walkthrough();
    }
    private void walkthrough(){
        new AlertDialog.Builder(this).setTitle("Your first Helix show").setMessage("1. Select your music.\n\n2. Select your lighting layout.\n\n3. Choose xLights or LOR.\n\n4. Generate your sequence.\n\n5. Preview and save your show.\n\nAdvanced settings are optional.")
            .setPositiveButton("Start with music",(d,w)->{getPreferences(0).edit().putBoolean("walkthrough_seen",true).apply();showPage(0);}).show();
    }
    private void showPage(int n){page=Math.max(0,Math.min(5,n));for(int i=0;i<pages.length;i++)pages[i].setVisibility(i==page?View.VISIBLE:View.GONE);
        stepTitle.setText("Step "+(page+1)+" of 6 · "+steps[page]);back.setEnabled(page>0);next.setEnabled(page<5);}
    private void restorePreferences(){
        android.content.SharedPreferences p=getPreferences(0);mode.setSelection(p.getInt("mode",0));palette.setSelection(p.getInt("palette",0));
        variants.setText(p.getString("variants","1"));duration.setText(p.getString("duration","30"));preview.setChecked(p.getBoolean("preview",true));
        spatial.setChecked(p.getBoolean("spatial",true));ac.setChecked(p.getBoolean("ac",false));polish.setChecked(p.getBoolean("polish",true));
        matrix.setChecked(p.getBoolean("matrix",true));birdsong.setChecked(p.getBoolean("birdsong",true));
        for(String key:selectors.keySet()){String value=p.getString("uri_"+key,"");if(!value.isEmpty()){Uri uri=Uri.parse(value);inputs.put(key,uri);selectors.get(key).setText(key+" · "+name(uri));}}
        String job=p.getString("job","");if(!job.isEmpty())currentJob=new File(job);page=p.getInt("page",0);
    }
    private void remember(){
        getPreferences(0).edit().putInt("mode",mode.getSelectedItemPosition()).putInt("palette",palette.getSelectedItemPosition())
            .putString("variants",variants.getText().toString()).putString("duration",duration.getText().toString())
            .putBoolean("preview",preview.isChecked()).putBoolean("spatial",spatial.isChecked()).putBoolean("ac",ac.isChecked())
            .putBoolean("polish",polish.isChecked()).putBoolean("matrix",matrix.isChecked()).putBoolean("birdsong",birdsong.isChecked()).putInt("page",page).apply();
    }
    private void updateMode(){
        boolean lor=mode.getSelectedItemPosition()==1,rgb=!lor&&!ac.isChecked();for(View v:settings)v.setEnabled(!busy);
        for(String key:new String[]{"layout","template","routing","networks"})selectors.get(key).setVisibility(lor?View.GONE:View.VISIBLE);
        selectors.get("lor").setVisibility(lor?View.VISIBLE:View.GONE);
        for(View v:new View[]{palette,matrix,birdsong,spatial})v.setEnabled(rgb&&!busy);ac.setEnabled(!lor&&!busy);
    }
    private String name(Uri uri){
        try(android.database.Cursor c=getContentResolver().query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)){if(c!=null&&c.moveToFirst())return c.getString(0);}
        catch(Exception ignored){}return "selected file";
    }
    private void startJob(){
        if(busy)return;
        try{
            if(android.system.Os.sysconf(android.system.OsConstants._SC_PAGESIZE)!=4096)throw new IllegalArgumentException("This beta needs a 4 KB-page device. Its numerical libraries must be rebuilt for this phone's memory page size.");
            if(!inputs.containsKey("audio"))throw new IllegalArgumentException("Choose your music in Step 1.");
            if(mode.getSelectedItemPosition()==1&&!inputs.containsKey("lor"))throw new IllegalArgumentException("Choose your existing LOR LMS in Step 2.");
            int n=Integer.parseInt(variants.getText().toString()),sec=Integer.parseInt(duration.getText().toString());
            if(n<1||n>8||sec<1||sec>120)throw new IllegalArgumentException("Use 1–8 variants and a 1–120 second preview.");
            JSONObject r=new JSONObject();r.put("mode",mode.getSelectedItemPosition()==1?"lor":"xlights");r.put("variants",n);r.put("preview_seconds",sec);
            r.put("preview",preview.isChecked());r.put("polish",polish.isChecked());r.put("palette",palette.getSelectedItemPosition()==1?"neon":"default");
            r.put("matrix",matrix.isChecked());r.put("birdsong",birdsong.isChecked());r.put("spatial",spatial.isChecked());r.put("ac_compatible",ac.isChecked());
            JSONObject uris=new JSONObject();for(Map.Entry<String,Uri> e:inputs.entrySet())uris.put(e.getKey(),e.getValue().toString());r.put("inputs",uris);
            currentJob=new File(getFilesDir(),"jobs/"+UUID.randomUUID());getPreferences(0).edit().putString("job",currentJob.getAbsolutePath()).apply();
            bundlePath=previewPath=sequencePath=reportPath="";lastState="";busy=wasBusy=true;
            for(Button v:new Button[]{sequence,watch,movie,save,share,report})v.setEnabled(false);run.setEnabled(false);cancel.setEnabled(true);status.setText("Starting local engine…");updateMode();remember();
            if(Build.VERSION.SDK_INT>=33&&!getPreferences(0).getBoolean("notifications_asked",false)){
                getPreferences(0).edit().putBoolean("notifications_asked",true).apply();requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"},1);
            }
            startForegroundService(new Intent(this,EngineService.class).putExtra("job",currentJob.getAbsolutePath()).putExtra("request",r.toString()));
        }catch(Exception e){busy=false;run.setEnabled(true);cancel.setEnabled(false);updateMode();alert(e.getMessage());}
    }
    private boolean available(String p){return !p.isEmpty()&&new File(p).isFile();}
    private void poll(){
        if(currentJob==null)return;File state=new File(currentJob,"state.json");if(!state.isFile())return;
        try{
            String raw=new String(java.nio.file.Files.readAllBytes(state.toPath()),StandardCharsets.UTF_8);if(raw.equals(lastState)&&!busy)return;lastState=raw;
            JSONObject s=new JSONObject(raw);String phase=s.getString("phase");busy=phase.equals("running");
            if(busy&&System.currentTimeMillis()-s.optLong("updated_ms",System.currentTimeMillis())>15000){
                List<ActivityManager.RunningAppProcessInfo> running=getSystemService(ActivityManager.class).getRunningAppProcesses();
                if(running!=null&&running.stream().noneMatch(p->p.processName.equals(getPackageName()+":engine"))){busy=false;s.put("message","Android interrupted this job. Completed files below can still be saved.");}
            }
            run.setEnabled(!busy);cancel.setEnabled(busy);progress.setVisibility(busy?View.VISIBLE:View.GONE);
            int percent=s.optInt("preview_percent",-1);boolean measured=busy&&"preview".equals(s.optString("active_stage"))&&percent>=0;progress.setIndeterminate(!measured);if(measured)progress.setProgress(percent);
            status.setText(s.optString("message",phase));log.setText(s.optString("log"));updateMode();
            bundlePath=s.optString("bundle");previewPath=s.optString("preview");sequencePath=s.optString("sequence");reportPath=s.optString("report");
            sequence.setEnabled(available(sequencePath));save.setEnabled(available(bundlePath));share.setEnabled(save.isEnabled());watch.setEnabled(available(previewPath));movie.setEnabled(watch.isEnabled());report.setEnabled(available(reportPath));
            StringBuilder summary=new StringBuilder(s.optString("message",phase));JSONObject stages=s.optJSONObject("stages");
            if(stages!=null)for(String key:new String[]{"sequencing","packaging","preview"}){
                JSONObject stage=stages.optJSONObject(key);if(stage!=null)summary.append("\n\n").append(key).append(": ").append(stage.optString("status")).append(stage.has("error")?" · "+stage.optString("error"):"");
            }results.setText(summary.toString());if(wasBusy&&!busy)showPage(5);wasBusy=busy;
        }catch(Exception ignored){/* Retry an interrupted atomic state write. */}
    }
    private final Runnable ticker=new Runnable(){public void run(){poll();handler.postDelayed(this,1000);}};
    @Override protected void onResume(){super.onResume();handler.removeCallbacks(ticker);handler.post(ticker);}
    @Override protected void onPause(){remember();handler.removeCallbacks(ticker);super.onPause();}
    @Override protected void onSaveInstanceState(Bundle s){s.putString("picking",picking);s.putString("exporting",exporting);s.putInt("page",page);remember();super.onSaveInstanceState(s);}
    private void export(String path,String mime,String filename){
        if(!available(path)){alert("This output is not available yet.");return;}exporting=path;
        startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).setType(mime).addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE,filename),200);
    }
    private void shareShow(){
        if(!available(bundlePath))return;Uri uri=FileProvider.getUriForFile(this,getPackageName()+".shows",new File(bundlePath));
        Intent intent=new Intent(Intent.ACTION_SEND).setType("application/zip").putExtra(Intent.EXTRA_STREAM,uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        intent.setClipData(ClipData.newRawUri("Helix show",uri));startActivity(Intent.createChooser(intent,"Share your show"));
    }
    @Override protected void onActivityResult(int code,int result,Intent data){
        super.onActivityResult(code,result,data);if(result!=RESULT_OK||data==null||data.getData()==null)return;Uri uri=data.getData();
        if(code==100&&picking!=null){
            try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(SecurityException ignored){}
            inputs.put(picking,uri);getPreferences(0).edit().putString("uri_"+picking,uri.toString()).apply();selectors.get(picking).setText(picking+" · "+name(uri));
        }else if(code==200&&exporting!=null){
            String source=exporting;files.submit(()->{
                try(InputStream in=new FileInputStream(source);OutputStream out=getContentResolver().openOutputStream(uri,"wt")){
                    if(out==null)throw new IOException("Cannot open destination");EngineService.copy(in,out);runOnUiThread(()->alert("Saved successfully."));
                }catch(Exception e){runOnUiThread(()->alert("Save failed: "+e.getMessage()));}
            });
        }
    }
    private void alert(String s){new AlertDialog.Builder(this).setMessage(s==null?"Unable to continue":s).setPositiveButton("OK",null).show();}
}

