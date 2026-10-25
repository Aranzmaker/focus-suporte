"""Produz evidência a partir das saídas reais dos comandos locais."""
import html
import json
from pathlib import Path
import platform
import subprocess
import sys

root=Path(__file__).parent
commands=[
    [sys.executable,'-m','compileall','-q','app.py','storage.py'],
    [sys.executable,'-m','coverage','run','--branch','--source=app,storage','-m','pytest','-q'],
    [sys.executable,'-m','coverage','report','--fail-under=80'],
]
records=[]
for command in commands:
    result=subprocess.run(command,cwd=root,capture_output=True,text=True,encoding='utf-8',errors='replace')
    records.append({'comando':['python',*command[1:]],'exit_code':result.returncode,
                    'stdout':result.stdout,'stderr':result.stderr})
    if result.returncode:
        break
revision=subprocess.run(['git','rev-parse','--verify','HEAD'],cwd=root,capture_output=True,text=True)
commit=revision.stdout.strip() if revision.returncode == 0 else 'Sem commit nesta verificação'
payload={'ambiente':platform.platform(),'python':platform.python_version(),'commit':commit,
         'escopo':'execução local com dados fictícios; não é GitHub Actions nem validação da Focus Fit',
         'comandos':records}
(root/'VALIDACAO_TECNICA.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
sections=''.join('<h2>'+html.escape(' '.join(r['comando']))+'</h2><p>Código de saída: '+str(r['exit_code'])+'</p><pre>'+html.escape(r['stdout']+r['stderr'])+'</pre>' for r in records)
document='<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>Validação técnica local — Focus Suporte</title><style>body{font:18px Arial;max-width:1000px;margin:32px auto;padding:0 24px;color:#172d39;background:#f3f6f7}h1{color:#166353}h2{font-size:20px;margin-top:28px}pre{background:#fff;border:1px solid #bdcbd1;border-radius:10px;padding:20px;white-space:pre-wrap;overflow-wrap:anywhere;font-size:16px}p{line-height:1.5}</style><h1>Focus Suporte — Validação técnica local</h1><p>'+html.escape(payload['escopo'])+'</p><p>Python '+html.escape(payload['python'])+' | '+html.escape(payload['ambiente'])+'</p><p>Commit: '+html.escape(commit)+'</p>'+sections+'</html>'
(root/'static'/'validacao-tecnica.html').write_text(document,encoding='utf-8')
print(json.dumps(payload,ensure_ascii=False,indent=2))
raise SystemExit(any(r['exit_code'] for r in records))
