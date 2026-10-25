# Candidato de implantação — ainda não publicado

A prática IV exige nuvem pública. O desenho local da prática II foi preservado como padrão de execução; foram preparados parâmetros específicos para uma futura implantação, sem expor o computador ou dados da Focus Fit.

- `FOCUS_PUBLIC_HOST`: domínio exato fornecido pela hospedagem, sem protocolo ou porta. Habilita cookie Secure e inclui esse Host na lista permitida.
- `FOCUS_DATA_DIRECTORY`: diretório privado e persistente para banco, segredo e cópias. Um disco efêmero não preserva registros entre reinicializações.
- `FOCUS_BIND_HOST`: endereço de escuta, padrão 127.0.0.1. O Dockerfile usa 0.0.0.0 somente dentro do contêiner.
- `PORT` ou `FOCUS_PORT`: porta do processo; padrão 8766.
- `/health`: verificação mínima do processo e leitura do banco, sem dados de usuário. Não mede sozinho disponibilidade histórica ou funcionamento de todas as funções.

O provedor deve oferecer HTTPS, volume persistente protegido e acesso para configuração pessoal da conta (`python app.py configurar`). Não existe conta padrão de produção nem cadastro aberto. Não inserir senha em código, chat, imagem ou GitHub. A execução remota exige também conferir acesso, backup, recursos, custos e políticas do provedor. A limitação de tentativas é local ao processo; uma implantação maior precisaria rever esse controle.

O Dockerfile foi preparado, mas não há build de contêiner, domínio, contratação, deploy ou monitoramento remoto comprovados. Somente os controles de configuração do Python foram testados localmente. Não usar um endereço de exemplo como URL de publicação.

Ainda precisam ser definidos e realizados: conta/repositório GitHub público autorizado; Pull Request e execução do Actions; serviço de nuvem; configuração de conta e armazenamento; publicação e ensaio por HTTPS; monitoramento com dados reais; duas rodadas com representante da Focus Fit; medição dos indicadores; Termo de Feedback com preenchimento e manifestação reais.
