# Focus Suporte

## Repositório e integração contínua

Código público: https://github.com/Aranzmaker/focus-suporte

Em **02/11/2026**, integrei os PRs [#1](https://github.com/Aranzmaker/focus-suporte/pull/1), [#2](https://github.com/Aranzmaker/focus-suporte/pull/2) e [#3](https://github.com/Aranzmaker/focus-suporte/pull/3) à `main`. A suíte atual contém **24 testes aprovados em execução local**, incluindo restauração de backup, inicialização da primeira conta em hospedagem e validação do monitoramento. Os checks dos três PRs passaram antes da integração. Ainda não houve revisão humana independente.

Preparei a publicação no Render e o monitoramento por GitHub Actions. O procedimento está em [PUBLICACAO_RENDER.md](PUBLICACAO_RENDER.md). Ainda falta autenticar a conta de hospedagem, executar o deploy e configurar `FOCUS_APP_URL`. Sem a URL, o job de monitoramento é ignorado. A configuração gratuita usa armazenamento temporário e destina-se a demonstração com dados fictícios; não substitui armazenamento persistente para uso contínuo.

O commit de recuperação `c4c4ab32c75d65108d0b511776ec93148fac15d1` foi publicado em 25/10/2026. O workflow [Testes do Focus Suporte — execução 1](https://github.com/Aranzmaker/focus-suporte/actions/runs/40237963119) concluiu com sucesso no GitHub Actions. Essa execução verifica compilação, testes unitários e de integração e cobertura mínima de 80%.

Publicação do código e execução de CI não significam implantação do aplicativo em nuvem nem validação pela Focus Fit. As próximas etapas dependem dessas evidências específicas.

## Recuperação em 25/10/2026

O código e os documentos desta pasta foram recuperados do histórico de alterações de 05–06/10/2026. As capturas e os bancos daquela sessão não foram recuperados. Os relatos abaixo sobre telas e formulários preservam o registro histórico; não representam novos testes com o parceiro ou aprovação acadêmica.

A versão recuperada foi verificada novamente em 25/10/2026: **16 testes aprovados e 87% de cobertura** em execução local com dados fictícios. O relatório atual pode ser gerado com `python validar.py`. O histórico Git anterior não foi recuperado; os commits deste repositório registram a recuperação atual, sem retroagir datas.

MVP acadêmico para organizar recursos informáticos, orientações e ocorrências de suporte. Desenvolvi o projeto a partir do atendimento de instalação de uma impressora em rede e do Office na Focus Fit, em Caridade do Piauí, em 05/10/2026. Realizei duas validações com Texeira, proprietário da Focus Fit: em 15/10/2026, recebi o retorno “o melhor possível”; em 27/10/2026, ele afirmou que “gostou de tudo”. Não recebi solicitação concreta de ajuste. Não confirmei adoção cotidiana nem medi ganhos operacionais na loja.

## O que foi construído

- Login local com Argon2id; sessão de 30 minutos; limite de cinco tentativas em cinco minutos por endereço local.
- Cadastro e pesquisa de recursos, com observações e orientações.
- Ocorrências vinculadas ao recurso, com data, descrição e situação; atualização para resolvida.
- Exportação e restauração de backup JSON. O arquivo não inclui credenciais. A restauração exige confirmação, valida todo o arquivo e preserva uma cópia dos registros anteriores.
- HTML com rótulos, mensagens, navegação por teclado, foco visível e CSS responsivo.

## Executar no Windows

Crie um ambiente virtual e instale as dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

O responsável deve configurar pessoalmente a conta local, sem usar a senha do portal acadêmico:

```powershell
.\.venv\Scripts\python.exe app.py configurar
.\.venv\Scripts\python.exe app.py
```

Abrir `http://127.0.0.1:8766`. O processo atende somente ao próprio computador. Não foi iniciado nem implantado na Focus Fit. Nenhuma conta real foi criada automaticamente. A configuração recusa alterar uma conta existente.

Banco, segredo de sessão e cópias de recuperação ficam, por padrão, em `%LOCALAPPDATA%\FocusSuporte`, fora da pasta de código no OneDrive. Proteja o perfil do Windows e a pasta local. O arquivo de banco e os backups não têm criptografia própria. Na execução local o cookie não usa Secure por atender HTTP no loopback. A configuração preparada para hospedagem exige domínio exato e habilita Secure; HTTPS e armazenamento persistente precisam ser fornecidos pelo provedor. Consulte `IMPLANTACAO_PENDENTE.md`. O código está publicado no GitHub; o aplicativo ainda não foi implantado em nuvem.

## Validação realizada

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Na primeira etapa, sete testes passaram. Em 25/10/2026, a suíte tinha **16 casos e 87% de cobertura combinada de linhas e ramificações** na medição local. A regressão de restauração elevou o total para 17; os casos de hospedagem e monitoramento elevaram a suíte atual para **24 testes aprovados**. A medição histórica de 87% não representa uma nova medição da suíte ampliada. Os testes incluem revogação da sessão no servidor, bloqueio do cookie anterior após saída, validade da sessão e configuração de Host/cookie para hospedagem. Os casos usam banco temporário e dados fictícios. `python validar.py` registra saídas reais em `VALIDACAO_TECNICA.json` e um relatório HTML. O GitHub Actions verifica os PRs; consulte as evidências na seção inicial.

Isso comprova os casos técnicos executados. As três telas foram conferidas no navegador interno: login, cadastro de recurso, registro e resolução de ocorrência. A sequência de Tab do cadastro foi verificada e um estouro horizontal no cabeçalho a 320 px foi corrigido; a tela de histórico ficou sem rolagem horizontal. As capturas reais estão em `capturas/`; os wireframes em `prototipos/` são desenhos de planejamento. Teste com leitor de tela, ampliação, medição completa de carregamento em rede simulada e acompanhamento de uso contínuo na Focus Fit continuam pendentes. O benchmark separado mede somente consulta SQLite e geração do HTML.

## Decisão técnica

A prática I planejava HTML/JavaScript e armazenamento no navegador. A prática II exige Java, Angular, Flutter ou Python e autenticação com hash robusto. O desenho foi evoluído para **Python + Flask + SQLite**, mantendo execução local e o mesmo núcleo funcional. A separação é: templates e CSS → rotas e validação → funções de persistência. Waitress executa o monólito sem debug. Não há nuvem, sincronização, instalação de drivers, ativação do Office, integração fiscal ou gestão de clientes.

Fontes verificadas: [Flask/SQLite](https://flask.palletsprojects.com/en/stable/tutorial/database/), [armazenamento de senhas OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [GLPI](https://www.glpi-project.org/en/features/), [Zammad](https://zammad.com/en/product/features). A comparação com os dois produtos foi documental; eles não foram testados na loja.

## Situação no portal em 02/11/2026

A prática I chegou a 100% das perguntas no DreamShaper. O requisito de evidência por foto/áudio/transcrição ficou desmarcado e explicado na reflexão. O PDF descritivo anexado representa o relato fornecido, sem comprovação independente.

A prática II chegou a **100% das perguntas preenchidas**, com três capturas anexadas, requisitos, modelagem e plano de teste. A prática III também chegou a **100%**, com repositório público, Pull Requests, CI e as duas validações relatadas acima. Mantive desmarcado o item de melhoria motivada por feedback, pois Texeira não solicitou ajuste. As correções técnicas e a preparação de hospedagem foram decisões minhas de desenvolvimento.

A prática IV está em **25%**, com identificação, funcionalidades, código-fonte, infraestrutura e monitoramento descritos em primeira pessoa. O avanço está bloqueado pelos campos obrigatórios de URL pública da aplicação e capturas da aplicação publicada e do monitoramento remoto. Ainda faltam implantação, evidências, indicadores e as etapas posteriores de impacto e feedback formal. O percentual de preenchimento no DreamShaper não confirma nota ou aprovação acadêmica.
