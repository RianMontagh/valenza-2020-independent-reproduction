#!/usr/bin/env python3
"""Run the documented procedure and preserve its actual outcome."""
import datetime
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
def main():
 mode=sys.argv[1] if len(sys.argv)>1 else '--offline'
 if mode not in ['--offline','--download']:raise SystemExit('Use --offline or --download')
 result=ROOT/'data/results';result.mkdir(parents=True,exist_ok=True)
 env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
 for name,subdir in [('TMPDIR','tmp'),('XDG_CACHE_HOME','cache'),('MPLCONFIGDIR','matplotlib'),('TEXMFVAR','texmf-var'),('TEXMFCONFIG','texmf-config'),('TEXMFCACHE','texmf-cache')]:
  path=ROOT/'.runtime'/subdir;path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
 command=['bash','rebuild.sh',mode]
 start=time.time();stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with (result/'rebuild.log').open('w') as log:
  proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
  for line in proc.stdout:log.write(line);log.flush();print(line,end='',flush=True)
  status=proc.wait()
 versions={}
 for name,cmd in [('compiler',['g++','--version']),('cmake',['cmake','--version']),('python',[str(ROOT/'.runtime/py311/bin/python'),'--version']),('pdflatex',['pdflatex','--version'])]:
  versions[name]=subprocess.check_output(cmd,cwd=ROOT,env=env,text=True).splitlines()[0]
 outcome={'command':' '.join(command),'started_utc':stamp,'elapsed_seconds':time.time()-start,'exit_code':status,'platform':platform.platform(),'cpu_count':os.cpu_count(),'versions':versions,'scientific_scope':'Partial reproduction; successful build does not imply all scientific panels reproduced.'}
 (result/'rebuild_outcome.json').write_text(json.dumps(outcome,indent=2)+'\n')
 (ROOT/'report/execution.tex').write_text('The documented '+r'\texttt{'+mode+'} procedure completed with exit code '+str(status)+f' in {outcome["elapsed_seconds"]:.1f} s. '+r'\texttt{data/results/rebuild\_outcome.json} records the command, platform, and tool versions.'+'\n')
 if status==0:
  with (result/'report_finalize.log').open('w') as log:
   for _ in range(2):subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','report.tex'],cwd=ROOT/'report',env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  subprocess.run([str(ROOT/'.runtime/py311/bin/python'),'scripts/manifest.py'],cwd=ROOT,env=env,check=True)
 print(json.dumps(outcome,indent=2))
 raise SystemExit(status)
if __name__=='__main__':main()
