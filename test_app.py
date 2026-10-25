import io
import json
import re
import sqlite3
import pytest
from app import create_app, HASHER
from storage import connect, export_data, restore_data

@pytest.fixture
def app(tmp_path):
    app=create_app({'TESTING':True,'SECRET_KEY':'segredo-exclusivo-do-teste',
        'DATABASE':str(tmp_path/'test.sqlite'),'DATA_DIRECTORY':str(tmp_path),
        'TRUSTED_HOSTS':['localhost']})
    with connect(app.config['DATABASE']) as db:
        db.execute('INSERT INTO users(username,password_hash) VALUES(?,?)',('teste',HASHER.hash('senha-ficticia-de-teste')))
    return app

def token(response):
    return re.search(rb'name="csrf" value="([^"]+)"',response.data)[1].decode()

def login(client):
    csrf=token(client.get('/login'))
    return client.post('/login',data={'csrf':csrf,'username':'teste','password':'senha-ficticia-de-teste'})

def post(client,path,data):
    csrf=token(client.get('/'))
    return client.post(path,data={**data,'csrf':csrf})

def test_auth_hash_and_private_routes(app):
    client=app.test_client()
    assert client.get('/').status_code==302
    assert client.get('/backup').status_code==302
    with connect(app.config['DATABASE']) as db:
        value=db.execute('SELECT password_hash FROM users').fetchone()[0]
        assert value.startswith('$argon2id$') and 'senha-ficticia' not in value
    assert login(client).status_code==302
    assert b'Recursos de trabalho' in client.get('/').data

def test_csrf_logout_expiry_and_headers(app):
    c=app.test_client(); login(c)
    assert c.post('/',data={'name':'Sem token','type':'Outro'}).status_code==400
    page=c.get('/')
    assert page.headers['X-Frame-Options']=='DENY'
    assert "form-action 'self'" in page.headers['Content-Security-Policy']
    old_cookie=c.get_cookie('session').value
    assert c.post('/logout',data={'csrf':token(page)}).status_code==302
    assert c.get('/resources/1').status_code==302
    replay=app.test_client()
    replay.set_cookie('session',old_cookie)
    assert replay.get('/').status_code==302
    login(c)
    with connect(app.config['DATABASE']) as db:
        db.execute('UPDATE auth_sessions SET expires=0')
    assert c.get('/').status_code==302
    with c.session_transaction() as s:
        s['uid']=999999
    assert c.get('/').status_code==302

def test_failed_logins_are_limited(app):
    c=app.test_client()
    for _ in range(5):
        csrf=token(c.get('/login'))
        assert c.post('/login',data={'csrf':csrf,'username':'teste','password':'errada'}).status_code==200
    csrf=token(c.get('/login'))
    assert c.post('/login',data={'csrf':csrf,'username':'teste','password':'senha-ficticia-de-teste'}).status_code==429

def test_resource_incident_search_resolution_and_persistence(app):
    c=app.test_client(); login(c)
    assert post(c,'/',{'name':'Impressora de teste','type':'Impressora','notes':'Orientação fictícia'}).status_code==302
    assert post(c,'/resources/1',{'date':'2026-10-05','description':'Caso fictício','status':'Aberta'}).status_code==302
    assert b'Caso fict' in c.get('/resources/1').data
    assert post(c,'/incidents/1/resolve',{}).status_code==302
    with connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT status FROM incidents').fetchone()[0]=='Resolvida'
        assert db.execute('SELECT name FROM resources').fetchone()[0]=='Impressora de teste'
    assert b'Impressora de teste' in c.get('/?q=teste').data
    assert b'Impressora de teste' not in c.get('/?q=inexistente').data
    assert c.get('/resources/999').status_code==404

def test_validation_sql_and_html_escape(app):
    c=app.test_client(); login(c)
    post(c,'/',{'name':'','type':'Impressora','notes':''})
    post(c,'/',{'name':'Inválido','type':'fora','notes':''})
    value='<script>alert(1)</script>'
    post(c,'/',{'name':value,'type':'Outro','notes':"x'); DROP TABLE resources;--"})
    assert b'<script>alert(1)</script>' not in c.get('/').data
    assert b'&lt;script&gt;' in c.get('/').data
    post(c,'/resources/1',{'date':'2026-02-30','description':'x','status':'Aberta'})
    post(c,'/resources/1',{'date':'2026-10-05','description':'x','status':'inválida'})
    with connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT count(*) FROM resources').fetchone()[0]==1
        assert db.execute('SELECT count(*) FROM incidents').fetchone()[0]==0

def test_backup_roundtrip_and_invalid_file_preserves_records(app,tmp_path):
    c=app.test_client(); login(c)
    post(c,'/',{'name':'Software de teste','type':'Software','notes':'Sem chaves reais'})
    post(c,'/resources/1',{'date':'2026-10-05','description':'Teste','status':'Resolvida'})
    data=c.get('/backup').json
    assert set(data)=={'version','resources','incidents'}
    post(c,'/',{'name':'Recurso posterior','type':'Outro','notes':''})
    with connect(app.config['DATABASE']) as db:
        safety=restore_data(db,data,tmp_path/'copies')
        assert len(json.loads(safety.read_text(encoding='utf-8'))['resources'])==2
        assert export_data(db)==data
        before=export_data(db)
        broken={**data,'incidents':[{'id':1,'resource_id':999,'date':'2026-10-05','description':'x','status':'Aberta'}]}
        with pytest.raises(ValueError): restore_data(db,broken,tmp_path/'copies')
        assert export_data(db)==before
    csrf=token(c.get('/'))
    c.post('/restore',data={'csrf':csrf,'confirm':'sim','backup':(io.BytesIO(b'not json'),'bad.json')})
    assert c.get('/backup').json==data

def test_restore_confirmation_and_empty_or_duplicate_rejection(app,tmp_path):
    c=app.test_client(); login(c)
    post(c,'/',{'name':'Preservado','type':'Outro','notes':''})
    data=c.get('/backup').json
    csrf=token(c.get('/'))
    c.post('/restore',data={'csrf':csrf,'backup':(io.BytesIO(json.dumps({'version':1,'resources':[],'incidents':[]}).encode()),'empty.json')})
    assert c.get('/backup').json==data
    broken={**data,'resources':data['resources']*2}
    with connect(app.config['DATABASE']) as db:
        with pytest.raises(ValueError): restore_data(db,broken,tmp_path/'copies')
        assert export_data(db)==data
    assert c.get('/backup',headers={'Host':'example.org'}).status_code==400

def test_public_host_uses_secure_cookie_and_health_is_minimal(tmp_path,monkeypatch):
    monkeypatch.setenv('FOCUS_PUBLIC_HOST','focus.example.test')
    app=create_app({'TESTING':True,'SECRET_KEY':'somente-teste-publico',
        'DATABASE':str(tmp_path/'public.sqlite'),'DATA_DIRECTORY':str(tmp_path)})
    c=app.test_client()
    response=c.get('/login',base_url='https://focus.example.test')
    assert response.status_code==200 and '; Secure;' in response.headers['Set-Cookie']
    health=c.get('/health',base_url='https://focus.example.test')
    assert health.json=={'status':'ok'}
    assert c.get('/health',headers={'Host':'outro.example.test'}).status_code==400
    monkeypatch.setenv('FOCUS_PUBLIC_HOST','https://invalido.example.test')
    with pytest.raises(ValueError): create_app({'TESTING':True})
