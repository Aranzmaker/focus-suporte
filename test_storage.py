"""Testes unitários de regras, separados dos testes HTTP/SQLite de integração."""
import pytest
from storage import resource_values, incident_values, validate_backup

def test_normalization_and_optional_notes():
    assert resource_values({'name':'  Recurso de teste  ','type':'Outro'})==('Recurso de teste','Outro','')
    assert incident_values({'date':'2024-02-29','description':'  Exemplo  ','status':'Aberta'})==('2024-02-29','Exemplo','Aberta')

@pytest.mark.parametrize('date',['2026-02-29','2026-10-5','05/10/2026'])
def test_invalid_or_noncanonical_calendar_dates(date):
    with pytest.raises(ValueError):
        incident_values({'date':date,'description':'Exemplo fictício','status':'Aberta'})

@pytest.mark.parametrize('data',[
    {'version':2,'resources':[],'incidents':[]},
    {'version':1,'resources':[],'incidents':[],'users':[]},
    {'version':1,'resources':{},'incidents':[]},
])
def test_unrecognized_backup_cannot_enter_restore(data):
    with pytest.raises(ValueError):
        validate_backup(data)

def test_boolean_is_not_a_resource_identifier():
    with pytest.raises(ValueError):
        validate_backup({'version':1,'resources':[{'id':True,'name':'Fictício','type':'Outro','notes':''}],'incidents':[]})
