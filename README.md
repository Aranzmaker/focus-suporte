# Focus Suporte

## Recuperação em 25/10/2026

O código e os documentos desta pasta foram recuperados do histórico de alterações de 05–06/10/2026. As capturas e os bancos daquela sessão não foram recuperados. Os relatos abaixo sobre telas e formulários preservam o registro histórico; não representam novos testes com o parceiro ou aprovação acadêmica.

A versão recuperada foi verificada novamente em 25/10/2026: **16 testes aprovados e 87% de cobertura** em execução local com dados fictícios. O relatório atual pode ser gerado com `python validar.py`. O histórico Git anterior não foi recuperado; os commits deste repositório registram a recuperação atual, sem retroagir datas.

MVP acadêmico local para organizar recursos informáticos, orientações e ocorrências de suporte. Preparado a partir do relato de Aran sobre instalação de uma impressora em rede e do Office na Focus Fit, em Caridade do Piauí, em 05/10/2026. A necessidade deste software e seu uso na loja ainda não foram validados.

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

Banco, segredo de sessão e cópias de recuperação ficam, por padrão, em `%LOCALAPPDATA%\FocusSuporte`, fora da pasta de código no OneDrive. Proteja o perfil do Windows e a pasta local. O arquivo de banco e os backups não têm criptografia própria. Na execução local o cookie não usa Secure por atender HTTP no loopback. A configuração preparada para hospedagem exige domínio exato e habilita Secure; HTTPS e armazenamento persistente precisam ser fornecidos pelo provedor. Consulte `IMPLANTACAO_PENDENTE.md`. Não houve publicação remota.

## Validação realizada

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Na primeira etapa, sete testes passaram. A suíte foi ampliada para **16 casos unitários e de integração**, com **87% de cobertura combinada de linhas e ramificações** na medição local. Inclui revogação da sessão no servidor, bloqueio do cookie anterior após saída, validade da sessão e configuração de Host/cookie para hospedagem. Os casos usam banco temporário e dados fictícios. `python validar.py` registra saídas reais em `VALIDACAO_TECNICA.json` e um relatório HTML; a configuração de GitHub Actions ainda depende de publicação e execução remota.

Isso comprova os casos técnicos executados, sem certificar segurança completa ou aceitação do parceiro. As três telas foram conferidas no navegador interno: login, cadastro de recurso, registro e resolução de ocorrência. A sequência de Tab do cadastro foi verificada e um estouro horizontal no cabeçalho a 320 px foi corrigido; a tela de histórico ficou sem rolagem horizontal. As capturas reais estão em `capturas/`; os wireframes em `prototipos/` são desenhos de planejamento. Teste com leitor de tela, ampliação, medição completa de carregamento em rede simulada e validação real com a Focus Fit continuam pendentes. O benchmark separado mede somente consulta SQLite e geração do HTML.

## Decisão técnica

A prática I planejava HTML/JavaScript e armazenamento no navegador. A prática II exige Java, Angular, Flutter ou Python e autenticação com hash robusto. O desenho foi evoluído para **Python + Flask + SQLite**, mantendo execução local e o mesmo núcleo funcional. A separação é: templates e CSS → rotas e validação → funções de persistência. Waitress executa o monólito sem debug. Não há nuvem, sincronização, instalação de drivers, ativação do Office, integração fiscal ou gestão de clientes.

Fontes verificadas: [Flask/SQLite](https://flask.palletsprojects.com/en/stable/tutorial/database/), [armazenamento de senhas OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html), [GLPI](https://www.glpi-project.org/en/features/), [Zammad](https://zammad.com/en/product/features). A comparação com os dois produtos foi documental; eles não foram testados na loja.

## O que falta no portal

A prática I chegou a 100% das perguntas no DreamShaper. O requisito de evidência por foto/áudio/transcrição ficou desmarcado e explicado na reflexão. O PDF descritivo anexado representa o relato fornecido, sem comprovação independente.

A sessão foi recuperada no navegador interno. A prática II chegou a **100% das perguntas preenchidas**, com as três capturas anexadas, requisitos, modelagem e plano de teste. O checklist preserva duas confirmações pendentes: PPC específico do curso e representante da loja. A pessoa encontrada no cadastro público foi indicada somente como candidata a convite; não há consentimento ou validação realizada. A prática III está iniciada e exige repositório público, Pull Request, CI remoto e duas rodadas reais com parceiro. A prática IV tem identificação e síntese salvas, mas o avanço exige a URL pública do código. Também exige implantação em nuvem, monitoramento, indicadores e feedback formal. Esses requisitos não podem ser comprovados por testes locais ou dados fictícios.

Não há nota ou aprovação acadêmica confirmada. Fotos, identidade de quem acompanhou o atendimento, testes de impressão/Office e retorno do parceiro não foram fornecidos.
