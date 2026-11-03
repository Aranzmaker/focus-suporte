"""Python 3.12; serve_hosted.py; inicialização do Focus Suporte no Render."""
from contextlib import closing
import os

from app import HASHER, create_app
from storage import connect, text


def build_hosted_app():
    host = os.environ.get('FOCUS_PUBLIC_HOST') or os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
    if not host:
        raise ValueError('Configure FOCUS_PUBLIC_HOST ou execute no Render.')
    os.environ['FOCUS_PUBLIC_HOST'] = host
    password = os.environ.pop('FOCUS_ADMIN_PASSWORD', '')
    app = create_app()
    with closing(connect(app.config['DATABASE'])) as db, db:
        if not db.execute('SELECT 1 FROM users').fetchone():
            username = text(os.environ.get('FOCUS_ADMIN_USERNAME', ''), 'Usuário', 80)
            if not 12 <= len(password) <= 200:
                raise ValueError('Configure FOCUS_ADMIN_PASSWORD com 12 a 200 caracteres no painel da hospedagem.')
            db.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',
                       (username, HASHER.hash(password)))
    return app


if __name__ == '__main__':
    from waitress import serve
    application = build_hosted_app()
    print('Focus Suporte iniciado; verificação de saúde em /health.', flush=True)
    serve(application, host='0.0.0.0', port=int(os.environ.get('PORT', '10000')), threads=2)
