import runpy,librosa,numpy as np
from core import bounded_audio as bounded
s=runpy.run_path('tests/test_bounded_audio.py')['source']
y=librosa.effects.hpss(s(22050))[0];sr=22050
m=np.abs(librosa.stft(y,n_fft=2048,hop_length=512));t=librosa.estimate_tuning(S=m,sr=sr)
c=librosa.feature.chroma_stft(S=m,sr=sr,hop_length=512,tuning=t)
def ent(c):
 p=c/(np.sum(c,axis=0)+1e-9);return -np.sum(p*np.log2(p+1e-9),axis=0)/np.log2(12)
e=ent(c)
print('full',m.shape,m.flags,c.flags,t,flush=True)
for width in [128,256,512,1024,1341,1344,1536,2048]:
 arr=[];mag=[]
 for a,b in bounded.magnitude_blocks(y,hop=512,block_frames=width):
  arr.append(librosa.feature.chroma_stft(S=b,sr=sr,hop_length=512,tuning=t));mag.append(b)
 cc=np.concatenate(arr,axis=1)
 print(width,'mag',np.max(np.abs(np.concatenate(mag,axis=1)-m)),'chroma',np.max(np.abs(c-cc)),np.sum(c!=cc),'e_full',np.max(np.abs(ent(cc)-e)),np.sum(np.abs(ent(cc)-e)>1e-7),'e_block',np.max(np.abs(np.concatenate([ent(x) for x in arr])-e)),flush=True)
