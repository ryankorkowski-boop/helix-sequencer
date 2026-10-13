package org.helixsequencer.android;

import android.app.*;
import android.content.*;
import android.content.pm.ServiceInfo;
import android.net.Uri;
import android.os.*;
import com.chaquo.python.*;
import com.chaquo.python.android.AndroidPlatform;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.zip.*;

/** Runs CPython in its own process so cancellation can stop analysis safely. */
public class EngineService extends Service {
    private File job;
    private final StringBuilder logs=new StringBuilder();
    private volatile boolean started;
    private MediaRuntime.VideoEncoder encoder;
    private String previewDestination, previewWav;
    private long previewDuration;
    private int previewFps;
    @Override public IBinder onBind(Intent intent){return null;}
    @Override public int onStartCommand(Intent intent,int flags,int id){
        if(intent==null){stopSelf();return START_NOT_STICKY;}
        if("cancel".equals(intent.getAction())){
            if(job!=null)state("cancelled","Build cancelled",null);stopSelf();return START_NOT_STICKY;
        }
        if(started)return START_NOT_STICKY;
        started=true;job=new File(intent.getStringExtra("job"));job.mkdirs();
        NotificationManager manager=getSystemService(NotificationManager.class);
        manager.createNotificationChannel(new NotificationChannel("helix-jobs","Helix local builds",NotificationManager.IMPORTANCE_LOW));
        PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class),PendingIntent.FLAG_IMMUTABLE);
        Notification notice=new Notification.Builder(this,"helix-jobs").setSmallIcon(org.helixsequencer.android.R.drawable.helix_icon)
            .setContentTitle("Helix is sequencing on your phone").setContentText("Tap to see progress").setOngoing(true).setContentIntent(open).build();
        startForeground(1,notice,ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC);
        state("running","Preparing offline engine…",null);
        String request=intent.getStringExtra("request");
        new Thread(()->execute(request),"helix-engine").start();return START_NOT_STICKY;
    }
    private void execute(String raw){
        try{
            JSONObject request=new JSONObject(raw);File engine=unpack();File input=new File(job,"input");input.mkdirs();
            JSONObject uris=request.getJSONObject("inputs");
            String[][] destinations={{"audio","original-audio"},{"layout","xlights_rgbeffects.xml"},{"template","template.xsq"},{"lor","source.lms"},{"networks","xlights_networks.xml"},{"routing","routing.json"}};
            boolean lor="lor".equals(request.optString("mode"));
            for(String[] pair:destinations){
                if(!uris.has(pair[0])||lor&& !pair[0].equals("audio")&&!pair[0].equals("lor")||!lor&&pair[0].equals("lor"))continue;
                try(InputStream in=getContentResolver().openInputStream(Uri.parse(uris.getString(pair[0])));OutputStream out=new FileOutputStream(new File(input,pair[1]))){
                    if(in==null)throw new IOException("Cannot read "+pair[0]);copy(in,out);
                }
            }
            log("Decoding audio locally with Android MediaCodec…");
            MediaRuntime.decodeWav(new File(input,"original-audio").getAbsolutePath(),new File(input,"audio.wav").getAbsolutePath());
            if(!Python.isStarted())Python.start(new AndroidPlatform(this));
            PyObject result=Python.getInstance().getModule("helix_mobile").callAttr("run",engine.getAbsolutePath(),job.getAbsolutePath(),raw,this);
            state("complete","Sequence build complete",new JSONObject(result.toString()));
        }catch(Throwable e){log(android.util.Log.getStackTraceString(e));state("failed","Build failed: "+e.getMessage(),null);}
        finally{abortPreview();stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();}
    }
    static void copy(InputStream in,OutputStream out)throws IOException{
        byte[] buffer=new byte[65536];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);
    }
    public File unpack()throws Exception{
        String build;try(InputStream in=getAssets().open("helix-engine-build.json")){ByteArrayOutputStream b=new ByteArrayOutputStream();copy(in,b);build=b.toString("UTF-8");}
        String hash=new JSONObject(build).getString("archive_sha256");
        File target=new File(getFilesDir(),"engine/"+hash);
        File marker=new File(target,".complete");if(marker.isFile())return target;
        target.mkdirs();
        try(ZipInputStream zip=new ZipInputStream(getAssets().open("helix-engine.zip"))){
            ZipEntry entry;while((entry=zip.getNextEntry())!=null){
                File dest=new File(target,entry.getName());
                if(!dest.getCanonicalPath().startsWith(target.getCanonicalPath()+File.separator))throw new IOException("Unsafe engine archive path");
                if(entry.isDirectory()){dest.mkdirs();continue;}dest.getParentFile().mkdirs();
                try(OutputStream out=new FileOutputStream(dest)){copy(zip,out);}
            }
        }
        marker.createNewFile();return target;
    }
    public synchronized void log(String line){
        if(logs.length()>60000)logs.delete(0,logs.length()-45000);
        logs.append(line).append('\n');
        try(FileWriter out=new FileWriter(new File(job,"run.log"),true)){out.write(line+"\n");}catch(IOException ignored){}
        state("running",line.isEmpty()?"Sequencing…":line,null);
    }
    private synchronized void state(String phase,String message,JSONObject result){
        try{
            JSONObject state=new JSONObject();state.put("phase",phase);state.put("message",message);state.put("log",logs.toString());state.put("updated_ms",System.currentTimeMillis());
            if(result!=null){state.put("bundle",result.optString("bundle"));state.put("preview",result.optString("preview"));}
            File tmp=new File(job,"state.json.tmp");try(FileOutputStream out=new FileOutputStream(tmp)){out.write(state.toString().getBytes(StandardCharsets.UTF_8));}
            Files.move(tmp.toPath(),new File(job,"state.json").toPath(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
        }catch(Exception e){android.util.Log.e("Helix","Cannot save job state",e);}
    }
    public void beginPreview(String output,String wav,int width,int height,int fps)throws Exception{
        previewDestination=output;previewWav=wav;previewFps=fps;previewDuration=0;
        encoder=new MediaRuntime.VideoEncoder(output+".video.mp4",width,height,fps);
    }
    public void previewFrame(byte[] png,long pts)throws Exception{encoder.frame(png,pts);previewDuration=pts+1_000_000L/previewFps;}
    public void endPreview()throws Exception{
        encoder.close();encoder=null;
        String audio=previewDestination+".audio.m4a";
        try{
            MediaRuntime.encodeAac(previewWav,audio,previewDuration);
            MediaRuntime.mux(previewDestination+".video.mp4",audio,previewDestination,previewDuration);
        }finally{new File(audio).delete();new File(previewDestination+".video.mp4").delete();}
    }
    public void abortPreview(){if(encoder!=null){encoder.abort();encoder=null;}}
    @Override public void onTimeout(int id,int fgsType){if(job!=null)state("failed","Android stopped a build after its foreground time limit",null);stopSelf();}
    @Override public void onDestroy(){abortPreview();super.onDestroy();android.os.Process.killProcess(android.os.Process.myPid());}
}
