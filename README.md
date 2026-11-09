# Refatoração Arquitetural Automatizada: skill `refactor-arch`

Skill do Claude Code que **analisa, audita e refatora para MVC** qualquer projeto backend, em 3 fases (análise, auditoria com pausa para confirmação, refatoração validada). Foi construída em `code-smells-project/` e copiada para os outros dois projetos para provar que funciona em stacks diferentes.

| Projeto | Stack | Skill | Relatório | Status |
|---|---|---|---|---|
| `code-smells-project/` | Python / Flask | `.claude/skills/refactor-arch/` | [audit-project-1.md](reports/audit-project-1.md) | Concluído |
| `ecommerce-api-legacy/` | Node.js / Express | cópia idêntica | [audit-project-2.md](reports/audit-project-2.md) | Concluído |
| `task-manager-api/` | Python / Flask (já em camadas) | cópia idêntica | [audit-project-3.md](reports/audit-project-3.md) | Concluído |

O enunciado original do desafio está no histórico do repositório (primeiro commit).

## Índice

1. [Análise Manual](#análise-manual)
2. [Construção da Skill](#construção-da-skill)
3. [Resultados](#resultados)
4. [Como Executar](#como-executar)

---

## Análise Manual

Com o objetivo de entender os problemas atuais dos projetos e identificar pontos comuns que sirvam como direcionamento para a skill, foi realizada uma análise de code review manual, buscando pontos de congruência entre os projetos para usá-los como habilidades amplas e até como guidelines da skill a ser criada.

A análise não foi minuciosa: foi focada nos pontos mais críticos. Utilizei a LLM como juiz (LLM as judge) para confirmar e identificar os apontamentos que encontrei, a fim de ter um segundo viés de confirmação. Todos os apontamentos podem ser encontrados com mais detalhes na pasta de relatórios ([reports](reports/)).

### code-smells-project (Python/Flask)

| # | Severidade | Onde | Problema e por que é relevante |
|---|---|---|---|
| 1 | CRITICAL | `models.py` | Problema de SQL Injection em várias funções dentro do arquivo. |
| 2 | CRITICAL | `app.py:47`, `app.py:59` | Rotas administrativas expostas, sem a realização ou uso de autenticação. |
| 3 | HIGH | `controllers.py` | Controller acessando diretamente a camada de dados e realizando queries. |
| 4 | MEDIUM | `models.py:171-233` | Queries N+1 na montagem de pedidos. |
| 5 | MEDIUM | `controllers.py` | Erros genéricos e sem derivação de uma exception específica. |
| 6 | LOW | `models.py:256-262` | Magic numbers para definição do desconto a ser aplicado, sem definição clara de regra de negócio. |
| 7 | LOW | controllers.py` | Uso incorreto de print como log na aplicação. |

### ecommerce-api-legacy (Node.js/Express)

| # | Severidade | Onde | Problema e por que é relevante |
|---|---|---|---|
| 1 | CRITICAL | `utils.js:4` | Secrets totalmente expostas. |
| 2 | CRITICAL | `utils.js:17` | Função de encriptação de senha totalmente caseira e sem seguir boas práticas de segurança. |
| 3 | HIGH | `AppManager.js` | Objeto Deus (God Class) com alta violação de SRP do SOLID (princípio de responsabilidade única). |
| 4 | MEDIUM | `AppManager.js:83-128` | Execução de Query N+1 dentro do relatório financeiro. |
| 5 | MEDIUM | `AppManager.js:29-33` | Possibilidade de registros órfãos na exclusão, gerando perda de integridade referencial. |
| 6 | LOW | `AppManager.js` | Arquivo contém vários problemas de clean code em nome de variáveis (`u`, `e`, `p`, `cid`, `cc`), prejudicando legibilidade e manutenção do código. |
| 7 | LOW | `utils.js:10` | Código exportado e importado sem utilização efetiva no projeto. |

### task-manager-api (Python/Flask)

| # | Severidade | Onde | Problema e por que é relevante |
|---|---|---|---|
| 1 | CRITICAL | `app.py:13` | Secret exposta e hardcoded na inicialização da aplicação. |
| 2 | CRITICAL | `user.py:21`, `user.py:29-32` | Uso de MD5 sem salt e exposição do hash diretamente em respostas da API. |
| 3 | MEDIUM | `helpers.py:57-108` | Falta de padronização sobre responsabilidade de validação de dados de entrada e funções nunca utilizadas (dead code). |
| 4 | MEDIUM | `app.py:15` | Exposição de CORS totalmente aberto da aplicação, gerando riscos de exposição das rotas. |
| 5 | LOW | `helpers.py:3-7` | Exceções sendo suprimidas por causa do `except:`. |
| 6 | LOW | `app.py:7` | Imports não utilizados gerando code smells. |

---

## Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                          # as 3 fases, as regras e os checklists de saída
├── references/
│   ├── project-analyzer.md           # Fase 1: heurísticas de linguagem, framework, banco e arquitetura
│   ├── anti-patterns-catalog.md      # Fase 2: AP-01..AP-14 com sinais, como confirmar e severidade
│   ├── report-template.md            # Fases 2 e 3: formato do relatório e do bloco da Fase 3
│   ├── mvc-architecture.md           # Fase 3: camadas MVC alvo, dependências e convenções
│   ├── refactoring-playbook.md       # Fase 3: PB-01..PB-14 com exemplos antes/depois
│   └── validation-guide.md           # Fase 3: baseline, validação incremental e verificação final
└── scripts/compare.py                # compara baseline x after (status, corpo, campos voláteis)
```

### Decisões de design

- **O `SKILL.md` é o prompt; as referências são o conhecimento.** O `SKILL.md` só diz o que fazer em cada fase e em que ordem. Cada referência é lida no momento em que a fase correspondente começa, não de uma vez.
- **Fases 1 e 2 são somente leitura.** A única escrita permitida é o relatório. A Fase 2 termina com a pergunta `Proceed with refactoring (Phase 3)? [y/n]` e qualquer resposta diferente de sim encerra a execução.
- **Decisões humanas antes de editar.** Antes da primeira edição a skill levanta todas as decisões (as marcadas no relatório, as dos playbooks e qualquer mudança de comportamento) e pergunta uma a uma. **A resposta do usuário é vinculante:** se não puder ser cumprida como foi dita, a skill para e pergunta de novo.
- **Checklist como portão de saída.** Cada fase termina com um checklist em que cada item só é marcado com evidência (comando, contagem ou `arquivo:linha`). Item não verificado fica `[ ]`.
- **Prova de que nada quebrou.** A Fase 3 grava um baseline da aplicação original antes de editar (incluindo caminhos de erro e a PoC de cada vulnerabilidade), valida a cada bloco pequeno e compara o resultado final com `compare.py`. Cada `✓` do relatório corresponde a uma verificação executada.
- **Relatório auditável.** Cada finding tem `arquivo:linha` conferido com comando, evidência, impacto e recomendação apontando o playbook (`AP-xx` corrige com `PB-xx`). A contagem é determinística: o catálogo define quando um mesmo AP gera mais de um achado (AP-02, AP-03, AP-10 e AP-13).

### Anti-patterns no catálogo (14) e por quê

Cobrem a escala de severidade da atividade e os problemas mais comuns de MVC/SOLID, de segurança e de integridade de dados:

| AP | Anti-pattern | Severidade |
|---|---|---|
| AP-01 | SQL Injection / query por concatenação | CRITICAL |
| AP-02 | Credenciais e segredos hardcoded ou expostos | CRITICAL |
| AP-03 | Ausência de autenticação/autorização e credenciais sem proteção | CRITICAL |
| AP-04 | God Class / God Module | CRITICAL |
| AP-05 | Lógica de negócio fora da camada correta | HIGH |
| AP-06 | Estado global mutável | HIGH |
| AP-07 | Acoplamento forte e quebra de camadas (sem DI) | HIGH |
| AP-08 | Transações ausentes ou sem rollback | HIGH |
| AP-09 | Queries N+1 | MEDIUM |
| AP-10 | Validação ausente e tratamento genérico de erros | MEDIUM |
| AP-11 | Código duplicado | MEDIUM |
| AP-12 | Uso de APIs deprecated ou obsoletas | MEDIUM (ajustável) |
| AP-13 | Magic numbers, strings soltas e nomenclatura ruim | LOW |
| AP-14 | Logging por print e código morto | LOW |

O AP-12 só considera a versão **declarada** nos arquivos do projeto; sem versão declarada o item vai para `Not Verified`, nunca vira finding por suposição. O AP-08 inclui o efeito de negócio que só é descrito em log (por exemplo, "devolver estoque").

### Como garantimos que é agnóstica de tecnologia

- Todo sinal de detecção do catálogo e todo playbook trazem exemplos para Python/Flask e Node/Express (e Java e PHP de forma curta). Nenhuma regra assume uma stack.
- Comandos de instalação, start e porta são **derivados dos arquivos do próprio projeto** (README, scripts, manifestos), nunca assumidos.
- A pasta da camada de dados é `models/`, a menos que o projeto já tenha outra convenção; os nomes de arquivos seguem o idioma do domínio.
- Há um fallback manual para a comparação com o baseline quando não há Python (projetos Node).
- A Fase 3 adapta-se ao contexto: em um monólito cria as camadas; em um projeto já organizado preserva o que está adequado e corrige só o que o relatório apontou.

### Desafios encontrados e como resolvemos

- **Decisões que apareciam tarde.** Na primeira execução, itens que dependiam de decisão só surgiram durante a implementação. A skill passou a levantar todas as decisões antes de editar e a tratar a resposta do usuário como vinculante.
- **Execução fora do combinado.** Em um caso, a skill descreveu uma variável de configuração na pergunta e entregou outra coisa. Virou regra: pare e pergunte de novo.
- **Evidência imprecisa.** Uma linha citada estava deslocada em um número. Agora cada `arquivo:linha` é conferido com `sed -n`/`grep -n`.
- **Falso positivo de limpeza.** Configuração definida e nunca lida passou pela detecção. O AP-14 agora exige achar o ponto de leitura de cada chave.
- **Dependência deprecated sem correção.** No projeto Node, atualizar o pacote direto não removeu uma dependência transitiva deprecated. A skill passou a verificar se existe versão que resolve antes de recomendar "atualizar".
- **PoC que não explora.** Um payload genérico de SQL Injection não funcionava dentro de um `LIKE ... (`. O guia exige que a PoC prove a exploração já no baseline.
- **Windows.** Frameworks com auto-reload deixam processo filho segurando a porta; o guia traz o encerramento seguro por caminho do executável.
- **Sobras no projeto.** Execuções deixavam `__pycache__` e bancos locais. A Fase 3 agora limpa o projeto e garante um `.gitignore`.
- **Variação entre execuções.** Uma execução limpa achou 15 findings contra 17 da primeira, por granularidade (agrupou AP-02 e AP-10). O catálogo agora define a granularidade.

---

## Resultados

### Resumo das auditorias (Fase 2)

| Projeto | Arquivos / linhas | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| code-smells-project | 4 / ~780 | 6 | 5 | 4 | 2 | **17** |
| ecommerce-api-legacy | 3 / ~180 | 4 | 5 | 4 | 2 | **15** |
| task-manager-api | 15 / ~1.160 | 5 | 2 | 4 | 3 | **14** |

Relatórios completos: [audit-project-1.md](reports/audit-project-1.md), [audit-project-2.md](reports/audit-project-2.md), [audit-project-3.md](reports/audit-project-3.md). Cada um traz a auditoria, o bloco da Fase 3, a comparação endpoint a endpoint e o checklist.

Critérios de aceite da atividade:

| Critério | Projeto 1 | Projeto 2 | Projeto 3 |
|---|:---:|:---:|:---:|
| Fase 1 detecta a stack | OK | OK | OK |
| Fase 2 encontra no mínimo 5 findings | OK (17) | OK (15) | OK (14) |
| Fase 2 inclui CRITICAL ou HIGH | OK | OK | OK |
| Aplicação funciona após a refatoração | OK | OK | OK |

### Cobertura da análise manual pela skill (Fase 2)

A atividade pede que a Fase 2 encontre pelo menos 5 dos problemas da análise manual. Comparando cada item manual com os findings dos relatórios:

| Projeto | Apontamentos manuais | Encontrados pela skill | Não encontrado |
|---|:---:|:---:|---|
| code-smells-project | 7 | **7** | |
| ecommerce-api-legacy | 7 | **6** | Nomes de variáveis ruins (`u`, `e`, `p`, `cid`, `cc`, em `AppManager.js:29-33`): na execução, o catálogo ainda não cobria nomenclatura; o AP-13 passou a cobri-la depois |
| task-manager-api | 6 | **5** | CORS totalmente aberto (`app.py:15`): na execução o catálogo não tinha sinal para isso; o AP-02 passou a cobri-lo depois |

Na severidade houve divergências esperadas: a análise manual classificou o `models.py` multi-domínio como MEDIUM (SRP) e os erros genéricos como LOW, enquanto a skill os classifica como CRITICAL (God Module) e MEDIUM (AP-10), seguindo a escala da atividade.

### Antes e depois da estrutura

**code-smells-project** (4 arquivos e ~780 linhas, para 46 módulos e ~1.250 linhas, em 10 pastas):

```
ANTES                         DEPOIS
├── app.py                    ├── app.py                 (entry point fino)
├── controllers.py            └── src/
├── models.py                     ├── app.py             (composition root)
├── database.py                   ├── config/            (única leitura do ambiente)
└── requirements.txt              ├── constants/  exceptions/  validators/
                                  ├── models/            (acesso a dados parametrizado, schema)
                                  ├── services/          (regras de negócio e transações)
                                  ├── controllers/  views/  routes/
                                  └── middlewares/       (handler global de erros, autenticação)
```

**ecommerce-api-legacy** (3 arquivos e ~180 linhas, para 30 arquivos e ~570 linhas, em 10 pastas):

```
ANTES                         DEPOIS
└── src/                      └── src/
    ├── app.js                    ├── app.js             (entry point e composition root)
    ├── AppManager.js             ├── config/  constants/  errors/  validators/
    └── utils.js                  ├── models/            (conexão, transação, schema e 1 model por entidade)
                                  ├── services/          (checkout, pagamento, relatório, senha)
                                  ├── controllers/  views/  routes/
                                  └── middlewares/       (autenticação, handler global de erros)
```

**task-manager-api** (15 arquivos e ~1.160 linhas, para 45 módulos e ~1.490 linhas, em 10 pastas): projeto já em camadas, em que a skill preservou o que existia e acrescentou o que faltava.

```
ANTES                             DEPOIS
├── app.py                        ├── app.py                 (composition root: create_app)
├── database.py                   ├── database.py  seed.py
├── seed.py                       ├── config/  constants/  exceptions/  validators/   (novos)
├── models/ (category, task,      ├── models/                (entidades ORM + *_model.py de acesso a dados
│   user)                         │                           + transaction.py)
├── routes/ (report, task,        ├── routes/                (só registram rotas; categoria e sistema separados)
│   user: rota + regra + dados)   ├── controllers/  views/   (novos: HTTP e serialização)
├── services/                     ├── services/              (regras de negócio e transações)
│   └── notification_service      └── middlewares/           (handler global de erros, autenticação)
└── utils/helpers                 (removidos: utils/ e NotificationService, ambos sem uso)
```

### Checklist de validação preenchido

As evidências de cada item estão nos relatórios (seção "Checklist de Validação (Fase 3)").

#### Projeto 1: code-smells-project

**Fase 1:** [x] linguagem · [x] framework · [x] domínio · [x] número de arquivos (4)
**Fase 2:** [x] segue o template · [x] arquivo e linhas exatos · [x] ordenado por severidade · [x] mínimo de 5 (17) · [x] APIs deprecated avaliadas (nenhuma, versão do Python não declarada) · [x] pausa e confirmação
**Fase 3:** [x] estrutura MVC · [x] configuração extraída · [x] models · [x] views/routes · [x] controllers · [x] error handling centralizado · [x] entry point claro · [x] boot sem erros · [x] endpoints originais respondem (59 chamadas: 49 idênticas, 10 mudanças intencionais aprovadas, 0 regressões)

#### Projeto 2: ecommerce-api-legacy

**Fase 1:** [x] linguagem · [x] framework · [x] domínio (LMS com checkout; 5 tabelas) · [x] número de arquivos (3)
**Fase 2:** [x] segue o template · [x] arquivo e linhas exatos · [x] ordenado por severidade · [x] mínimo de 5 (15) · [x] APIs deprecated avaliadas (9 dependências transitivas deprecated no lock) · [x] pausa e confirmação
**Fase 3:** [x] estrutura MVC · [x] configuração extraída · [x] models · [x] views/routes · [x] controllers · [x] error handling centralizado · [x] entry point claro · [x] boot sem erros · [x] endpoints originais respondem (15 endpoints, 0 diferenças)

#### Projeto 3: task-manager-api

**Fase 1:** [x] linguagem · [x] framework · [x] domínio (Task Manager; 3 tabelas, 22 endpoints) · [x] número de arquivos (15)
**Fase 2:** [x] segue o template · [x] arquivo e linhas exatos · [x] ordenado por severidade · [x] mínimo de 5 (14) · [x] APIs deprecated avaliadas (`datetime.utcnow()` e `Model.query.get()`, ver relatório) · [x] pausa e confirmação
**Fase 3:** [x] estrutura MVC · [x] configuração extraída · [x] models · [x] views/routes · [x] controllers · [x] error handling centralizado · [x] entry point claro · [x] boot sem erros · [x] endpoints originais respondem (111 chamadas: 87 idênticas, 24 mudanças intencionais aprovadas, 0 regressões)

### Itens pendentes por decisão do autor

Registrados nos relatórios, com o motivo:

- **Projeto 1:** `PUT /produtos/<id>` continua sem validar tamanho do nome e categoria (AP-10), mantido por decisão do usuário.
- **Projeto 2:** `DELETE /api/users/:id` continua deixando matrículas e pagamentos órfãos (AP-08), por decisão do usuário. O `prebuild-install` continua deprecated no lock (AP-12) porque o `sqlite3` 6.0.1, versão mais nova existente, ainda depende dele.
- **Projeto 3:** só as rotas destrutivas exigem autenticação (AP-03), por decisão do usuário; as demais (`GET /users`, `POST /users`, `POST /tasks`) seguem abertas. O `datetime.utcnow()` permanece em 12 linhas (AP-12): o projeto não declara a versão do Python e trocar por datas com fuso mudaria o formato dos timestamps. O relatório recomenda `datetime.now(timezone.utc)`.

### Logs das aplicações rodando após a refatoração

Logs reais, capturados de um checkout limpo do commit `703eba7` (Python 3.15.2, Node v26.13.0, Windows). Cada aplicação foi iniciada pelo comando do seu README, em uma porta de teste, e as chamadas mostram status e um trecho do corpo. A comparação completa com o baseline (todos os endpoints) está nos relatórios.

**code-smells-project** (`SECRET_KEY=... python app.py`)

```
2026-11-09 15:37:01,249 INFO __main__: Servidor iniciado em http://127.0.0.1:5201
 * Serving Flask app 'src.app'
 * Debug mode: off

GET    /health                                   -> 200  {"ambiente": "producao", "counts": {"pedidos": 0, "produtos": 10, "usuarios": 3}, "database": "connected", ...
GET    /produtos                                 -> 200  10 itens
GET    /usuarios                                 -> 200  3 itens                      (sem o campo senha)
POST   /login                                    -> 200  {"dados": {"email": "admin@loja.com", "id": 1, "nome": "Admin", "tipo": "admin"}, "mensagem": "Login OK", ...
POST   /login (SQL Injection: ' OR '1'='1' --)   -> 401  {"erro": "Email ou senha inválidos", "sucesso": false}
GET    /produtos/busca?q=zzzz') OR 1=1--         -> 200  0 itens                      (antes: todos os produtos)
POST   /pedidos                                  -> 201  {"dados": {"pedido_id": 1, "total": 11999.98}, "mensagem": "Pedido criado com sucesso", ...
POST   /admin/reset-db (sem token)               -> 401  {"erro": "Token ausente"}
POST   /admin/query                              -> 404  (rota removida)
```

**ecommerce-api-legacy** (`ADMIN_TOKEN=... npm start`)

```
2026-11-09T18:37:05.849Z INFO Frankenstein LMS rodando na porta 3201...
2026-11-09T18:37:28.018Z INFO Checkout concluído: curso=1 usuario=2 matricula=2      (o log não traz mais cartão nem chave)

POST   /api/checkout (cartão aprovado)           -> 200  {"msg": "Sucesso", "enrollment_id": 2}
POST   /api/checkout (cartão recusado)           -> 400  Pagamento recusado
POST   /api/checkout (card numérico)             -> 400  Bad Request                  (antes: derrubava o processo)
GET    /api/admin/financial-report (sem token)   -> 401  Unauthorized
GET    /api/admin/financial-report (+token)      -> 200  [{"course": "Clean Architecture", "revenue": 1994, "students": [...
DELETE /api/users/1 (sem token)                  -> 401  Unauthorized
```

**task-manager-api** (`SECRET_KEY=... python seed.py` e depois `python app.py`)

```
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks
 * Serving Flask app 'app'
 * Debug mode: off

GET    /health                                   -> 200  {"status": "ok", "timestamp": "2026-11-09 15:37:27.570465"}
GET    /tasks                                    -> 200  10 itens
GET    /users/1                                  -> 200  campos: active, created_at, email, id, name, role, tasks     (sem password)
POST   /login                                    -> 200  {"message": "Login realizado com sucesso", "token": "eyJpZCI6MSwicm...", ...
DELETE /tasks/1 (sem token)                      -> 401  {"error": "Token ausente"}
DELETE /tasks/1 (+token)                         -> 200  {"message": "Task deletada com sucesso"}
GET    /tasks/search?priority=abc                -> 400  {"error": "Prioridade inválida"}     (antes: 500)
```

> Screenshots não foram incluídos: as três aplicações são APIs JSON, e os logs acima mostram o mesmo comportamento. Se quiser, o autor pode acrescentar prints de um cliente HTTP (por exemplo, usando o `api.http` do projeto 2) nesta seção.

### Observações sobre o comportamento da skill nas stacks

- **Flask monolítico (projeto 1):** muitas falhas de segurança e de arquitetura. As PoCs de SQL Injection foram confirmadas no baseline (a busca com `OR` devolvia todos os produtos, a com `UNION` vazava as senhas, o login era burlado) e deixaram de funcionar depois.
- **Express (projeto 2):** nenhum SQL Injection (todas as queries já eram parametrizadas, e a skill registrou o AP-01 como avaliado e descartado), mas achou o checkout sem transação, estado global, hash de senha caseiro e uma queda do processo com `card` numérico (confirmada no baseline, corrigida depois). É o projeto em que o AP-12 encontrou algo de verdade.
- **A skill se adaptou à stack sem mudança de sinais:** nenhum ajuste específico de Node foi necessário; os ajustes feitos entre as execuções foram gerais.
- **Reprodutibilidade:** uma execução limpa do projeto 1 em worktree, a partir do commit inicial e em sessão nova, completou o fluxo inteiro; a diferença de contagem (15 contra 17) veio da granularidade e foi corrigida no catálogo.
- **Projeto parcialmente organizado (projeto 3):** a skill não recriou tudo em outra estrutura: manteve `models/`, `routes/` e `services/` e acrescentou as camadas que faltavam (controllers, views, validators, middlewares, config). As rotas, que acumulavam validação, regra, acesso a dados e serialização, passaram a só registrar caminhos. As consultas N+1 caíram de 17 para 1 em `/tasks`, de 4 para 2 em `/users`, de 5 para 2 em `/categories` e de 19 para 10 em `/reports/summary`.
- **Lacuna encontrada pela análise manual:** o CORS aberto do projeto 3 não foi achado na execução. Ele levou o AP-02 a ganhar um terceiro achado (CORS totalmente aberto) e o playbook a trazer a configuração por lista de origens. O mesmo aconteceu com a nomenclatura de variáveis do projeto 2.
- **APIs deprecated sem versão declarada:** o projeto 3 não declara a versão do Python. A regra estrita da skill (só vale a versão declarada) deixou o `datetime.utcnow()` como não confirmado, com a recomendação do equivalente moderno no relatório. Já o `Model.query.get()` pôde ser confirmado, porque a `flask-sqlalchemy` pinada exige `sqlalchemy>=2.0.16`.

---

## Como Executar

### Pré-requisitos

- **Claude Code** instalado e configurado (a skill usa o recurso de Custom Skills: `.claude/skills/refactor-arch/`).
- **Git**.
- **Python 3** com `pip` (projetos 1 e 3, e o script `compare.py`).
- **Node.js 20.17 ou mais novo** com `npm` (projeto 2: o `sqlite3` 6 exige essa versão).

### Executar a skill em cada projeto

Abra uma sessão nova do Claude Code na pasta do projeto e invoque:

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

O fluxo é: a Fase 1 imprime a análise; a Fase 2 grava o relatório em `reports/audit-project-N.md` (na raiz do repositório) e pergunta `[y/n]`; só com `y` a skill levanta as decisões humanas, grava o baseline e refatora. O relatório da Fase 2 é o ponto de revisão: nada é alterado antes da confirmação.

### Como validar que a refatoração funcionou

1. Leia o bloco `PHASE 3: REFACTORING COMPLETE` no relatório: estrutura nova, `Validation`, `Intentional changes`, `Not verified` e a tabela `Endpoint comparison`. Nenhuma linha pode estar como `FAIL`.
2. Suba a aplicação refatorada:

```bash
# Projeto 1: em desenvolvimento gera uma SECRET_KEY temporária; em produção, defina SECRET_KEY
cd code-smells-project && pip install -r requirements.txt && APP_DEBUG=1 python app.py   # http://127.0.0.1:5000

# Projeto 2: as rotas admin exigem Authorization: Bearer <ADMIN_TOKEN>
cd ecommerce-api-legacy && npm install && ADMIN_TOKEN=meu-token npm start                # http://localhost:3000

# Projeto 3: o seed vem antes do app; exige SECRET_KEY (ou APP_DEBUG=1 em desenvolvimento)
cd task-manager-api && pip install -r requirements.txt && APP_DEBUG=1 python seed.py && APP_DEBUG=1 python app.py   # http://127.0.0.1:5000
```

3. Chame os endpoints originais (`api.http` no projeto 2; no projeto 1, as rotas `/produtos`, `/usuarios`, `/pedidos`, `/login`, `/relatorios/vendas` e `/health`) e confira que respondem como no baseline.
4. Para comparar baseline e depois por conta própria, use `python .claude/skills/refactor-arch/scripts/compare.py <dir_baseline> <dir_after>` (código de saída 1 indica divergência).

No projeto 3, `DELETE /tasks/<id>` e `DELETE /categories/<id>` exigem `Authorization: Bearer <token>` do `POST /login`, e `PUT` e `DELETE /users/<id>` exigem o token de um usuário `admin`. O CORS não aceita nenhuma origem de navegador por padrão: liste as permitidas em `CORS_ORIGINS`.
