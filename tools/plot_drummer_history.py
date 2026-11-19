"""Independent mix waveform, band, onset and historical/rejected event plots."""
import librosa,numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
from pathlib import Path
out=Path('test_runs/drummer_recovery');h=json.loads((out/'historical.json').read_text())['events']; r=json.loads((out/'rejected.json').read_text())['events']
y,sr=librosa.load('Helix Audiolights.mp3',sr=None,mono=True)
_,p=librosa.effects.hpss(y)
S=np.abs(librosa.stft(y,n_fft=2048,hop_length=128));f=librosa.fft_frequencies(sr=sr);t=librosa.frames_to_time(np.arange(S.shape[1]),sr=sr,hop_length=128)
e=librosa.onset.onset_strength(y=p,sr=sr,hop_length=512);te=librosa.frames_to_time(np.arange(len(e)),sr=sr,hop_length=512)
colors=dict(kick='red',snare='purple',tom='green',hihat='orange',cymbal='blue',drum_bus='gray');kinds=list(colors)
for start,end in [(10.7,14.9),(18.5,20.5),(23,24.8),(65,68),(100,103)]:
 fig,axes=plt.subplots(6,1,figsize=(17,11),sharex=True,gridspec_kw={'height_ratios':[1,2,1,1,1,1]})
 a=int(start*sr);b=int(end*sr);axes[0].plot(np.arange(a,b,32)/sr,y[a:b:32],lw=.4);axes[0].set_ylabel('mix waveform')
 ix=(t>=start)&(t<end);axes[1].pcolormesh(t[ix],f,20*np.log10(S[:,ix]+1e-7),vmin=-50,vmax=20,cmap='magma',shading='auto');axes[1].set_ylim(20,14000);axes[1].set_yscale('log');axes[1].set_ylabel('mix spectrum Hz')
 for lo,hi,col,label in [(30,180,'red','30–180Hz'),(180,2500,'purple','180–2500Hz'),(5000,14000,'orange','5–14kHz')]:
  band=np.sqrt(np.mean(S[(f>=lo)&(f<hi)]**2,axis=0));axes[2].plot(t[ix],band[ix]/max(band[ix].max(),1e-9),color=col,label=label,lw=1)
 axes[2].legend(loc='upper right');axes[2].set_ylabel('band amplitudes')
 sel=(te>=start)&(te<end);axes[3].plot(te[sel],e[sel]);axes[3].set_ylabel('HPSS onset')
 for ax,rows,key,name in [(axes[4],h,'drum_type','historical'),(axes[5],r,'drum_type','rejected')]:
  for x in rows:
   if start<=x['timestamp']<=end: ax.scatter(x['timestamp'],kinds.index(x[key]),color=colors[x[key]],s=25);ax.annotate(f"{x['timestamp']:.3f}",(x['timestamp'],kinds.index(x[key])),fontsize=6,rotation=65)
  ax.set_yticks(range(6),kinds);ax.set_ylabel(name);ax.grid(axis='x',alpha=.4)
 axes[-1].set_xlim(start,end);axes[-1].set_xlabel('absolute song seconds');fig.suptitle(f'Independent mix evidence and detector disagreement {start}–{end}s');fig.tight_layout();fig.savefig(out/f'comparison_{start}.png');plt.close(fig)
print('plots saved')
