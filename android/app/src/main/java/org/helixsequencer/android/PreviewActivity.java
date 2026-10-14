package org.helixsequencer.android;
import android.app.Activity;
import android.net.Uri;
import android.os.Bundle;
import android.widget.*;
public class PreviewActivity extends Activity {
    private VideoView video;
    @Override public void onCreate(Bundle state){
        super.onCreate(state); video=new VideoView(this); setContentView(video);
        MediaController controls=new MediaController(this);controls.setAnchorView(video);video.setMediaController(controls);
        video.setVideoURI(Uri.fromFile(new java.io.File(getIntent().getStringExtra("path"))));
        video.setOnPreparedListener(p->{if(state!=null)video.seekTo(state.getInt("position"));video.start();});
        video.setOnErrorListener((p,w,e)->{new android.app.AlertDialog.Builder(this).setMessage("Preview playback failed ("+w+", "+e+")").setPositiveButton("Close",(d,x)->finish()).show();return true;});
    }
    @Override protected void onSaveInstanceState(Bundle state){state.putInt("position",video.getCurrentPosition());super.onSaveInstanceState(state);}
    @Override protected void onPause(){video.pause();super.onPause();}
}
