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
        context.getSharedPreferences(MainActivity.class.getSimpleName(),0).edit().putBoolean("walkthrough_seen",true).apply();
        android.app.Instrumentation instrumentation=InstrumentationRegistry.getInstrumentation();
        instrumentation.runOnMainSync(()->context.startActivity(new Intent(context,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)));
        instrumentation.getUiAutomation().waitForIdle(1000,5000);
        android.graphics.Bitmap shot=instrumentation.getUiAutomation().takeScreenshot();
        if(shot!=null){ByteArrayOutputStream png=new ByteArrayOutputStream();shot.compress(android.graphics.Bitmap.CompressFormat.PNG,100,png);shot.recycle();publishProof(context,"launcher.png",png.toByteArray(),"image/png");}
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

