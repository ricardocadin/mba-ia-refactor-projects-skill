# ARCHITECTURE AUDIT REPORT

Project: task-manager-api
Stack:   Python (versão não confirmada) + Flask 3.0.0
Files:   15 analyzed | ~1158 lines of code

## Summary
Date:    2026-11-09
CRITICAL: 5 | HIGH: 2 | MEDIUM: 4 | LOW: 3

## Achados por severidade
| # | Severidade | Problema | Localização | Observações | Ação proposta |
|---|:----------:|---|---|---|---|
| 1 | CRITICAL | Segredos hardcoded (SECRET_KEY e credenciais SMTP) | `app.py:13` | Também em `services/notification_service.py:9-10` | Mover para configuração por variável de ambiente. Requer decisão humana (variáveis obrigatórias ou default). |
| 2 | CRITICAL | Modo debug e bind de rede inseguro (`debug=True`, `host='0.0.0.0'`) | `app.py:34` | | Tornar debug e host configuráveis, com default seguro. Requer decisão humana (default de execução). |
| 3 | CRITICAL | Rotas sem autenticação/autorização e token falso | `routes/user_routes.py:210` | Todas as 22 rotas são anônimas, inclusive DELETE | Introduzir autenticação real e checagem de role. Requer decisão humana. |
| 4 | CRITICAL | Senha com hash fraco (MD5 sem salt) e hash devolvido nas respostas | `models/user.py:29` | Hash devolvido em `models/user.py:21` | Usar hash adequado e parar de devolver a senha. Requer decisão humana. |
| 5 | CRITICAL | God Module: relatórios e CRUD de categorias no mesmo arquivo de rotas | `routes/report_routes.py:12-223` | | Separar em controllers e models por entidade. |
| 6 | HIGH | Lógica de negócio nas rotas (overdue, estatísticas, cascata de exclusão) | `routes/task_routes.py:30-39` | `Task.is_overdue()` existe e não é usado | Mover regras para o model e para controllers. |
| 7 | HIGH | Acoplamento forte e quebra de camadas (rotas acessam `db` e models diretamente) | `routes/task_routes.py:14` | Sem controllers nem DI | Introduzir controllers entre rotas e models. |
| 8 | MEDIUM | Queries N+1 | `routes/task_routes.py:42` | | Carregar relacionamentos e contagens em lote. |
| 9 | MEDIUM | Tratamento genérico de erros (`except:` e sem handler global) | `routes/task_routes.py:62` | Corpo da resposta não vaza exceção; o erro é descartado | Centralizar em handler global. Requer decisão humana (formato de erro). |
| 10 | MEDIUM | Validação de entrada ausente ou inconsistente | `routes/task_routes.py:113` | Hoje gera 500 em vários casos | Validar tipos e corpo nulo. Requer decisão humana (500 passa a 400). |
| 11 | MEDIUM | Código duplicado (overdue, serialização, regex de e-mail, listas de status) | `routes/task_routes.py:30` | | Centralizar em model e em constantes. |
| 12 | LOW | Magic numbers e strings soltas | `routes/task_routes.py:110` | Constantes existem em `utils/helpers.py:110-116` e não são usadas | Usar constantes nomeadas. |
| 13 | LOW | Nomenclatura ruim | `routes/report_routes.py:24` | | Renomear variáveis crípticas. |
| 14 | LOW | Logging por print e código morto | `routes/task_routes.py:149` | | Usar `logging` e remover código morto. |

## Findings

### [CRITICAL] Segredos hardcoded (SECRET_KEY e credenciais SMTP) (AP-02)
File: `app.py:13` (+ `services/notification_service.py:9`, `services/notification_service.py:10`)
Description: `SECRET_KEY` fixo como `'super-secret-key-123'` e usuário/senha de SMTP (`taskmanager@gmail.com` / `senha123`) escritos no código versionado.
Evidence: `app.config['SECRET_KEY'] = 'super-secret-key-123'` (`app.py:13`); `self.email_password = 'senha123'` (`services/notification_service.py:10`)
Impact: quem tem acesso ao repositório conhece a chave e a senha de e-mail; sessões assinadas e a conta SMTP ficam comprometidas.
Recommendation: Requer decisão humana: ler os valores de variáveis de ambiente e decidir se ficam obrigatórias (a aplicação deixa de subir sem elas) ou se mantêm um default de desenvolvimento. (→ PB-02)

### [CRITICAL] Modo debug e bind de rede inseguro (AP-02)
File: `app.py:34`
Description: a aplicação sobe com `debug=True` e `host='0.0.0.0'`, expondo o debugger do Werkzeug em todas as interfaces de rede.
Evidence: `app.run(debug=True, host='0.0.0.0', port=5000)`
Impact: execução remota de código via console do debugger para quem alcançar a porta.
Recommendation: Requer decisão humana: definir o default de execução (debug desligado, host `127.0.0.1`) e como ligar em desenvolvimento. (→ PB-02)

### [CRITICAL] Rotas sem autenticação/autorização e token falso (AP-03)
File: `routes/user_routes.py:210` (+ `routes/user_routes.py:134`, `routes/task_routes.py:225`, `routes/report_routes.py:211`)
Description: nenhuma das 22 rotas verifica identidade ou role. `DELETE /users/<id>`, `DELETE /tasks/<id>`, `DELETE /categories/<id>` e `PUT /users/<id>` (que altera `role`) aceitam chamadas anônimas. O login devolve um token previsível, que ninguém valida. O campo `role` e `User.is_admin()` (`models/user.py:34`) nunca são consultados.
Evidence: `'token': 'fake-jwt-token-' + str(user.id)` (`routes/user_routes.py:210`)
Impact: qualquer cliente anônimo apaga dados, lista usuários e promove a si mesmo a admin.
Recommendation: Requer decisão humana: emitir token real (JWT ou sessão), decidir quais rotas passam a exigir autenticação e quais roles podem executar cada ação. Isso muda o que a API aceita. (→ PB-03)

### [CRITICAL] Senha com hash fraco (MD5 sem salt) e hash devolvido nas respostas (AP-03)
File: `models/user.py:29` (+ `models/user.py:32`, `models/user.py:21`, `routes/user_routes.py:33`, `routes/user_routes.py:85`, `routes/user_routes.py:129`, `routes/user_routes.py:209`)
Description: a senha é guardada com `hashlib.md5` sem salt, e `User.to_dict()` inclui o campo `password`, devolvido por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `/login`.
Evidence: `self.password = hashlib.md5(pwd.encode()).hexdigest()` (`models/user.py:29`); `'password': self.password,` (`models/user.py:21`)
Impact: hashes MD5 são quebrados por tabela e força bruta em segundos, e qualquer cliente anônimo os obtém pela API.
Recommendation: Requer decisão humana: (a) remover `password` das respostas (campo some do JSON); (b) trocar o algoritmo, o que invalida os hashes MD5 existentes e o `seed.py` (migração ou recriação das senhas). (→ PB-03)

### [CRITICAL] God Module: relatórios e CRUD de categorias no mesmo arquivo de rotas (AP-04)
File: `routes/report_routes.py:12-223`
Description: o blueprint `reports` mistura relatórios agregados de Task e User (`routes/report_routes.py:12`, `routes/report_routes.py:103`) com o CRUD completo de Category (`routes/report_routes.py:157-223`). O arquivo importa `db` e o framework web, faz consultas, calcula regras e monta a resposta HTTP.
Evidence: `@report_bp.route('/categories', methods=['GET'])` (`routes/report_routes.py:157`) no mesmo módulo de `/reports/summary` (`routes/report_routes.py:12`)
Impact: uma mudança em categorias ou em relatórios mexe no mesmo arquivo; testes isolados são inviáveis.
Recommendation: separar rotas, controllers e models por entidade (Category, Report). (→ PB-04)

### [HIGH] Lógica de negócio nas rotas (AP-05)
File: `routes/task_routes.py:30-39` (+ `routes/task_routes.py:71`, `routes/task_routes.py:284`, `routes/user_routes.py:171`, `routes/report_routes.py:34`, `routes/report_routes.py:132`, `routes/report_routes.py:56`, `routes/task_routes.py:296`, `routes/user_routes.py:140`)
Description: a regra de atraso (overdue), os cálculos de taxa de conclusão e estatísticas e a exclusão em cascata das tasks do usuário estão nos handlers. `Task.is_overdue()` (`models/task.py:50`) existe e não é chamado.
Evidence: `if t.due_date:` seguido de comparação com `datetime.utcnow()` e status (`routes/task_routes.py:30`); `db.session.delete(t)` em laço (`routes/user_routes.py:142`)
Impact: regras divergentes entre endpoints e impossíveis de testar sem HTTP e banco.
Recommendation: mover a regra para o model e a orquestração para controllers. (→ PB-05)

### [HIGH] Acoplamento forte e quebra de camadas (AP-07)
File: `routes/task_routes.py:14` (+ `routes/task_routes.py:2`, `routes/user_routes.py:2`, `routes/user_routes.py:12`, `routes/report_routes.py:2`, `routes/report_routes.py:15`)
Description: os módulos de rotas importam `db` e os models e consultam o banco direto (`Task.query`, `db.session`), pulando qualquer camada intermediária. Não existe camada de controllers nem de services ativa.
Evidence: `tasks = Task.query.all()` (`routes/task_routes.py:14`); `from database import db` (`routes/task_routes.py:2`)
Impact: não é possível testar as rotas com mock nem trocar a fonte de dados sem editá-las.
Recommendation: introduzir controllers que recebam a requisição e chamem os models, com rotas só registrando caminhos. (→ PB-07)

### [MEDIUM] Queries N+1 (AP-09)
File: `routes/task_routes.py:42` (+ `routes/task_routes.py:51`, `routes/user_routes.py:22`, `routes/report_routes.py:56`, `routes/report_routes.py:163`)
Description: `GET /tasks` consulta User e Category dentro do laço de tasks. `GET /users` percorre `len(u.tasks)` (carga lazy por usuário). `/reports/summary` consulta as tasks de cada usuário em laço. `GET /categories` faz um `count()` por categoria.
Evidence: `user = User.query.get(t.user_id)` dentro de `for t in tasks:` (`routes/task_routes.py:42`)
Impact: o número de consultas cresce linearmente com o volume de dados.
Recommendation: usar `joinedload` ou consultas agregadas em lote. (→ PB-09)

### [MEDIUM] Tratamento genérico de erros (AP-10)
File: `routes/task_routes.py:62` (+ `routes/task_routes.py:137`, `routes/task_routes.py:204`, `routes/task_routes.py:236`, `routes/user_routes.py:130`, `routes/user_routes.py:149`, `routes/report_routes.py:186`, `routes/report_routes.py:207`, `routes/report_routes.py:221`)
Description: `except:` sem tipo em 9 handlers captura até `KeyboardInterrupt` e descarta o erro sem registro. Não há handler global de erros. A resposta ao cliente não vaza a exceção, mas as formas de erro variam entre rotas.
Evidence: `except:` seguido de `return jsonify({'error': 'Erro interno'}), 500` (`routes/task_routes.py:62`)
Impact: falhas reais ficam invisíveis; diagnóstico fraco.
Recommendation: Requer decisão humana: registrar um tratador global e definir o formato de erro (hoje `{'error': '<mensagem>'}`), pois erros não tratados (ex.: 404 de rota inexistente, 500) passam a seguir o novo formato. (→ PB-10)

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-10)
File: `routes/task_routes.py:113` (+ `routes/task_routes.py:182`, `routes/task_routes.py:167`, `routes/task_routes.py:261`, `routes/task_routes.py:264`, `routes/report_routes.py:197`, `routes/user_routes.py:103`, `routes/user_routes.py:125`)
Description: `priority` não numérico quebra a comparação (`TypeError`, 500) em POST e PUT de tasks. `int(priority)` e `int(user_id)` em `/tasks/search` geram 500 com texto não numérico. `PUT /categories/<id>` não checa corpo nulo. `PUT /users/<id>` aceita `name` vazio ou de qualquer tipo, e `active` sem validação. `title` em PUT não checa tipo.
Evidence: `if priority < 1 or priority > 5:` (`routes/task_routes.py:113`); `if 'name' in data:` com `data` possivelmente `None` (`routes/report_routes.py:197`)
Impact: respostas 500 evitáveis e dados inconsistentes no banco.
Recommendation: Requer decisão humana: validar tipo e corpo em todas as rotas. Entradas que hoje geram 500 ou são aceitas passam a gerar 400 (mudança de comportamento). (→ PB-10)

### [MEDIUM] Código duplicado (AP-11)
File: `routes/task_routes.py:30` (+ `routes/task_routes.py:71`, `routes/task_routes.py:284`, `routes/user_routes.py:171`, `routes/report_routes.py:34`, `routes/report_routes.py:132`, `routes/task_routes.py:18`, `routes/user_routes.py:162`, `models/task.py:24`, `routes/user_routes.py:61`, `routes/user_routes.py:106`, `utils/helpers.py:21`, `routes/task_routes.py:110`, `routes/task_routes.py:177`, `models/task.py:39`)
Description: a regra de overdue está copiada em 6 handlers (além de `Task.is_overdue`, `models/task.py:50`). A serialização de Task é montada à mão em `routes/task_routes.py:18` e `routes/user_routes.py:162`, duplicando `Task.to_dict`. O regex de e-mail aparece em 3 lugares e a lista de status em 3.
Evidence: `task_data['id'] = t.id` (`routes/task_routes.py:18`) repete `data['id'] = self.id` (`models/task.py:25`)
Impact: uma mudança de regra ou de schema precisa ser replicada em vários pontos, com risco de divergência.
Recommendation: centralizar overdue, serialização e validação no model e em constantes. (→ PB-11)

### [LOW] Magic numbers e strings soltas (AP-13)
File: `routes/task_routes.py:110` (+ `routes/task_routes.py:177`, `models/task.py:39`, `routes/user_routes.py:71`, `routes/user_routes.py:120`, `routes/task_routes.py:113`, `routes/task_routes.py:182`, `models/task.py:46`, `routes/task_routes.py:96`, `routes/task_routes.py:99`, `routes/user_routes.py:64`, `routes/user_routes.py:115`, `routes/report_routes.py:45`, `routes/report_routes.py:180`, `models/category.py:10`)
Description: listas de status e roles, limites de prioridade (1 a 5), tamanho de título (3 e 200), tamanho mínimo de senha (4), janela de 7 dias e cor padrão `'#000000'` repetidos como literais. As constantes `VALID_STATUSES`, `VALID_ROLES`, `MIN_PASSWORD_LENGTH` e demais existem em `utils/helpers.py:110-116` e não são usadas.
Evidence: `if status not in ['pending', 'in_progress', 'done', 'cancelled']:` (`routes/task_routes.py:110`)
Impact: regra difícil de localizar e de alterar, com risco de divergência.
Recommendation: usar constantes nomeadas em um único módulo. (→ PB-13)

### [LOW] Nomenclatura ruim (AP-13)
File: `routes/report_routes.py:24` (+ `routes/task_routes.py:16`, `routes/task_routes.py:122`, `models/task.py:45`)
Description: `p1` a `p5` guardam contagens por prioridade (`routes/report_routes.py:24-28`). `t` percorre mais de 40 linhas de regra de negócio (`routes/task_routes.py:16`). `cat` (`routes/task_routes.py:122`) e o parâmetro `p` (`models/task.py:45`) não revelam o conteúdo.
Evidence: `p1 = Task.query.filter_by(priority=1).count()` (`routes/report_routes.py:24`)
Impact: a leitura exige contexto adicional para entender o que cada variável guarda.
Recommendation: renomear para nomes descritivos (por exemplo `critical_count`, `task`, `category`). (→ PB-13)

### [LOW] Logging por print e código morto (AP-14)
File: `routes/task_routes.py:149` (+ `routes/task_routes.py:153`, `routes/task_routes.py:219`, `routes/task_routes.py:234`, `routes/user_routes.py:83`, `routes/user_routes.py:89`, `routes/user_routes.py:147`, `services/notification_service.py:21`, `services/notification_service.py:24`, `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`, `routes/report_routes.py:7`, `routes/report_routes.py:8`, `models/task.py:3`, `utils/helpers.py:2`, `utils/helpers.py:57`, `utils/helpers.py:110`, `services/notification_service.py:4`, `requirements.txt:4`)
Description: `print` usado como log em handlers e no serviço de e-mail. Imports sem uso (`os`, `sys`, `json`, `time`, `hashlib`, `format_date`, `calculate_percentage`). `NotificationService` nunca é instanciada, `process_task_data`, `log_action` e as constantes de `utils/helpers.py` não são usados. `SECRET_KEY` só é escrita (`app.py:13`, sem leitura nem uso de sessão). `marshmallow`, `requests` e `python-dotenv` (`requirements.txt:4-6`) não são importados em nenhum arquivo.
Evidence: `print(f"Task criada: {task.id} - {task.title}")` (`routes/task_routes.py:149`); `import json, os, sys, time` (`routes/task_routes.py:7`)
Impact: diagnóstico fraco em produção e ruído na leitura.
Recommendation: usar o módulo `logging` e remover o código morto. Requer decisão humana quanto à `NotificationService` e às dependências não usadas (remover ou manter para uso futuro). (→ PB-14)

## Not Verified
- AP-12 `datetime.utcnow()` (`models/task.py:15`, `routes/task_routes.py:31` e outros): a depreciação depende da versão do Python | Reason: o runtime não está declarado (sem `.python-version`, `Dockerfile` ou CI), então não é confirmado.
- AP-12 `Model.query.get()` (`routes/task_routes.py:67` e outros): API legada do SQLAlchemy | Reason: o SQLAlchemy não está pinado em `requirements.txt` (só `flask-sqlalchemy==3.1.1`), então a versão não é confirmada.
- AP-12 bibliotecas sem manutenção (`requirements.txt:1-6`): estado de manutenção das versões pinadas | Reason: não há lockfile nem acesso a registro de pacotes na Fase 2 (somente leitura).
- AP-01, AP-03 e AP-10 por execução (PoC sem credenciais, corpo inválido): não executados | Reason: a Fase 2 é somente leitura e a aplicação só sobe na Fase 3.
- AP-14 por linter (pyflakes/ruff): não executado | Reason: ferramenta não instalada na Fase 2. Os imports sem uso foram verificados por busca textual do nome em cada arquivo.

### Total: 14 findings

# PHASE 3: REFACTORING COMPLETE

## New Project Structure
```
task-manager-api/
├── app.py                      # composition root (create_app) e entry point
├── seed.py                     # script de carga inicial (usa create_app)
├── database.py                 # extensão SQLAlchemy (db)
├── config/
│   ├── settings.py             # único módulo que lê o ambiente (Config)
│   └── logging_config.py
├── constants/                  # status, roles, limites, regex, cores, rótulos (task, user, category, report)
├── exceptions/errors.py        # AppError, ValidationError, NotFoundError, ConflictError, Unauthorized/Forbidden, PersistenceError
├── middlewares/
│   ├── auth_middleware.py      # exige token (e role, quando indicada)
│   └── error_middleware.py     # handler global de erros
├── models/
│   ├── task.py, user.py, category.py                    # entidades ORM e regras intrínsecas (is_overdue, hash de senha)
│   ├── task_model.py, user_model.py, category_model.py  # acesso a dados (sem estado e sem commit)
│   └── transaction.py          # fronteira de transação (commit/rollback)
├── validators/                 # validação de formato de entrada (task, user, category)
├── services/                   # regras de negócio e transações (task, user, category, report, auth, metrics)
├── controllers/                # HTTP -> service -> view (task, user, category, report, system)
├── views/                      # serializadores de saída (task, user, category, report)
├── routes/                     # registro de rotas por recurso (task, user, category, report, system)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```
Removidos: `utils/` (helpers sem uso) e `services/notification_service.py`.

## Validation
- [x] ✓ Application boots without errors (boot limpo, `after-boot.log` sem traceback/exception; `seed.py` e `python app.py` executados)
- [x] ✓ 111/111 chamadas respondem como esperado (87 OK, 24 CHANGED aprovados, 0 FAIL) nos 22 endpoints, incluindo caminhos de erro
- [x] ✓ Status codes match baseline (exceto os 24 CHANGED listados em Intentional changes)
- [x] ✓ 13/14 findings resolved (re-detected with the catalog signals); AP-03a resolvido apenas no escopo decidido
- [x] ✓ Rotas anônimas (PoC AP-03) deixam de funcionar: `DELETE /tasks/6` sem token era 200, agora 401; `DELETE /users/2` com token de role `user` era 200, agora 403; `PUT /users/1` sem token era 200, agora 401
- [x] ✓ Hash de senha não é mais devolvido (`"password"` em 13 corpos do baseline, 0 no after) e o hash MD5 legado é regravado em scrypt no login (`joao@email.com` com prefixo `scrypt:` no banco após o login)
- [x] ✓ Consultas N+1 eliminadas: `/tasks` 1 consulta, `/users` 2, `/categories` 2, `/reports/summary` 10 (fixo, independente do volume)
- [ ] ✗ 1 anti-pattern remaining: AP-03a (as demais rotas, como `GET /users`, `POST /users` e `POST /tasks`, seguem abertas por decisão do usuário)
- [x] ✓ DeprecationWarnings: 11 no baseline, 4 no after (`Model.query.get()` foi substituído por `db.session.get()`; `datetime.utcnow()` permanece, ver Not verified)

### Intentional changes
- Autenticação (decisão do usuário: token assinado, exigido só nas rotas destrutivas): `/login` devolve token assinado (itsdangerous, validade `TOKEN_MAX_AGE`); `DELETE /tasks/<id>` e `DELETE /categories/<id>` exigem `Authorization: Bearer` (401 sem token ou com token inválido); `PUT /users/<id>` e `DELETE /users/<id>` exigem token de `admin` (403 para outra role).
- Campo `password` removido das respostas de `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` (decisão do usuário).
- Hash de senha trocado de MD5 para scrypt (werkzeug), com migração transparente no primeiro login válido de usuários com hash MD5 (decisão do usuário). O MD5 permanece apenas em `models/user.py`, para verificar hashes legados.
- Configuração por ambiente (decisão do usuário): `SECRET_KEY` obrigatória, exceto com `APP_DEBUG=1` (gera uma chave aleatória por processo com `secrets.token_hex`, sem literal no código; os tokens emitidos não sobrevivem a um reinício); o padrão de execução passa a ser debug desligado e host `127.0.0.1` (antes `debug=True` e `0.0.0.0`). `seed.py` também exige `SECRET_KEY` ou `APP_DEBUG=1`. As credenciais SMTP saíram do código junto com `NotificationService`.
- CORS restrito (decisão do usuário: nenhuma origem por padrão): `CORS(app, origins=config.CORS_ORIGINS)` com a nova variável `CORS_ORIGINS` (origens de navegador separadas por vírgula; vazia = nenhuma). Navegadores de outras origens deixam de receber `Access-Control-Allow-Origin`; `curl` e outros serviços não são afetados. A auditoria da Fase 2 não reportou o CORS aberto (`app.py:38`) porque o catálogo ainda não tinha esse sinal; ele foi tratado depois, a pedido do autor.
- Entradas que antes geravam 500 passam a gerar 400 com mensagem (decisão do usuário): `priority` não numérico em `POST`/`PUT /tasks`, `priority` e `user_id` não numéricos em `GET /tasks/search`, `title` que não é texto em `PUT /tasks/<id>`, corpo `null` em `PUT /categories/<id>`.
- Exceção não tratada passa a devolver JSON `{"error": "Erro interno"}` (500), com o stack trace só no log, em vez da página HTML do Flask (decisão do usuário). Os demais erros mantêm o formato `{"error": "<mensagem>"}` e as mensagens atuais; 404, 405 e 415 do Flask seguem em HTML.
- Dependências `marshmallow` e `requests` removidas de `requirements.txt` e código morto (`utils/helpers.py`, `NotificationService`) apagado (decisão do usuário).
- `GET /tasks` passa a ordenar por `id` (antes sem `ORDER BY`; na prática a mesma ordem).
- AP-12, `Model.query.get()` (decisão do usuário: tratar como confirmado): as 16 chamadas em `routes/` foram substituídas por 3 métodos de `models/*_model.py` que usam `db.session.get(Model, id)`, o equivalente moderno recomendado pelo SQLAlchemy 2.x. A depreciação é confirmada porque a `flask-sqlalchemy==3.1.1`, pinada em `requirements.txt:2`, exige `sqlalchemy>=2.0.16`, e a partir da 2.0 o `Query.get()` é um recurso legado. As respostas não mudam (nenhuma diferença nas chamadas comparadas). Na Fase 2 este item estava em Not Verified por o SQLAlchemy não estar pinado; a versão mínima passou a ser derivada da exigência da `flask-sqlalchemy`.

### Not verified
- CORS: o comportamento foi verificado com o cliente de teste do Flask (origem não listada sem cabeçalho, origem listada com cabeçalho), não em um navegador real nem com um front-end.
- AP-12, `datetime.utcnow()` (não confirmado e não alterado): **permanece em 12 linhas** (`models/category.py:14`, `models/task.py:17`, `models/task.py:18`, `models/task.py:28`, `models/user.py:20`, `services/report_service.py:22`, `services/task_service.py:93` e `seed.py:70`, `seed.py:71`, `seed.py:73`, `seed.py:74`, `seed.py:78`). É uma API deprecated desde o Python 3.12 (devolve um `datetime` sem fuso e emite `DeprecationWarning`); o equivalente moderno recomendado é `datetime.now(timezone.utc)`. A depreciação não é confirmada porque o projeto não declara a versão do Python (sem `.python-version`, `Dockerfile` ou CI) e a regra da skill só considera a versão declarada. Também não foi alterada porque trocar por uma data com fuso mudaria o formato dos timestamps e quebraria comparações com as datas sem fuso já gravadas no banco (mudança de comportamento sem decisão). A validação rodou em Python 3.15.2, que emite 11 `DeprecationWarning` no baseline e 4 no after.
- Carga de `.env` por python-dotenv, `APP_DEBUG=1`, `HOST` e `PORT` customizados: não executados (a validação usou variáveis de ambiente diretas e só testou o aborto sem `SECRET_KEY`).
- A autorização por role usa a role gravada no token (não consulta o banco): um usuário rebaixado mantém a role antiga até o token expirar (`TOKEN_MAX_AGE`, padrão 3600 s). A expiração do token não foi testada.
- Desempenho e concorrência: não medidos (apenas a contagem de consultas). O projeto não tem testes automatizados.
- Entradas ainda sem validação (fora do escopo decidido): `tags` com itens não texto, `user_id` e `category_id` de tipo inesperado, `email` não texto. Geram o 500 genérico em JSON.
- Endpoints destrutivos: não existe rota de reset ou de SQL arbitrário; as exclusões (`DELETE`) rodaram contra uma cópia descartável do banco.

### Endpoint comparison
| Method | Path | Baseline | After | Result |
|---|---|:---:|:---:|:---:|
| GET | `/` (root) | 200 | 200 | OK |
| GET | `/health` (health) | 200 | 200 | OK |
| GET | `/tasks` (tasks_list) | 200 | 200 | OK |
| GET | `/tasks/1` (task_1) | 200 | 200 | OK |
| GET | `/tasks/9999` (task_404) | 404 | 404 | OK |
| GET | `/tasks/search?q=Configurar` (search_q) | 200 | 200 | OK |
| GET | `/tasks/search?status=pending` (search_status) | 200 | 200 | OK |
| GET | `/tasks/search?priority=1` (search_priority) | 200 | 200 | OK |
| GET | `/tasks/search?user_id=1` (search_user) | 200 | 200 | OK |
| GET | `/tasks/search` (search_all) | 200 | 200 | OK |
| GET | `/tasks/search?q=%25` (search_special) | 200 | 200 | OK |
| GET | `/tasks/search?q=zzzz%27)%20OR%201=1--%20` (search_sqli) | 200 | 200 | OK |
| GET | `/tasks/search?priority=abc` (search_badprio) | 500 | 400 | CHANGED |
| GET | `/tasks/search?user_id=x` (search_baduser) | 500 | 400 | CHANGED |
| GET | `/tasks/stats` (stats) | 200 | 200 | OK |
| GET | `/users` (users_list) | 200 | 200 | OK |
| GET | `/users/1` (user_1) | 200 | 200 | CHANGED |
| GET | `/users/9999` (user_404) | 404 | 404 | OK |
| GET | `/users/1/tasks` (user_1_tasks) | 200 | 200 | OK |
| GET | `/users/9999/tasks` (user_404_tasks) | 404 | 404 | OK |
| GET | `/reports/summary` (reports_summary) | 200 | 200 | OK |
| GET | `/reports/user/1` (report_user_1) | 200 | 200 | OK |
| GET | `/reports/user/9999` (report_user_404) | 404 | 404 | OK |
| GET | `/categories` (categories_list) | 200 | 200 | OK |
| POST | `/login` (login_ok) | 200 | 200 | CHANGED |
| POST | `/login` (login_ok_again) | 200 | 200 | CHANGED |
| POST | `/login` (login_bad_pw) | 401 | 401 | OK |
| POST | `/login` (login_unknown) | 401 | 401 | OK |
| POST | `/login` (login_missing) | 400 | 400 | OK |
| POST | `/login` (login_empty) | 400 | 400 | OK |
| POST | `/login` (login_maria) | 200 | 200 | CHANGED |
| POST | `/tasks` (task_create_ok) | 201 | 201 | OK |
| POST | `/tasks` (task_create_min) | 201 | 201 | OK |
| POST | `/tasks` (task_create_tags_str) | 201 | 201 | OK |
| POST | `/tasks` (task_create_empty) | 400 | 400 | OK |
| POST | `/tasks` (task_create_short) | 400 | 400 | OK |
| POST | `/tasks` (task_create_long) | 400 | 400 | OK |
| POST | `/tasks` (task_create_badstatus) | 400 | 400 | OK |
| POST | `/tasks` (task_create_badprio) | 400 | 400 | OK |
| POST | `/tasks` (task_create_prio_str) | 500 | 400 | CHANGED |
| POST | `/tasks` (task_create_baduser) | 404 | 404 | OK |
| POST | `/tasks` (task_create_badcat) | 404 | 404 | OK |
| POST | `/tasks` (task_create_baddate) | 400 | 400 | OK |
| PUT | `/tasks/2` (task_update_ok) | 200 | 200 | OK |
| PUT | `/tasks/3` (task_update_tags_list) | 200 | 200 | OK |
| PUT | `/tasks/3` (task_update_cleardate) | 200 | 200 | OK |
| PUT | `/tasks/9999` (task_update_404) | 404 | 404 | OK |
| PUT | `/tasks/2` (task_update_empty) | 400 | 400 | OK |
| PUT | `/tasks/2` (task_update_short) | 400 | 400 | OK |
| PUT | `/tasks/2` (task_update_long) | 400 | 400 | OK |
| PUT | `/tasks/2` (task_update_badstatus) | 400 | 400 | OK |
| PUT | `/tasks/2` (task_update_badprio) | 400 | 400 | OK |
| PUT | `/tasks/2` (task_update_prio_str) | 500 | 400 | CHANGED |
| PUT | `/tasks/2` (task_update_title_int) | 500 | 400 | CHANGED |
| PUT | `/tasks/2` (task_update_baduser) | 404 | 404 | OK |
| PUT | `/tasks/2` (task_update_badcat) | 404 | 404 | OK |
| PUT | `/tasks/2` (task_update_baddate) | 400 | 400 | OK |
| POST | `/users` (user_create_ok) | 201 | 201 | CHANGED |
| POST | `/users` (user_create_default_role) | 201 | 201 | CHANGED |
| POST | `/users` (user_create_empty) | 400 | 400 | OK |
| POST | `/users` (user_create_noname) | 400 | 400 | OK |
| POST | `/users` (user_create_noemail) | 400 | 400 | OK |
| POST | `/users` (user_create_nopw) | 400 | 400 | OK |
| POST | `/users` (user_create_bademail) | 400 | 400 | OK |
| POST | `/users` (user_create_shortpw) | 400 | 400 | OK |
| POST | `/users` (user_create_dup) | 409 | 409 | OK |
| POST | `/users` (user_create_badrole) | 400 | 400 | OK |
| POST | `/login` (login_new_user) | 200 | 200 | CHANGED |
| PUT | `/users/2` (user_update_ok) | 200 | 200 | CHANGED |
| POST | `/login` (login_after_pw_change) | 200 | 200 | CHANGED |
| POST | `/login` (login_old_pw_rejected) | 401 | 401 | OK |
| PUT | `/users/9999` (user_update_404) | 404 | 404 | OK |
| PUT | `/users/2` (user_update_empty) | 400 | 400 | OK |
| PUT | `/users/2` (user_update_bademail) | 400 | 400 | OK |
| PUT | `/users/2` (user_update_dup) | 409 | 409 | OK |
| PUT | `/users/2` (user_update_shortpw) | 400 | 400 | OK |
| PUT | `/users/2` (user_update_badrole) | 400 | 400 | OK |
| PUT | `/users/3` (user_update_inactive) | 200 | 200 | CHANGED |
| POST | `/login` (login_inactive) | 403 | 403 | OK |
| GET | `/users/3/tasks` (user_tasks_after) | 200 | 200 | OK |
| POST | `/categories` (cat_create_ok) | 201 | 201 | OK |
| POST | `/categories` (cat_create_min) | 201 | 201 | OK |
| POST | `/categories` (cat_create_empty) | 400 | 400 | OK |
| POST | `/categories` (cat_create_noname) | 400 | 400 | OK |
| PUT | `/categories/1` (cat_update_ok) | 200 | 200 | OK |
| PUT | `/categories/2` (cat_update_noop) | 200 | 200 | OK |
| PUT | `/categories/9999` (cat_update_404) | 404 | 404 | OK |
| PUT | `/categories/2` (cat_update_null) | 500 | 400 | CHANGED |
| DELETE | `/tasks/10` (task_delete_ok) | 200 | 200 | OK |
| DELETE | `/tasks/9999` (task_delete_404) | 404 | 404 | OK |
| DELETE | `/categories/5` (cat_delete_ok) | 200 | 200 | OK |
| DELETE | `/categories/9999` (cat_delete_404) | 404 | 404 | OK |
| DELETE | `/users/4` (user_delete_ok) | 200 | 200 | OK |
| DELETE | `/users/9999` (user_delete_404) | 404 | 404 | OK |
| DELETE | `/users/3` (user_delete_cascade) | 200 | 200 | OK |
| GET | `/tasks` (tasks_list_final) | 200 | 200 | OK |
| GET | `/users` (users_list_final) | 200 | 200 | OK |
| GET | `/categories` (categories_list_final) | 200 | 200 | OK |
| GET | `/tasks/stats` (stats_final) | 200 | 200 | OK |
| GET | `/reports/summary` (reports_summary_final) | 200 | 200 | OK |
| GET | `/reports/user/1` (report_user_1_final) | 200 | 200 | OK |
| GET | `/users/1` (user_1_final) | 200 | 200 | CHANGED |
| DELETE | `/tasks/6` (poc_task_delete_noauth) | 200 | 401 | CHANGED |
| DELETE | `/categories/4` (poc_cat_delete_noauth) | 200 | 401 | CHANGED |
| PUT | `/users/1` (poc_user_put_noauth) | 200 | 401 | CHANGED |
| DELETE | `/users/2` (poc_user_delete_nonadmin) | 200 | 403 | CHANGED |
| PUT | `/users/1` (poc_user_put_nonadmin) | 200 | 403 | CHANGED |
| DELETE | `/tasks/5` (poc_task_delete_badtoken) | 200 | 401 | CHANGED |
| DELETE | `/users/2` (poc_user_delete_noauth) | 404 | 401 | CHANGED |
| POST | `/tasks (sem JSON)` (task_create_notjson) | 415 | 415 | OK |
| POST | `/users (sem JSON)` (user_create_notjson) | 415 | 415 | OK |

Nos 24 `CHANGED`: 11 por remoção do campo `password` (`user_1`, `user_1_final`, `login_ok`, `login_ok_again`, `login_maria`, `login_new_user`, `login_after_pw_change`, `user_create_ok`, `user_create_default_role`, `user_update_ok`, `user_update_inactive`), 6 por 500 convertido em 400 (`search_badprio`, `search_baduser`, `task_create_prio_str`, `task_update_prio_str`, `task_update_title_int`, `cat_update_null`) e 7 por autenticação exigida (`poc_*`). A comparação foi feita com `scripts/compare.py` (`--ignore generated_at,password`), mais a checagem separada do campo `password`.

## Checklist de Validação (Fase 3)
- [x] Estrutura de diretórios segue padrão MVC: `find . -type f` mostra `config/`, `models/`, `routes/`, `controllers/`, `views/`, `services/`, `middlewares/`, `validators/`, `exceptions/`, `constants/`, com os arquivos nas camadas (ver New Project Structure).
- [x] Configuração extraída para módulo de config (sem hardcoded): a busca do AP-02 (`SECRET_KEY`/`password` com literal) retorna vazio, e a chave de desenvolvimento (`APP_DEBUG=1`) é gerada com `secrets.token_hex`; porta, URL do banco e origens do CORS só em `config/settings.py`. Sobram literais de status apenas como chaves do JSON de resposta (`services/task_service.py:126-129`, `services/report_service.py:73-76`) e em `seed.py`.
- [x] Models criados para abstrair dados: `grep -rnE "\.query|db\.session|from database|sqlalchemy" services controllers routes views validators middlewares` retorna vazio; o acesso a dados está em `models/*_model.py` e `models/transaction.py`.
- [x] Views/Routes separadas para visualização ou roteamento: `routes/*_routes.py` só registram rotas (`add_url_rule`) e `views/*_view.py` só serializam.
- [x] Controllers concentram o fluxo da aplicação: `controllers/*.py` leem a requisição, validam o corpo, chamam o service e devolvem `jsonify`; `grep -rnE "if .*status|datetime|round\(" controllers routes` (exceto `system_controller.py`) retorna vazio.
- [x] Error handling centralizado: um único registro em `middlewares/error_middleware.py` (`AppError` e `Exception`); `grep -rnE "except:|str\(e\)|except Exception" controllers routes validators views` retorna vazio. Os `except Exception` dos services convertem em `PersistenceError` com a mensagem original.
- [x] Entry point claro: `app.py` (`create_app` monta config, models, services, controllers e rotas; o `__main__` só inicia).
- [x] Aplicação inicia sem erros: boot final com `python app.py`, `grep -ciE 'traceback|exception|ModuleNotFound'` no log = 0; porta 5000 livre depois.
- [x] Endpoints originais respondem corretamente: `compare.py` baseline x after, 111 chamadas, 87 OK, 24 CHANGED (todas aprovadas), 0 FAIL.
