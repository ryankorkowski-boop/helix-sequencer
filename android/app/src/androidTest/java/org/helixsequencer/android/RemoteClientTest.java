package org.helixsequencer.android;

import android.content.*;
import android.provider.MediaStore;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import org.junit.*;
import org.junit.runner.RunWith;
import org.json.*;
import java.io.*;
import java.nio.file.*;
import java.util.zip.*;
import static org.junit.Assert.*;

/** Native transport proof against the actual Python desktop API; synthetic job only. */
@RunWith(AndroidJUnit4.class)
public class RemoteClientTest {
    private static final String TOKEN="synthetic-emulator-transport-key-only-123456789";
    @Test public void pairsUploadsControlsAndDownloadsAcrossEmulatorNetwork()throws Exception{
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        RemoteClient client=new RemoteClient("http://10.0.2.2:8765",TOKEN);
        assertEquals("helix.remote.v1",client.json("GET","/v1/status",null).getString("schema"));
        try{new RemoteClient("http://10.0.2.2:8765","incorrect-pairing-key-long-enough-1234").json("GET","/v1/status",null);fail("Unauthenticated connection accepted");}catch(IOException expected){}
        for(String endpoint:new String[]{"http://8.8.8.8:8765","http://public.example.com:8765","http://user:password@127.0.0.1:8765"}){
            try{new RemoteClient(endpoint,TOKEN);fail("Unsafe endpoint accepted");}catch(IOException expected){}
        }
        JSONObject settings=new JSONObject();settings.put("preview",false);String id=client.json("POST","/v1/jobs",settings).getString("id");String prefix="/v1/jobs/"+id;
        File source=new File(context.getCacheDir(),"remote-transport-source");Files.write(source.toPath(),"Synthetic transport test only".getBytes("UTF-8"));client.upload(id,"audio",source);
        assertEquals("audio",client.json("GET",prefix,null).getJSONArray("uploaded").getString(0));
        client.json("POST",prefix+"/start",new JSONObject());JSONObject state=null;
        for(int i=0;i<100;i++){state=client.json("GET",prefix,null);if(!state.getString("phase").equals("running"))break;Thread.sleep(100);}
        assertEquals("complete",state.getString("phase"));File bundle=new File(context.getCacheDir(),"transport-show.zip");client.download(id,"bundle",bundle);
        try(ZipFile zip=new ZipFile(bundle)){assertNotNull(zip.getEntry("transport-only.txt"));}
        String cancelId=client.json("POST","/v1/jobs",new JSONObject()).getString("id");assertEquals("cancelled",client.json("POST","/v1/jobs/"+cancelId+"/cancel",new JSONObject()).getString("phase"));
        InstrumentationRegistry.getInstrumentation().startActivitySync(new Intent(context,RemoteActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));InstrumentationRegistry.getInstrumentation().waitForIdleSync();
        JSONObject proof=new JSONObject();proof.put("schema","helix.remote.transport.proof.v1");proof.put("native_android_transport",true);proof.put("desktop_api",true);proof.put("auth_upload_start_status_cancel_download",true);proof.put("musical_engine_test",false);proof.put("remote_activity_launched",true);
        ContentValues values=new ContentValues();values.put(MediaStore.Downloads.DISPLAY_NAME,"remote-transport.json");values.put(MediaStore.Downloads.MIME_TYPE,"application/json");values.put(MediaStore.Downloads.RELATIVE_PATH,"Download/HelixAndroidSmoke");android.net.Uri uri=context.getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,values);assertNotNull(uri);
        try(OutputStream out=context.getContentResolver().openOutputStream(uri)){out.write(proof.toString().getBytes("UTF-8"));}
    }
}
