package org.helixsequencer.android;

import android.app.*;
import android.content.*;
import android.net.Uri;
import android.os.*;
import android.graphics.Color;
import android.view.View;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

/** Optional desktop control screen; the offline engine remains independent. */
public class RemoteActivity extends Activity {
    private LinearLayout body;private EditText address,key,variants,duration;private Spinner mode,palette;
    private CheckBox preview,polish,matrix,birdsong,spatial,ac;
    private TextView status,log;private Button build,cancel,watch,save,movie;
    private final Map<String,Uri> inputs=new HashMap<>();private final Map<String,Button> selectors=new HashMap<>();
    private final ExecutorService network=Executors.newSingleThreadExecutor();private final Handler handler=new Handler(Looper.getMainLooper());
    private String picking,exporting,identity="";private boolean busy=false,polling=false,resumed=false;private File folder;
    private RemoteClient client;private String lastPhase="";
    private int dp(int n){return(int)(n*getResources().getDisplayMetrics().density);}
    private TextView text(String value,int size){TextView v=new TextView(this);v.setText(value);v.setTextSize(size);v.setTextColor(Color.WHITE);v.setPadding(0,dp(7),0,dp(7));body.addView(v);return v;}
    private Button button(String value,Runnable action){Button v=new Button(this);v.setAllCaps(false);v.setText(value);v.setOnClickListener(w->action.run());body.addView(v,new LinearLayout.LayoutParams(-1,dp(52)));return v;}
    private EditText field(String label,String value,boolean numeric){text(label,13);EditText e=new EditText(this);e.setSingleLine();e.setInputType(numeric?2:1);e.setText(value);body.addView(e);return e;}
    private CheckBox check(String value,boolean initial){CheckBox c=new CheckBox(this);c.setText(value);c.setChecked(initial);body.addView(c);return c;}
    private Spinner spinner(String... values){Spinner s=new Spinner(this);s.setAdapter(new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,values));body.addView(s);return s;}
    private void select(String role,String label){selectors.put(role,button(label,()->{picking=role;startActivityForResult(new Intent(Intent.ACTION_OPEN_DOCUMENT).setType(role.equals("audio")?"audio/*":"*/*").addCategory(Intent.CATEGORY_OPENABLE).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION),100);}));}
    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);ScrollView scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(1);body.setPadding(dp(20),dp(24),dp(20),dp(28));scroll.addView(body);setContentView(scroll);
        body.setOnApplyWindowInsetsListener((v,i)->{v.setPadding(dp(20),dp(24)+i.getSystemWindowInsetTop(),dp(20),dp(28)+i.getSystemWindowInsetBottom());return i;});
        text("HELIX · Desktop remote",27);text("Start Phone Remote in desktop Helix, then pair here. Use a reachable local network, USB tether or VPN. HTTPS is required for a public address.",14);
        SupportLinks.add(this,body);
        address=field("Desktop URL · e.g. http://192.168.1.20:8765",getPreferences(0).getString("address",""),false);
        key=field("Pairing key from desktop Helix",getPreferences(0).getString("key",""),false);key.setInputType(129);
        button("Connect to desktop",this::connect);text("Sequence mode",14);mode=spinner("xLights · XSQ","Light-O-Rama · LMS");
        select("audio","Choose song");select("layout","Choose xLights layout (or desktop bundled layout)");select("template","Choose XSQ template (or desktop bundled template)");select("lor","Choose existing LOR .lms channel layout");select("networks","Optional xLights controller XML");select("routing","Optional model routing JSON");
        palette=spinner("Layout/template colors (recommended)","Neon · optional RGB palette");
        preview=check("Generate desktop MP4 preview with audio",true);
        text("Default colors follow your compatible layout/template. Neon is an optional RGB palette override.",13);
        LinearLayout normal=body,expert=new LinearLayout(this);expert.setOrientation(1);
        button("Show / hide Advanced desktop settings",()->expert.setVisibility(expert.getVisibility()==View.VISIBLE?View.GONE:View.VISIBLE));
        normal.addView(expert);expert.setVisibility(View.GONE);body=expert;
        variants=field("Variants ·1–8","1",true);
        duration=field("Preview seconds ·1–120","30",true);
        spatial=check("Automatic RGB chorus/drop chase",true);
        ac=check("AC-compatible effects",false);
        text("Chase accents use eligible RGB models and layout positions. LOR uses AC-safe effects.",13);
        polish=check("Polish · automatic finishing pass",true);
        matrix=check("Matrix Intelligence · supported pixel models",true);
        birdsong=check("Birdsong · confidence-gated canopy phrasing",true);
        body=normal;
        build=button("Build on desktop",this::start);cancel=button("Cancel desktop build",this::cancel);cancel.setEnabled(false);
        status=text("Not connected",17);log=text("",12);log.setTextIsSelectable(true);
        watch=button("Download and play MP4",()->download("preview",false));movie=button("Download and save MP4…",()->download("preview",true));save=button("Download and save show ZIP…",()->download("bundle",true));watch.setEnabled(false);movie.setEnabled(false);save.setEnabled(false);
        text("Desktop previews are simulated effect-level views. Native xLights/controller playback needs separate verification. Builds continue on the desktop while this screen is closed; reopen to see progress.",12);
        mode.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){public void onItemSelected(AdapterView<?> p,View v,int n,long id){updateMode();}public void onNothingSelected(AdapterView<?> p){}});ac.setOnCheckedChangeListener((b,v)->updateMode());
        for(String role:selectors.keySet()){String value=getPreferences(0).getString("uri_"+role,"");if(!value.isEmpty()){inputs.put(role,Uri.parse(value));selectors.get(role).setText(role+" · file selected");}}
        identity=getPreferences(0).getString("job","");if(saved!=null){picking=saved.getString("picking");exporting=saved.getString("exporting");}
        if(!identity.isEmpty()){folder=new File(getFilesDir(),"remote/"+identity);folder.mkdirs();try{client=new RemoteClient(address.getText().toString(),key.getText().toString());}catch(Exception ignored){}}
    }
    private void updateMode(){address.setEnabled(!busy);key.setEnabled(!busy);boolean lor=mode.getSelectedItemPosition()==1,rgb=!lor&&!ac.isChecked();for(String role:new String[]{"layout","template","networks","routing"})selectors.get(role).setVisibility(lor?View.GONE:View.VISIBLE);selectors.get("lor").setVisibility(lor?View.VISIBLE:View.GONE);for(View v:new View[]{palette,matrix,birdsong,spatial})v.setEnabled(rgb&&!busy);ac.setEnabled(!lor&&!busy);}
    private RemoteClient selectedClient()throws Exception{return new RemoteClient(address.getText().toString(),key.getText().toString());}
    private void remember(){getPreferences(0).edit().putString("address",address.getText().toString().trim()).putString("key",key.getText().toString().trim()).putString("job",identity).apply();}
    private void connect(){
        if(busy)return;
        try{RemoteClient candidate=selectedClient();status.setText("Connecting…");network.submit(()->{try{candidate.json("GET","/v1/status",null);runOnUiThread(()->{if(!address.getText().toString().trim().equals(getPreferences(0).getString("address",""))||!key.getText().toString().trim().equals(getPreferences(0).getString("key",""))){identity="";folder=null;lastPhase="";log.setText("");save.setEnabled(false);watch.setEnabled(false);movie.setEnabled(false);}client=candidate;remember();status.setText("Desktop connected");});}catch(Exception e){error(e);}});}catch(Exception e){error(e);}
    }
    private void start(){
        if(busy)return;
        try{
            RemoteClient candidate=selectedClient();if(!inputs.containsKey("audio"))throw new IOException("Choose a song first");boolean lor=mode.getSelectedItemPosition()==1;if(lor&&!inputs.containsKey("lor"))throw new IOException("Choose your LOR LMS first");
            int count=Integer.parseInt(variants.getText().toString()),seconds=Integer.parseInt(duration.getText().toString());if(count<1||count>8||seconds<1||seconds>120)throw new IOException("Use1–8 variants and1–120 seconds");
            JSONObject request=new JSONObject();request.put("mode",lor?"lor":"xlights");request.put("variants",count);request.put("preview_seconds",seconds);request.put("preview",preview.isChecked());request.put("palette",palette.getSelectedItemPosition()==1?"neon":"default");request.put("polish",polish.isChecked());request.put("matrix",matrix.isChecked());request.put("birdsong",birdsong.isChecked());request.put("spatial",spatial.isChecked());request.put("ac_compatible",ac.isChecked());
            Map<String,Uri> selected=new HashMap<>(inputs);remember();busy=true;build.setEnabled(false);status.setText("Preparing desktop job…");watch.setEnabled(false);movie.setEnabled(false);save.setEnabled(false);updateMode();
            network.submit(()->{
                String created="";
                try{
                    created=candidate.json("POST","/v1/jobs",request).getString("id");String id=created;File local=new File(getFilesDir(),"remote/"+id);local.mkdirs();
                    for(Map.Entry<String,Uri> item:selected.entrySet()){
                        String role=item.getKey();if(lor&&!role.equals("audio")&&!role.equals("lor")||!lor&&role.equals("lor"))continue;
                        runOnUiThread(()->status.setText("Uploading "+role+"…"));File copy=new File(local,"upload-"+role);
                        try(InputStream in=getContentResolver().openInputStream(item.getValue());OutputStream out=new FileOutputStream(copy)){
                            if(in==null)throw new IOException("Cannot open "+role);byte[] bytes=new byte[65536];long size=0;int n;while((n=in.read(bytes))!=-1){size+=n;if(size>512L*1024*1024)throw new IOException("File exceeds512MiB");out.write(bytes,0,n);}
                        }
                        try{candidate.upload(id,role,copy);}finally{copy.delete();}
                    }
                    JSONObject state=candidate.json("POST","/v1/jobs/"+id+"/start",new JSONObject());runOnUiThread(()->{client=candidate;identity=id;folder=local;remember();show(state);});
                }catch(Exception e){if(!created.isEmpty())try{candidate.json("POST","/v1/jobs/"+created+"/cancel",new JSONObject());}catch(Exception ignored){}runOnUiThread(()->{busy=false;build.setEnabled(true);updateMode();});error(e);}
            });
        }catch(Exception e){error(e);}
    }
    private void show(JSONObject state){lastPhase=state.optString("phase");busy=lastPhase.equals("running");build.setEnabled(!busy);cancel.setEnabled(busy);status.setText(state.optString("message",lastPhase));log.setText(state.optString("log"));save.setEnabled(state.optBoolean("bundle"));watch.setEnabled(state.optBoolean("preview"));movie.setEnabled(watch.isEnabled());updateMode();}
    private void cancel(){RemoteClient c=client;String id=identity;if(c==null||id.isEmpty())return;network.submit(()->{try{JSONObject state=c.json("POST","/v1/jobs/"+id+"/cancel",new JSONObject());runOnUiThread(()->show(state));}catch(Exception e){error(e);}});}
    private void poll(){if(!resumed||polling||client==null||identity.isEmpty()||busy&&!lastPhase.equals("running"))return;polling=true;RemoteClient c=client;String id=identity;network.submit(()->{try{JSONObject state=c.json("GET","/v1/jobs/"+id,null);runOnUiThread(()->show(state));}catch(Exception e){runOnUiThread(()->status.setText("Desktop unavailable: "+e.getMessage()));}finally{runOnUiThread(()->polling=false);}});}
    private void download(String type,boolean export){RemoteClient c=client;String id=identity;if(c==null||folder==null)return;File target=new File(folder,type.equals("bundle")?"Helix-show.zip":"Helix-preview.mp4");status.setText("Downloading "+type+"…");network.submit(()->{try{c.download(id,type,target);runOnUiThread(()->{status.setText("Download ready");if(export){exporting=target.toString();startActivityForResult(new Intent(Intent.ACTION_CREATE_DOCUMENT).setType(type.equals("bundle")?"application/zip":"video/mp4").addCategory(Intent.CATEGORY_OPENABLE).putExtra(Intent.EXTRA_TITLE,target.getName()),200);}else startActivity(new Intent(this,PreviewActivity.class).putExtra("path",target.toString()));});}catch(Exception e){error(e);}});}
    @Override protected void onActivityResult(int code,int result,Intent data){super.onActivityResult(code,result,data);if(result!=RESULT_OK||data==null||data.getData()==null)return;Uri uri=data.getData();if(code==100&&picking!=null){try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(SecurityException ignored){}getPreferences(0).edit().putString("uri_"+picking,uri.toString()).apply();inputs.put(picking,uri);selectors.get(picking).setText(picking+" · file selected");}else if(code==200&&exporting!=null){String source=exporting;network.submit(()->{try(InputStream in=new FileInputStream(source);OutputStream out=getContentResolver().openOutputStream(uri,"wt")){if(out==null)throw new IOException("Cannot save file");EngineService.copy(in,out);runOnUiThread(()->status.setText("Saved successfully"));}catch(Exception e){error(e);}});}}
    private void error(Exception e){runOnUiThread(()->{status.setText("Remote operation failed");new AlertDialog.Builder(this).setMessage(e.getMessage()).setPositiveButton("OK",null).show();});}
    private final Runnable ticker=new Runnable(){public void run(){poll();handler.postDelayed(this,2000);}};
    @Override protected void onResume(){super.onResume();resumed=true;handler.post(ticker);}
    @Override protected void onPause(){resumed=false;handler.removeCallbacks(ticker);super.onPause();}
    @Override protected void onSaveInstanceState(Bundle saved){saved.putString("picking",picking);saved.putString("exporting",exporting);super.onSaveInstanceState(saved);}
}

