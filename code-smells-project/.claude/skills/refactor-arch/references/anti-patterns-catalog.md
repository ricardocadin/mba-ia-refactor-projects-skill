# Catálogo de Anti-Patterns (AP)

Documento de referência para identificar anti-patterns durante a auditoria de código. Cada entrada traz definição, sinais observáveis, como confirmar e a transformação associada (playbook `PB-xx`, a ser definido em documento próprio).

## Definição de Severidades

Escala baseada em problemas de MVC e SOLID, usada para padronizar a auditoria e os relatórios.

| Severidade | Critério | Exemplos |
|---|---|---|
| CRITICAL | Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis ou violam completamente a separação de responsabilidades. | Credenciais hardcoded, SQL Injection, "God Class" com banco, lógica complexa e roteamento no mesmo arquivo |
| HIGH | Fortes violações de MVC ou SOLID que dificultam muito a manutenção e os testes. | Lógica de negócio pesada em Controllers, acoplamento forte sem Injeção de Dependência, estado global mutável |
| MEDIUM | Problemas de padronização, duplicação de código ou gargalos de performance moderada. | Queries N+1, uso inadequado de middlewares, validações ausentes nas rotas |
| LOW | Melhorias de legibilidade. | Nomenclatura ruim, magic numbers |

## Regras de classificação

Quando um achado cabe em mais de um anti-pattern, classifique-o uma só vez, pela causa principal. Senhas de usuários em texto puro (armazenadas, comparadas ou devolvidas) pertencem ao AP-03; segredos de infraestrutura (chave de aplicação, tokens, credenciais de serviços ou de banco) pertencem ao AP-02.

## Índice

| ID | Anti-Pattern | Severidade | Categoria |
|---|---|---|---|
| AP-01 | SQL Injection / Query por concatenação | CRITICAL | Segurança |
| AP-02 | Credenciais e segredos hardcoded ou expostos | CRITICAL | Segurança |
| AP-03 | Ausência de autenticação/autorização e credenciais sem proteção | CRITICAL | Segurança |
| AP-04 | God Class / God Module | CRITICAL | Arquitetura |
| AP-05 | Lógica de negócio fora da camada correta | HIGH | MVC / SOLID |
| AP-06 | Estado global mutável | HIGH | Arquitetura |
| AP-07 | Acoplamento forte e quebra de camadas (sem DI) | HIGH | SOLID |
| AP-08 | Transações ausentes ou sem rollback | HIGH | Integridade de dados |
| AP-09 | Queries N+1 | MEDIUM | Performance |
| AP-10 | Validação ausente e tratamento genérico de erros | MEDIUM | Robustez |
| AP-11 | Código duplicado | MEDIUM | Padronização |
| AP-12 | Uso de APIs deprecated ou obsoletas | MEDIUM | Manutenibilidade |
| AP-13 | Magic numbers, strings soltas e nomenclatura ruim | LOW | Legibilidade |
| AP-14 | Logging por print e código morto | LOW | Legibilidade |

Distribuição: 4 CRITICAL, 4 HIGH, 4 MEDIUM, 2 LOW (14 anti-patterns).

---

## AP-01 — SQL Injection / Query por concatenação
**Severidade:** CRITICAL · **Categoria:** Segurança

**Definição:** entrada externa é concatenada ou interpolada em uma string SQL em vez de passar por parâmetro vinculado (bind).

**Sinais**
- Python: `cursor.execute("SELECT ... " + var)`, `execute(f"... {var}")`, `execute("..." % var)`
- Node: `db.run(\`SELECT ... ${var}\`)`, `"SELECT ..." + var`
- Java: `Statement` + concatenação (em vez de `PreparedStatement`)
- PHP: `mysqli_query("... $var")`
- Qualquer: construção incremental de `WHERE` via `query += "..." + valor`

**Como confirmar:** a variável concatenada tem origem externa (body, query string, path param, header)? Se sim, é explorável. Concatenar uma constante interna não é injeção. Também não é explorável, e deve ser descartado, o valor que passa por: conversor de tipo da rota (ex.: `<int:id>`, `:id` numérico), conversão explícita (`int()`, `float()`), validação contra lista fechada de valores, ou que vem do próprio banco. Valores extraídos do corpo JSON ou da query string sem conversão de tipo continuam explorável, mesmo quando embrulhados em `str()`. Teste rápido: passar `x' OR '1'='1` no campo e ver se o filtro é ignorado.

**Impacto:** leitura, alteração ou destruição de qualquer dado do banco.
**Transformação:** → PB-01

---

## AP-02 — Credenciais e segredos hardcoded ou expostos
**Severidade:** CRITICAL · **Categoria:** Segurança

**Definição:** chaves, senhas, tokens ou caminhos sensíveis escritos diretamente no código-fonte, ou devolvidos em respostas da API ou em logs.

**Sinais**
- Python: `app.config["SECRET_KEY"] = "texto-literal"`, `DEBUG = True` fixo, `password = "..."`
- Node: `const secret = "..."`, `jwt.sign(x, "literal")`
- Java: `@Value` ausente com literal em `static final String SECRET`
- PHP: `define('DB_PASS', '...')` em arquivo versionado
- Qualquer: endpoint de saúde/diagnóstico que devolve `secret_key`, `db_path`, `debug`; credenciais de serviço ou de banco no código; `debug=True` com `host=0.0.0.0`

**Granularidade:** reporte como achados separados (a) segredos e credenciais hardcoded ou expostos em respostas e (b) modo debug ou bind de rede inseguro (`debug=True`, `host=0.0.0.0`). Cada achado cita seus próprios arquivos e linhas.

**Como confirmar:** o literal é um segredo real ou de uso produtivo, e não um valor de teste claramente isolado? Procure o mesmo valor em respostas HTTP (`/health`, `/config`) e no controle de versão. Se o valor está no repositório ou sai em alguma resposta, está exposto.

**Impacto:** comprometimento de sessões, tokens e contas; acesso ao debugger remoto quando o modo debug está ativo.
**Transformação:** → PB-02

---

## AP-03 — Ausência de autenticação/autorização e credenciais sem proteção
**Severidade:** CRITICAL · **Categoria:** Segurança

**Definição:** rotas sensíveis acessíveis sem verificar identidade ou permissão, e/ou senhas armazenadas e trafegadas em texto puro.

**Sinais**
- Python/Flask: rotas `/admin/*` sem decorator ou verificação; `login` que devolve dados mas não emite token ou sessão; coluna `senha` comparada diretamente em SQL (`WHERE senha = '...'`)
- Node/Express: rotas sem middleware de auth; `bcrypt` ausente
- Java/Spring: ausência de `@PreAuthorize` ou de filtro de segurança
- PHP: ausência de checagem de sessão antes de ações destrutivas
- Qualquer: endpoint que executa SQL arbitrário, apaga dados ou lista usuários; resposta de listagem de usuários que inclui o campo da senha; campo `tipo`/`role` existe mas nunca é consultado; usuários com senha em texto puro no seed ou no código

**Como confirmar:** chame a rota sem credenciais. Se ela executa a ação (ou retorna dados sensíveis), falta controle de acesso. Inspecione a tabela de usuários: senha legível (não é hash) confirma armazenamento em texto puro.

**Granularidade:** reporte como achados separados (a) as rotas sem controle de acesso, incluindo a que executa SQL arbitrário, e (b) a senha em texto puro (armazenada, comparada ou devolvida). Cada achado cita seus próprios arquivos e linhas.

**Impacto:** qualquer cliente anônimo pode apagar o banco, executar SQL, ler senhas e assumir contas.
**Transformação:** → PB-03

---

## AP-04 — God Class / God Module
**Severidade:** CRITICAL · **Categoria:** Arquitetura

**Definição:** um único arquivo ou classe concentra responsabilidades de camadas distintas (roteamento, acesso a dados, regras de negócio, DDL, seed), violando a separação de responsabilidades e o princípio da responsabilidade única.

**Sinais**
- Python: módulo com CRUD de várias entidades + regras de negócio + SQL; arquivo de bootstrap que também define rotas com acesso direto ao banco
- Node: `app.js`/`server.js` com rotas, queries e regras no mesmo arquivo
- Java: classe `*Manager`/`*Service` com dezenas de métodos de entidades diferentes
- PHP: arquivo único com HTML, SQL e lógica
- Qualquer: arquivo que importa o driver de banco e também o framework web; mais de uma entidade de domínio no mesmo módulo; módulo muito longo cujo nome é genérico (`models`, `utils`, `helpers`)

**Como confirmar:** liste as razões pelas quais o arquivo mudaria (nova rota, nova regra, novo campo, mudança de schema). Se forem camadas diferentes, há God Module. Verifique se o arquivo contém ao mesmo tempo SQL e decisões de negócio ou resposta HTTP.

**Impacto:** mudanças em uma responsabilidade quebram outras; testes unitários isolados ficam inviáveis.
**Transformação:** → PB-04

---

## AP-05 — Lógica de negócio fora da camada correta
**Severidade:** HIGH · **Categoria:** MVC / SOLID

**Definição:** regras de negócio (cálculos, políticas, efeitos colaterais como notificações) implementadas em Controllers ou misturadas a código de acesso a dados.

**Sinais**
- Python: controller que decide notificações (`print("ENVIANDO EMAIL...")`) e transições de estado; model que calcula desconto por faixas de faturamento
- Node: handler Express com `if` de regras de preço, estoque ou status
- Java: `@RestController` com cálculo de domínio
- PHP: controller que executa regras e envia e-mails inline
- Qualquer: função de "repositório" com `if`/`elif` de regras de negócio; efeito colateral descrito em texto mas não executado (por exemplo, "devolver estoque" apenas impresso)

**Como confirmar:** a regra poderia ser testada sem HTTP e sem banco? Se não, está presa à camada errada. Procure `if`/cálculos sobre valores de domínio dentro de handlers ou funções de acesso a dados.

**Impacto:** regras duplicadas ou inconsistentes, difíceis de testar e de reutilizar.
**Transformação:** → PB-05

---

## AP-06 — Estado global mutável
**Severidade:** HIGH · **Categoria:** Arquitetura

**Definição:** variáveis globais mutáveis (conexão, cache, configuração) compartilhadas por toda a aplicação e alteradas em tempo de execução.

**Sinais**
- Python: `global db_connection`, variável de módulo inicializada com `None` e preenchida sob demanda; `check_same_thread=False` para contornar threads
- Node: `let db;` no módulo atribuído por função de init
- Java: campo `static` mutável (singleton não thread-safe)
- PHP: `global $conn;`
- Qualquer: singleton de conexão sem ciclo de vida (nunca fechada), sem pool e sem escopo por requisição

**Como confirmar:** localize a palavra-chave `global`, campos `static` mutáveis ou variáveis de módulo reatribuídas. Verifique se vários módulos dependem desse estado e se ele é compartilhado entre requisições concorrentes.

**Impacto:** condições de corrida, testes dependentes de ordem e impossibilidade de isolar dependências.
**Transformação:** → PB-06

---

## AP-07 — Acoplamento forte e quebra de camadas (sem DI)
**Severidade:** HIGH · **Categoria:** SOLID (DIP)

**Definição:** camadas superiores dependem diretamente de implementações concretas e pulam camadas intermediárias, sem injeção de dependência.

**Sinais**
- Python: controller ou arquivo de rotas importando `get_db` e executando SQL diretamente; módulos que importam funções concretas em vez de receber dependências
- Node: `require('./db')` dentro de controllers e rotas
- Java: `new Repository()` dentro de serviços e controllers (em vez de injeção)
- PHP: `new PDO(...)` dentro de controllers
- Qualquer: grafo de dependências em que a camada de apresentação aponta direto para a infraestrutura

**Como confirmar:** trace os imports. Se a camada de apresentação importa o módulo de banco (ou usa o cursor), a camada de dados foi contornada. Verifique se é possível trocar o banco ou usar um mock sem editar os controllers.

**Impacto:** impossibilidade de testar em isolamento; trocar o banco ou a fonte de dados exige mexer em várias camadas.
**Transformação:** → PB-07

---

## AP-08 — Transações ausentes ou sem rollback
**Severidade:** HIGH · **Categoria:** Integridade de dados

**Definição:** uma operação de negócio composta por várias escritas dependentes (por exemplo, criar o pedido, inserir os itens e baixar o estoque) não é executada de forma atômica: não há fronteira de transação explícita, nem `rollback` em caso de falha, e o `commit` pode ocorrer só no fim ou várias vezes ao longo do fluxo. Também entra aqui o efeito de negócio que deveria ser desfeito junto com a operação (por exemplo, devolver o estoque ao cancelar) e que não é executado.

**Sinais**
- Python: função com dois ou mais `INSERT`/`UPDATE`/`DELETE` seguidos de um único `db.commit()` e sem `try/except` com `db.rollback()`; `return` de erro no meio do fluxo depois de escritas já feitas; várias escritas em sequência (`INSERT`/`UPDATE`/`DELETE`) com um único `commit` no fim e sem `try/except` com `rollback`, mesmo sem efeito de negócio associado (ex.: limpeza de várias tabelas); `commit()` dentro de cada função de acesso a dados só conta quando impede que uma operação de negócio com duas ou mais escritas dependentes seja atômica
- Node: sequência de `db.run(...)` sem `BEGIN`/`COMMIT`/`ROLLBACK`; `await` de várias escritas sem `try/catch` que desfaça as anteriores
- Java: método de serviço com várias gravações sem `@Transactional` ou sem `try/catch` com `rollback()`
- PHP: várias `mysqli_query` de escrita sem `begin_transaction()`/`rollback()` (ou `PDO::beginTransaction`)
- Qualquer: mudança de status que só imprime a ação de negócio correspondente (por exemplo, "devolver estoque") sem executá-la; checagem de pré-condição (estoque) separada da escrita, sem bloqueio ou condição na própria escrita

**Como confirmar:** liste as escritas da operação e imagine uma falha entre duas delas (chave inexistente, erro de constraint, exceção). O estado do banco ficaria parcial (pedido sem itens, estoque baixado sem pedido)? Há `rollback` ou um bloco de transação que desfaça o que já foi escrito? Se não, confirmado. Uma função com uma única escrita e um único `commit` não é achado. `return` de erro antes da primeira escrita (apenas leituras) também não é. Para efeitos de negócio, confira se a ação descrita no log ou no `print` é realmente executada.

**Impacto:** dados parciais e inconsistentes após falhas, estoque divergente do que foi vendido e perda de atomicidade em operações críticas.
**Transformação:** → PB-08

---

## AP-09 — Queries N+1
**Severidade:** MEDIUM · **Categoria:** Performance

**Definição:** uma query inicial retorna N registros e, para cada um, é executada uma query adicional (em vez de um JOIN ou carga em lote).

**Sinais**
- Python: `for row in rows:` com `cursor.execute(...)` dentro, às vezes aninhado em dois níveis (pedido → itens → produto)
- Node: `await` de query dentro de `for`/`map`
- Java/JPA: associação `LAZY` percorrida em loop
- PHP: `mysqli_query` dentro de `foreach`
- Qualquer: criação de cursores adicionais dentro do loop de resultados

**Como confirmar:** ative o log de queries e compare o número de execuções com o tamanho da listagem. Se cresce linearmente com os registros, é N+1.

**Impacto:** latência e carga no banco crescem de forma proporcional ao volume de dados.
**Transformação:** → PB-09

---

## AP-10 — Validação ausente e tratamento genérico de erros
**Severidade:** MEDIUM · **Categoria:** Robustez

**Definição:** entradas não são validadas (tipo, formato, existência, unicidade) de forma consistente, e as exceções são capturadas de forma genérica, devolvendo a mensagem interna ao cliente.

**Sinais**
- Python: `except Exception as e: return jsonify({"erro": str(e)}), 500` repetido em todos os handlers; `request.get_json()` usado sem checar `None`; comparação numérica sem checar tipo; validações presentes em `criar` e ausentes em `atualizar`
- Node: `catch (e) { res.status(500).send(e.message) }`
- Java: `catch (Exception e)` retornando `e.getMessage()`
- PHP: `die(mysqli_error($conn))`
- Qualquer: ausência de checagem de existência antes de atualizar; campos únicos (como e-mail) sem restrição; ausência de middleware/handler global de erro

**Como confirmar:** envie corpo vazio, tipos errados (string no lugar de número) e IDs inexistentes. Respostas 500 com texto de exceção, ou sucesso silencioso, confirmam o problema.

**Granularidade:** reporte como achados separados (a) o tratamento genérico de erros (`except Exception` devolvendo a mensagem interna) e (b) a validação de entrada ausente ou inconsistente. Cada achado cita seus próprios arquivos e linhas.

**Impacto:** respostas 500 evitáveis, vazamento de detalhes internos e dados inconsistentes.
**Transformação:** → PB-10

---

## AP-11 — Código duplicado
**Severidade:** MEDIUM · **Categoria:** Padronização

**Definição:** o mesmo trecho de lógica (serialização, montagem de objetos, validações) é copiado em vários pontos em vez de centralizado.

**Sinais**
- Python: dicionário de campos de uma entidade montado de forma idêntica em várias funções; funções "listar todos" e "listar por usuário" com corpo quase igual; bloco de validação repetido entre criar e atualizar
- Node: blocos de `res.json({...})` idênticos em vários handlers
- Java: DTOs convertidos manualmente em vários métodos
- PHP: trechos de `while ($row = fetch())` repetidos com a mesma montagem
- Qualquer: copia-e-cola com diferença apenas no filtro

**Como confirmar:** compare os trechos suspeitos. Se a diferença é apenas um parâmetro ou filtro, é duplicação. Uma ferramenta de detecção de clones ou uma busca pelas mesmas chaves de dicionário ajuda.

**Impacto:** correções e mudanças de schema precisam ser repetidas em vários lugares, com risco de divergência.
**Transformação:** → PB-11

---

## AP-12 — Uso de APIs deprecated ou obsoletas
**Severidade:** MEDIUM (padrão; ajustável, ver abaixo) · **Categoria:** Manutenibilidade

**Definição:** o código usa funções, classes, parâmetros, bibliotecas ou configurações marcados como deprecated, removidos ou sem manutenção na versão da linguagem, do framework ou da dependência em uso, existindo um equivalente moderno.

**Sinais**
- Python: `datetime.utcnow()`, `asyncio.get_event_loop()` sem loop em execução, `imp`, `distutils`, `collections.Mapping`, `@app.before_first_request` (Flask), `flask.json.JSONEncoder`; `DeprecationWarning` ao executar com `python -W error`
- Node: `new Buffer()`, `url.parse()`, `fs.exists()`, `request` (biblioteca arquivada), `body-parser` como dependência separada no Express 4.16+
- Java: `new Integer(x)`, `Thread.stop()`, `Date` com métodos `getYear()`, classes anotadas com `@Deprecated`
- PHP: funções `mysql_*`, `each()`, `create_function()`, `magic_quotes`
- Qualquer: dependência fixada em versão antiga ou de projeto arquivado/sem release; chaves de configuração removidas na versão atual; avisos de depreciação em logs de build ou de execução

**Como confirmar:** consulte as notas de versão ou a documentação oficial da versão em uso (indicada nos arquivos de dependência). A API consta como deprecated ou removida nessa versão e existe um substituto documentado? Se sim, confirmado. A versão considerada é somente a declarada nos arquivos de dependência, de runtime, de build ou de CI do projeto; nunca infira a versão a partir do framework ou do conhecimento prévio. Se a versão não estiver declarada, ou estiver sem versão fixa, ou se a depreciação não for verificável, registre como "não confirmado" em vez de assumir. Uma API que apenas parece antiga, mas não está marcada como deprecated, não conta.

**Dependência transitiva deprecated:** antes de recomendar "atualizar a dependência", verifique se existe versão que resolve (por exemplo `npm view <pacote> dist-tags` e as dependências da versão mais nova, ou o lock). Se a versão mais nova do pacote direto ainda exige a dependência deprecated, atualizar não resolve: declare isso na recomendação e apresente as opções (substituir o pacote direto por outro, aceitar o risco registrado, ou aguardar correção do mantenedor), indicando se a dependência atua só na instalação ou também na execução. Quem decide é o usuário.

**Ajuste de severidade**

| Situação | Severidade |
|---|---|
| Só emite warning hoje, com suporte garantido | LOW |
| Será removida na próxima major, ou a biblioteca está sem manutenção | MEDIUM (padrão) |
| Já removida na versão em uso, ou bloqueia a atualização de versão | HIGH |
| Sem correções de segurança, ou recurso de segurança obsoleto (hash fraco, protocolo legado, `mysql_*`) | CRITICAL |

**Impacto:** quebra em upgrades de versão, acúmulo de dívida técnica e, em casos extremos, falhas de segurança sem correção.
**Transformação:** → PB-12

---

## AP-13 — Magic numbers, strings soltas e nomenclatura ruim
**Severidade:** LOW · **Categoria:** Legibilidade

**Definição:** (a) valores literais com significado de negócio (limites, percentuais, status, categorias, mensagens) espalhados pelo código sem nome ou constante; (b) nomes de variáveis, parâmetros e funções que não revelam o que guardam ou fazem (letras soltas, abreviações crípticas), obrigando a ler o código ao redor para entendê-los.

**Sinais**
- Python: `if faturamento > 10000: desconto = faturamento * 0.1`; listas literais de status e categorias dentro de funções; `"pendente"`, `"aprovado"` repetidos em várias camadas; variáveis de 1 ou 2 letras fora de laços (`d`, `t`, `r`, `cc`) e parâmetros `a`, `b` em funções de domínio
- Node: números e strings literais em `if`/`switch`; `let u = req.body.usr;`, `let cid = req.body.c_id;`, `let cc = req.body.card;`
- Java: ausência de `enum` ou `static final` para status; variáveis como `s`, `o`, `lst`
- PHP: literais em condições e queries; variáveis como `$d`, `$r`
- Qualquer: o mesmo literal em mais de um arquivo; faixas de valores sem comentário; abreviação que exige olhar a origem do valor para entender; o mesmo conceito com nomes diferentes em arquivos diferentes; nome que contradiz o conteúdo

**Granularidade:** reporte como achados separados (a) magic numbers e strings soltas e (b) nomenclatura ruim. Cada achado cita seus próprios arquivos e linhas.

**Como confirmar:** para os literais, pergunte "o que significa este número ou texto?". Se a resposta exige conhecer o negócio, e o valor aparece em mais de um lugar, é magic value. Para os nomes, leia a linha sem o contexto: o nome diz o que guarda (e a unidade, quando houver)? Nome de 1 ou 2 letras em escopo de mais de cerca de 10 linhas, ou que entra em regra de negócio, é achado. **Descarte:** contadores de laço (`i`, `j`, `k`), `e` ou `err` em captura de exceção, `_` para valor ignorado, convenções do framework (`req`, `res`, `next`, `db`, `cb`) e identificadores de domínio matemático (`x`, `y`).

**Impacto:** regras difíceis de localizar e alterar; risco de divergência entre os pontos de uso.
**Transformação:** → PB-13

---

## AP-14 — Logging por print e código morto
**Severidade:** LOW · **Categoria:** Legibilidade

**Definição:** uso de `print`/`console.log` como mecanismo de log e de notificação, e presença de imports, variáveis ou configurações que nunca são usados.

**Sinais**
- Python: `print("ERRO: " + str(e))` em handlers; `import os` ou `import sqlite3` sem uso; configuração definida e nunca lida (`SECRET_KEY` sem sessão)
- Node: `console.log` espalhado; `require` sem uso
- Java: `System.out.println`, imports não utilizados
- PHP: `echo`/`var_dump` em fluxo de produção
- Qualquer: log sem nível, timestamp ou contexto; mensagem de "envio" de e-mail/SMS que só imprime; colunas ou campos criados e nunca usados

**Como confirmar:** procure por `print`/`console.log` fora de scripts utilitários; rode o linter da stack (ex.: pyflakes/ruff, ESLint com `no-unused-vars`, `javac -Xlint`, PHP_CodeSniffer), quando disponível. Sem linter, busque o nome de cada import no próprio arquivo: sem uso além da linha do import, é código morto. Cite o arquivo e a linha do import. Verifique também se cada configuração ou coluna declarada é lida em algum ponto: para cada chave definida (por exemplo `app.config[...]`, `app.config.update(...)`, variável de ambiente lida), busque o ponto de leitura (`current_app.config`, `app.config[...]` em leitura, `config.<NOME>`). Chave que só é escrita é código morto, inclusive depois de uma refatoração que passou a injetar o valor por outro caminho.

**Impacto:** diagnóstico fraco em produção e ruído que confunde a leitura.
**Transformação:** → PB-14
