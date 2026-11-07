"""CI transport fixture only: authentic HTTP API, synthetic child, no musical claims."""
import argparse
from pathlib import Path
import sys
from tools.desktop_remote import RemoteJobs,RemoteServer

TOKEN='synthetic-emulator-transport-key-only-123456789'
SCRIPT="import sys,json,zipfile;from pathlib import Path;p=Path(sys.argv[1]);(p/'result.json').write_text(json.dumps({'preview':''}));z=zipfile.ZipFile(p/'Helix-show.zip','w');z.writestr('transport-only.txt','Not a musical render');z.close()"

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--jobs',type=Path,required=True);args=parser.parse_args()
    jobs=RemoteJobs(args.jobs,TOKEN,command=lambda folder:[sys.executable,'-c',SCRIPT,str(folder)])
    server=RemoteServer(('0.0.0.0',8765),jobs)
    try:server.serve_forever()
    finally:jobs.close();server.server_close()

if __name__=='__main__':main()
