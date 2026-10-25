"""Medição local de consulta+render HTML; não mede rede nem uso pelo parceiro."""
import json
import hashlib
import platform
import statistics
import tempfile
import time
from pathlib import Path
from app import create_app
from storage import connect

out=Path(__file__).parent/'resultados-desempenho.json'
with tempfile.TemporaryDirectory(prefix='focus-benchmark-') as directory:
    app=create_app({'TESTING':True,'SECRET_KEY':'somente-benchmark',
        'DATABASE':str(Path(directory)/'bench.sqlite'),'DATA_DIRECTORY':directory})
    with connect(app.config['DATABASE']) as db:
        db.execute('INSERT INTO users VALUES(1,?,?)',('fixture-benchmark','hash-inativo-nao-utilizado-para-login'))
        db.execute('INSERT INTO auth_sessions VALUES(?,?,?)',(hashlib.sha256(b'sessao-ficticia-benchmark').hexdigest(),1,time.time()+1800))
        db.executemany('INSERT INTO resources VALUES(?,?,?,?)',[(i,f'Recurso fictício {i}','Outro','Orientação fictícia') for i in range(1,101)])
        db.executemany('INSERT INTO incidents VALUES(?,?,?,?,?)',[(i,(i-1)%100+1,'2026-10-05','Ocorrência fictícia','Aberta') for i in range(1,1001)])
    db.close()
    client=app.test_client()
    with client.session_transaction() as s:
        s['uid']=1
        s['sid']='sessao-ficticia-benchmark'
    urls={'consulta_recursos':'/?q=Recurso','historico_recurso':'/resources/1'}
    results={}
    for name,url in urls.items():
        assert client.get(url).status_code==200
        samples=[]
        for _ in range(30):
            start=time.perf_counter()
            assert client.get(url).status_code==200
            samples.append((time.perf_counter()-start)*1000)
        results[name]={'amostras':30,'mediana_ms':round(statistics.median(samples),3),
                       'maximo_ms':round(max(samples),3),'amostras_ms':[round(x,3) for x in samples]}
    document={'escopo':'cliente de teste Flask: consulta SQLite + render HTML; sem rede, pintura do navegador ou usuário externo',
              'dados':'100 recursos e 1000 ocorrências fictícias','python':platform.python_version(),
              'sistema':platform.platform(),'resultados':results}
    out.write_text(json.dumps(document,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(document,ensure_ascii=False,indent=2))
