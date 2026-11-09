# ARCHITECTURE AUDIT REPORT

Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code

## Summary
Date:    2026-11-09
CRITICAL: 6 | HIGH: 5 | MEDIUM: 4 | LOW: 2

## Achados por severidade
| # | Severidade | Problema | Localização | Observações | Ação proposta |
|---|:----------:|---|---|---|---|
| 1 | CRITICAL | SQL Injection / Query por concatenação | `models.py:48-49` | Ocorrências em 7 funções do model | Usar queries parametrizadas |
| 2 | CRITICAL | Segredo da aplicação hardcoded e exposto | `app.py:7` | Também devolvido por `/health` | Ler de variável de ambiente e remover do `/health` |
| 3 | CRITICAL | Modo debug ativo exposto na rede | `app.py:88` | `debug=True` com `host="0.0.0.0"` | Debug e host configuráveis, desligados por padrão. Requer decisão humana (host padrão e chave obrigatória) |
| 4 | CRITICAL | Rotas administrativas sem autenticação | `app.py:47-78` | Inclui SQL arbitrário | Exigir autenticação/autorização. Requer decisão humana |
| 5 | CRITICAL | Senhas em texto puro | `models.py:126-128` | Armazenada, comparada e devolvida | Aplicar hash na gravação e na comparação. Requer decisão humana |
| 6 | CRITICAL | God Module (models, app e database) | `models.py:1-314` | 4 domínios no mesmo arquivo | Separar em models e controllers por domínio |
| 7 | HIGH | Lógica de negócio fora da camada correta | `controllers.py:208-210` | Notificações e desconto fora de uma camada de serviço | Mover regras para a camada adequada |
| 8 | HIGH | Estado global mutável (conexão) | `database.py:4-10` | | Substituir por conexão por requisição/fábrica |
| 9 | HIGH | Acoplamento forte e quebra de camadas | `controllers.py:3` | Controller e rota executam SQL | Acessar dados só pelos models, com injeção |
| 10 | HIGH | Criação de pedido sem transação/rollback | `models.py:133-169` | Também `app.py:51-55` | Envolver em transação com rollback |
| 11 | HIGH | Cancelamento não devolve estoque | `controllers.py:249-250` | Efeito de negócio só impresso | Executar a devolução de estoque. Requer decisão humana |
| 12 | MEDIUM | Queries N+1 | `models.py:187-193` | Dois níveis aninhados | Carregar itens e produtos com JOIN |
| 13 | MEDIUM | Tratamento genérico de erros | `controllers.py:10-12` | `str(e)` devolvido ao cliente | Handler global de erro. Requer decisão humana (formato do erro) |
| 14 | MEDIUM | Validação de entrada ausente ou inconsistente | `controllers.py:239-240` | | Validar corpo, tipos e existência de forma centralizada. Requer decisão humana (validações que rejeitam entrada hoje aceita) |
| 15 | MEDIUM | Código duplicado | `models.py:12-21` | Serialização e validações repetidas | Centralizar serialização e validação |
| 16 | LOW | Magic numbers e strings soltas | `models.py:257-262` | Faixas de desconto, status e categorias | Extrair para constantes nomeadas |
| 17 | LOW | Logging por print e código morto | `controllers.py:8` | Imports sem uso | Usar `logging` e remover código morto |

## Findings

### [CRITICAL] SQL Injection / Query por concatenação (AP-01)
File: models.py:48-49 (+ models.py:58-60, models.py:110, models.py:127-128, models.py:140, models.py:148-150, models.py:155, models.py:157-160, models.py:163-165, models.py:291-297)
Description: valores vindos do corpo JSON e da query string (`nome`, `descricao`, `categoria`, `email`, `senha`, `usuario_id`, `produto_id`, `quantidade`, `q`) são concatenados em strings SQL em `criar_produto`, `atualizar_produto`, `login_usuario`, `criar_usuario`, `criar_pedido` e `buscar_produtos`.
Evidence: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` (models.py:109-111). Os `id` de `<int:id>` (models.py:28, 68, 92, 174, 280), `preco_min`/`preco_max` (convertidos com `float()`, controllers.py:118-121), `status` (lista fechada, controllers.py:242) e valores lidos do banco (models.py:188, 192, 220, 224) foram avaliados e descartados: não são exploráveis.
Impact: leitura, alteração ou destruição de qualquer dado do banco; bypass do login com `' OR '1'='1`.
Recommendation: usar queries parametrizadas em todo o acesso a dados (→ PB-01)

### [CRITICAL] Segredo da aplicação hardcoded e exposto (AP-02)
File: app.py:7 (+ controllers.py:289)
Description: `SECRET_KEY` fixa no código-fonte (`minha-chave-super-secreta-123`) e devolvida em texto na resposta de `/health`, junto com `db_path`.
Evidence: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` (app.py:7); `"secret_key": "minha-chave-super-secreta-123"` e `"db_path": "loja.db"` no JSON de `/health` (controllers.py:287, 289).
Impact: qualquer cliente lê o segredo e pode forjar sessões ou tokens assinados com ele.
Recommendation: carregar o segredo de variável de ambiente em um módulo de config e remover os campos sensíveis do `/health` (→ PB-02)

### [CRITICAL] Modo debug ativo exposto na rede (AP-02)
File: app.py:88 (+ app.py:8, controllers.py:288)
Description: a aplicação sobe com `debug=True` em `host="0.0.0.0"`, e `/health` reporta `"debug": True` fixo.
Evidence: `app.run(host="0.0.0.0", port=5000, debug=True)` (app.py:88); `app.config["DEBUG"] = True` (app.py:8).
Impact: o debugger interativo do Werkzeug fica acessível pela rede, permitindo execução remota de código.
Recommendation: tornar debug, host e porta configuráveis por ambiente, com debug desligado por padrão . Requer decisão humana: o host padrão passa a ser local e a SECRET_KEY passa a ser obrigatória no ambiente, o que muda como a aplicação é iniciada (→ PB-02)

### [CRITICAL] Rotas administrativas sem autenticação (AP-03)
File: app.py:47-57 (+ app.py:59-78)
Description: `/admin/reset-db` apaga todas as tabelas e `/admin/query` executa qualquer SQL recebido em `sql`, ambos sem verificação de identidade ou permissão. O campo `tipo` de `usuarios` (database.py:32) nunca é consultado e `login` não emite token ou sessão (controllers.py:167-186).
Evidence: `@app.route("/admin/reset-db", methods=["POST"])` sem decorator (app.py:47); `cursor.execute(query)` com o SQL do corpo (app.py:69).
Impact: qualquer cliente anônimo apaga o banco, lê e altera dados arbitrários.
Recommendation: proteger as rotas com autenticação e autorização. Requer decisão humana: como autenticar (token, sessão) e se `/admin/query` deve continuar existindo (→ PB-03)

### [CRITICAL] Senhas em texto puro (AP-03)
File: models.py:126-128 (+ models.py:109-111, models.py:83, models.py:99, database.py:76-78)
Description: a senha é gravada, comparada no SQL do login e devolvida por `GET /usuarios` e `GET /usuarios/<id>` sem hash.
Evidence: `"... VALUES ('" + nome + "', '" + email + "', '" + senha + "', ..."` (models.py:127-128); `"senha": row["senha"]` (models.py:83, 99); seed `("Admin", "admin@loja.com", "admin123", "admin")` (database.py:76).
Impact: vazamento imediato de todas as credenciais e tomada de contas.
Recommendation: aplicar hash na gravação e na verificação, e não devolver a senha nas respostas. Requer decisão humana: usuários já gravados em texto puro precisam de migração ou reset (→ PB-03)

### [CRITICAL] God Module (AP-04)
File: models.py:1-314 (+ app.py:47-78, database.py:7-84)
Description: `models.py` concentra acesso a dados, regras de negócio (estoque, total, desconto) e montagem de respostas para os 4 domínios (produtos, usuários, pedidos, relatórios). `app.py` mistura rotas, configuração e SQL (rotas admin). `database.py` mistura conexão, DDL e seed.
Evidence: razões de mudança distintas no mesmo arquivo: nova rota, nova regra, novo campo e mudança de schema.
Impact: qualquer mudança afeta tudo e os testes em isolamento ficam inviáveis.
Recommendation: separar em models e controllers por domínio e deixar `app.py` só como composition root (→ PB-04)

### [HIGH] Lógica de negócio fora da camada correta (AP-05)
File: controllers.py:208-210 (+ controllers.py:247-250, models.py:256-262, models.py:144-146)
Description: o controller decide e dispara notificações (e-mail, SMS, push) e transições de status; o model calcula o desconto por faixas de faturamento e valida estoque dentro da função de acesso a dados.
Evidence: `print("ENVIANDO EMAIL: Pedido " + ...)` (controllers.py:208); `if faturamento > 10000: desconto = faturamento * 0.1` (models.py:257-258).
Impact: regras difíceis de testar e de reutilizar, sem HTTP e sem banco.
Recommendation: mover as regras para a camada adequada (→ PB-05)

### [HIGH] Estado global mutável (AP-06)
File: database.py:4-10 (+ database.py:86)
Description: `db_connection` é uma variável global iniciada com `None`, preenchida sob demanda, nunca fechada e compartilhada entre requisições com `check_same_thread=False`.
Evidence: `global db_connection` (database.py:8); `sqlite3.connect(db_path, check_same_thread=False)` (database.py:10).
Impact: condições de corrida e testes dependentes de ordem.
Recommendation: criar a conexão por requisição ou por fábrica, sem global (→ PB-06)

### [HIGH] Acoplamento forte e quebra de camadas (AP-07)
File: controllers.py:3 (+ controllers.py:266-274, app.py:4, app.py:49-55, app.py:66-75)
Description: `controllers.py` e `app.py` importam `get_db` e executam SQL diretamente, contornando o model. Nada é injetado.
Evidence: `from database import get_db` (controllers.py:3, app.py:4); `cursor.execute("SELECT COUNT(*) FROM produtos")` em `health_check` (controllers.py:269-270).
Impact: impossível trocar o banco ou usar mock sem editar controllers e rotas.
Recommendation: acessar dados apenas pelos models e injetar a dependência (→ PB-07)

### [HIGH] Criação de pedido sem transação/rollback (AP-08)
File: models.py:133-169 (+ app.py:51-55)
Description: `criar_pedido` faz `INSERT` em `pedidos`, vários `INSERT` em `itens_pedido` e `UPDATE` de estoque com um único `commit` no fim e sem `try/except` com `rollback`. A checagem de estoque (models.py:144) é separada da escrita (models.py:163-166). `reset_database` apaga 4 tabelas com um commit e sem rollback.
Evidence: `db.commit()` único em models.py:168; nenhum `rollback()` no projeto.
Impact: falha no meio deixa pedido sem itens ou estoque baixado sem pedido; dois pedidos simultâneos podem vender estoque que não existe.
Recommendation: executar a operação em uma transação com rollback em caso de falha (→ PB-08)

### [HIGH] Cancelamento não devolve estoque (AP-08)
File: controllers.py:249-250 (+ models.py:275-283)
Description: ao cancelar o pedido, o controller só imprime "Devolver estoque"; o model apenas atualiza o status.
Evidence: `print("NOTIFICAÇÃO: Pedido " + ... + " cancelado. Devolver estoque.")` (controllers.py:250).
Impact: estoque diverge do que foi vendido a cada cancelamento.
Recommendation: executar a devolução de estoque junto com o cancelamento. Requer decisão humana: hoje a devolução não acontece, então implementá-la muda o comportamento (→ PB-08)

### [MEDIUM] Queries N+1 (AP-09)
File: models.py:187-193 (+ models.py:219-225)
Description: `get_pedidos_usuario` e `get_todos_pedidos` executam uma query de itens por pedido e, dentro dela, uma de produto por item.
Evidence: `cursor2.execute(...)` e `cursor3.execute(...)` dentro de `for` (models.py:187-193, 219-225).
Impact: o número de queries cresce com pedidos x itens.
Recommendation: carregar itens e nomes de produto com JOIN em uma query (→ PB-09)

### [MEDIUM] Tratamento genérico de erros (AP-10)
File: controllers.py:10-12 (+ controllers.py:21, 60, 95, 108, 125, 133, 143, 164, 185, 218, 226, 234, 254, 261, 291, app.py:77)
Description: todos os handlers repetem `except Exception as e` e devolvem `str(e)` ao cliente com 500, sem handler global.
Evidence: `return jsonify({"erro": str(e)}), 500` (controllers.py:12).
Impact: vazamento de detalhes internos e repetição em cada handler.
Recommendation: criar um tratador global de erros. Requer decisão humana: o formato de erro atual faz parte do contrato da API (→ PB-10)

### [MEDIUM] Validação de entrada ausente ou inconsistente (AP-10)
File: controllers.py:239-240 (+ controllers.py:169-171, controllers.py:43-46, controllers.py:87-90, controllers.py:198-201, app.py:61-62)
Description: `atualizar_status_pedido`, `login` e `/admin/query` usam `request.get_json()` sem checar `None`; `criar_produto` e `atualizar_produto` comparam `preco < 0` sem checar tipo; `atualizar_produto` não valida tamanho do nome (compare com controllers.py:47-50) nem categoria; `criar_pedido` não valida `quantidade` nem a existência do usuário; não há unicidade de e-mail.
Evidence: `novo_status = dados.get("status", "")` com `dados` possivelmente `None` (controllers.py:240).
Impact: respostas 500 evitáveis e dados inconsistentes.
Recommendation: validar o corpo, os tipos e a existência de forma centralizada . Requer decisão humana: validar tamanho do nome e categoria na atualização de produto, rejeitar quantidade menor ou igual a zero e usuário inexistente no pedido, e exigir e-mail único no cadastro rejeitam entradas que hoje são aceitas (→ PB-10)

### [MEDIUM] Código duplicado (AP-11)
File: models.py:12-21 (+ models.py:31-40, models.py:304-313, models.py:79-86, models.py:95-102, models.py:178-199, models.py:211-231, controllers.py:28-46, controllers.py:72-90)
Description: o dicionário de produto é montado de forma idêntica em 3 funções, o de usuário em 2, a montagem de pedido com itens em 2, e o bloco de validação é repetido entre criar e atualizar produto.
Evidence: mesmas chaves (`id`, `nome`, `descricao`, `preco`, `estoque`, `categoria`, `ativo`, `criado_em`) nos trechos citados.
Impact: mudança de schema precisa ser repetida em vários lugares, com risco de divergência.
Recommendation: centralizar serialização e validação (→ PB-11)

### [LOW] Magic numbers e strings soltas (AP-13)
File: models.py:257-262 (+ controllers.py:52, controllers.py:242, models.py:150, models.py:247-253)
Description: faixas de faturamento e percentuais de desconto, lista de categorias, lista de status e o literal `"pendente"` aparecem sem constante (status em controllers.py:242 e models.py:150, 247).
Evidence: `elif faturamento > 5000: desconto = faturamento * 0.05` (models.py:259-260).
Impact: regras difíceis de localizar e alterar, com risco de divergência.
Recommendation: extrair para constantes nomeadas (→ PB-13)

### [LOW] Logging por print e código morto (AP-14)
File: controllers.py:8 (+ controllers.py:11, 57, 106, 161, 179, 182, 208-210, 219, 248, 250, app.py:56, app.py:83-86, models.py:2, database.py:2, app.py:7)
Description: `print` como log e como "envio" de notificações; `import sqlite3` em `models.py:2` e `import os` em `database.py:2` nunca usados; `SECRET_KEY` definida e nunca lida (sem sessão).
Evidence: `sqlite3` só aparece na linha do import em `models.py`; `os` só aparece na linha do import em `database.py`.
Impact: diagnóstico fraco em produção e ruído na leitura.
Recommendation: usar `logging` com níveis e remover imports sem uso (→ PB-14)

## Not Verified
- AP-12 (APIs deprecated da linguagem): versão do Python não declarada (sem `.python-version`, `Dockerfile` ou CI) | Reason: a regra do catálogo proíbe inferir a versão; nenhuma API foi classificada como deprecated por esse motivo. Flask 3.1.1 e flask-cors 5.0.1 estão declarados e nenhuma API deprecated dessas versões foi encontrada.
- AP-01 (exploração real): as PoCs de injeção não foram executadas | Reason: Fases 1 e 2 são somente leitura; a confirmação por execução fica para o baseline da Fase 3.
- AP-09 (contagem de queries): não medida com log de queries | Reason: exigiria subir a aplicação, o que só ocorre na Fase 3.


### Total: 17 findings


# PHASE 3: REFACTORING COMPLETE

## New Project Structure
```
code-smells-project/
├── app.py                         (entry point: python app.py)
├── .env.example, .gitignore, README.md, requirements.txt
└── src/
    ├── app.py                     (composition root: create_app)
    ├── config/                    settings.py (único leitor do ambiente), logging_config.py
    ├── constants/                 aplicacao, pedido, produto, relatorio, usuario
    ├── exceptions/                errors.py (erros de domínio)
    ├── middlewares/               error_middleware.py (handler global), auth_middleware.py
    ├── models/                    database.py, schema.py, admin/health/pedido/produto/relatorio/usuario_model.py
    ├── services/                  admin, auth, health, notificacao, pedido, produto, relatorio, usuario
    ├── validators/                common, pedido_validator, produto_validator, usuario_validator
    ├── controllers/               admin, health, pedido, produto, relatorio, usuario
    ├── views/                     health_view, pedido_view, produto_view, usuario_view
    └── routes/                    admin, health, pedido, produto, usuario (blueprints)
```
Removidos: controllers.py, models.py, database.py (substituídos por src/).

## Validation
- [x] ✓ Application boots without errors (python app.py com -W error::DeprecationWarning; log sem exceções)
- [x] ✓ 59/59 baseline calls respond (49 OK idênticas ao baseline, 10 CHANGED intencionais, 0 FAIL)
- [x] ✓ Status codes match baseline (54/59; os 5 que diferem são 500 -> 400, listados em Intentional changes)
- [x] ✓ 17/17 findings addressed (re-detected with the catalog signals); no finding 14 (AP-10, validação) a atualização de produto foi mantida sem validação extra por decisão do usuário
- [x] ✓ SQL Injection PoC no longer exploitable (busca OR: 10 -> 0 registros; busca UNION com senhas: 4 -> 0; filtro de categoria: 10 -> 0; bypass de login: 200 -> 401; nome com apóstrofo: 500 -> 201)
- [x] ✓ 0 DeprecationWarnings (nenhum no baseline)
- [x] ✓ Regressão após as decisões de validação: original x nova com a mesma sequência (45 chamadas, cliente de teste do Flask): 42 idênticas e 3 diferenças, todas aprovadas (sem `senha` em GET /usuarios/<id>, e-mail duplicado 409, estoque devolvido no cancelamento)
- [ ] ✗ 1 anti-pattern remaining: AP-10 (PUT /produtos/<id> continua sem validar tamanho do nome e categoria, mantido por decisão do usuário)

### Intentional changes
- GET /health deixa de devolver secret_key, db_path e debug (AP-02; finding 2).
- GET /usuarios e GET /usuarios/<id> deixam de devolver o campo senha (AP-03; finding 5). Senhas passam a ter hash (scrypt) e as já gravadas em texto puro são migradas no boot (decisão: token assinado + migração).
- POST /login passa a devolver também o campo token (decisão: token assinado emitido pelo /login).
- POST /admin/reset-db passa a exigir token de admin (401 sem token, 403 sem perfil) e POST /admin/query foi removida (404) (decisão: remover /admin/query e proteger /admin/reset-db).
- PUT /pedidos/<id>/status para "cancelado" passa a devolver o estoque dos itens, uma única vez (idempotente) (decisão: executar a devolução).
- Erros inesperados passam a devolver {"erro": "Erro interno do servidor"} sem o texto da exceção; o envelope {"erro": ...} foi mantido (decisão: manter o envelope).
- Corpo ausente/inválido e tipos inválidos passam de 500 para 400 com a mensagem "Dados inválidos" (POST /produtos, PUT /produtos/<id>, POST /pedidos, PUT /pedidos/<id>/status); preco_min/preco_max não numéricos em /produtos/busca passam de 500 para 400 (AP-10; finding 14).
- Pedido com o mesmo produto em duas linhas que somam mais que o estoque passa a ser recusado (400, com rollback); antes o estoque ficava negativo (AP-08).
- POST /pedidos passa a recusar quantidade menor ou igual a zero (400) e usuario_id inexistente (400, "Usuario não encontrado"); antes eram aceitos e quantidade negativa aumentava o estoque (AP-10; decisão: rejeitar os dois).
- POST /usuarios passa a recusar e-mail já cadastrado (409, "Email já cadastrado"); antes duplicatas eram aceitas. Usuários já gravados não são alterados (AP-10; decisão: exigir e-mail único).
- Mantido por decisão do usuário: PUT /produtos/<id> continua aceitando nome fora do tamanho e categoria inválida (AP-10; decisão: manter como está).
- Execução: HOST padrão 127.0.0.1 (era 0.0.0.0), debug desligado por padrão e SECRET_KEY obrigatória no ambiente (ou APP_DEBUG=1 em desenvolvimento). README e .env.example atualizados (AP-02; findings 2 e 3).

### Not verified
- POST /admin/reset-db e POST /admin/query não foram executados contra o servidor do baseline (destrutivos, sem autorização explícita); o comportamento novo (401, 403, 200 com admin) foi verificado com o cliente de teste do Flask contra bancos descartáveis, sem comparação com o original.
- Caminho de falha do /health (erro de banco): não exercitado.
- Expiração do token por tempo (TOKEN_MAX_AGE): só token inválido foi testado.
- Carga/concorrência (PB-06 passo 3): não executada.
- A tabela "Endpoint comparison" abaixo é anterior às decisões de validação de pedido e de e-mail único; essas duas mudanças foram revalidadas na comparação original x nova de 45 chamadas (item de Validation), sem repetir a tabela de 59 chamadas.
- Unicidade de e-mail é verificada no cadastro, sem restrição UNIQUE no banco (o banco atual pode ter duplicatas); duas requisições simultâneas com o mesmo e-mail não foram testadas.
- AP-12 (APIs deprecated da linguagem): versão do Python não declarada (ver Not Verified da auditoria).

### Endpoint comparison
| Method | Path | Baseline | After | Result |
|---|---|:---:|:---:|:---:|
| GET | / | 200 | 200 | OK |
| GET | /health | 200 | 200 | CHANGED |
| GET | /produtos | 200 | 200 | OK |
| GET | /produtos/1 | 200 | 200 | OK |
| GET | /produtos/999999 | 404 | 404 | OK |
| GET | /produtos/busca?q=Mouse | 200 | 200 | OK |
| GET | /produtos/busca?categoria=moveis | 200 | 200 | OK |
| GET | /produtos/busca?preco_min=100&preco_max=300 | 200 | 200 | OK |
| GET | /produtos/busca?q=zzzznaoexiste | 200 | 200 | OK |
| GET | /produtos/busca?preco_min=abc | 500 | 400 | CHANGED |
| POST | /produtos | 400 | 400 | OK |
| POST | /produtos | 500 | 400 | CHANGED |
| POST | /produtos | 400 | 400 | OK |
| POST | /produtos | 400 | 400 | OK |
| POST | /produtos | 400 | 400 | OK |
| POST | /produtos | 400 | 400 | OK |
| POST | /produtos | 400 | 400 | OK |
| POST | /produtos | 400 | 400 | OK |
| POST | /produtos | 400 | 400 | OK |
| POST | /produtos | 201 | 201 | OK |
| GET | /produtos/11 | 200 | 200 | OK |
| PUT | /produtos/11 | 200 | 200 | OK |
| PUT | /produtos/999999 | 404 | 404 | OK |
| PUT | /produtos/11 | 400 | 400 | OK |
| PUT | /produtos/11 | 500 | 400 | CHANGED |
| DELETE | /produtos/11 | 200 | 200 | OK |
| DELETE | /produtos/999999 | 404 | 404 | OK |
| GET | /produtos/11 | 404 | 404 | OK |
| GET | /usuarios | 200 | 200 | CHANGED |
| GET | /usuarios/1 | 200 | 200 | CHANGED |
| GET | /usuarios/999999 | 404 | 404 | OK |
| POST | /usuarios | 201 | 201 | OK |
| POST | /usuarios | 400 | 400 | OK |
| POST | /usuarios | 400 | 400 | OK |
| POST | /login | 200 | 200 | OK |
| POST | /login | 200 | 200 | OK |
| POST | /login | 401 | 401 | OK |
| POST | /login | 400 | 400 | OK |
| GET | /pedidos | 200 | 200 | OK |
| POST | /pedidos | 201 | 201 | OK |
| POST | /pedidos | 400 | 400 | OK |
| POST | /pedidos | 400 | 400 | OK |
| POST | /pedidos | 500 | 400 | CHANGED |
| POST | /pedidos | 400 | 400 | OK |
| POST | /pedidos | 400 | 400 | OK |
| POST | /pedidos | 201 | 201 | OK |
| GET | /pedidos | 200 | 200 | OK |
| GET | /pedidos/usuario/2 | 200 | 200 | OK |
| GET | /pedidos/usuario/999999 | 200 | 200 | OK |
| GET | /produtos/1 | 200 | 200 | OK |
| PUT | /pedidos/1/status | 200 | 200 | OK |
| PUT | /pedidos/1/status | 400 | 400 | OK |
| PUT | /pedidos/1/status | 500 | 400 | CHANGED |
| PUT | /pedidos/1/status | 200 | 200 | OK |
| GET | /produtos/1 | 200 | 200 | CHANGED |
| PUT | /pedidos/1/status | 200 | 200 | OK |
| GET | /produtos/1 | 200 | 200 | CHANGED |
| GET | /relatorios/vendas | 200 | 200 | OK |
| GET | /pedidos | 200 | 200 | OK |
| POST | /admin/reset-db | SKIPPED | 401 | SKIPPED |
| POST | /admin/query | SKIPPED | 404 | SKIPPED |

## Checklist de Validação (Fase 3)
- [x] Estrutura de diretórios segue padrão MVC — `src/` com config/, models/, routes/, controllers/, views/, middlewares/ (mais services/, validators/, constants/, exceptions/); árvore real listada em "New Project Structure".
- [x] Configuração extraída para módulo de config (sem hardcoded) — buscas AP-02 e AP-13 vazias fora de `src/config/` e `src/constants/` (SECRET_KEY, debug, host, porta e caminho do banco só em `src/config/settings.py`).
- [x] Models criados para abstrair dados — `sqlite3` só em `src/models/`; buscas AP-01, AP-05 e AP-07 vazias em controllers e rotas (único acerto do AP-01 é `estoque + ?` dentro de um UPDATE parametrizado: falso positivo do grep).
- [x] Views/Routes separadas para visualização ou roteamento — `src/routes/*_routes.py` (5 blueprints) e `src/views/*_view.py` (serializers).
- [x] Controllers concentram o fluxo da aplicação — `src/controllers/` só lê a entrada, valida, chama o Service e responde; busca por `print`, desconto, SQL e `str(e)` vazia.
- [x] Error handling centralizado — `src/middlewares/error_middleware.py` registra o handler de `AppError` e o de `Exception`; busca do AP-10 (`str(e)`, `except Exception`) vazia em `src/controllers/`.
- [x] Entry point claro — `app.py` (cria a config, chama `create_app` e sobe o servidor) e `src/app.py` (composition root).
- [x] Aplicação inicia sem erros — `python app.py` com `APP_DEBUG=1 -W error::DeprecationWarning`, log de boot sem exceções nem avisos; pyflakes sem avisos.
- [x] Endpoints originais respondem corretamente — `scripts/compare.py` baseline x after: 59 chamadas, 49 OK, 10 CHANGED (todas listadas em Intentional changes), 0 FAIL; /admin/reset-db e /admin/query SKIPPED (ver Not verified).
