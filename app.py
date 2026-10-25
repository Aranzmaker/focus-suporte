"""MVP acadêmico local; nenhuma implantação no parceiro foi realizada."""
import datetime as dt
import functools
import getpass
import hashlib
import json
import os
import re
from pathlib import Path
import secrets
import threading
import time

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError
from flask import Flask, abort, flash, g, redirect, render_template, request, session, url_for
from storage import (TYPES, STATES, connect, initialize, text, resource_values,
                     incident_values, export_data, restore_data)

HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=1)

def create_app(config=None):
    default_directory = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'FocusSuporte'
    directory = Path(os.environ.get('FOCUS_DATA_DIRECTORY', str(default_directory)))
    public_host = os.environ.get('FOCUS_PUBLIC_HOST', '').strip().lower()
    if public_host and not all(re.fullmatch(r'(?!-)[a-z0-9-]{1,63}(?<!-)', label) for label in public_host.split('.')):
        raise ValueError('FOCUS_PUBLIC_HOST deve conter somente o hostname exato, sem URL, porta ou curinga.')
    app = Flask(__name__)
    app.config.update(DATABASE=str(directory / 'focus.sqlite3'), DATA_DIRECTORY=str(directory),
                      MAX_CONTENT_LENGTH=2 * 1024 * 1024, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Strict', SESSION_REFRESH_EACH_REQUEST=False,
                      PERMANENT_SESSION_LIFETIME=dt.timedelta(minutes=30),
                      SESSION_COOKIE_SECURE=bool(public_host),
                      TRUSTED_HOSTS=['127.0.0.1', 'localhost'] + ([public_host] if public_host else []))
    if config:
        app.config.update(config)
    if not app.config.get('SECRET_KEY'):
        secret_path = Path(app.config['DATA_DIRECTORY']) / 'session.secret'
        secret_path.parent.mkdir(parents=True, exist_ok=True)
        if not secret_path.exists():
            secret_path.write_text(secrets.token_hex(32), encoding='ascii')
        app.config['SECRET_KEY'] = secret_path.read_text(encoding='ascii')
    initialize(app.config['DATABASE'])
    attempts, lock = {}, threading.Lock()

    def db():
        if 'db' not in g:
            g.db = connect(app.config['DATABASE'])
        return g.db

    @app.teardown_appcontext
    def close_db(error):
        if 'db' in g:
            g.pop('db').close()

    def csrf():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_urlsafe(32)
        return session['csrf']

    app.jinja_env.globals['csrf_token'] = csrf

    @app.get('/health')
    def health():
        db().execute('SELECT 1')
        return {'status':'ok'}

    @app.before_request
    def protect():
        if request.method == 'POST':
            expected = session.get('csrf')
            supplied = request.form.get('csrf', '')
            if not expected or not secrets.compare_digest(expected, supplied):
                abort(400, 'Formulário expirado. Reabra a página e tente novamente.')

    @app.after_request
    def headers(response):
        response.headers.update({'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY',
            'Content-Security-Policy': "default-src 'self'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
            'Referrer-Policy': 'no-referrer', 'Cache-Control': 'no-store'})
        return response

    def authenticated(fn):
        @functools.wraps(fn)
        def wrapped(*args, **kwargs):
            uid = session.get('uid')
            sid = session.get('sid', '')
            record = db().execute('SELECT user_id,expires FROM auth_sessions WHERE token_hash=?',
                                  (hashlib.sha256(sid.encode()).hexdigest(),)).fetchone()
            if not uid or not record or record['user_id'] != uid or record['expires'] <= time.time():
                session.clear()
                return redirect(url_for('login'))
            return fn(*args, **kwargs)
        return wrapped

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username', '')[:80].strip()
            key = request.remote_addr or 'local'
            now = time.monotonic()
            with lock:
                for expired in [k for k, v in attempts.items() if now - v[1] >= 300]:
                    attempts.pop(expired)
                failures, start = attempts.get(key, (0, now))
            if failures >= 5 and now - start < 300:
                flash('Aguarde cinco minutos antes de tentar novamente.', 'erro')
                return render_template('login.html'), 429
            user = db().execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
            password = request.form.get('password', '')
            valid = False
            if user and 0 < len(password) <= 200:
                try:
                    valid = HASHER.verify(user['password_hash'], password)
                except VerificationError:
                    pass
            if valid:
                with lock:
                    attempts.pop(key, None)
                old_sid = session.get('sid', '')
                new_sid = secrets.token_urlsafe(32)
                with db():
                    db().execute('DELETE FROM auth_sessions WHERE expires<=? OR token_hash=?',
                                 (time.time(), hashlib.sha256(old_sid.encode()).hexdigest()))
                    db().execute('INSERT INTO auth_sessions VALUES(?,?,?)',
                                 (hashlib.sha256(new_sid.encode()).hexdigest(), user['id'], time.time()+1800))
                session.clear()
                session['uid'] = user['id']
                session['sid'] = new_sid
                session.permanent = True
                return redirect(url_for('resources'))
            with lock:
                attempts[key] = (failures + 1, start)
            flash('Usuário ou senha inválidos.', 'erro')
        return render_template('login.html')

    @app.post('/logout')
    @authenticated
    def logout():
        with db():
            db().execute('DELETE FROM auth_sessions WHERE token_hash=?',
                         (hashlib.sha256(session['sid'].encode()).hexdigest(),))
        session.clear()
        return redirect(url_for('login'))

    @app.route('/', methods=['GET', 'POST'])
    @authenticated
    def resources():
        if request.method == 'POST':
            try:
                values = resource_values(request.form)
                with db():
                    db().execute('INSERT INTO resources(name,type,notes) VALUES(?,?,?)', values)
                flash('Recurso cadastrado.', 'sucesso')
                return redirect(url_for('resources'))
            except ValueError as error:
                flash(str(error), 'erro')
        query = request.args.get('q', '')[:120]
        rows = db().execute('SELECT * FROM resources WHERE instr(lower(name),lower(?))>0 ORDER BY id DESC', (query,)).fetchall()
        return render_template('resources.html', resources=rows, types=TYPES, query=query)

    @app.route('/resources/<int:resource_id>', methods=['GET', 'POST'])
    @authenticated
    def history(resource_id):
        resource = db().execute('SELECT * FROM resources WHERE id=?', (resource_id,)).fetchone()
        if not resource:
            abort(404)
        if request.method == 'POST':
            try:
                values = incident_values(request.form)
                with db():
                    db().execute('INSERT INTO incidents(resource_id,date,description,status) VALUES(?,?,?,?)', (resource_id, *values))
                flash('Ocorrência registrada.', 'sucesso')
                return redirect(url_for('history', resource_id=resource_id))
            except ValueError as error:
                flash(str(error), 'erro')
        rows = db().execute('SELECT * FROM incidents WHERE resource_id=? ORDER BY date DESC,id DESC', (resource_id,)).fetchall()
        return render_template('history.html', resource=resource, incidents=rows, states=STATES, today=dt.date.today().isoformat())

    @app.post('/incidents/<int:incident_id>/resolve')
    @authenticated
    def resolve(incident_id):
        inc = db().execute('SELECT * FROM incidents WHERE id=?', (incident_id,)).fetchone()
        if not inc:
            abort(404)
        with db():
            db().execute('UPDATE incidents SET status=? WHERE id=?', ('Resolvida', incident_id))
        flash('Situação atualizada para resolvida.', 'sucesso')
        return redirect(url_for('history', resource_id=inc['resource_id']))

    @app.get('/backup')
    @authenticated
    def backup():
        return app.response_class(json.dumps(export_data(db()), ensure_ascii=False, indent=2), mimetype='application/json',
                                  headers={'Content-Disposition': 'attachment; filename="focus-suporte-backup.json"'})

    @app.post('/restore')
    @authenticated
    def restore():
        try:
            if request.form.get('confirm') != 'sim':
                raise ValueError('Confirme a substituição dos registros pelo backup.')
            upload = request.files.get('backup')
            if not upload:
                raise ValueError('Selecione o arquivo JSON.')
            data = json.loads(upload.read().decode('utf-8'))
            restore_data(db(), data, Path(app.config['DATA_DIRECTORY']) / 'backups')
            flash('Backup restaurado. Os registros anteriores foram preservados em cópia local.', 'sucesso')
        except (ValueError, UnicodeError, TypeError) as error:
            flash(f'Backup rejeitado: {error}', 'erro')
        return redirect(url_for('resources'))

    @app.errorhandler(400)
    @app.errorhandler(404)
    @app.errorhandler(413)
    def error_page(error):
        if request.routing_exception:
            # Host não confiável: não construir URLs com um adaptador rejeitado.
            return 'Requisição rejeitada.', error.code
        return render_template('error.html', error=error), error.code
    return app

if __name__ == '__main__':
    import sys
    app = create_app()
    if len(sys.argv) > 1 and sys.argv[1] == 'configurar':
        with connect(app.config['DATABASE']) as db:
            if db.execute('SELECT 1 FROM users').fetchone():
                raise SystemExit('Conta local já configurada. Nenhuma credencial foi alterada.')
            username = text(input('Nome do usuário local: '), 'Usuário', 80)
            password = getpass.getpass('Crie uma senha local (mínimo 12 caracteres): ')
            confirmation = getpass.getpass('Repita a senha: ')
            if len(password) < 12 or len(password) > 200 or password != confirmation:
                raise SystemExit('Senha inválida ou confirmação diferente; nada foi gravado.')
            db.execute('INSERT INTO users(username,password_hash) VALUES(?,?)', (username, HASHER.hash(password)))
        print('Conta configurada. Execute app.py para iniciar no computador local.')
    else:
        from waitress import serve
        print('Focus Suporte acadêmico local: http://127.0.0.1:8766 (Ctrl+C encerra)')
        serve(app, host=os.environ.get('FOCUS_BIND_HOST','127.0.0.1'),
              port=int(os.environ.get('PORT',os.environ.get('FOCUS_PORT','8766'))), threads=2)
