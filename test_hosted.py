from contextlib import closing
import io

import pytest

from app import HASHER
from monitorar import health_url, probe
from serve_hosted import build_hosted_app
from storage import connect


def hosted_env(monkeypatch, tmp_path):
    monkeypatch.setenv('RENDER_EXTERNAL_HOSTNAME', 'focus-teste.onrender.com')
    monkeypatch.delenv('FOCUS_PUBLIC_HOST', raising=False)
    monkeypatch.setenv('FOCUS_DATA_DIRECTORY', str(tmp_path))
    monkeypatch.setenv('FOCUS_ADMIN_USERNAME', 'teste-hospedagem')
    monkeypatch.setenv('FOCUS_ADMIN_PASSWORD', 'senha-ficticia-para-testes')


def test_hosted_initializes_account_without_overwriting(monkeypatch, tmp_path):
    hosted_env(monkeypatch, tmp_path)
    app = build_hosted_app()
    assert app.config['SESSION_COOKIE_SECURE']
    assert app.test_client().get('/health', base_url='https://focus-teste.onrender.com').json == {'status': 'ok'}
    assert app.test_client().get('/health', base_url='https://outro.example').status_code == 400
    with closing(connect(app.config['DATABASE'])) as db:
        original = dict(db.execute('SELECT * FROM users').fetchone())
        assert HASHER.verify(original['password_hash'], 'senha-ficticia-para-testes')
    monkeypatch.setenv('FOCUS_ADMIN_USERNAME', 'outro-usuario')
    monkeypatch.setenv('FOCUS_ADMIN_PASSWORD', 'outra-senha-ficticia')
    build_hosted_app()
    with closing(connect(app.config['DATABASE'])) as db:
        assert [dict(row) for row in db.execute('SELECT * FROM users')] == [original]


def test_hosted_rejects_missing_initial_password(monkeypatch, tmp_path):
    hosted_env(monkeypatch, tmp_path)
    monkeypatch.delenv('FOCUS_ADMIN_PASSWORD')
    with pytest.raises(ValueError, match='FOCUS_ADMIN_PASSWORD'):
        build_hosted_app()
    with closing(connect(tmp_path / 'focus.sqlite3')) as db:
        assert db.execute('SELECT COUNT(*) FROM users').fetchone()[0] == 0


@pytest.mark.parametrize('url', ['http://focus.onrender.com', 'https://localhost',
    'https://focus.onrender.com@127.0.0.1', 'https://focus.onrender.com/?secret=abc'])
def test_monitor_rejects_unexpected_targets(url):
    with pytest.raises(ValueError):
        health_url(url)


def test_monitor_checks_http_and_application_status():
    url = health_url('https://focus-teste.onrender.com/')

    class Response(io.BytesIO):
        status = 200

        def geturl(self):
            return url

    assert probe(url, lambda request, timeout: Response(b'{"status":"ok"}')) >= 0
    with pytest.raises(ValueError):
        probe(url, lambda request, timeout: Response(b'{"status":"error"}'))
