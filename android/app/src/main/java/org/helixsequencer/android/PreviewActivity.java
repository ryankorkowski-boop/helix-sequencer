package org.helixsequencer.android;
import android.app.Activity;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.view.Gravity;
import android.widget.*;
/** Controls remain below the video, with no floating popup window. */
public class PreviewActivity extends Activity {
    private VideoView video;
    private SeekBar seek;
    private Button play;
    private final Handler handler=new Handler();
    private boolean seeking,prepared,resumePlayback=true;
    private int position;
    private final Runnable tick=new Runnable(){public void run(){
        if(prepared&&!seeking){seek.setMax(video.getDuration());seek.setProgress(video.getCurrentPosition());}
        play.setText(video.isPlaying()?"Pause":"Play");handler.postDelayed(this,250);
    }};
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        if(state!=null){position=state.getInt("position");resumePlayback=state.getBoolean("playing",true);}
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(Color.BLACK);
        root.setOnApplyWindowInsetsListener((v,i)->{v.setPadding(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());return i;});
        FrameLayout picture=new FrameLayout(this);root.addView(picture,new LinearLayout.LayoutParams(-1,0,1));
        video=new VideoView(this);picture.addView(video,new FrameLayout.LayoutParams(-1,-1,Gravity.CENTER));
        LinearLayout controls=new LinearLayout(this);root.addView(controls,new LinearLayout.LayoutParams(-1,-2));
        play=new Button(this);play.setText("Play");controls.addView(play);play.setEnabled(false);
        seek=new SeekBar(this);seek.setContentDescription("Preview position");controls.addView(seek,new LinearLayout.LayoutParams(0,-2,1));
        Button close=new Button(this);close.setText("Close");controls.addView(close);close.setOnClickListener(v->finish());setContentView(root);
        play.setOnClickListener(v->{if(video.isPlaying()){video.pause();resumePlayback=false;}else{video.start();resumePlayback=true;}});
        seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onStartTrackingTouch(SeekBar s){seeking=true;}
            public void onProgressChanged(SeekBar s,int p,boolean user){if(user&&prepared){position=p;video.seekTo(p);}}
            public void onStopTrackingTouch(SeekBar s){seeking=false;}
        });
        video.setVideoURI(Uri.fromFile(new java.io.File(getIntent().getStringExtra("path"))));
        video.setOnPreparedListener(p->{prepared=true;play.setEnabled(true);seek.setMax(video.getDuration());video.seekTo(position);if(resumePlayback)video.start();});
        video.setOnCompletionListener(p->{resumePlayback=false;play.setText("Play");});
        video.setOnErrorListener((p,w,e)->{new android.app.AlertDialog.Builder(this).setMessage("Preview playback failed ("+w+", "+e+")").setPositiveButton("Close",(d,x)->finish()).show();return true;});
    }
    @Override protected void onResume(){super.onResume();handler.post(tick);if(prepared&&resumePlayback)video.start();}
    @Override protected void onSaveInstanceState(Bundle state){state.putInt("position",video.getCurrentPosition());state.putBoolean("playing",video.isPlaying()||resumePlayback);super.onSaveInstanceState(state);}
    @Override protected void onPause(){resumePlayback=video.isPlaying();position=video.getCurrentPosition();video.pause();handler.removeCallbacks(tick);super.onPause();}
}
