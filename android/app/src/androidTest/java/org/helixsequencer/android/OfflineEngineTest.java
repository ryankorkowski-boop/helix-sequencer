package org.helixsequencer.android;

import android.content.Context;
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
        public void log(String value){android.util.Log.i("HelixSmoke",value);}
        public void beginPreview(String path,String wav,int width,int height,int fps)throws Exception{this.path=path;this.wav=wav;this.fps=fps;video=new MediaRuntime.VideoEncoder(path+".video.mp4",width,height,fps);}
        public void previewFrame(byte[] data,long pts)throws Exception{video.frame(data,pts);end=pts+1_000_000L/fps;}
        public void endPreview()throws Exception{video.close();video=null;MediaRuntime.encodeAac(wav,path+".audio.m4a",end);MediaRuntime.mux(path+".video.mp4",path+".audio.m4a",path,end);new File(path+".audio.m4a").delete();new File(path+".video.mp4").delete();}
        public void abortPreview(){if(video!=null){video.abort();video=null;}}
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
        }
    }
    static void syntheticWav(File file)throws Exception{
        int sr=22050,n=sr*8;ByteBuffer data=ByteBuffer.allocate(44+n*2).order(ByteOrder.LITTLE_ENDIAN);
        data.put("RIFF".getBytes()).putInt(n*2+36).put("WAVEfmt ".getBytes()).putInt(16).putShort((short)1).putShort((short)1).putInt(sr).putInt(sr*2).putShort((short)2).putShort((short)16).put("data".getBytes()).putInt(n*2);
        for(int i=0;i<n;i++){double y=.15*Math.sin(2*Math.PI*220*i/sr)+.1*Math.sin(2*Math.PI*440*i/sr);int beat=(i-(int)(.1*sr))%(sr/2);if(beat>=0&&beat<700)y+=.65*Math.exp(-beat/80.0)*Math.cos(beat*.3);data.putShort((short)(y*32767));}
        Files.write(file.toPath(),data.array());
    }
}
