package org.helixsequencer.android;
import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.widget.*;
import java.nio.charset.StandardCharsets;

/** Persistent Instructions and Legal tabs; no changes to the engine workflow. */
public class InfoActivity extends Activity {
    private String load(String name) {
        try (java.io.InputStream in=getAssets().open(name)) {
            java.io.ByteArrayOutputStream out=new java.io.ByteArrayOutputStream();
            byte[] b=new byte[4096];int n;while((n=in.read(b))!=-1)out.write(b,0,n);
            return new String(out.toByteArray(),StandardCharsets.UTF_8);
        } catch(Exception e) { return "This page could not be loaded. See the included Helix documentation."; }
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        TabHost host=new TabHost(this);LinearLayout root=new LinearLayout(this);root.setOrientation(1);
        root.setPadding(16,48,16,24);host.addView(root);
        TextView title=new TextView(this);title.setText("HELIX\nAudio in. Lights out.");title.setTextSize(23);root.addView(title);
        TabWidget tabs=new TabWidget(this);tabs.setId(android.R.id.tabs);root.addView(tabs);
        FrameLayout frames=new FrameLayout(this);frames.setId(android.R.id.tabcontent);root.addView(frames,new LinearLayout.LayoutParams(-1,0,1));
        host.setup();String[] names={"Instructions","Legal"};
        for(int i=0;i<2;i++) {
            ScrollView page=new ScrollView(this);page.setId(10000+i);
            TextView text=new TextView(this);text.setText(load("helix_"+names[i].toLowerCase()+".txt"));text.setTextSize(16);
            text.setTextColor(Color.WHITE);text.setPadding(14,18,14,28);text.setTextIsSelectable(true);page.addView(text);frames.addView(page);
            host.addTab(host.newTabSpec(names[i]).setIndicator(names[i]).setContent(page.getId()));
        }
        host.setCurrentTab(getIntent().getBooleanExtra("legal",false)?1:0);setContentView(host);
    }
}
