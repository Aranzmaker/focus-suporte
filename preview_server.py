"""Ambiente visual temporário de teste, isolado da conta real e do banco local."""
import tempfile
from pathlib import Path
from waitress import serve
from app import create_app, HASHER
from storage import connect

if __name__ == '__main__':
    with tempfile.TemporaryDirectory(prefix='focus-suporte-visual-') as directory:
        app = create_app({'DATABASE':str(Path(directory)/'visual.sqlite'),
                          'DATA_DIRECTORY':directory})
        with connect(app.config['DATABASE']) as db:
            db.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',
                       ('teste-visual', HASHER.hash('apenas-teste-visual-2026')))
            db.execute('INSERT INTO resources(name,type,notes) VALUES(?,?,?)',
                       ('Impressora de exemplo', 'Impressora',
                        'Dado fictício. Consulte o técnico antes de alterar a configuração.'))
            db.execute('INSERT INTO incidents(resource_id,date,description,status) VALUES(?,?,?,?)',
                       (1,'2026-10-05','Exemplo fictício de atendimento para teste da interface.','Aberta'))
        db.close()
        print('Ambiente temporário de teste visual: http://127.0.0.1:8767', flush=True)
        serve(app,host='127.0.0.1',port=8767,threads=2)
