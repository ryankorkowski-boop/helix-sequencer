package org.helixsequencer.android;
import android.content.Context;
import org.json.*;
import java.io.*;

/** Shared engine, desktop and phone catalog. */
final class UiOptions {
    private final JSONArray palettes,layouts;
    UiOptions(Context context) {
        try (InputStream in=context.getAssets().open("gui-options.json")) {
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] buffer=new byte[4096];int n;
            while((n=in.read(buffer))!=-1)bytes.write(buffer,0,n);
            JSONObject options=new JSONObject(bytes.toString("UTF-8"));
            palettes=options.getJSONArray("palettes");layouts=new JSONArray();
            layouts.put(new JSONObject().put("key","custom").put("title","Imported layout (takes priority)"));
            for(String group:new String[]{"layouts","stages"}) {
                JSONArray items=options.getJSONArray(group);
                for(int i=0;i<items.length();i++)layouts.put(items.getJSONObject(i));
            }
        } catch(Exception e) {throw new IllegalStateException("Helix sample catalog is missing",e);}
    }
    private String[] titles(JSONArray items) {
        String[] result=new String[items.length()];
        for(int i=0;i<items.length();i++)result[i]=items.optJSONObject(i).optString("title");
        return result;
    }
    String[] paletteTitles(){return titles(palettes);}
    String[] layoutTitles(){return titles(layouts);}
    String palette(int index){return palettes.optJSONObject(Math.max(0,Math.min(index,palettes.length()-1))).optString("key");}
    String layout(int index){return layouts.optJSONObject(Math.max(0,Math.min(index,layouts.length()-1))).optString("key");}
}
