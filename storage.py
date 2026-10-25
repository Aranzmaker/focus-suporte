"""Regras e persistência do MVP local. Não contém dados reais da Focus Fit."""
import datetime as dt
import json
import sqlite3
from contextlib import closing
from pathlib import Path

TYPES = ('Impressora', 'Computador', 'Software', 'Outro')
STATES = ('Aberta', 'Resolvida')

def connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def initialize(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS auth_sessions (
          token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS resources (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS incidents (
          id INTEGER PRIMARY KEY, resource_id INTEGER NOT NULL REFERENCES resources(id),
          date TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('Aberta','Resolvida')));
        CREATE INDEX IF NOT EXISTS incident_resource ON incidents(resource_id);
        ''')

def text(value, label, maximum, required=True):
    if not isinstance(value, str):
        raise ValueError(f'{label}: valor inválido.')
    value = value.strip()
    if (required and not value) or len(value) > maximum:
        raise ValueError(f'{label}: preencha até {maximum} caracteres.')
    return value

def resource_values(data):
    name = text(data.get('name'), 'Nome', 120)
    kind = data.get('type')
    if kind not in TYPES:
        raise ValueError('Selecione um tipo válido.')
    return name, kind, text(data.get('notes', ''), 'Observações', 1000, False)

def incident_values(data):
    date = text(data.get('date'), 'Data', 10)
    try:
        if dt.date.fromisoformat(date).isoformat() != date:
            raise ValueError()
    except ValueError:
        raise ValueError('Informe uma data válida no formato ano-mês-dia.') from None
    description = text(data.get('description'), 'Descrição', 1000)
    status = data.get('status')
    if status not in STATES:
        raise ValueError('Selecione uma situação válida.')
    return date, description, status

def export_data(db):
    return {'version': 1,
            'resources': [dict(r) for r in db.execute('SELECT * FROM resources ORDER BY id')],
            'incidents': [dict(r) for r in db.execute('SELECT * FROM incidents ORDER BY id')]}

def validate_backup(data):
    if not isinstance(data, dict) or set(data) != {'version', 'resources', 'incidents'} or type(data['version']) is not int or data['version'] != 1:
        raise ValueError('Formato ou versão de backup inválidos.')
    rs, ins = data['resources'], data['incidents']
    if not isinstance(rs, list) or not isinstance(ins, list) or len(rs) > 1000 or len(ins) > 5000:
        raise ValueError('Backup fora dos limites do MVP.')
    ids, incident_ids = set(), set()
    resources, incidents = [], []
    for r in rs:
        if not isinstance(r, dict) or set(r) != {'id', 'name', 'type', 'notes'}:
            raise ValueError('Recurso inválido no backup.')
        rid = r['id']
        if type(rid) is not int or rid <= 0 or rid in ids:
            raise ValueError('Identificador de recurso inválido ou duplicado.')
        ids.add(rid)
        resources.append((rid, *resource_values(r)))
    for inc in ins:
        if not isinstance(inc, dict) or set(inc) != {'id', 'resource_id', 'date', 'description', 'status'}:
            raise ValueError('Ocorrência inválida no backup.')
        iid, rid = inc['id'], inc['resource_id']
        if type(iid) is not int or iid <= 0 or iid in incident_ids or type(rid) is not int or rid not in ids:
            raise ValueError('Identificador ou vínculo inválido na ocorrência.')
        incident_ids.add(iid)
        incidents.append((iid, rid, *incident_values(inc)))
    return resources, incidents

def restore_data(db, data, safety_directory):
    # A validação integral acontece antes de qualquer alteração.
    resources, incidents = validate_backup(data)
    safety_directory = Path(safety_directory)
    safety_directory.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    safety = safety_directory / f'antes-restauracao-{stamp}.json'
    safety.write_text(json.dumps(export_data(db), ensure_ascii=False, indent=2), encoding='utf-8')
    with db:
        db.execute('DELETE FROM incidents')
        db.execute('DELETE FROM resources')
        db.executemany('INSERT INTO resources VALUES(?,?,?,?)', resources)
        db.executemany('INSERT INTO incidents VALUES(?,?,?,?,?)', incidents)
    return safety
