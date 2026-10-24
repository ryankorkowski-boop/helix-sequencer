package org.helixsequencer.android;
import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.widget.*;
import java.io.*;
import org.json.JSONObject;

/** Opens the existing donation pages in the user's browser; no payment is made. */
public final class SupportLinks {
    public static void add(Activity activity,LinearLayout parent){
        try(InputStream in=activity.getAssets().open("support-links.json")){
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();EngineService.copy(in,bytes);JSONObject links=new JSONObject(bytes.toString("UTF-8"));
            LinearLayout row=new LinearLayout(activity);row.setOrientation(0);parent.addView(row);
            String[][] entries={{"xlights","Donate to xLights"},{"helix","Donate to Helix"}};
            for(String[] entry:entries){Button button=new Button(activity);button.setText(entry[1]);button.setAllCaps(false);row.addView(button,new LinearLayout.LayoutParams(0,-2,1));String url=links.getString(entry[0]);
                button.setOnClickListener(v->{try{activity.startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(url)));}catch(Exception e){Toast.makeText(activity,"No browser is available to open this donation page",Toast.LENGTH_LONG).show();}});
            }
        }catch(Exception error){throw new IllegalStateException("Donation links missing from this build",error);}
    }
}
