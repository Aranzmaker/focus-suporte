"""Python 3.12; monitorar.py; monitor HTTPS do Focus Suporte no Render."""
import datetime as dt
import json
import os
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def health_url(base):
    parsed = urlsplit(base.strip())
    if (parsed.scheme != 'https' or not parsed.hostname
            or not parsed.hostname.endswith('.onrender.com')
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.port not in (None, 443) or parsed.path not in ('', '/')):
        raise ValueError('FOCUS_APP_URL deve ser a URL HTTPS raiz do serviço .onrender.com, sem credenciais ou parâmetros.')
    return f'https://{parsed.hostname}/health'


def probe(url, opener=urlopen):
    started = time.monotonic()
    request = Request(url, headers={'User-Agent': 'FocusSuporte-HealthMonitor/1.0'})
    with opener(request, timeout=30) as response:
        if response.geturl() != url:
            raise ValueError('O endpoint de saúde redirecionou para outro endereço.')
        payload = response.read(4097)
        if response.status != 200 or len(payload) > 4096:
            raise ValueError('Resposta HTTP de saúde inválida.')
        if json.loads(payload).get('status') != 'ok':
            raise ValueError('A aplicação não confirmou status ok.')
    return round((time.monotonic() - started) * 1000)


def main():
    url = health_url(os.environ.get('FOCUS_APP_URL', ''))
    checks = []
    for attempt in range(1, 4):
        try:
            checks.append({'attempt': attempt, 'status': 'UP', 'elapsed_ms': probe(url)})
            break
        except Exception as error:
            checks.append({'attempt': attempt, 'status': 'DOWN', 'error_type': type(error).__name__})
    status = checks[-1]['status']
    print(json.dumps({'checked_at': dt.datetime.now(dt.timezone.utc).isoformat(),
                      'url': url, 'status': status, 'checks': checks}, ensure_ascii=False, indent=2))
    return 0 if status == 'UP' else 1


if __name__ == '__main__':
    sys.exit(main())
