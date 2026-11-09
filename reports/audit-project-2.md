# ARCHITECTURE AUDIT REPORT

Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js, versão não confirmada) + Express ^4.18.2 (lock: 4.22.1) + sqlite3 ^5.1.6 (lock: 5.1.7)
Files:   3 analyzed | ~180 lines of code

## Summary
Date:    2026-11-09
CRITICAL: 4 | HIGH: 5 | MEDIUM: 4 | LOW: 2

## Achados por severidade
| # | Severidade | Problema | Localização | Observações | Ação proposta |
|---|:----------:|---|---|---|---|
| 1 | CRITICAL | Credenciais e segredos hardcoded ou expostos | `src/utils.js:2-5` | Chave do gateway e número completo do cartão também vão para o log (`src/AppManager.js:45`) | Ler segredos de variáveis de ambiente e remover segredo e cartão do log. Requer decisão humana (valores padrão e variáveis obrigatórias) |
| 2 | CRITICAL | Rotas administrativas e destrutivas sem autenticação | `src/AppManager.js:80` | Inclui `DELETE /api/users/:id` (`src/AppManager.js:131`) | Exigir autenticação e autorização nas rotas. Requer decisão humana (mecanismo e quem é admin) |
| 3 | CRITICAL | Senhas sem proteção adequada | `src/utils.js:17-23` | Seed com senha em texto puro (`src/AppManager.js:18`); hash caseiro no cadastro (`src/AppManager.js:68`) | Trocar por hash de senha adequado. Requer decisão humana (muda o valor gravado em `users.pass`) |
| 4 | CRITICAL | God Class / God Module (AppManager) | `src/AppManager.js:4-139` | DDL, seed, rotas, SQL e regras na mesma classe | Separar em config, models, controllers e rotas |
| 5 | HIGH | Lógica de negócio fora da camada correta | `src/AppManager.js:46` | Decisão de pagamento, criação de usuário e receita dentro dos handlers | Mover as regras para controllers e models |
| 6 | HIGH | Estado global mutável | `src/utils.js:9` | `globalCache` exportado e alterado em runtime | Remover ou encapsular o estado compartilhado |
| 7 | HIGH | Acoplamento forte e quebra de camadas (sem DI) | `src/AppManager.js:7` | Conexão criada no construtor e usada direto nos handlers | Injetar a conexão e isolar o acesso a dados em models |
| 8 | HIGH | Checkout sem transação nem rollback | `src/AppManager.js:50-57` | Até 4 escritas dependentes em callbacks aninhados | Envolver as escritas em uma transação com rollback |
| 9 | HIGH | Exclusão de usuário deixa matrículas e pagamentos órfãos | `src/AppManager.js:133-135` | A própria resposta admite o dado "sujo" | Tratar matrículas e pagamentos na exclusão. Requer decisão humana (cascata ou bloqueio; muda a mensagem) |
| 10 | MEDIUM | Queries N+1 no relatório financeiro | `src/AppManager.js:92` | Três níveis de query dentro de laços | Carregar os dados em lote com JOIN |
| 11 | MEDIUM | Tratamento de erros ausente e inconsistente | `src/AppManager.js:93` | `err` ignorado em várias queries; sem handler global. Requer decisão humana (formato de erro) | Centralizar o tratamento de erros em um handler global |
| 12 | MEDIUM | Validação de entrada ausente ou insuficiente | `src/AppManager.js:35` | Só checa presença dos campos | Validar tipo e formato na entrada. Requer decisão humana (passa a rejeitar entradas hoje aceitas) |
| 13 | MEDIUM | Dependências transitivas deprecated | `package-lock.json:2117` | 9 pacotes marcados `deprecated` no lock, vindos do `sqlite3` | Atualizar as dependências afetadas. Requer decisão humana (versão do `sqlite3`) |
| 14 | LOW | Magic numbers e strings soltas | `src/AppManager.js:46` | Status `PAID`/`DENIED`, prefixo `"4"`, senha padrão `"123456"` | Nomear em constantes |
| 15 | LOW | Logging por console.log e código morto | `src/AppManager.js:45` | `totalRevenue` e várias chaves de `config` nunca usadas | Usar logger apropriado e remover o código morto |

## Findings

### [CRITICAL] Credenciais e segredos hardcoded ou expostos (AP-02)
File: `src/utils.js:2-5` (+ `src/AppManager.js:45`)
Description: o objeto `config` traz `dbUser: "admin_master"`, `dbPass: "senha_super_secreta_prod_123"`, `paymentGatewayKey: "pk_live_1234567890abcdef"` e `smtpUser` escritos no código versionado. O handler de checkout ainda escreve no log a chave do gateway e o número completo do cartão informado.
Evidence: `src/utils.js:3:    dbPass: "senha_super_secreta_prod_123",` e `src/AppManager.js:45: console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`);`
Impact: qualquer pessoa com acesso ao repositório ou aos logs obtém a chave de produção do gateway e dados de cartão.
Recommendation: mover os segredos para variáveis de ambiente e remover chave e cartão do log. Requer decisão humana: quais variáveis passam a ser obrigatórias e quais valores padrão (inclusive a porta) são aceitáveis. (→ PB-02)

### [CRITICAL] Rotas administrativas e destrutivas sem autenticação (AP-03)
File: `src/AppManager.js:80` (+ `src/AppManager.js:131`)
Description: `GET /api/admin/financial-report` devolve nomes de alunos e valores pagos, e `DELETE /api/users/:id` apaga usuários, ambos sem verificar identidade ou permissão. Não existe middleware de autenticação no projeto.
Evidence: `src/AppManager.js:80: app.get('/api/admin/financial-report', (req, res) => {` e `src/AppManager.js:131: app.delete('/api/users/:id', (req, res) => {`
Impact: qualquer cliente anônimo lê o relatório financeiro e apaga qualquer usuário.
Recommendation: proteger as rotas com autenticação e autorização. Requer decisão humana: mecanismo de autenticação, quem é administrador e o código de resposta para não autenticados (as rotas hoje respondem a qualquer cliente). (→ PB-03)

### [CRITICAL] Senhas sem proteção adequada (AP-03)
File: `src/utils.js:17-23` (+ `src/AppManager.js:18`, `src/AppManager.js:68`)
Description: `badCrypto` repete 10000 vezes os 2 primeiros caracteres do base64 da senha e devolve 10 caracteres, então o valor depende só do início da senha, sem sal, e senhas diferentes colidem. O seed grava a senha `'123'` em texto puro. Quando o usuário não informa senha, é usada a padrão `"123456"`.
Evidence: `src/utils.js:19: for(let i = 0; i < 10000; i++) {` e `src/AppManager.js:18: ... VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')`
Impact: senhas recuperáveis ou colidíveis; conta criada sem senha fica com credencial previsível.
Recommendation: usar hash de senha adequado (com sal e custo configurável) e remover a senha em texto puro do seed. Requer decisão humana: o valor gravado em `users.pass` muda, e é preciso decidir a senha padrão e o tratamento do seed. (→ PB-03)

### [CRITICAL] God Class / God Module (AP-04)
File: `src/AppManager.js:4-139` (+ `src/utils.js:1-25`)
Description: a classe `AppManager` cria a conexão SQLite (`:7`), define DDL e seed (`:10-22`), registra três rotas (`:28`, `:80`, `:131`), executa SQL em todas e decide regras de negócio. `src/utils.js` mistura config, cache global e criptografia sob um nome genérico.
Evidence: `src/AppManager.js:4: class AppManager {` com `sqlite3` importado na linha 1 e rotas Express em `setupRoutes`.
Impact: mudar rota, schema ou regra exige editar o mesmo arquivo; testes isolados são inviáveis.
Recommendation: separar em config, models, controllers e rotas, com um entry point que só compõe a aplicação. (→ PB-04)

### [HIGH] Lógica de negócio fora da camada correta (AP-05)
File: `src/AppManager.js:46` (+ `src/AppManager.js:66-69`, `src/AppManager.js:108-110`)
Description: a aprovação do pagamento (`cc.startsWith("4")`), o cadastro implícito do usuário e o cálculo da receita por curso estão dentro dos handlers, misturados com SQL e resposta HTTP.
Evidence: `src/AppManager.js:46: let status = cc.startsWith("4") ? "PAID" : "DENIED";`
Impact: regras não testáveis sem HTTP e sem banco, e difíceis de reutilizar.
Recommendation: mover as regras para os controllers e o acesso a dados para models, sem alterar o comportamento. (→ PB-05)

### [HIGH] Estado global mutável (AP-06)
File: `src/utils.js:9` (+ `src/utils.js:10`, `src/utils.js:14`, `src/utils.js:25`)
Description: `globalCache` é um objeto de módulo alterado por `logAndCache` a cada checkout e exportado. `totalRevenue` é outra variável de módulo mutável, exportada e importada em `src/AppManager.js:2`.
Evidence: `src/utils.js:14:     globalCache[key] = data;`
Impact: estado compartilhado entre requisições, crescimento ilimitado em memória e testes dependentes de ordem. Nenhum ponto do código lê `globalCache`.
Recommendation: remover o estado global ou encapsulá-lo em um componente injetado. (→ PB-06)

### [HIGH] Acoplamento forte e quebra de camadas (sem DI) (AP-07)
File: `src/AppManager.js:7` (+ `src/AppManager.js:37`, `src/AppManager.js:83`, `src/AppManager.js:133`)
Description: a conexão é criada no construtor (`new sqlite3.Database(':memory:')`) e os handlers chamam `this.db` diretamente, sem camada intermediária nem injeção de dependência.
Evidence: `src/AppManager.js:7:         this.db = new sqlite3.Database(':memory:');`
Impact: não dá para trocar o banco nem usar um mock sem editar os handlers.
Recommendation: injetar a conexão e concentrar o acesso a dados em models. (→ PB-07)

### [HIGH] Checkout sem transação nem rollback (AP-08)
File: `src/AppManager.js:50-57` (+ `src/AppManager.js:69`)
Description: o checkout grava usuário (quando novo), matrícula, pagamento e auditoria em `db.run` encadeados, sem `BEGIN`/`COMMIT`/`ROLLBACK`. Uma falha após a primeira escrita deixa dados parciais: por exemplo, matrícula sem pagamento (`:54-55` responde 500 depois de a matrícula já ter sido gravada em `:50`). O erro da auditoria em `:57` é ignorado e o handler responde 200 em `:60`.
Evidence: `src/AppManager.js:50: this.db.run("INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, cid], function(err) {`
Impact: matrículas e usuários órfãos após falhas no meio do fluxo.
Recommendation: executar as escritas do checkout dentro de uma transação com rollback. (→ PB-08)

### [HIGH] Exclusão de usuário deixa matrículas e pagamentos órfãos (AP-08)
File: `src/AppManager.js:133-135`
Description: `DELETE /api/users/:id` remove só a linha de `users`. A resposta diz explicitamente que as matrículas e os pagamentos ficaram no banco, e o relatório financeiro passa a listar esses alunos como `Unknown` (`src/AppManager.js:113`).
Evidence: `src/AppManager.js:135: res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");`
Impact: dados inconsistentes entre `users`, `enrollments` e `payments`.
Recommendation: tratar matrículas e pagamentos do usuário na mesma operação. Requer decisão humana: apagar em cascata, bloquear a exclusão ou manter o comportamento atual; qualquer opção muda a resposta e o estado do banco. (→ PB-08)

### [MEDIUM] Queries N+1 no relatório financeiro (AP-09)
File: `src/AppManager.js:92` (+ `src/AppManager.js:104`, `src/AppManager.js:106`)
Description: para cada curso (`:83`) roda uma query de matrículas; para cada matrícula, uma de usuário e outra de pagamento. O número de queries cresce linearmente com cursos e matrículas.
Evidence: `src/AppManager.js:104: this.db.get("SELECT name, email FROM users WHERE id = ?", [enr.user_id], (err, user) => {`
Impact: latência e carga no banco proporcionais ao volume de dados.
Recommendation: buscar os dados em lote com JOIN, preservando o formato da resposta. (→ PB-09)

### [MEDIUM] Tratamento de erros ausente e inconsistente (AP-10)
File: `src/AppManager.js:93` (+ `src/AppManager.js:57-60`, `src/AppManager.js:104`, `src/AppManager.js:106`, `src/AppManager.js:133-135`)
Description: o `err` de várias queries é ignorado. Em `:92` a falha deixaria `enrollments` indefinido e `enrollments.length` (`:93`) lançaria exceção dentro do callback. O `DELETE` responde sucesso mesmo com erro (`:133-135`). Os erros restantes são mensagens soltas (`"Erro DB"`, `"Erro Matrícula"`) e não existe handler global de erro.
Evidence: `src/AppManager.js:93: let enrPending = enrollments.length;`
Impact: falhas silenciosas, respostas inconsistentes e exceções não tratadas em callbacks.
Recommendation: centralizar o tratamento de erros em um handler global. Requer decisão humana: o formato e as mensagens de erro hoje devolvidos ao cliente. (→ PB-10)

### [MEDIUM] Validação de entrada ausente ou insuficiente (AP-10)
File: `src/AppManager.js:35` (+ `src/AppManager.js:46`, `src/AppManager.js:68`, `src/AppManager.js:132`)
Description: o checkout valida só a presença de `usr`, `eml`, `c_id` e `card`; não verifica tipo nem formato (e-mail, número do cartão, `c_id` numérico). `cc.startsWith` na linha 46 só existe em string, então um `card` de outro tipo lançaria exceção (comportamento a confirmar no baseline da Fase 3, não executado na Fase 2). A coluna `email` não tem restrição de unicidade (`:12`) e o `:id` do `DELETE` não é validado.
Evidence: `src/AppManager.js:35: if (!u || !e || !cid || !cc) return res.status(400).send("Bad Request");`
Impact: entradas inválidas chegam ao banco e à regra de pagamento, com risco de erro 500 ou queda do processo.
Recommendation: validar tipo e formato na entrada dos controllers. Requer decisão humana: a validação passa a rejeitar entradas hoje aceitas, e é preciso definir as regras e o formato do erro. (→ PB-10)

### [MEDIUM] Dependências transitivas deprecated (AP-12)
File: `package-lock.json:2117` (+ `package-lock.json:831`, `package-lock.json:1078`, `package-lock.json:1722`, `package-lock.json:164`, `package-lock.json:767`, `package-lock.json:1482`, `package-lock.json:1573`, `package-lock.json:37`)
Description: o lock registra como `deprecated` os pacotes `tar` 6.2.1, `glob` 7.2.3, `inflight` 1.0.6, `rimraf` 3.0.2, `are-we-there-yet` 3.0.1, `gauge` 4.0.4, `npmlog` 6.0.2, `prebuild-install` 7.1.3 e `@npmcli/move-file` 1.1.2. Entram pela cadeia de instalação do `sqlite3` (`package-lock.json:2030` lista `prebuild-install` e `tar` como dependências). Os avisos de `tar` e `glob` citam vulnerabilidades já corrigidas em versões novas.
Evidence: `package-lock.json:2117:      "deprecated": "Old versions of tar are not supported, and contain widely publicized security vulnerabilities, ..."`
Impact: dependências sem manutenção, e dois pacotes sem correções de segurança na versão fixada. Se atingem a execução da API ou só a instalação do `sqlite3` não foi verificado.
Recommendation: atualizar as dependências afetadas. Requer decisão humana: trocar a versão do `sqlite3` altera o `package.json` e o lock. A versão em que cada pacote foi marcado deprecated não está no lock (não confirmado). (→ PB-12)

### [LOW] Magic numbers e strings soltas (AP-13)
File: `src/AppManager.js:46` (+ `src/AppManager.js:21`, `src/AppManager.js:48`, `src/AppManager.js:68`, `src/AppManager.js:108`, `src/utils.js:19`, `src/utils.js:22`)
Description: os status `"PAID"` e `"DENIED"` e o prefixo de cartão `"4"` aparecem como literais; `"PAID"` se repete em `:21`, `:46` e `:108`. A senha padrão `"123456"`, as `10000` iterações e o `substring(0, 10)` não têm nome.
Evidence: `src/AppManager.js:68: let hash = badCrypto(p || "123456");`
Impact: regras difíceis de localizar e risco de divergência entre os pontos de uso.
Recommendation: nomear os literais em constantes. (→ PB-13)

### [LOW] Logging por console.log e código morto (AP-14)
File: `src/AppManager.js:45` (+ `src/utils.js:13`, `src/app.js:13`, `src/AppManager.js:2`, `src/utils.js:10`, `src/utils.js:2`, `src/utils.js:3`, `src/utils.js:5`)
Description: `console.log` sem nível nem timestamp é o único mecanismo de log. `totalRevenue` é importado em `src/AppManager.js:2` e nunca usado, e em `src/utils.js:10` nunca é alterado. `config.dbUser`, `config.dbPass` e `config.smtpUser` são definidos e nunca lidos.
Evidence: `src/utils.js:13:     console.log(\`[LOG] Salvando no cache: ${key}\`);`
Impact: diagnóstico fraco em produção e ruído na leitura.
Recommendation: usar um logger com nível e remover imports e chaves sem uso. (→ PB-14)

## Not Verified
- AP-12 (APIs deprecated de linguagem e runtime): `package.json` não declara a versão do Node (sem `engines`, `.nvmrc` ou Dockerfile), então nenhuma API do runtime foi classificada como deprecated | Reason: versão do Node não declarada nos arquivos do projeto
- AP-12 (APIs do Express): `package.json:10` declara `^4.18.2` (faixa) e o lock fixa 4.22.1; as chamadas usadas (`express.json()`, `app.get/post/delete`, `res.status().send/json`) não foram confirmadas como deprecated | Reason: sem evidência de deprecação nas notas da versão declarada
- AP-12 (release em que cada pacote foi marcado deprecated): o lock informa só a mensagem, não a versão | Reason: dado não disponível nos arquivos do projeto
- AP-01 (SQL Injection): todas as queries usam parâmetros vinculados (`?`), nenhuma concatenação encontrada | Reason: não é falta de verificação, apenas registro de que o anti-pattern foi avaliado e descartado
- AP-11 (código duplicado): nenhum bloco duplicado com evidência suficiente | Reason: avaliado e descartado
- Execução da aplicação: as Fases 1 e 2 são somente leitura, então nenhum endpoint foi chamado | Reason: a execução só ocorre na Fase 3

### Total: 15 findings

---

# PHASE 3: REFACTORING COMPLETE

## New Project Structure
```
ecommerce-api-legacy/
├── package.json                   # sqlite3 ^6.0.1 (antes ^5.1.6)
├── package-lock.json
├── README.md                      # variáveis de ambiente e estrutura
├── api.http                       # rotas admin com Authorization: Bearer
├── .env.example                   # PORT, ADMIN_TOKEN, LOG_LEVEL
├── .gitignore                     # node_modules, .env, logs, bancos locais
└── src/
    ├── app.js                     # entry point e composition root (monta e inicia)
    ├── config/
    │   ├── env.js                 # única leitura de variáveis de ambiente
    │   └── logger.js              # logger com nível e timestamp
    ├── constants/
    │   ├── messages.js            # mensagens de resposta
    │   └── payment.js             # PaymentStatus, prefixo de cartão, senhas padrão/seed
    ├── routes/
    │   ├── checkout.routes.js     # POST /api/checkout
    │   └── admin.routes.js        # GET /api/admin/financial-report, DELETE /api/users/:id
    ├── controllers/
    │   ├── checkout.controller.js
    │   ├── report.controller.js
    │   └── user.controller.js
    ├── validators/
    │   └── checkout.validator.js  # validação do corpo do checkout
    ├── services/
    │   ├── checkout.service.js    # caso de uso do checkout e fronteiras de transação
    │   ├── payment.service.js     # regra de aprovação do cartão
    │   ├── report.service.js      # receita por curso e alunos
    │   ├── user.service.js        # exclusão de usuário
    │   └── password.service.js    # hash scrypt com sal
    ├── models/
    │   ├── database.js            # conexão SQLite e transaction() com rollback
    │   ├── schema.js              # DDL e seed
    │   ├── user.model.js
    │   ├── course.model.js
    │   ├── enrollment.model.js
    │   ├── payment.model.js
    │   ├── audit-log.model.js
    │   └── report.model.js        # consulta única com JOIN
    ├── views/
    │   ├── checkout.view.js
    │   └── report.view.js
    ├── middlewares/
    │   ├── auth.middleware.js     # Bearer ADMIN_TOKEN
    │   ├── error.middleware.js    # tratador global de erros
    │   └── async-handler.js
    └── errors/
        └── app-error.js
```
Removidos: `src/AppManager.js` e `src/utils.js`.

## Validation
- [x] ✓ Application boots without errors (boot limpo com `node --throw-deprecation`, log sem erro nem exceção)
- [x] ✓ 15/15 endpoints respond correctly (`compare.py`: 15 endpoints comparados, 0 diferença(s))
- [x] ✓ Status codes match baseline (15/15)
- [ ] ✗ 13/15 findings resolved (re-detected with the catalog signals): pendentes #9 (AP-08, mantido por decisão do usuário) e #13 (AP-12, parcial: de 9 para 1 pacote deprecated; o que sobrou foi aceito pelo usuário, ver abaixo)
- [ ] ✗ 2 anti-patterns remaining: AP-08 (exclusão de usuário deixa matrículas e pagamentos órfãos, mantido por decisão do usuário), AP-12 (`prebuild-install` 7.1.3 continua marcado `deprecated` no lock; é dependência direta do `sqlite3` 6.0.1, e essa é a versão mais nova publicada (`npm view sqlite3 dist-tags`: `latest` = 6.0.1), que ainda declara `prebuild-install@^7.1.3`. Atualizar o `sqlite3` não remove a dependência; só trocar o driver (por exemplo, pelo `node:sqlite` embutido no Node) a removeria. Aceito como está por decisão do usuário)
- [x] ✓ Rotas administrativas sem autenticação PoC no longer exploitable (sem credencial: 200 no baseline, 401 depois, nas 2 rotas; token errado também 401)
- [x] ✓ Crash por `card` numérico PoC no longer exploitable (baseline: processo derrubado com `TypeError`, status 000; depois: 400 "Bad Request" e o processo continua respondendo 200)
- [x] ✓ Segredos e cartão no log: o baseline imprimia o cartão completo e `pk_live_...`; o log do app refatorado não contém nenhum dos dois
- [x] ✓ Senhas gravadas com scrypt e sal (4/4 linhas de `users.pass` com prefixo `scrypt$`, inclusive o seed; a colisão do baseline, `senhaforte` e `sabcdefgh` com o mesmo hash `c2c2c2c2c2`, deixa de existir porque cada hash tem sal aleatório)
- [x] ✓ Checkout atômico: com falha simulada no pagamento, a contagem de matrículas ficou em 3 (rollback confirmado); cartão recusado continua criando o usuário e não cria matrícula
- [x] ✓ Concorrência: 8 checkouts simultâneos responderam 200 e o relatório listou 10 alunos e receita 9970, corretamente
- [x] ✓ 0 DeprecationWarnings (boot refatorado com `--throw-deprecation`; o baseline não foi medido com a flag)

### Intentional changes
- Rotas `GET /api/admin/financial-report` e `DELETE /api/users/:id` passam a exigir `Authorization: Bearer <ADMIN_TOKEN>`; sem token ou com token errado respondem 401 "Unauthorized", e sem `ADMIN_TOKEN` configurado respondem sempre 401. Decisão do usuário: token admin via ambiente.
- A senha do usuário passa a ser gravada com scrypt e sal em vez de `badCrypto`; o seed do usuário Leonan guarda a senha `123` com hash. O formato de `users.pass` muda, nenhuma resposta HTTP muda. A senha padrão `123456` quando `pwd` não vem foi mantida. Decisão do usuário: scrypt nativo.
- O checkout valida tipos: `usr`, `eml` e `card` não-string, `pwd` truthy não-string e `c_id` que não seja inteiro (número ou string de dígitos) respondem 400 "Bad Request". Antes, `card` numérico derrubava o processo e `c_id` como `"abc"` respondia 404 "Curso não encontrado". Sem validação de formato de e-mail nem unicidade. Decisão do usuário: manter textos e validação mínima.
- Matrícula, pagamento e auditoria do checkout são atômicos; o usuário novo continua sendo gravado antes e fora da transação. Falha na auditoria (antes ignorada, com 200) passa a desfazer a operação e responder 500, e erro de banco na consulta do curso (antes 404) passa a responder 500. Esses caminhos não são alcançáveis por entrada normal. Decisão do usuário: preservar a criação do usuário.
- Falhas inesperadas passam a ser tratadas por um handler global (500 "Erro interno do servidor", detalhe só no log). Os textos e status das respostas de erro existentes foram mantidos. Decisão do usuário: manter textos.
- A ordem de cursos e alunos no relatório financeiro passa a ser determinística (por id); antes dependia da ordem de término das queries. Efeito colateral da correção do N+1.
- Variáveis de ambiente novas: `PORT` (padrão 3000), `ADMIN_TOKEN` e `LOG_LEVEL`. O servidor continua escutando em todas as interfaces, como antes. Decisão do usuário: opcionais e bind igual.
- Removidos do código `dbUser`, `dbPass` e `smtpUser` (nunca lidos) e `paymentGatewayKey`. Esta última só era usada no log; o gateway é simulado e não faz chamada externa, então não há ponto de leitura para a chave. Por isso `PAYMENT_GATEWAY_KEY` não foi criada, o que difere do que foi descrito ao usuário na pergunta de configuração.
- Os logs deixam de registrar cartão e chave e passam a ter nível e timestamp. A mensagem `[LOG] Salvando no cache` saiu junto com o cache global, que nunca era lido.
- Mantido por decisão do usuário (AP-12): o pacote `prebuild-install` 7.1.3 continua `deprecated` no lock, porque o `sqlite3` 6.0.1, a versão mais nova existente, ainda depende dele. A atualização do `sqlite3` removeu 8 dos 9 pacotes deprecated (`tar`, `glob`, `inflight`, `rimraf`, `are-we-there-yet`, `gauge`, `npmlog`, `@npmcli/move-file`). Trocar o driver não foi feito.
- `sqlite3` atualizado de `^5.1.6` para `^6.0.1` e lock regenerado (`express` continua em 4.22.1). O `sqlite3` 6 exige Node >= 20.17.0 (`package-lock.json:1295`), e o `package.json` não declara `engines`. Decisão do usuário: tentar atualizar.

### Not verified
- Falhas de banco nos passos de criação de usuário, matrícula e auditoria: só a falha no pagamento foi simulada (rollback confirmado); os demais caminhos 500 internos não foram exercitados.
- O corpo do 400 para JSON malformado: só o status foi comparado (400 nos dois), porque o HTML padrão do Express inclui caminhos do disco. O tratamento padrão do Express foi preservado, o que mantém o stack trace na página fora de `NODE_ENV=production`.
- O `sqlite3` 6.0.1 foi testado só com Node v26.13.0 e npm 11.20.0; as versões intermediárias (>= 20.17.0) não foram testadas.
- Se o `prebuild-install` participa da execução da API ou só da instalação do `sqlite3`: não foi verificado. Pelo que o pacote faz (baixa o binário pré-compilado do `sqlite3` na instalação), parece ser só de instalação, mas isso é inferência.
- Rotação dos segredos antigos: `senha_super_secreta_prod_123` e `pk_live_1234567890abcdef` continuam no histórico do git; considerá-los comprometidos e rotacioná-los é decisão do usuário.
- O baseline de DeprecationWarnings do projeto original não foi medido com `--throw-deprecation`.
- Validação de formato de e-mail e unicidade de e-mail: fora do escopo por decisão do usuário.

### Endpoint comparison
As chamadas de rotas admin levam o cabeçalho `Authorization: Bearer` nos dois lados (o original ignora o cabeçalho).

| Method | Path | Baseline | After | Result |
|---|---|:---:|:---:|:---:|
| GET | / (rota inexistente) | 404 | 404 | OK |
| GET | /api/admin/financial-report (inicial) | 200 | 200 | OK |
| POST | /api/checkout (usuário novo, cartão aprovado) | 200 | 200 | OK |
| POST | /api/checkout (usuário existente) | 200 | 200 | OK |
| POST | /api/checkout (cartão recusado) | 400 | 400 | OK |
| POST | /api/checkout (mesmo usuário após recusa, aprovado) | 200 | 200 | OK |
| POST | /api/checkout (corpo vazio) | 400 | 400 | OK |
| POST | /api/checkout (sem card) | 400 | 400 | OK |
| POST | /api/checkout (curso inexistente) | 404 | 404 | OK |
| POST | /api/checkout (sem pwd) | 200 | 200 | OK |
| GET | /api/admin/financial-report (após checkouts) | 200 | 200 | OK |
| DELETE | /api/users/1 | 200 | 200 | OK |
| GET | /api/admin/financial-report (após exclusão) | 200 | 200 | OK |
| DELETE | /api/users/9999 | 200 | 200 | OK |
| DELETE | /api/users/abc | 200 | 200 | OK |

Mudanças intencionais verificadas à parte (PoCs, listadas em `Validation`): rotas admin sem credencial (200 para 401) e `card` numérico (queda do processo para 400).

## Checklist de Validação (Fase 3)
- [x] Estrutura de diretórios segue padrão MVC: árvore real com `config/`, `models/`, `views/`, `routes/`, `controllers/`, `middlewares/`, mais `services/`, `validators/`, `constants/` e `errors/` (`find src -type f`, 30 arquivos).
- [x] Configuração extraída para módulo de config (sem hardcoded): `src/config/env.js` é o único leitor de ambiente; a busca de segredos literais (AP-02) e a de literais de status e senha fora de `constants/` (AP-13) em `src/` retornaram vazio.
- [x] Models criados para abstrair dados: `grep -rnE "SELECT |INSERT |DELETE |UPDATE |CREATE TABLE" src | grep -v "^src/models/"` retornou vazio; `grep sqlite3` em controllers e routes retornou vazio (AP-01, AP-05, AP-07).
- [x] Views/Routes separadas para visualização ou roteamento: rotas em `src/routes/checkout.routes.js` e `src/routes/admin.routes.js`; formato de resposta em `src/views/`.
- [x] Controllers concentram o fluxo da aplicação: `src/controllers/*.js` validam a entrada, chamam o service e devolvem a resposta, sem SQL nem regra de negócio.
- [x] Error handling centralizado: um único `errorMiddleware` registrado em `src/app.js`; `grep -rnE "catch|e\.message|err\.message" src/controllers` retornou vazio (AP-10).
- [x] Entry point claro: `src/app.js` só monta as dependências, registra rotas e middlewares e chama `listen` (`npm start` inalterado).
- [x] Aplicação inicia sem erros: boot limpo com `node --throw-deprecation src/app.js` a partir de `npm ci` com os manifestos novos, log sem exceção.
- [x] Endpoints originais respondem corretamente: `scripts/compare.py` baseline x after, 15 endpoints comparados, 0 diferença(s), nenhum FAIL (ver `Endpoint comparison`).
