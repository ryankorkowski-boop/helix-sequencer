package org.helixsequencer.android;
import android.app.Activity;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.view.Gravity;
import android.widget.*;
import java.util.ArrayList;
/** Controls remain below the video, with no floating popup window. */
public class PreviewActivity extends Activity {
    private VideoView video;
    private SeekBar seek;
    private Button play,previous,next;
    private TextView variantLabel;
    private ArrayList<String> playlist;
    private int playlistIndex;
    private final Handler handler=new Handler();
    private boolean seeking,prepared,resumePlayback=true;
    private int position;
    private final Runnable tick=new Runnable(){public void run(){
        if(video!=null&&prepared&&!seeking){seek.setMax(video.getDuration());seek.setProgress(video.getCurrentPosition());}
        if(play!=null&&video!=null)play.setText(video.isPlaying()?"Pause":"Play");handler.postDelayed(this,250);
    }};
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        playlist=getIntent().getStringArrayListExtra("playlist");
        if(playlist==null)playlist=new ArrayList<>();
        String initial=getIntent().getStringExtra("path");
        if(playlist.isEmpty()&&initial!=null)playlist.add(initial);
        playlistIndex=Math.max(0,Math.min(getIntent().getIntExtra("playlist_index",0),playlist.size()-1));
        if(state!=null){position=state.getInt("position");resumePlayback=state.getBoolean("playing",true);
            playlistIndex=Math.max(0,Math.min(state.getInt("playlist_index",playlistIndex),playlist.size()-1));}
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(Color.BLACK);
        root.setOnApplyWindowInsetsListener((v,i)->{v.setPadding(i.getSystemWindowInsetLeft(),i.getSystemWindowInsetTop(),i.getSystemWindowInsetRight(),i.getSystemWindowInsetBottom());return i;});
        FrameLayout picture=new FrameLayout(this);root.addView(picture,new LinearLayout.LayoutParams(-1,0,1));
        video=new VideoView(this);picture.addView(video,new FrameLayout.LayoutParams(-1,-1,Gravity.CENTER));
        LinearLayout controls=new LinearLayout(this);root.addView(controls,new LinearLayout.LayoutParams(-1,-2));
        previous=new Button(this);previous.setText("Previous");controls.addView(previous);
        play=new Button(this);play.setText("Play");controls.addView(play);play.setEnabled(false);
        seek=new SeekBar(this);seek.setContentDescription("Preview position");controls.addView(seek,new LinearLayout.LayoutParams(0,-2,1));
        next=new Button(this);next.setText("Next");controls.addView(next);
        Button close=new Button(this);close.setText("Close");controls.addView(close);close.setOnClickListener(v->finish());
        variantLabel=new TextView(this);variantLabel.setTextColor(Color.WHITE);variantLabel.setGravity(Gravity.CENTER);
        root.addView(variantLabel,new LinearLayout.LayoutParams(-1,-2));setContentView(root);
        previous.setOnClickListener(v->selectVariant(playlistIndex-1));
        next.setOnClickListener(v->selectVariant(playlistIndex+1));
        play.setOnClickListener(v->{if(video.isPlaying()){video.pause();resumePlayback=false;}else{video.start();resumePlayback=true;}});
        seek.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){
            public void onStartTrackingTouch(SeekBar s){seeking=true;}
            public void onProgressChanged(SeekBar s,int p,boolean user){if(user&&prepared){position=p;video.seekTo(p);}}
            public void onStopTrackingTouch(SeekBar s){seeking=false;}
        });
        video.setOnPreparedListener(p->{prepared=true;play.setEnabled(true);seek.setMax(video.getDuration());video.seekTo(position);if(resumePlayback)video.start();});
        video.setOnCompletionListener(p->{resumePlayback=false;play.setText("Play");});
        selectVariant(playlistIndex, state!=null);
        video.setOnErrorListener((p,w,e)->{new android.app.AlertDialog.Builder(this).setMessage("Preview playback failed ("+w+", "+e+")").setPositiveButton("Close",(d,x)->finish()).show();return true;});
    }
    private void selectVariant(int index){selectVariant(index,false);}
    private void selectVariant(int index,boolean restoring){
        if(index<0||index>=playlist.size())return;
        playlistIndex=index;
        previous.setEnabled(index>0);next.setEnabled(index<playlist.size()-1);
        variantLabel.setText("Completed preview "+(index+1)+" of "+playlist.size());
        String path=playlist.get(index);
        if(path==null||path.isEmpty()||!new java.io.File(path).isFile()){
            new android.app.AlertDialog.Builder(this)
                .setMessage("This variant preview is no longer available. Return to Results and choose a completed preview.")
                .setPositiveButton("Close",(d,x)->finish()).setOnCancelListener(d->finish()).show();
            return;
        }
        video.stopPlayback();prepared=false;play.setEnabled(false);
        if(!restoring){position=0;resumePlayback=true;}
        seek.setProgress(position);
        video.setVideoURI(Uri.fromFile(new java.io.File(path)));
    }
    @Override protected void onResume(){super.onResume();handler.post(tick);if(prepared&&resumePlayback)video.start();}
    @Override protected void onSaveInstanceState(Bundle state){state.putInt("position",prepared?video.getCurrentPosition():position);state.putBoolean("playing",prepared?video.isPlaying():resumePlayback);state.putInt("playlist_index",playlistIndex);super.onSaveInstanceState(state);}
    @Override protected void onPause(){if(prepared){resumePlayback=video.isPlaying();position=video.getCurrentPosition();video.pause();}handler.removeCallbacks(tick);super.onPause();}
}
