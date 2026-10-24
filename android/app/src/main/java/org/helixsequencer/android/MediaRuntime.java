package org.helixsequencer.android;

import android.graphics.*;
import android.media.*;
import android.opengl.*;
import android.view.Surface;
import java.io.*;
import java.nio.*;

/** Native decoding and H.264/AAC encoding; no downloaded FFmpeg executables. */
public final class MediaRuntime {
    private MediaRuntime(){}
    static int track(MediaExtractor e,String prefix)throws IOException{
        for(int i=0;i<e.getTrackCount();i++)if(e.getTrackFormat(i).getString(MediaFormat.KEY_MIME).startsWith(prefix))return i;
        throw new IOException("No "+prefix+" track");
    }
    public static void decodeWav(String source,String output)throws Exception{
        MediaExtractor extractor=new MediaExtractor();MediaCodec codec=null;
        try(RandomAccessFile wav=new RandomAccessFile(output,"rw")){
            extractor.setDataSource(source);int index=track(extractor,"audio/");extractor.selectTrack(index);
            MediaFormat format=extractor.getTrackFormat(index);codec=MediaCodec.createDecoderByType(format.getString(MediaFormat.KEY_MIME));
            format.setInteger(MediaFormat.KEY_PCM_ENCODING,AudioFormat.ENCODING_PCM_16BIT);codec.configure(format,null,null,0);codec.start();
            wav.setLength(0);wav.write(new byte[44]);boolean inputDone=false,outputDone=false;
            int rate=format.getInteger(MediaFormat.KEY_SAMPLE_RATE),channels=format.getInteger(MediaFormat.KEY_CHANNEL_COUNT),encoding=AudioFormat.ENCODING_PCM_16BIT;
            MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();long bytes=0,lastProgress=System.nanoTime();
            while(!outputDone){
                if(!inputDone){int i=codec.dequeueInputBuffer(10000);if(i>=0){ByteBuffer b=codec.getInputBuffer(i);int n=extractor.readSampleData(b,0);
                    codec.queueInputBuffer(i,0,Math.max(n,0),n<0?0:extractor.getSampleTime(),n<0?MediaCodec.BUFFER_FLAG_END_OF_STREAM:0);
                    if(n<0)inputDone=true;else extractor.advance();}}
                int i=codec.dequeueOutputBuffer(info,10000);
                if(i==MediaCodec.INFO_OUTPUT_FORMAT_CHANGED){MediaFormat f=codec.getOutputFormat();rate=f.getInteger(MediaFormat.KEY_SAMPLE_RATE);channels=f.getInteger(MediaFormat.KEY_CHANNEL_COUNT);
                    if(f.containsKey(MediaFormat.KEY_PCM_ENCODING))encoding=f.getInteger(MediaFormat.KEY_PCM_ENCODING);}
                if(i>=0){lastProgress=System.nanoTime();ByteBuffer b=codec.getOutputBuffer(i);b.position(info.offset);b.limit(info.offset+info.size);b.order(ByteOrder.LITTLE_ENDIAN);
                    byte[] data;
                    if(encoding==AudioFormat.ENCODING_PCM_FLOAT){data=new byte[(info.size/4)*2];ByteBuffer pcm=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
                        while(b.remaining()>=4)pcm.putShort((short)Math.round(Math.max(-1,Math.min(1,b.getFloat()))*32767));}
                    else if(encoding==AudioFormat.ENCODING_PCM_16BIT){data=new byte[info.size];b.get(data);}
                    else throw new IOException("Unsupported decoded PCM encoding "+encoding);
                    wav.write(data);bytes+=data.length;outputDone=(info.flags&MediaCodec.BUFFER_FLAG_END_OF_STREAM)!=0;codec.releaseOutputBuffer(i,false);
                    if(bytes>1024L*1024*1024)throw new IOException("Decoded audio exceeds 1 GB; shorten the song");}
                if(System.nanoTime()-lastProgress>30_000_000_000L)throw new IOException("Audio decoder stalled");
            }
            if(bytes==0)throw new IOException("Audio decoder returned no samples");
            wav.seek(0);ByteBuffer h=ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN);
            h.put("RIFF".getBytes("US-ASCII")).putInt((int)bytes+36).put("WAVEfmt ".getBytes("US-ASCII")).putInt(16).putShort((short)1).putShort((short)channels)
                .putInt(rate).putInt(rate*channels*2).putShort((short)(channels*2)).putShort((short)16).put("data".getBytes("US-ASCII")).putInt((int)bytes);wav.write(h.array());
        }finally{if(codec!=null){try{codec.stop();}catch(Exception ignored){}codec.release();}extractor.release();}
    }
    static void encodeAac(String wav,String output,long duration)throws Exception{
        MediaCodec codec=null;MediaMuxer muxer=null;boolean muxStarted=false;
        try(RandomAccessFile in=new RandomAccessFile(wav,"r")){
            byte[] header=new byte[44];in.readFully(header);ByteBuffer h=ByteBuffer.wrap(header).order(ByteOrder.LITTLE_ENDIAN);
            int channels=h.getShort(22),rate=h.getInt(24);long available=in.length()-44,max=duration*rate*channels*2/1_000_000;
            MediaFormat format=MediaFormat.createAudioFormat("audio/mp4a-latm",rate,channels);format.setInteger(MediaFormat.KEY_AAC_PROFILE,MediaCodecInfo.CodecProfileLevel.AACObjectLC);
            format.setInteger(MediaFormat.KEY_BIT_RATE,128000);codec=MediaCodec.createEncoderByType("audio/mp4a-latm");codec.configure(format,null,null,MediaCodec.CONFIGURE_FLAG_ENCODE);codec.start();
            muxer=new MediaMuxer(output,MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4);int track=-1;boolean inputDone=false,done=false;long consumed=0,lastProgress=System.nanoTime();
            MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();
            while(!done){
                if(!inputDone){int i=codec.dequeueInputBuffer(10000);if(i>=0){ByteBuffer b=codec.getInputBuffer(i);int n=(int)Math.min(b.capacity(),max-consumed);n-=n%(channels*2);
                    byte[] data=new byte[n];int real=(int)Math.min(n,Math.max(0,available-consumed));if(real>0)in.readFully(data,0,real);b.put(data);codec.queueInputBuffer(i,0,n,consumed*1_000_000/(rate*channels*2),n==0?MediaCodec.BUFFER_FLAG_END_OF_STREAM:0);consumed+=n;if(n==0)inputDone=true;}}
                int i=codec.dequeueOutputBuffer(info,10000);
                if(i==MediaCodec.INFO_OUTPUT_FORMAT_CHANGED){track=muxer.addTrack(codec.getOutputFormat());muxer.start();muxStarted=true;}
                if(i>=0){lastProgress=System.nanoTime();if(info.size>0&&(info.flags&MediaCodec.BUFFER_FLAG_CODEC_CONFIG)==0)muxer.writeSampleData(track,codec.getOutputBuffer(i),info);
                    done=(info.flags&MediaCodec.BUFFER_FLAG_END_OF_STREAM)!=0;codec.releaseOutputBuffer(i,false);}
                if(System.nanoTime()-lastProgress>30_000_000_000L)throw new IOException("AAC encoder stalled");
            }
        }finally{if(codec!=null){try{codec.stop();}catch(Exception ignored){}codec.release();}if(muxer!=null){if(muxStarted)muxer.stop();muxer.release();}}
    }
    static void mux(String video,String audio,String output,long maxPts)throws Exception{
        MediaExtractor v=new MediaExtractor(),a=new MediaExtractor();MediaMuxer m=null;boolean started=false;
        try{
            v.setDataSource(video);a.setDataSource(audio);int vi=track(v,"video/"),ai=track(a,"audio/");v.selectTrack(vi);a.selectTrack(ai);
            m=new MediaMuxer(output,MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4);int vo=m.addTrack(v.getTrackFormat(vi)),ao=m.addTrack(a.getTrackFormat(ai));m.start();started=true;
            ByteBuffer buffer=ByteBuffer.allocateDirect(4*1024*1024);MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();
            while(v.getSampleTime()>=0||a.getSampleTime()>=0){
                long vt=v.getSampleTime(),at=a.getSampleTime();boolean videoNext=vt>=0&&(at<0||vt<=at);MediaExtractor e=videoNext?v:a;
                if(videoNext&&e.getSampleTime()>=maxPts){while(e.advance()){}continue;}
                buffer.clear();int n=e.readSampleData(buffer,0);if(n<0)break;
                info.set(0,n,e.getSampleTime(),e.getSampleFlags());m.writeSampleData(videoNext?vo:ao,buffer,info);e.advance();
            }
        }finally{v.release();a.release();if(m!=null){if(started)m.stop();m.release();}}
    }
    public static final class VideoEncoder implements AutoCloseable {
        private MediaCodec codec;private MediaMuxer muxer;private boolean muxStarted,closed;private int track=-1,width,height;
        private Surface input;private EGLDisplay display;private EGLContext context;private EGLSurface eglSurface;
        private int program,texture;private FloatBuffer vertices,uv;
        VideoEncoder(String output,int w,int h,int fps)throws Exception{
            width=w;height=h;
            try{
                MediaFormat f=MediaFormat.createVideoFormat("video/avc",w,h);f.setInteger(MediaFormat.KEY_COLOR_FORMAT,MediaCodecInfo.CodecCapabilities.COLOR_FormatSurface);
                f.setInteger(MediaFormat.KEY_BIT_RATE,2_000_000);f.setInteger(MediaFormat.KEY_FRAME_RATE,fps);f.setInteger(MediaFormat.KEY_I_FRAME_INTERVAL,1);
                codec=MediaCodec.createEncoderByType("video/avc");codec.configure(f,null,null,MediaCodec.CONFIGURE_FLAG_ENCODE);input=codec.createInputSurface();codec.start();
                muxer=new MediaMuxer(output,MediaMuxer.OutputFormat.MUXER_OUTPUT_MPEG_4);setupEgl();
            }catch(Exception e){abort();throw e;}
        }
        private static FloatBuffer floats(float... a){FloatBuffer b=ByteBuffer.allocateDirect(a.length*4).order(ByteOrder.nativeOrder()).asFloatBuffer();b.put(a).position(0);return b;}
        private void setupEgl()throws IOException{
            display=EGL14.eglGetDisplay(EGL14.EGL_DEFAULT_DISPLAY);int[] version=new int[2];if(!EGL14.eglInitialize(display,version,0,version,1))throw new IOException("Cannot initialize EGL");
            int[] attribs={EGL14.EGL_RED_SIZE,8,EGL14.EGL_GREEN_SIZE,8,EGL14.EGL_BLUE_SIZE,8,EGL14.EGL_RENDERABLE_TYPE,EGL14.EGL_OPENGL_ES2_BIT,0x3142,1,EGL14.EGL_NONE};
            EGLConfig[] configs=new EGLConfig[1];int[] count=new int[1];EGL14.eglChooseConfig(display,attribs,0,configs,0,1,count,0);if(count[0]==0)throw new IOException("No recordable EGL config");
            context=EGL14.eglCreateContext(display,configs[0],EGL14.EGL_NO_CONTEXT,new int[]{EGL14.EGL_CONTEXT_CLIENT_VERSION,2,EGL14.EGL_NONE},0);
            eglSurface=EGL14.eglCreateWindowSurface(display,configs[0],input,new int[]{EGL14.EGL_NONE},0);
            if(!EGL14.eglMakeCurrent(display,eglSurface,eglSurface,context))throw new IOException("Cannot activate preview surface");
            int vertex=shader(GLES20.GL_VERTEX_SHADER,"attribute vec4 p;attribute vec2 u;varying vec2 v;void main(){gl_Position=p;v=u;}");
            int fragment=shader(GLES20.GL_FRAGMENT_SHADER,"precision mediump float;varying vec2 v;uniform sampler2D s;void main(){gl_FragColor=texture2D(s,v);}");
            program=GLES20.glCreateProgram();GLES20.glAttachShader(program,vertex);GLES20.glAttachShader(program,fragment);GLES20.glLinkProgram(program);
            int[] ok=new int[1];GLES20.glGetProgramiv(program,GLES20.GL_LINK_STATUS,ok,0);if(ok[0]==0)throw new IOException(GLES20.glGetProgramInfoLog(program));
            GLES20.glDeleteShader(vertex);GLES20.glDeleteShader(fragment);
            int[] textures=new int[1];GLES20.glGenTextures(1,textures,0);texture=textures[0];GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture);
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_LINEAR);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_LINEAR);
            GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_S,GLES20.GL_CLAMP_TO_EDGE);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_T,GLES20.GL_CLAMP_TO_EDGE);
            vertices=floats(-1,-1,1,-1,-1,1,1,1);uv=floats(0,1,1,1,0,0,1,0);
        }
        private static int shader(int type,String code)throws IOException{int s=GLES20.glCreateShader(type);GLES20.glShaderSource(s,code);GLES20.glCompileShader(s);int[] ok=new int[1];GLES20.glGetShaderiv(s,GLES20.GL_COMPILE_STATUS,ok,0);if(ok[0]==0)throw new IOException(GLES20.glGetShaderInfoLog(s));return s;}
        public void frame(byte[] png,long pts)throws Exception{
            drain(false);Bitmap bitmap=BitmapFactory.decodeByteArray(png,0,png.length);if(bitmap==null)throw new IOException("Invalid preview frame");
            try{GLES20.glViewport(0,0,width,height);GLES20.glUseProgram(program);GLES20.glActiveTexture(GLES20.GL_TEXTURE0);GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture);GLUtils.texImage2D(GLES20.GL_TEXTURE_2D,0,bitmap,0);
                int p=GLES20.glGetAttribLocation(program,"p"),u=GLES20.glGetAttribLocation(program,"u");GLES20.glEnableVertexAttribArray(p);GLES20.glEnableVertexAttribArray(u);
                GLES20.glVertexAttribPointer(p,2,GLES20.GL_FLOAT,false,0,vertices);GLES20.glVertexAttribPointer(u,2,GLES20.GL_FLOAT,false,0,uv);
                GLES20.glUniform1i(GLES20.glGetUniformLocation(program,"s"),0);GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP,0,4);
                EGLExt.eglPresentationTimeANDROID(display,eglSurface,pts*1000);if(!EGL14.eglSwapBuffers(display,eglSurface))throw new IOException("Preview surface swap failed");
            }finally{bitmap.recycle();}
        }
        private void drain(boolean eos)throws Exception{
            MediaCodec.BufferInfo info=new MediaCodec.BufferInfo();long start=System.nanoTime();
            while(true){int i=codec.dequeueOutputBuffer(info,10000);
                if(i==MediaCodec.INFO_TRY_AGAIN_LATER){if(!eos)return;if(System.nanoTime()-start>30_000_000_000L)throw new IOException("H.264 encoder stalled");}
                else if(i==MediaCodec.INFO_OUTPUT_FORMAT_CHANGED){track=muxer.addTrack(codec.getOutputFormat());muxer.start();muxStarted=true;}
                else if(i>=0){if(info.size>0&&(info.flags&MediaCodec.BUFFER_FLAG_CODEC_CONFIG)==0)muxer.writeSampleData(track,codec.getOutputBuffer(i),info);
                    boolean done=(info.flags&MediaCodec.BUFFER_FLAG_END_OF_STREAM)!=0;codec.releaseOutputBuffer(i,false);if(done)return;}
            }
        }
        public void close()throws Exception{if(closed)return;try{codec.signalEndOfInputStream();drain(true);}finally{abort();}}
        public void abort(){if(closed)return;closed=true;
            if(display!=null){if(program!=0)GLES20.glDeleteProgram(program);EGL14.eglMakeCurrent(display,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_SURFACE,EGL14.EGL_NO_CONTEXT);
                if(eglSurface!=null)EGL14.eglDestroySurface(display,eglSurface);if(context!=null)EGL14.eglDestroyContext(display,context);EGL14.eglTerminate(display);}
            if(input!=null)input.release();if(codec!=null){try{codec.stop();}catch(Exception ignored){}codec.release();}
            if(muxer!=null){try{if(muxStarted)muxer.stop();}catch(Exception ignored){}muxer.release();}
        }
    }
}
