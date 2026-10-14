"""Temporary, encrypted file transfer for the authorized sampler rebuild.
Only an ephemeral runner key decrypts source capabilities; never log URLs/headers.
"""
from __future__ import annotations
import argparse, base64, json, os, subprocess, time, urllib.parse, uuid
from pathlib import Path
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

PUBLIC = Path('evidence/sampler_recovery/public_key.json')
PAYLOAD = 'evidence/sampler_recovery/encrypted_inputs.json'
LABEL = b'helix-sampler-transfer-v1'

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['prepare','receive']);a=p.parse_args()
    private=Path(os.environ['RUNNER_TEMP'])/'helix_sampler_ephemeral.pem'
    if a.mode=='prepare':
        key=rsa.generate_private_key(public_exponent=65537,key_size=3072)
        private.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
        private.chmod(0o600);n=key.public_key().public_numbers()
        PUBLIC.parent.mkdir(parents=True,exist_ok=True)
        PUBLIC.write_text(json.dumps(dict(run_id=os.environ['GITHUB_RUN_ID'],nonce=uuid.uuid4().hex,n=str(n.n),e=n.e,source_commit=os.environ['GITHUB_SHA']),indent=2)+'\n')
        print('Prepared public transfer key; private key stays in the runner.',flush=True);return
    public=json.loads(PUBLIC.read_text());token=os.environ['GH_TOKEN']
    api='https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+'/contents/'+PAYLOAD
    deadline=time.monotonic()+900;payload=None
    while time.monotonic()<deadline:
        r=requests.get(api,params={'ref':os.environ['GITHUB_REF_NAME']},headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'},timeout=30)
        if r.status_code==200:
            candidate=json.loads(base64.b64decode(r.json()['content']))
            if candidate.get('nonce')==public['nonce'] and str(candidate.get('run_id'))==public['run_id']:
                payload=candidate;break
        time.sleep(5)
    if payload is None:raise RuntimeError('Encrypted input did not arrive within the transfer window')
    key=serialization.load_pem_private_key(private.read_bytes(),password=None)
    raw=b''.join(key.decrypt(bytes.fromhex(block),padding.OAEP(mgf=padding.MGF1(hashes.SHA256()),algorithm=hashes.SHA256(),label=LABEL)) for block in payload['blocks'])
    items=json.loads(raw);private.unlink()
    root=Path(os.environ['RUNNER_TEMP'])/'helix_sampler_private_inputs';root.mkdir(exist_ok=True)
    if {x['name'] for x in items}!={'sampler.zip','kit.zip'}:raise RuntimeError('Unexpected source file set')
    for item in items:
        u=urllib.parse.urlparse(item['url'])
        if u.scheme!='https' or not (u.hostname=='chatgpt.com' or u.hostname.endswith(('.blob.core.windows.net','.oaiusercontent.com','.amazonaws.com'))):
            raise RuntimeError('Unapproved source transfer host')
        try:
            with requests.get(item['url'],headers=item.get('headers') or {},stream=True,timeout=120) as r:
                if r.status_code!=200:raise RuntimeError('Source transfer status '+str(r.status_code))
                with (root/item['name']).open('wb') as out:
                    for chunk in r.iter_content(1048576):out.write(chunk)
        except Exception as exc:
            raise RuntimeError('Source transfer failed: '+type(exc).__name__) from None
        print('Received '+item['name']+'; capabilities are not persisted.',flush=True)

if __name__=='__main__':main()
