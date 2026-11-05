import runpy,librosa,numpy as np
from core import bounded_audio as bounded
s=runpy.run_path('tests/test_bounded_audio.py')['source'];sr=22050
frames=4097;y=s(sr,seconds=((frames-1)*512+137)/sr)
m=np.abs(librosa.stft(y,n_fft=2048,hop_length=512));t=librosa.estimate_tuning(S=m,sr=sr)
c=librosa.feature.chroma_stft(S=m,sr=sr,hop_length=512,tuning=t)
def ent(c):
 p=c/(np.sum(c,axis=0)+1e-9);return -np.sum(p*np.log2(p+1e-9),axis=0)/np.log2(12)
e=ent(c)
for width in [512,768,1024,1344,1536,1920,2048,3072,4096]:
 arr=[]
 for a,b in bounded.magnitude_blocks(y,hop=512,block_frames=width):
  arr.append(librosa.feature.chroma_stft(S=b,sr=sr,hop_length=512,tuning=t))
 cc=np.concatenate(arr,axis=1);diff=np.abs(ent(cc)-e)
 print(width,'chroma',np.max(np.abs(c-cc)),np.sum(c!=cc),'e',np.max(diff),np.sum(diff>1e-7),'indices',np.where(diff>1e-7)[0][:25],flush=True)
