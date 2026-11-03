# Publicação do Focus Suporte no Render

O repositório contém a aplicação Flask original e uma entrada específica de hospedagem. A configuração não cria uma conta no Render nem publica o serviço automaticamente.

## Demonstração gratuita

O `render.yaml` usa exclusivamente o plano **free**, sem disco pago e sem deploy automático a cada push. O SQLite, o segredo de sessão e os backups ficam em `/tmp/focus-suporte`, que é efêmero. Reinícios e novos deploys podem apagar esses dados. Esta configuração serve para demonstração acadêmica com dados fictícios. Para adoção cotidiana, é necessário armazenamento persistente e aprovação do custo antes de contratar recursos pagos.

1. Acesse uma conta do Render e crie um Blueprint a partir deste repositório e de sua branch `main`.
2. Confira que o serviço continua no plano free, sem recursos pagos.
3. Configure pessoalmente `FOCUS_ADMIN_USERNAME` e `FOCUS_ADMIN_PASSWORD` no painel do Render. Use uma senha exclusiva de 12 a 200 caracteres. Não coloque os valores no GitHub, na atividade acadêmica, em capturas ou no chat.
4. Inicie a publicação. O Render define `RENDER_EXTERNAL_HOSTNAME` e `PORT`; `serve_hosted.py` utiliza esses valores para o Host permitido, cookie Secure e execução pelo Waitress.
5. O primeiro início cria a conta com Argon2id. Se o banco já tiver uma conta, a entrada de hospedagem a preserva. O script não sobrescreve credenciais existentes.
6. Confira `/health`, login, cadastro/pesquisa de recursos, registro/resolução de ocorrência e exportação/restauração de backup com dados fictícios.
7. Guarde uma captura com a barra do navegador mostrando a URL pública e a aplicação funcionando.

## Monitoramento

Depois que existir uma URL real, configure a variável de repositório `FOCUS_APP_URL` com a raiz HTTPS do serviço `.onrender.com`, sem parâmetros ou credenciais. O workflow `Disponibilidade do Focus Suporte` consulta `/health` em agenda nominal de 30 minutos e também aceita execução manual. Agendas do GitHub podem sofrer atrasos e não são garantia de SLA.

O monitor verifica HTTP 200 e JSON com `status: ok`. Após três falhas, o job falha e registra DOWN; uma resposta válida registra UP e o tempo de resposta. O JSON é retido como artefato por 30 dias. As notificações de falha dependem das preferências existentes no GitHub. Até configurar a URL, o job é ignorado: não existe evidência de monitoramento remoto ativo.

Após publicar, execute manualmente o monitor e guarde uma captura do job e do relatório real para a prática IV. Descreva também as limitações da instância gratuita: ociosidade, reinícios, armazenamento efêmero e ausência de SLA.

## Fontes

- https://render.com/docs/deploy-flask
- https://render.com/docs/free
- https://render.com/docs/blueprint-spec
- https://render.com/docs/environment-variables
- https://render.com/docs/health-checks
