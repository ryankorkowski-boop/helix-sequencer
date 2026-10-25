package org.helixsequencer.android;

import android.content.Context;
import android.content.ContentValues;
import android.content.Intent;
import android.provider.MediaStore;
import android.media.*;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import com.chaquo.python.*;
import com.chaquo.python.android.AndroidPlatform;
import org.junit.*;
import org.junit.runner.RunWith;
import static org.junit.Assert.*;
import org.json.*;
import java.io.*;
import java.nio.*;
import java.nio.file.*;
import java.util.zip.*;

/** Real APK smoke: original engine -> nonempty XSQ/LMS -> H.264 + AAC -> ZIP. */
@RunWith(AndroidJUnit4.class)
public class OfflineEngineTest {
    public static class Callbacks {
        MediaRuntime.VideoEncoder video;String path,wav;long end;int fps;
        JSONObject checkpoint;
        public void checkpoint(String raw)throws Exception{checkpoint=new JSONObject(raw);}
        public void stage(String stage,String message){}
        public void previewProgress(int frame,int total){}
        public void log(String value){android.util.Log.i("HelixSmoke",value);}
        public void beginPreview(String path,String wav,int width,int height,int fps)throws Exception{this.path=path;this.wav=wav;this.fps=fps;video=new MediaRuntime.VideoEncoder(path+".video.mp4",width,height,fps);}
        public void previewFrame(byte[] data,long pts)throws Exception{video.frame(data,pts);end=pts+1_000_000L/fps;}
        public void endPreview()throws Exception{video.close();video=null;MediaRuntime.encodeAac(wav,path+".audio.m4a",end+500_000);MediaRuntime.mux(path+".video.mp4",path+".audio.m4a",path,end);new File(path+".audio.m4a").delete();new File(path+".video.mp4").delete();}
        public void decodePreviewAudio(String movie,String wav)throws Exception{MediaRuntime.decodeWav(movie,wav);}
        public void abortPreview(){if(video!=null){video.abort();video=null;}}
    }
    public static class FailedPreview extends Callbacks {
        @Override public void beginPreview(String path,String wav,int width,int height,int fps)throws Exception{
            assertNotNull(checkpoint);
            assertTrue(new File(checkpoint.getString("sequence")).isFile());
            assertTrue(new File(checkpoint.getString("bundle")).isFile());
            throw new IOException("Injected native preview failure");
        }
    }
    @Test public void runsBothModesLocallyAndEncodesRealAudio()throws Exception{
        Context context=InstrumentationRegistry.getInstrumentation().getTargetContext();
        File engine=new File(context.getFilesDir(),"instrumentation-engine");engine.mkdirs();
        try(ZipInputStream zip=new ZipInputStream(context.getAssets().open("helix-engine.zip"))){ZipEntry e;while((e=zip.getNextEntry())!=null){File p=new File(engine,e.getName());p.getParentFile().mkdirs();try(OutputStream out=new FileOutputStream(p)){EngineService.copy(zip,out);}}}
        if(!Python.isStarted())Python.start(new AndroidPlatform(context));
        // Test modes in separate Python sub-interpreters are unavailable. run() supports
        // re-entry after the numerical module was installed once in this test process.
        for(String mode:new String[]{"xlights","lor"}){
            File job=new File(context.getFilesDir(),"smoke-"+mode);File input=new File(job,"input");input.mkdirs();
            syntheticWav(new File(input,"source.wav"));
            MediaRuntime.decodeWav(new File(input,"source.wav").toString(),new File(input,"audio.wav").toString());
            if(mode.equals("lor")){
                String lms="<sequence musicFilename=\"old.wav\"><channels><channel name=\"Roof red\" deviceType=\"LOR\" unit=\"1\" circuit=\"1\" color=\"255\" savedIndex=\"0\" centiseconds=\"800\"/><channel name=\"Roof green\" deviceType=\"LOR\" unit=\"1\" circuit=\"2\" color=\"65280\" savedIndex=\"1\" centiseconds=\"800\"/></channels><tracks><track totalCentiseconds=\"800\"><channels><channel savedIndex=\"0\"/><channel savedIndex=\"1\"/></channels></track></tracks></sequence>";
                Files.write(new File(input,"source.lms").toPath(),lms.getBytes("UTF-8"));
            }
            JSONObject request=new JSONObject();request.put("mode",mode);request.put("variants",1);request.put("preview",true);request.put("preview_seconds",3);request.put("palette","neon");
            Callbacks callbacks=new Callbacks();
            JSONObject result=new JSONObject(Python.getInstance().getModule("helix_mobile").callAttr("run",engine.toString(),job.toString(),request.toString(),callbacks).toString());
            assertTrue(result.getInt("sequence_count")>0);File bundle=new File(result.getString("bundle"));assertTrue(bundle.length()>1000);
            try(ZipFile z=new ZipFile(bundle)){assertNotNull(z.getEntry("android-run.json"));}
            MediaExtractor mp4=new MediaExtractor();try{mp4.setDataSource(result.getString("preview"));int v=MediaRuntime.track(mp4,"video/"),a=MediaRuntime.track(mp4,"audio/");
                assertEquals("video/avc",mp4.getTrackFormat(v).getString(MediaFormat.KEY_MIME));assertEquals("audio/mp4a-latm",mp4.getTrackFormat(a).getString(MediaFormat.KEY_MIME));
                assertTrue(mp4.getTrackFormat(v).getLong(MediaFormat.KEY_DURATION)>2_000_000);
            }finally{mp4.release();}
            // Gradle uninstalls the debug app after instrumentation. Keep only
            // synthetic test proof in public Downloads so the host can collect it.
            publishProof(context,mode+"-show.zip",Files.readAllBytes(bundle.toPath()),"application/zip");
        }
        // Real repository music through Android's MP3 decoder and the current RGB layout.
        File real=new File(context.getFilesDir(),"smoke-real-rgb");File ri=new File(real,"input");ri.mkdirs();
        Context test=InstrumentationRegistry.getInstrumentation().getContext();
        try(InputStream in=test.getAssets().open("real-song.mp3");OutputStream out=new FileOutputStream(new File(ri,"source.mp3"))){EngineService.copy(in,out);}
        try(InputStream in=test.getAssets().open("stability-rgb.xml");OutputStream out=new FileOutputStream(new File(ri,"xlights_rgbeffects.xml"))){EngineService.copy(in,out);}
        MediaRuntime.decodeWav(new File(ri,"source.mp3").toString(),new File(ri,"audio.wav").toString());
        JSONObject realRequest=new JSONObject();realRequest.put("mode","xlights");realRequest.put("preview",true);realRequest.put("preview_seconds",8);
        JSONObject realResult=new JSONObject(Python.getInstance().getModule("helix_mobile").callAttr("run",engine.toString(),real.toString(),realRequest.toString(),new Callbacks()).toString());
        File withoutBand=new File(context.getFilesDir(),"smoke-band-off");File bi=new File(withoutBand,"input");bi.mkdirs();
        Files.copy(new File(ri,"audio.wav").toPath(),new File(bi,"audio.wav").toPath(),StandardCopyOption.REPLACE_EXISTING);
        try(InputStream in=test.getAssets().open("stability-rgb.xml");OutputStream out=new FileOutputStream(new File(bi,"xlights_rgbeffects.xml"))){EngineService.copy(in,out);}
        JSONObject bandRequest=new JSONObject(realRequest.toString());bandRequest.put("band_enabled",false);bandRequest.put("preview_seconds",3);
        JSONObject bandResult=new JSONObject(Python.getInstance().getModule("helix_mobile").callAttr("run",engine.toString(),withoutBand.toString(),bandRequest.toString(),new Callbacks()).toString());
        JSONObject bandManifest=new JSONObject(new String(Files.readAllBytes(new File(withoutBand,"outputs/android-run.json").toPath()),"UTF-8"));
        assertFalse(bandManifest.getBoolean("band_enabled"));
        assertTrue(bandManifest.getJSONObject("band_visibility").getJSONArray("removed_models").length()>0);
        javax.xml.parsers.DocumentBuilderFactory factory=javax.xml.parsers.DocumentBuilderFactory.newInstance();
        org.w3c.dom.NodeList remaining=factory.newDocumentBuilder().parse(new File(bi,"xlights_rgbeffects.xml")).getElementsByTagName("model");
        for(int i=0;i<remaining.getLength();i++){
            String name=((org.w3c.dom.Element)remaining.item(i)).getAttribute("name");
            assertFalse(name.startsWith("HX_SNOWMAN_DRUMMER_"));assertFalse(name.startsWith("HX_SNOWMAN_SINGER_"));
        }
        publishProof(context,"band-off-show.zip",Files.readAllBytes(new File(bandResult.getString("bundle")).toPath()),"application/zip");
        assertEquals("success",realResult.getJSONObject("stages").getJSONObject("preview").getString("status"));
        publishProof(context,"real-rgb-show.zip",Files.readAllBytes(new File(realResult.getString("bundle")).toPath()),"application/zip");
        // A fresh actual engine run with an intentionally failing encoder must export.
        File failed=new File(context.getFilesDir(),"smoke-failed-preview");File fi=new File(failed,"input");fi.mkdirs();
        Files.copy(new File(ri,"audio.wav").toPath(),new File(fi,"audio.wav").toPath(),StandardCopyOption.REPLACE_EXISTING);
        JSONObject failedResult=new JSONObject(Python.getInstance().getModule("helix_mobile").callAttr("run",engine.toString(),failed.toString(),realRequest.toString(),new FailedPreview()).toString());
        assertEquals("success",failedResult.getJSONObject("stages").getJSONObject("sequencing").getString("status"));
        assertEquals("failed",failedResult.getJSONObject("stages").getJSONObject("preview").getString("status"));
        assertEquals("",failedResult.getString("preview"));
        assertTrue(new File(failedResult.getString("sequence")).isFile());
        publishProof(context,"failed-preview-show.zip",Files.readAllBytes(new File(failedResult.getString("bundle")).toPath()),"application/zip");
        File full=new File(context.getFilesDir(),"smoke-full-song");File fullInput=new File(full,"input");fullInput.mkdirs();
        try(InputStream in=test.getAssets().open("full-song.mp3");OutputStream out=new FileOutputStream(new File(fullInput,"source.mp3"))){EngineService.copy(in,out);}
        MediaRuntime.decodeWav(new File(fullInput,"source.mp3").toString(),new File(fullInput,"audio.wav").toString());
        assertTrue(new File(fullInput,"audio.wav").length()>22050L*2*30);
        JSONObject fullRequest=new JSONObject();fullRequest.put("mode","xlights");fullRequest.put("preview",true);fullRequest.put("preview_seconds",600);
        Callbacks fullCallbacks=new Callbacks();
        JSONObject fullResult=new JSONObject(Python.getInstance().getModule("helix_mobile").callAttr("run",engine.toString(),full.toString(),fullRequest.toString(),fullCallbacks).toString());
        assertEquals("success",fullResult.getJSONObject("stages").getJSONObject("sequencing").getString("status"));
        assertEquals("success",fullResult.getJSONObject("stages").getJSONObject("preview").getString("status"));
        assertTrue("Full-song preview must exceed the former 120-second limit",fullCallbacks.end>120_000_000L);
        publishProof(context,"full-song-show.zip",Files.readAllBytes(new File(fullResult.getString("bundle")).toPath()),"application/zip");
        JSONObject launcherState=new JSONObject(realResult.toString());launcherState.put("phase","complete");launcherState.put("message","Real music sequenced and exported on this device");launcherState.put("updated_ms",System.currentTimeMillis());
        Files.write(new File(real,"state.json").toPath(),launcherState.toString().getBytes("UTF-8"));
        context.getSharedPreferences(MainActivity.class.getSimpleName(),0).edit().putBoolean("walkthrough_seen",true).putString("job",real.toString()).apply();
        android.app.Instrumentation instrumentation=InstrumentationRegistry.getInstrumentation();
        android.app.Instrumentation.ActivityMonitor monitor=instrumentation.addMonitor(MainActivity.class.getName(),null,false);
        instrumentation.runOnMainSync(()->context.startActivity(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)));
        android.app.Activity launcher=monitor.waitForActivityWithTimeout(5000);
        assertNotNull(launcher);instrumentation.removeMonitor(monitor);
        instrumentation.getUiAutomation().waitForIdle(1000,5000);
        android.graphics.Bitmap shot=instrumentation.getUiAutomation().takeScreenshot();
        if(shot!=null){ByteArrayOutputStream png=new ByteArrayOutputStream();shot.compress(android.graphics.Bitmap.CompressFormat.PNG,100,png);shot.recycle();publishProof(context,"launcher.png",png.toByteArray(),"image/png");}
        for(String screen:new String[]{"Music","Layout","Style","Advanced","Generate","Results"}){
            instrumentation.runOnMainSync(()->{
                android.widget.Button tab=findButton(launcher.getWindow().getDecorView(),screen);assertNotNull(tab);tab.performClick();
            });
            instrumentation.getUiAutomation().waitForIdle(1000,5000);
            // Accessibility idleness alone can precede the compositor's frame.
            instrumentation.waitForIdleSync();Thread.sleep(500);
            android.graphics.Bitmap image=instrumentation.getUiAutomation().takeScreenshot();assertNotNull(image);
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();image.compress(android.graphics.Bitmap.CompressFormat.PNG,100,bytes);image.recycle();
            publishProof(context,"screen-"+screen.toLowerCase()+".png",bytes.toByteArray(),"image/png");
        }
        // Exercise the real VideoView/MediaPlayer after the MP4 presentation edit.
        assertNotNull(findButton(launcher.getWindow().getDecorView(),"Donate to Helix"));
        assertNotNull(findButton(launcher.getWindow().getDecorView(),"Donate to xLights"));
        android.app.Instrumentation.ActivityMonitor playback=instrumentation.addMonitor(PreviewActivity.class.getName(),null,false);
        instrumentation.runOnMainSync(()->findButton(launcher.getWindow().getDecorView(),"Play preview").performClick());
        android.app.Activity player=playback.waitForActivityWithTimeout(5000);assertNotNull(player);instrumentation.removeMonitor(playback);
        boolean[] playing={false};
        for(int attempt=0;attempt<40&&!playing[0];attempt++){
            Thread.sleep(250);
            instrumentation.runOnMainSync(()->{android.widget.VideoView view=findVideo(player.getWindow().getDecorView());playing[0]=view!=null&&view.isPlaying()&&view.getCurrentPosition()>0;});
        }
        assertTrue("Corrected MP4 must actually play in Android VideoView",playing[0]);
        instrumentation.runOnMainSync(()->{
            android.widget.VideoView view=findVideo(player.getWindow().getDecorView());
            android.widget.Button close=findButton(player.getWindow().getDecorView(),"Close");
            assertNotNull("Preview has in-layout controls",close);
            android.graphics.Rect movieBounds=new android.graphics.Rect(),controlBounds=new android.graphics.Rect();
            assertTrue(view.getGlobalVisibleRect(movieBounds));assertTrue(close.getGlobalVisibleRect(controlBounds));
            assertTrue("Playback controls must remain below the video",movieBounds.bottom<=controlBounds.top);
        });
        android.graphics.Bitmap frame=instrumentation.getUiAutomation().takeScreenshot();assertNotNull(frame);
        ByteArrayOutputStream movieFrame=new ByteArrayOutputStream();frame.compress(android.graphics.Bitmap.CompressFormat.PNG,100,movieFrame);frame.recycle();
        publishProof(context,"screen-playback.png",movieFrame.toByteArray(),"image/png");
        instrumentation.runOnMainSync(player::finish);
        instrumentation.getUiAutomation().waitForIdle(1000,5000);
        // Cancel only a fresh service job. Earlier completed show files must survive.
        File cancelJob=new File(context.getFilesDir(),"smoke-cancelled");
        JSONObject cancelRequest=new JSONObject();JSONObject inputUris=new JSONObject();inputUris.put("audio",android.net.Uri.fromFile(new File(ri,"source.mp3")).toString());
        cancelRequest.put("inputs",inputUris);cancelRequest.put("mode","xlights");
        instrumentation.runOnMainSync(()->context.startForegroundService(new Intent(context,EngineService.class).putExtra("job",cancelJob.toString()).putExtra("request",cancelRequest.toString())));
        File cancelState=new File(cancelJob,"state.json");
        for(int attempt=0;attempt<80&&!cancelState.isFile();attempt++)Thread.sleep(250);
        assertTrue(cancelState.isFile());
        instrumentation.runOnMainSync(()->context.startService(new Intent(context,EngineService.class).setAction("cancel")));
        boolean cancelled=false;
        for(int attempt=0;attempt<40&&!cancelled;attempt++){Thread.sleep(250);cancelled="cancelled".equals(new JSONObject(new String(Files.readAllBytes(cancelState.toPath()),"UTF-8")).optString("phase"));}
        assertTrue("Foreground engine job must report cancellation",cancelled);
        assertTrue(new File(realResult.getString("bundle")).isFile());assertTrue(new File(fullResult.getString("bundle")).isFile());
        publishProof(context,"cancellation.json",Files.readAllBytes(cancelState.toPath()),"application/json");
    }
    private static android.widget.Button findButton(android.view.View root,String label){
        if(root instanceof android.widget.Button && label.contentEquals(((android.widget.Button)root).getText()))return (android.widget.Button)root;
        if(root instanceof android.view.ViewGroup){
            android.view.ViewGroup group=(android.view.ViewGroup)root;
            for(int i=0;i<group.getChildCount();i++){android.widget.Button match=findButton(group.getChildAt(i),label);if(match!=null)return match;}
        }
        return null;
    }
    private static android.widget.VideoView findVideo(android.view.View root){
        if(root instanceof android.widget.VideoView)return (android.widget.VideoView)root;
        if(root instanceof android.view.ViewGroup){
            android.view.ViewGroup group=(android.view.ViewGroup)root;
            for(int i=0;i<group.getChildCount();i++){android.widget.VideoView match=findVideo(group.getChildAt(i));if(match!=null)return match;}
        }
        return null;
    }
    static void publishProof(Context context,String name,byte[] bytes,String mime)throws Exception{
        ContentValues values=new ContentValues();values.put(MediaStore.MediaColumns.DISPLAY_NAME,name);values.put(MediaStore.MediaColumns.MIME_TYPE,mime);
        values.put(MediaStore.MediaColumns.RELATIVE_PATH,"Download/HelixAndroidSmoke");values.put(MediaStore.MediaColumns.IS_PENDING,1);
        android.net.Uri uri=context.getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI,values);assertNotNull(uri);
        try(OutputStream out=context.getContentResolver().openOutputStream(uri)){assertNotNull(out);out.write(bytes);}
        values.clear();values.put(MediaStore.MediaColumns.IS_PENDING,0);context.getContentResolver().update(uri,values,null,null);
    }
    static void syntheticWav(File file)throws Exception{
        int sr=22050,n=sr*8;ByteBuffer data=ByteBuffer.allocate(44+n*2).order(ByteOrder.LITTLE_ENDIAN);
        data.put("RIFF".getBytes()).putInt(n*2+36).put("WAVEfmt ".getBytes()).putInt(16).putShort((short)1).putShort((short)1).putInt(sr).putInt(sr*2).putShort((short)2).putShort((short)16).put("data".getBytes()).putInt(n*2);
        for(int i=0;i<n;i++){double y=.15*Math.sin(2*Math.PI*220*i/sr)+.1*Math.sin(2*Math.PI*440*i/sr);int beat=(i-(int)(.1*sr))%(sr/2);if(beat>=0&&beat<700)y+=.65*Math.exp(-beat/80.0)*Math.cos(beat*.3);data.putShort((short)(y*32767));}
        Files.write(file.toPath(),data.array());
    }
}

