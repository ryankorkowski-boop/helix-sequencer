"""Small source-bound review batch for corrected band logic, separate from history."""
import json
from tools.rebuild_band_logic_review import ROOT,OUT
from tools.render_readable_band import render

JOBS=[
    dict(id='02',layout='infinity_observatory',start=100,focus='bass',seconds=12),
    dict(id='01',layout='cymatic_geode',start=108,focus='guitar',seconds=12),
    dict(id='05',layout='woven_aurora',start=0,focus='keyboard',seconds=12),
    dict(id='01',layout='prismatic_orrery',start=27,focus='stage',seconds=18),
    dict(id='05',layout='quasicrystal_theatre',start=68,focus='stage',seconds=18),
    dict(id='00',layout='prismatic_orrery',start=189,focus='drummer',seconds=3),
    dict(id='02',layout='prismatic_orrery',start=191,focus='drummer',seconds=3),
    dict(id='03',layout='prismatic_orrery',start=4,focus='drummer',seconds=3),
]


def main():
    sources={r['id']:r for r in json.loads((ROOT/'outputs/Snowman_Ensemble/sources.json').read_text())}
    proofs=[]
    for job in JOBS:
        args={k:v for k,v in job.items() if k!='id'}
        proofs.append(render(sources[job['id']],**args,output_root=OUT,suffix='_reassessed'))
    (ROOT/'evidence/band_logic_reassessment/render_batch.json').write_text(json.dumps(proofs,indent=2)+'\n')


if __name__=='__main__':main()
