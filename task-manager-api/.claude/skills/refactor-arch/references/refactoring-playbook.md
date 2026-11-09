# Playbook de Refatoração (PB)

Documento de referência, agnóstico de tecnologia, com um padrão de transformação para cada anti-pattern do catálogo (`anti-patterns-catalog.md`). O `PB-xx` tem sempre o mesmo número do `AP-xx`. Cada playbook traz a descrição do problema, um exemplo do uso errado, a correção alinhada à arquitetura-alvo de `mvc-architecture.md` e a forma de validar que a refatoração preservou o comportamento (ou alterou apenas o que era esperado).

Todos os exemplos são ilustrativos: os nomes de domínio (`Product`, `Order`, `User`), de rotas e de variáveis são genéricos e devem ser adaptados ao projeto auditado. Python/Flask e Node/Express aparecem em todos os playbooks; Java/Spring e PHP aparecem de forma curta quando o padrão se beneficia deles.

> Regra herdada de `mvc-architecture.md`: este documento é somente referência. Nenhuma refatoração deve ser executada sem a aprovação explícita do usuário, depois da apresentação das mudanças propostas. Itens marcados como "Decisão humana" não devem ser decididos pelo agente.

## Índice

Cada playbook segue a mesma ordem de seções: **Descrição** (problema e quando aplicar), **Problema (código)**, **Correção (código)** (camada MVC de destino e pontos de decisão humana) e **Como validar**. Localize um playbook pelo ID (`PB-XX`), que tem sempre o mesmo número do `AP-XX` do catálogo.

| PB | AP correspondente | Severidade | Camada MVC alvo |
|---|---|---|---|
| [PB-01](#pb-01--sql-injection--query-por-concatenação-ap-01) | AP-01 SQL Injection / Query por concatenação | CRITICAL | Repository |
| [PB-02](#pb-02--credenciais-e-segredos-hardcoded-ou-expostos-ap-02) | AP-02 Credenciais e segredos hardcoded ou expostos | CRITICAL | Config |
| [PB-03](#pb-03--ausência-de-autenticaçãoautorização-e-credenciais-sem-proteção-ap-03) | AP-03 Ausência de autenticação/autorização e credenciais sem proteção | CRITICAL | Middlewares + Service/Repository |
| [PB-04](#pb-04--god-class--god-module-ap-04) | AP-04 God Class / God Module | CRITICAL | Todas (divisão por responsabilidade e domínio) |
| [PB-05](#pb-05--lógica-de-negócio-fora-da-camada-correta-ap-05) | AP-05 Lógica de negócio fora da camada correta | HIGH | Service (e Model) |
| [PB-06](#pb-06--estado-global-mutável-ap-06) | AP-06 Estado global mutável | HIGH | Config + Repository (infraestrutura de dados) |
| [PB-07](#pb-07--acoplamento-forte-e-quebra-de-camadas-sem-di-ap-07) | AP-07 Acoplamento forte e quebra de camadas (sem DI) | HIGH | Routes / Entry point (composition root) + Controller |
| [PB-08](#pb-08--transações-ausentes-ou-sem-rollback-ap-08) | AP-08 Transações ausentes ou sem rollback | HIGH | Service (fronteira de transação) + Repository |
| [PB-09](#pb-09--queries-n1-ap-09) | AP-09 Queries N+1 | MEDIUM | Repository |
| [PB-10](#pb-10--validação-ausente-e-tratamento-genérico-de-erros-ap-10) | AP-10 Validação ausente e tratamento genérico de erros | MEDIUM | Controller (validação) + Middlewares (handler global) |
| [PB-11](#pb-11--código-duplicado-ap-11) | AP-11 Código duplicado | MEDIUM | View (Serializer) + Service/Validator compartilhados |
| [PB-12](#pb-12--uso-de-apis-deprecated-ou-obsoletas-ap-12) | AP-12 Uso de APIs deprecated ou obsoletas | MEDIUM (padrão; ajustável) | Todas as camadas |
| [PB-13](#pb-13--magic-numbers-strings-soltas-e-nomenclatura-ruim-ap-13) | AP-13 Magic numbers, strings soltas e nomenclatura ruim | LOW | `constants/` e nomes em todas as camadas |
| [PB-14](#pb-14--logging-por-print-e-código-morto-ap-14) | AP-14 Logging por print e código morto | LOW | Middlewares (logging) + higiene geral |

## Convenções comuns

- **Estrutura e nomes:** seguem a seção 5 e a seção 6 de `mvc-architecture.md`. Onde os exemplos abaixo dizem `repositories/` e `Repository`, a skill usa a pasta **`models/`** e arquivos `<entidade>_model` (regra de "Pasta da camada de dados" na seção 5.1 de `mvc-architecture.md`), salvo convenção existente no projeto. Pastas possíveis, conforme a seção 6 (`config/`, `routes/`, `controllers/`, `views/` ou `serializers/`, `services/`, `models/`, `repositories/`, `middlewares/`, `exceptions/`, `constants/`). Exemplos: `product_repository.py` / `product.repository.js`, `ProductService`, `ProductController`.
- **Acesso a dados nos exemplos:** Python usa a DB-API (`conn.execute(sql, params)`, da DB-API; os exemplos usam `?`, do sqlite3, e psycopg usa `%s`); Node usa um objeto `db` hipotético com `db.all(sql, params)`, `db.get(sql, params)` e `db.run(sql, params)` (equivalente a `sqlite`, `mysql2` ou `pg`). Troque pelo driver real do projeto.
- **Repositories** são sem estado, recebem a conexão/transação como primeiro argumento e nunca fazem `commit`. A transação é aberta no Service (PB-06 e PB-08).
- **Contrato externo preservado:** a refatoração mantém URLs, métodos, envelope e códigos de resposta existentes. Mudanças de contrato (versionamento de rotas, novo formato de erro) são decisão humana e só entram com aprovação. Mudanças intencionais de segurança (por exemplo, a senha deixar de ser devolvida) devem ser listadas como esperadas.
- **Baseline de comportamento (golden master):** antes de refatorar, com a aplicação original rodando em um ambiente descartável, capture as respostas dos endpoints de leitura e compare depois com `diff`.

```bash
BASE=http://localhost:PORT            # porta da aplicação auditada
mkdir -p baseline
for p in /products /products/1 /orders; do      # endpoints de leitura do projeto
  nome=$(echo "$p" | tr '/?=' '___')
  curl -s "$BASE$p" | python -m json.tool --sort-keys > "baseline/$nome.json"
done
# depois da refatoração, repita para a pasta "depois/" e compare: diff -r baseline depois
```

Campos voláteis (timestamps gerados) devem ser ignorados ou comparados sobre o mesmo banco.

---

## PB-01 — SQL Injection / Query por concatenação (AP-01)
**Descrição:** entrada externa (body, query string, header) é concatenada ou interpolada na string SQL em vez de passar por parâmetro vinculado. Viola a regra de que toda consulta é parametrizada e fica em Repository (seções 2.7 e 3.3 de `mvc-architecture.md`). Permite ler, alterar ou destruir qualquer dado. Valores que passam por conversor de tipo da rota (ex.: `<int:id>`), conversão explícita (`int()`, `float()`), validação contra lista fechada ou que vêm do próprio banco não são exploráveis (ver AP-01 em `anti-patterns-catalog.md`) e não devem ser reportados, mas podem ser parametrizados por consistência. Aplicar sempre que uma consulta receber valor de origem externa por concatenação ou interpolação.

**Problema (código)**

Python/Flask (exemplo ilustrativo):
```python
# controller ou rota: termo e categoria vêm da query string
query = "SELECT * FROM products WHERE 1=1"
if term:
    query += " AND name LIKE '%" + term + "%'"
if category:
    query += " AND category = '" + category + "'"
rows = conn.execute(query).fetchall()

# login por concatenação
conn.execute("SELECT * FROM users WHERE email = '" + email + "' AND password = '" + password + "'")
```

Node/Express (exemplo ilustrativo):
```javascript
app.get("/products", async (req, res) => {
  const rows = await db.all(`SELECT * FROM products WHERE name LIKE '%${req.query.q}%'`);
  res.json(rows);
});
```

Java/Spring: `stmt.executeQuery("SELECT * FROM users WHERE email = '" + email + "'")` com `Statement`.
PHP: `mysqli_query($conn, "SELECT * FROM users WHERE id = $id")`.

**Correção (código)**

Camada de destino: **Repository** (`repositories/`). O SQL existe somente ali, com parâmetros vinculados. Fragmentos concatenados no `WHERE` são constantes internas; os valores vão em `params`. O curinga do `LIKE` vai no valor, nunca no SQL.

Python/Flask (`repositories/product_repository.py`):
```python
class ProductRepository:
    def find_by_id(self, conn, product_id):
        row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return dict(row) if row else None

    def search(self, conn, term=None, category=None):
        query = "SELECT * FROM products WHERE 1=1"
        params = []
        if term:
            query += " AND name LIKE ?"
            params.append("%" + term + "%")
        if category:
            query += " AND category = ?"
            params.append(category)
        return [dict(r) for r in conn.execute(query, params).fetchall()]
```

Node/Express (`repositories/product.repository.js`):
```javascript
class ProductRepository {
  findById(db, id) {
    return db.get("SELECT * FROM products WHERE id = ?", [id]);
  }

  search(db, { term, category } = {}) {
    let sql = "SELECT * FROM products WHERE 1=1";
    const params = [];
    if (term) { sql += " AND name LIKE ?"; params.push(`%${term}%`); }
    if (category) { sql += " AND category = ?"; params.push(category); }
    return db.all(sql, params);
  }
}
module.exports = { ProductRepository };
```

Java/Spring: `PreparedStatement ps = conn.prepareStatement("... WHERE email = ?"); ps.setString(1, email);` (ou Spring Data com parâmetros nomeados).
PHP: `$stmt = $pdo->prepare("... WHERE id = :id"); $stmt->execute(['id' => $id]);`.

Observação para login: a consulta busca apenas por e-mail e a senha é verificada por hash no Service (PB-03); `WHERE email = ? AND password = ?` é apenas uma etapa transitória.

**Como validar**
1. Busca por padrão proibido (resultado esperado: nenhuma linha):
```bash
grep -rnE "execute\(.*(\+|%|f\"|f')" src/ app/ 2>/dev/null          # Python
grep -rnE "(query|run|all|get)\(\`.*\\$\{|(query|run|all|get)\(.*\" *\+" src/ 2>/dev/null   # Node
```
2. Teste de injeção contra um endpoint hipotético (substitua rota e campo). Antes, o filtro era ignorado ou a autenticação burlada; depois, a entrada é tratada como texto literal (lista vazia, 401 ou 400):
```bash
curl -s "http://localhost:PORT/products?q=%27%20OR%20%271%27%3D%271"
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:PORT/login \
  -H "Content-Type: application/json" -d "{\"email\":\"' OR '1'='1' --\",\"password\":\"x\"}"
```
3. Regressão: uma busca legítima devolve os mesmos resultados do baseline, e um valor com apóstrofo (`D'Angelo`) é gravado sem erro.

---

## PB-02 — Credenciais e segredos hardcoded ou expostos (AP-02)
**Descrição:** chaves, senhas, tokens, flags de debug ou caminhos sensíveis escritos no código-fonte, ou devolvidos em respostas (por exemplo, um endpoint de saúde que devolve a chave). Viola a camada Config (segredos fora do código e do repositório, seção 2.8 de `mvc-architecture.md`). Permite forjar sessões e tokens; debug ativo com bind em todas as interfaces expõe o debugger remoto. Aplicar quando houver segredo literal no código ou no versionamento, ou quando uma resposta ou log expuser segredo ou configuração interna.

**Problema (código)**

Python/Flask:
```python
app.config["SECRET_KEY"] = "literal-no-codigo"
app.config["DEBUG"] = True
app.run(host="0.0.0.0", port=5000, debug=True)

@app.get("/health")
def health():
    return jsonify({"status": "ok", "secret_key": app.config["SECRET_KEY"], "debug": True, "db_path": "app.db"})
```

Node/Express:
```javascript
const SECRET = "literal-no-codigo";
const token = jwt.sign({ id: user.id }, "literal-no-codigo");
app.get("/health", (req, res) => res.json({ status: "ok", secret: SECRET, dbPath: "./app.db" }));
```

Java/Spring: `private static final String SECRET = "...";`. PHP: `define('DB_PASS', '...');` em arquivo versionado.

**Correção (código)**

Camada de destino: **Config** (`config/`). É o único lugar que lê o ambiente; os demais módulos recebem os valores por injeção (PB-07). O repositório ganha `.env.example` (chaves sem valores) e o `.gitignore` exclui `.env`.

Python/Flask (`config/settings.py`):
```python
import os
import secrets


class Config:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        self.DEBUG = env.get("APP_DEBUG", "0") == "1"
        self.SECRET_KEY = env.get("SECRET_KEY")
        self.DATABASE_URL = env.get("DATABASE_URL", "app.db")
        self.HOST = env.get("HOST", "127.0.0.1")         # padrão seguro: apenas local
        self.PORT = int(env.get("PORT", "5000"))
        self.TOKEN_MAX_AGE = int(env.get("TOKEN_MAX_AGE", "3600"))   # segundos; validade do token (PB-03)
        self.LOG_LEVEL = env.get("LOG_LEVEL", "INFO")                # nível de log (PB-14)
        # origens permitidas pelo CORS, separadas por vírgula; vazio = nenhuma origem de navegador
        self.CORS_ORIGINS = [o.strip() for o in env.get("CORS_ORIGINS", "").split(",") if o.strip()]
        if not self.SECRET_KEY:
            if not self.DEBUG:
                raise RuntimeError("SECRET_KEY não definida no ambiente")
            # só em desenvolvimento: chave aleatória por processo, sem literal no código
            # (os tokens emitidos não sobrevivem a um reinício)
            self.SECRET_KEY = secrets.token_hex(32)
```

Node/Express (`config/env.js`):
```javascript
function loadConfig(env = process.env) {
  const config = {
    debug: env.APP_DEBUG === "1",
    secret: env.SECRET_KEY || (env.APP_DEBUG === "1" ? require("crypto").randomBytes(32).toString("hex") : undefined),
    databaseUrl: env.DATABASE_URL || "./app.db",
    host: env.HOST || "127.0.0.1",
    port: Number(env.PORT || 3000),
    tokenMaxAge: Number(env.TOKEN_MAX_AGE || 3600),   // segundos; validade do token (PB-03)
    logLevel: env.LOG_LEVEL || "info",                // nível de log (PB-14)
    corsOrigins: (env.CORS_ORIGINS || "").split(",").map((o) => o.trim()).filter(Boolean),
  };
  if (!config.secret && !config.debug) throw new Error("SECRET_KEY não definida no ambiente");
  return config;
}
module.exports = { loadConfig };
```

O endpoint de saúde devolve somente estado e contadores, nunca segredos nem configuração interna:
```python
return jsonify({"status": "ok", "database": "connected"}), 200       # Python
```
```javascript
res.json({ status: "ok", database: "connected" });                    // Node
```

Java/Spring: `@Value("${app.secret}")` lido de `application.yml` com `${APP_SECRET}`. PHP: `getenv('DB_PASS')`.

**CORS (parte c do AP-02):** a política de CORS vem da Config e lista as origens permitidas, em vez de aceitar qualquer origem.
```python
CORS(app, origins=config.CORS_ORIGINS)          # Python (flask-cors)
```
```javascript
app.use(cors({ origin: config.corsOrigins }));   // Node (pacote cors)
```
Java/Spring: `allowedOrigins(...)` com a lista da configuração. PHP: devolver `Access-Control-Allow-Origin` somente para origens da lista.

**Decisão humana:** (1) um segredo que já foi versionado ou exposto em resposta deve ser considerado comprometido; a rotação e a limpeza do histórico do VCS cabem ao usuário. (2) Onde o segredo de produção é guardado (variável do deploy, cofre). (3) Se o bind em todas as interfaces (`0.0.0.0`) é aceitável no ambiente. (4) Quais origens o CORS deve permitir e o padrão quando a lista está vazia (nenhuma origem de navegador, ou `*` só em desenvolvimento): restringir muda o que navegadores de outras origens conseguem acessar; clientes que não são navegador (curl, outros serviços) não são afetados.

**Como validar**
1. O segredo não aparece no código nem em respostas (resultado esperado: nenhuma linha):
```bash
grep -rnE "SECRET(_KEY)?\s*=\s*[\"'][^\"']+[\"']|password\s*=\s*[\"'][^\"']+[\"']" src/ app/ 2>/dev/null
curl -s http://localhost:PORT/health | grep -iE "secret|debug|db_path|password" || echo "OK: sem segredos na resposta"
```
2. Falha rápida: iniciar sem `SECRET_KEY` e sem `APP_DEBUG=1` deve abortar com mensagem clara; com a variável definida, a aplicação sobe.
3. O endpoint de saúde continua respondendo 200. A ausência dos campos sensíveis é mudança intencional de segurança.
4. `git log -S"<valor-antigo>" --oneline` mostra se o segredo está no histórico (nesse caso, rotacionar).
5. CORS: uma origem não permitida não recebe o cabeçalho, e uma permitida recebe (resultado esperado: a primeira linha imprime "OK" e a segunda mostra o cabeçalho):
```bash
curl -s -i -H "Origin: https://origem-nao-permitida.exemplo" http://localhost:PORT/ | grep -i access-control-allow-origin || echo "OK: sem cabeçalho"
curl -s -i -H "Origin: https://origem-permitida.exemplo" http://localhost:PORT/ | grep -i access-control-allow-origin
```
6. Sem literal de chave de desenvolvimento no código: o fallback de `APP_DEBUG=1` gera um valor aleatório (a busca do passo 1 continua vazia).

---

## PB-03 — Ausência de autenticação/autorização e credenciais sem proteção (AP-03)
**Descrição:** rotas sensíveis (administração, execução de SQL, remoção de dados, listagem de usuários) acessíveis sem verificar identidade ou permissão, e/ou senhas armazenadas, comparadas e devolvidas em texto puro. Viola a camada de Middlewares (autenticação/autorização, seção 2.9) e a regra de que Service/Repository usam hash adequado para senhas (seção 7 de `mvc-architecture.md`). Reporte separadamente (a) rotas sem controle de acesso e (b) senha em texto puro. Aplicar quando houver rota sensível sem verificação de identidade ou permissão, ou senha armazenada, comparada ou devolvida em texto puro.

**Problema (código)**

Python/Flask:
```python
@app.post("/admin/reset")                    # nenhuma verificação de identidade
def reset():
    conn.execute("DELETE FROM orders")
    conn.commit()
    return jsonify({"ok": True})

conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))  # texto puro
user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
return jsonify({"data": dict(user)})         # devolve inclusive o campo password
```

Node/Express:
```javascript
app.post("/admin/reset", async (req, res) => {   // sem middleware de autenticação
  await db.run("DELETE FROM orders");
  res.json({ ok: true });
});
await db.run("INSERT INTO users (email, password) VALUES (?, ?)", [email, password]);
```

Java/Spring: ausência de `@PreAuthorize`/filtro de segurança. PHP: ação destrutiva sem checar `$_SESSION`.

**Correção (código)**

Camadas de destino: **Service** (hash e verificação de senha), **Repository** (apenas persiste o hash), **Middlewares** (autenticação/autorização) e **View/Serializer** (nunca incluir o campo da senha na resposta, ver PB-11).

Python/Flask:
```python
# services/user_service.py
from werkzeug.security import check_password_hash, generate_password_hash


class UserService:
    def __init__(self, db, user_repository):
        self._db = db
        self._repo = user_repository

    def create(self, name, email, password):
        with self._db.transaction() as conn:
            return self._repo.create(conn, name, email, generate_password_hash(password))

    def authenticate(self, email, password):
        with self._db.transaction() as conn:
            user = self._repo.find_by_email(conn, email)
        if user is None or not check_password_hash(user["password"], password):
            return None
        return user
```
```python
# middlewares/auth_middleware.py (exemplo mínimo; ver decisões humanas abaixo)
# TOKEN_MAX_AGE vem da Config (PB-02) e chega ao app.config pelo composition root (PB-07)
from functools import wraps
from flask import current_app, request
from itsdangerous import BadSignature, URLSafeTimedSerializer
from exceptions.errors import ForbiddenError, UnauthorizedError


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth")


def issue_token(user):
    return _serializer().dumps({"id": user["id"], "role": user["role"]})


def require_role(role):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                raise UnauthorizedError("Token ausente")
            try:
                payload = _serializer().loads(header[7:], max_age=current_app.config["TOKEN_MAX_AGE"])
            except BadSignature:
                raise UnauthorizedError("Token inválido ou expirado")
            if payload.get("role") != role:
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)
        return wrapper
    return decorator

# routes/admin_routes.py: bp.add_url_rule("/reset", "reset", require_role("admin")(controller.reset), methods=["POST"])
```

Node/Express:
```javascript
// services/user.service.js
const bcrypt = require("bcrypt");
class UserService {
  constructor(db, userRepository) { this.db = db; this.repo = userRepository; }
  async create(name, email, password) {
    const hash = await bcrypt.hash(password, 10);
    return this.db.transaction((tx) => this.repo.create(tx, name, email, hash));
  }
  async authenticate(email, password) {
    const user = await this.db.transaction((tx) => this.repo.findByEmail(tx, email));
    if (!user || !(await bcrypt.compare(password, user.password))) return null;
    return user;
  }
}

// services/auth.service.js (emissão do token; a validade vem da Config, PB-02)
const jwt = require("jsonwebtoken");
const issueToken = (user, config) =>
  jwt.sign({ id: user.id, role: user.role }, config.secret, { expiresIn: config.tokenMaxAge });

// middlewares/auth.middleware.js (UnauthorizedError e ForbiddenError vêm de exceptions/errors)
const requireRole = (role, secret) => (req, res, next) => {
  const header = req.headers.authorization || "";
  if (!header.startsWith("Bearer ")) return next(new UnauthorizedError("Token ausente"));
  let payload;
  try {
    payload = jwt.verify(header.slice(7), secret);   // rejeita assinatura inválida e token expirado (exp)
  } catch (e) {
    return next(new UnauthorizedError("Token inválido ou expirado"));
  }
  if (payload.role !== role) return next(new ForbiddenError("Acesso negado"));
  req.user = payload;
  next();
};
// routes/admin.routes.js: router.post("/admin/reset", requireRole("admin", config.secret), controller.reset);
```

Java/Spring: `BCryptPasswordEncoder` no service e `@PreAuthorize("hasRole('ADMIN')")` no controller. PHP: `password_hash()` / `password_verify()` e um middleware que checa a sessão.

Bancos existentes com senhas em texto puro exigem uma migração de uso único (com backup): ler cada linha, e se o valor ainda não tem o prefixo do algoritmo de hash, gravar o hash. Sem ela, os usuários antigos deixam de conseguir login.

**Decisão humana (confirmar antes de aplicar):** política de autenticação (token assinado, sessão com cookie, JWT, provedor externo), formato e validade do token e refresh, quais rotas exigem autenticação além das administrativas (por exemplo, listagem de usuários), uso de papéis em outras rotas, e o destino de rotas que executam SQL arbitrário (a recomendação é removê-las; se mantidas, somente administrador e somente leitura). Os exemplos acima são um mínimo ilustrativo, não uma imposição.

**Como validar**
1. Rota protegida sem credencial, com perfil comum e com administrador (resultado esperado 401, 403, 2xx), em ambiente descartável:
```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://localhost:PORT/admin/reset
curl -s -o /dev/null -w "%{http_code}\n" -X POST -H "Authorization: Bearer $TOKEN_USUARIO_COMUM" http://localhost:PORT/admin/reset
curl -s -o /dev/null -w "%{http_code}\n" -X POST -H "Authorization: Bearer $TOKEN_ADMIN" http://localhost:PORT/admin/reset
```
2. Senha com hash e nunca devolvida:
```bash
# consulte a tabela de usuários no banco do ambiente: o valor deve começar com o prefixo do algoritmo (scrypt:, pbkdf2:, $2b$)
curl -s http://localhost:PORT/users | grep -ci '"password"'      # esperado: 0
```
3. Login com a senha correta continua funcionando e com senha errada retorna 401. Mudanças esperadas e intencionais: a resposta deixa de conter a senha, o login passa a devolver um token (campo adicional) e as rotas administrativas passam a exigir credencial.
4. Teste unitário sem HTTP: `authenticate` com repositório falso retorna `None` para senha errada e o usuário para a correta.

---

## PB-04 — God Class / God Module (AP-04)
**Descrição:** um único arquivo ou classe concentra responsabilidades de camadas e domínios distintos (rotas, SQL, regras de negócio, DDL, seed, várias entidades). Viola o SRP e a separação de camadas da seção 2 de `mvc-architecture.md`, e impede testes isolados. Sinal típico: módulo com nome genérico (`models`, `utils`, `app`) que importa o driver de banco e o framework web ao mesmo tempo. Aplicar quando um arquivo ou classe concentrar mais de uma camada ou mais de uma entidade.

**Problema (código)**

Python/Flask:
```python
# app.py (exemplo ilustrativo): rotas + SQL + regra + DDL no mesmo arquivo
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)
conn = sqlite3.connect("app.db")
conn.execute("CREATE TABLE IF NOT EXISTS products (...)")          # DDL

@app.get("/products")
def list_products():
    return jsonify([dict(r) for r in conn.execute("SELECT * FROM products")])   # SQL na rota

@app.post("/orders")
def create_order():
    ...  # regra de estoque + SQL + resposta HTTP
```

Node/Express:
```javascript
// server.js (exemplo ilustrativo)
const express = require("express");
const sqlite3 = require("sqlite3");
const db = new sqlite3.Database("app.db");
const app = express();
app.get("/products", (req, res) => db.all("SELECT * FROM products", (e, rows) => res.json(rows)));
app.post("/orders", (req, res) => { /* regra de preço + queries + resposta */ });
```

Java/Spring: classe `StoreManager` com dezenas de métodos de entidades diferentes. PHP: arquivo único com HTML, SQL e lógica.

**Correção (código)**

Camadas de destino: todas, por responsabilidade (SRP) e por domínio (uma entidade por conjunto de arquivos). Cada função é movida para a camada que a justifica, sem reescrever o comportamento; as demais PBs refinam cada arquivo.

| Responsabilidade encontrada | Camada de destino |
|---|---|
| Criação da aplicação, registro de rotas e dependências | Entry point / composition root (PB-07) |
| Mapeamento método + caminho | `routes/<recurso>_routes` |
| Leitura de entrada, escolha de status HTTP | `controllers/<recurso>_controller` |
| Regras de negócio e casos de uso | `services/<recurso>_service` |
| SQL e persistência | `repositories/<recurso>_repository` |
| Formatação de saída | `serializers/` (View) |
| DDL, migração e seed | `migrations/` ou módulo de schema, fora das rotas |
| Leitura de ambiente | `config/` |

Python/Flask (rotas só mapeiam; `routes/product_routes.py`):
```python
from flask import Blueprint


def build_product_blueprint(controller):
    bp = Blueprint("products", __name__, url_prefix="/products")
    bp.add_url_rule("", "list_products", controller.list, methods=["GET"])
    bp.add_url_rule("/<int:product_id>", "get_product", controller.get, methods=["GET"])
    bp.add_url_rule("", "create_product", controller.create, methods=["POST"])
    return bp
```

Node/Express (`routes/product.routes.js`):
```javascript
const { Router } = require("express");

function buildProductRouter(controller) {
  const router = Router();
  router.get("/products", controller.list);
  router.get("/products/:id", controller.get);
  router.post("/products", controller.create);
  return router;
}
module.exports = { buildProductRouter };
```

Ordem sugerida, um passo por vez e rodando o baseline entre eles: (1) extrair config e acesso ao banco; (2) extrair repositories movendo o SQL; (3) extrair services movendo as regras; (4) dividir controllers; (5) criar routes e o entry point; (6) remover o módulo antigo. **Decisão humana:** mudar prefixos de rota (por exemplo, `/api/v1`).

Java/Spring: separar a classe grande em `@RestController`, `@Service` e `Repository` por entidade. PHP: separar o arquivo em controller, service e classe de acesso a dados.

**Como validar**
1. Nenhum arquivo mistura framework web e driver de banco (resultado esperado: nenhuma linha):
```bash
grep -rlE "sqlite3|psycopg|mysql|pg\b" src/ | xargs -r grep -lE "flask|express"
```
2. Tamanho e coesão: nenhum arquivo concentra mais de uma entidade ou camada; o módulo genérico original foi removido.
3. Todos os endpoints originais continuam respondendo (smoke test com a lista de rotas do projeto):
```bash
for p in / /products /products/1 /orders; do
  printf "%s -> " "$p"; curl -s -o /dev/null -w "%{http_code}\n" "http://localhost:PORT$p"
done
```
4. `diff -r baseline depois` sem diferenças além das mudanças intencionais de PB-02 e PB-03.

---

## PB-05 — Lógica de negócio fora da camada correta (AP-05)
**Descrição:** regras de negócio (cálculos, políticas, transições de estado, efeitos colaterais como notificações) implementadas em Controllers ou misturadas ao acesso a dados. Viola as regras "Controller não tem regra" e "Repository não contém regra de negócio" (seções 2.4, 2.7 e 3.3 de `mvc-architecture.md`) e o SRP. A regra não pode ser testada sem HTTP e sem banco. Aplicar quando houver cálculo, política, transição de estado ou efeito colateral em Controller ou em função de acesso a dados.

**Problema (código)**

Python/Flask:
```python
# repositório calculando desconto (regra dentro do acesso a dados)
def sales_report(conn):
    revenue = conn.execute("SELECT SUM(total) FROM orders").fetchone()[0] or 0
    discount = 0
    if revenue > 10000:
        discount = revenue * 0.1
    elif revenue > 5000:
        discount = revenue * 0.05
    elif revenue > 1000:
        discount = revenue * 0.02
    return {"revenue": revenue, "discount": discount}

# controller decidindo política de notificação
def update_status(order_id):
    ...
    if new_status == "approved":
        print("NOTIFICAÇÃO: pedido aprovado")
```

Node/Express:
```javascript
app.put("/orders/:id/status", async (req, res) => {
  await db.run("UPDATE orders SET status = ? WHERE id = ?", [req.body.status, req.params.id]);
  if (req.body.status === "approved") console.log("notificar aprovação");   // regra no handler
  res.json({ ok: true });
});
```

Java/Spring: cálculo de domínio dentro do `@RestController`. PHP: controller que executa a regra e envia e-mail inline.

**Correção (código)**

Camadas de destino: **Service** (regra e orquestração de casos de uso), **Repository** (apenas dados agregados) e **Controller** (apenas HTTP). Efeitos colaterais viram um serviço próprio chamado pelo Service depois que a operação foi confirmada.

Python/Flask:
```python
# services/report_service.py
DISCOUNT_BANDS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))      # PB-13: mover para constants/


def calculate_discount(revenue):
    for threshold, rate in DISCOUNT_BANDS:
        if revenue > threshold:
            return revenue * rate
    return 0


class ReportService:
    def __init__(self, db, order_repository):
        self._db, self._orders = db, order_repository

    def sales(self):
        with self._db.transaction() as conn:
            revenue = self._orders.total_revenue(conn)           # repository só devolve o dado
        discount = calculate_discount(revenue)
        # sem arredondamento: o Service devolve o valor calculado; a View/Serializer formata (ver nota abaixo)
        return {"revenue": revenue, "discount": discount, "net": revenue - discount}

# services/notification_service.py
import logging
logger = logging.getLogger(__name__)

class NotificationService:
    def order_approved(self, order_id):
        logger.info("Pedido %s aprovado", order_id)             # integração real: decisão humana
```
```python
# controllers/report_controller.py
class ReportController:
    def __init__(self, service):
        self._service = service

    def sales(self):
        return jsonify({"data": self._service.sales()}), 200
```

Node/Express:
```javascript
// services/report.service.js
const DISCOUNT_BANDS = [[10000, 0.10], [5000, 0.05], [1000, 0.02]];      // PB-13: mover para constants/
const calculateDiscount = (revenue) => {
  const band = DISCOUNT_BANDS.find(([threshold]) => revenue > threshold);
  return band ? revenue * band[1] : 0;
};

class ReportService {
  constructor(db, orderRepository) { this.db = db; this.orders = orderRepository; }
  async sales() {
    const revenue = await this.db.transaction((tx) => this.orders.totalRevenue(tx));
    const discount = calculateDiscount(revenue);
    return { revenue, discount, net: revenue - discount };
  }
}

// controllers/report.controller.js
const sales = (service) => async (req, res, next) => {
  try { res.json({ data: await service.sales() }); } catch (e) { next(e); }
};
module.exports = { calculateDiscount, ReportService, sales };
```

**Arredondamento e formatação:** o Service devolve o valor calculado, sem arredondar. Casas decimais e formato numérico são definidos pela camada de apresentação (View/Serializer, PB-11), de acordo com a regra de negócio do produto. Se o código original arredondava a resposta, mova esse arredondamento para o serializer, preservando o contrato do endpoint.

**Decisão humana:** se um efeito de negócio hoje apenas descrito (por exemplo "devolver estoque" só impresso) deve passar a ser executado, é mudança de comportamento (ver PB-08). Também é decisão humana a integração real de e-mail, SMS ou push.

**Como validar**
1. Teste da regra sem HTTP e sem banco, incluindo as fronteiras (comparação estrita):
```python
def test_discount_bands():
    assert calculate_discount(1000) == 0
    assert calculate_discount(5000) == 5000 * 0.02
    assert calculate_discount(10000) == 10000 * 0.05
    assert calculate_discount(12000) == 12000 * 0.1
```
```javascript
test("faixas de desconto", () => {
  expect(calculateDiscount(1000)).toBe(0);
  expect(calculateDiscount(5000)).toBeCloseTo(100);
  expect(calculateDiscount(10000)).toBeCloseTo(500);
  expect(calculateDiscount(12000)).toBeCloseTo(1200);
});
```
2. Controllers sem regra (resultado esperado: nenhuma linha): `grep -rnE "discount|if .*status ==|print\(|console\.log" src/controllers/`.
3. Regressão: o endpoint de relatório devolve o mesmo JSON do baseline. Se o original arredondava, o arredondamento agora está no serializer e o JSON final permanece igual.

---

## PB-06 — Estado global mutável (AP-06)
**Descrição:** variáveis globais mutáveis (conexão, cache, configuração) compartilhadas por toda a aplicação e reatribuídas em tempo de execução, sem ciclo de vida (conexão nunca fechada), muitas vezes com contornos para problemas de concorrência (ex.: `check_same_thread=False`). Viola a regra 8 da seção 3.3 de `mvc-architecture.md` (estado compartilhado mutável global é proibido) e o DIP. Causa condições de corrida e testes dependentes de ordem. Aplicar quando houver variável global mutável (conexão, cache, configuração) reatribuída em tempo de execução.

**Problema (código)**

Python/Flask:
```python
db_connection = None

def get_db():
    global db_connection
    if db_connection is None:
        db_connection = sqlite3.connect("app.db", check_same_thread=False)   # contorna o erro de threads
    return db_connection

def list_products():
    db = get_db()          # repetido em toda função de acesso a dados
```

Node/Express:
```javascript
let db;                                   // variável de módulo reatribuída
async function init() { db = await open({ filename: "app.db" }); }
module.exports = { init, getDb: () => db };
```

Java/Spring: campo `static` mutável (singleton não thread-safe). PHP: `global $conn;`.

**Correção (código)**

Camada de destino: **Config + Repository (infraestrutura de dados)**. Uma classe encapsula o caminho/URL do banco (lido de `Config`, PB-02) e entrega uma conexão por unidade de trabalho, aberta e fechada dentro de um bloco. A instância é criada uma vez no composition root (PB-07) e injetada nos Services. Não há variável global.

Python/Flask (`repositories/database.py` ou `config/database.py`):
```python
import sqlite3
from contextlib import contextmanager


class Database:
    def __init__(self, url):
        self._url = url

    @contextmanager
    def transaction(self):
        conn = sqlite3.connect(self._url)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
```

Node/Express (`repositories/database.js`, com pool; exemplo com `pg`):
```javascript
const { Pool } = require("pg");

class Database {
  constructor(connectionString) { this.pool = new Pool({ connectionString }); }

  async transaction(work) {
    const client = await this.pool.connect();
    try {
      await client.query("BEGIN");
      const result = await work({ all: async (s, p) => (await client.query(s, p)).rows,
                                   get: async (s, p) => (await client.query(s, p)).rows[0],
                                   run: (s, p) => client.query(s, p) });
      await client.query("COMMIT");
      return result;
    } catch (e) {
      await client.query("ROLLBACK");
      throw e;
    } finally {
      client.release();
    }
  }
}
module.exports = { Database };
```

Java/Spring: `DataSource` gerenciado pelo container. PHP: objeto `PDO` passado ao construtor, em vez de `global $conn;`.

A criação de tabelas e seed sai da função que abre a conexão e roda uma vez na inicialização, em módulo próprio. **Decisão humana:** conexão por requisição (escopo de requisição) ou por unidade de trabalho (exemplo acima), e uso de pool conforme o banco real; o contrato exposto aos Services (`transaction`) é o mesmo.

**Como validar**
1. Sem estado global (resultado esperado: nenhuma linha):
```bash
grep -rnE "^\s*global |check_same_thread|^let (db|conn|connection)\b" src/ app/ 2>/dev/null
```
2. A transação é desfeita em erro e a conexão é fechada ao final:
```python
def test_rollback_e_fechamento(tmp_path):
    database = Database(str(tmp_path / "t.db"))
    with database.transaction() as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
    with pytest.raises(RuntimeError):
        with database.transaction() as conn:
            conn.execute("INSERT INTO t VALUES (1)")
            raise RuntimeError()
    with database.transaction() as conn:
        assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 0
    with pytest.raises(sqlite3.ProgrammingError):
        conn.execute("SELECT 1")
```
3. Concorrência: `ab -n 200 -c 20 http://localhost:PORT/products` (ou `autocannon`) termina sem respostas 5xx, e os endpoints respondem como no baseline.

---

## PB-07 — Acoplamento forte e quebra de camadas (sem DI) (AP-07)
**Descrição:** camadas superiores dependem de implementações concretas e pulam camadas intermediárias: controllers ou rotas importam o módulo de banco e executam SQL, ou instanciam suas próprias dependências. Viola a matriz de dependências (seção 3.2 de `mvc-architecture.md`: Controller não acessa banco nem Repository), o DIP e a regra do composition root (seção 3.4). Aplicar quando controllers ou rotas importarem o banco, executarem SQL ou instanciarem dependências concretas.

**Problema (código)**

Python/Flask:
```python
# controllers: importa a infraestrutura e executa SQL
from database import get_db
import models                       # módulo concreto, não injetado

def health():
    cursor = get_db().cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    return jsonify({"products": cursor.fetchone()[0]})
```

Node/Express:
```javascript
// controllers/health.controller.js
const db = require("../db");        // controller acoplado ao banco
exports.health = async (req, res) => res.json({ products: await db.get("SELECT COUNT(*) AS n FROM products") });
```

Java/Spring: `new ProductRepository()` dentro de serviços e controllers. PHP: `new PDO(...)` dentro do controller.

**Correção (código)**

Camadas de destino: **Routes / Entry point** (composition root: único lugar que cria as implementações concretas e as conecta) e **Controller** (recebe o Service pronto). Fluxo: `Config -> Database -> Repository -> Service -> Controller -> Routes`.

Python/Flask:
```python
# controllers/health_controller.py (sem import de banco ou repository)
class HealthController:
    def __init__(self, service):
        self._service = service

    def health(self):
        return jsonify({"status": "ok", "counts": self._service.counts()}), 200

# __init__.py (composition root)
def create_app(config=None):
    config = config or Config()
    app = Flask(__name__)
    app.config.update(SECRET_KEY=config.SECRET_KEY, TOKEN_MAX_AGE=config.TOKEN_MAX_AGE)

    database = Database(config.DATABASE_URL)
    product_repository = ProductRepository()
    product_service = ProductService(database, product_repository)
    health_service = HealthService(database, HealthRepository())

    app.register_blueprint(build_product_blueprint(ProductController(product_service)))
    app.register_blueprint(build_health_blueprint(HealthController(health_service)))
    register_error_handlers(app)
    return app
```

Node/Express:
```javascript
// app.js (composition root)
function createApp(config = loadConfig()) {
  const app = express();
  app.use(express.json());

  const db = new Database(config.databaseUrl);
  const productService = new ProductService(db, new ProductRepository());
  const healthService = new HealthService(db, new HealthRepository());

  app.use(buildProductRouter(new ProductController(productService)));
  app.use(buildHealthRouter(new HealthController(healthService)));
  app.use(errorMiddleware);
  return app;
}
module.exports = { createApp };
```

Java/Spring: injeção por construtor (`@Service`, `@Repository`); o container de DI é o composition root. PHP: injeção do `PDO` e dos serviços por construtor (ou container PSR-11).

Quando a linguagem permitir, o Service depende de um contrato do Repository (`typing.Protocol`, classe abstrata, interface), para permitir substituição (LSP/DIP).

**Como validar**
1. Controllers e routes não conhecem banco nem repositories (resultado esperado: nenhuma linha):
```bash
grep -rnE "sqlite3|psycopg|get_db|require\(.*(db|repositor)|from .*repositories|import .*Database" src/controllers src/routes
```
2. Substituição sem editar o controller, com um Service falso:
```python
def test_controller_usa_service_injetado():
    class FakeService:
        def list(self): return [{"id": 1}]
    app = Flask(__name__)
    app.register_blueprint(build_product_blueprint(ProductController(FakeService())))
    assert app.test_client().get("/products").status_code == 200
```
```javascript
test("controller usa service injetado", async () => {
  const app = express();
  app.use(buildProductRouter(new ProductController({ list: async () => [{ id: 1 }] })));
  const res = await request(app).get("/products");
  expect(res.status).toBe(200);
});
```
3. A aplicação inicia sem erro de import (sem ciclos) e o smoke test do PB-04 retorna os mesmos códigos HTTP de antes.

---

## PB-08 — Transações ausentes ou sem rollback (AP-08)
**Descrição:** uma operação de negócio composta por várias escritas dependentes (criar pedido, inserir itens, baixar estoque) não é atômica: sem fronteira de transação, sem `rollback` em falha, com `commit` isolado em cada função de dados ou só no fim, e com a pré-condição checada separada da escrita. Também entra aqui o efeito de negócio que deveria ocorrer na mesma operação (devolver estoque ao cancelar) e é apenas descrito, não executado. Viola a regra de que o Service define a fronteira de transação e o Repository não faz `commit` próprio (seções 2.6, 2.7 e 7 de `mvc-architecture.md`). Aplicar quando uma operação de negócio com duas ou mais escritas dependentes não for atômica, ou quando um efeito de negócio existir apenas em `print` ou log.

**Problema (código)**

Python/Flask:
```python
def create_order(user_id, items):
    total = sum(item["price"] * item["qty"] for item in items)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders (user_id, total) VALUES (?, ?)", (user_id, total))
    order_id = cursor.lastrowid
    for item in items:
        cursor.execute("INSERT INTO order_items (order_id, product_id, qty) VALUES (?, ?, ?)", (order_id, item["id"], item["qty"]))
        cursor.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (item["qty"], item["id"]))
    conn.commit()                   # falha no meio deixa pedido sem itens ou estoque baixado sem pedido

def cancel(order_id):
    print("pedido cancelado, devolver estoque")      # efeito de negócio só impresso
```

Node/Express:
```javascript
const total = items.reduce((sum, item) => sum + item.price * item.qty, 0);
const { lastID } = await db.run("INSERT INTO orders (user_id, total) VALUES (?, ?)", [userId, total]);
for (const item of items) {
  await db.run("INSERT INTO order_items (order_id, product_id, qty) VALUES (?, ?, ?)", [lastID, item.id, item.qty]);
  await db.run("UPDATE products SET stock = stock - ? WHERE id = ?", [item.qty, item.id]);   // sem BEGIN/ROLLBACK
}
```

Java/Spring: método de serviço com várias gravações sem `@Transactional`. PHP: várias escritas sem `beginTransaction()`/`rollBack()`.

**Correção (código)**

Camadas de destino: **Service** (abre a transação, agrupa as escritas, define `commit`/`rollback`) e **Repository** (executa as escritas, sem `commit`). A baixa de estoque vira uma escrita condicional, para checagem e escrita não ficarem separadas. Efeitos colaterais externos (notificação) ocorrem depois do commit.

Python/Flask (usa `Database.transaction()` do PB-06):
```python
# repositories/product_repository.py
def decrease_stock(self, conn, product_id, qty):
    cursor = conn.execute(
        "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?", (qty, product_id, qty))
    return cursor.rowcount == 1

# services/order_service.py
def create_order(self, user_id, items):
    with self._db.transaction() as conn:                  # commit no fim; rollback em qualquer exceção
        total, lines = 0, []
        for item in items:
            product = self._products.find_by_id(conn, item["product_id"])
            if product is None:
                raise ValidationError(f"Produto {item['product_id']} não encontrado")
            if product["stock"] < item["qty"]:
                raise ValidationError(f"Estoque insuficiente para {product['name']}")
            total += product["price"] * item["qty"]
            lines.append((product["id"], item["qty"], product["price"]))

        order_id = self._orders.create(conn, user_id, total)
        for product_id, qty, price in lines:
            self._orders.add_item(conn, order_id, product_id, qty, price)
            if not self._products.decrease_stock(conn, product_id, qty):
                raise ValidationError("Estoque alterado durante o pedido")
    self._notifications.order_created(order_id, user_id)   # somente após o commit
    return {"order_id": order_id, "total": total}
```

Node/Express (usa `Database.transaction()` do PB-06):
```javascript
// services/order.service.js
async createOrder(userId, items) {
  const result = await this.db.transaction(async (tx) => {   // BEGIN/COMMIT/ROLLBACK dentro de transaction()
    let total = 0;
    const lines = [];
    for (const item of items) {
      const product = await this.products.findById(tx, item.productId);
      if (!product) throw new ValidationError(`Produto ${item.productId} não encontrado`);
      if (product.stock < item.qty) throw new ValidationError(`Estoque insuficiente para ${product.name}`);
      total += product.price * item.qty;
      lines.push([product.id, item.qty, product.price]);
    }
    const orderId = await this.orders.create(tx, userId, total);
    for (const [productId, qty, price] of lines) {
      await this.orders.addItem(tx, orderId, productId, qty, price);
      if (!(await this.products.decreaseStock(tx, productId, qty))) throw new ValidationError("Estoque alterado durante o pedido");
    }
    return { orderId, total };
  });
  await this.notifications.orderCreated(result.orderId, userId);   // após o commit
  return result;
}
```

Node/Express (repositories com `pg`; o `Database.transaction()` do PB-06 devolve o resultado do driver, então o id vem de `RETURNING` e a contagem de linhas vem de `rowCount`):
```javascript
// repositories/order.repository.js
async create(tx, userId, total) {
  const row = await tx.get("INSERT INTO orders (user_id, total) VALUES ($1, $2) RETURNING id", [userId, total]);
  return row.id;
}

// repositories/product.repository.js
async decreaseStock(tx, productId, qty) {
  const result = await tx.run("UPDATE products SET stock = stock - $1 WHERE id = $2 AND stock >= $1", [qty, productId]);
  return result.rowCount === 1;
}
```

Java/Spring: `@Transactional` no método do `@Service` (rollback em `RuntimeException`). PHP: `$pdo->beginTransaction(); try { ...; $pdo->commit(); } catch (Throwable $e) { $pdo->rollBack(); throw $e; }`.

Operações administrativas com várias escritas (por exemplo, limpar várias tabelas) também ficam dentro de uma única transação no Service.

**Decisão humana:** executar o efeito hoje apenas descrito (devolver estoque ao cancelar) é mudança de comportamento e só deve ser aplicado com aprovação; se aplicado, deve ser feito na mesma transação e ser idempotente (não devolver duas vezes ao repetir o cancelamento). O status HTTP de erros de negócio (400 versus 404/409) deve respeitar o contrato atual.

**Como validar**
1. Teste de atomicidade: forçar falha no meio da operação e verificar que nada foi gravado.
```python
def test_rollback_quando_falha_no_meio(monkeypatch, database, order_service, order_repository):
    chamadas = {"n": 0}
    original = order_repository.add_item
    def falha_no_segundo(*a, **kw):
        chamadas["n"] += 1
        if chamadas["n"] == 2:
            raise RuntimeError("falha simulada")
        return original(*a, **kw)
    monkeypatch.setattr(order_repository, "add_item", falha_no_segundo)
    with pytest.raises(RuntimeError):
        order_service.create_order(1, [{"product_id": 1, "qty": 1}, {"product_id": 2, "qty": 1}])
    with database.transaction() as conn:
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM order_items").fetchone()[0] == 0
```
2. Nenhum Repository ou Controller faz commit (resultado esperado: nenhuma linha). O módulo de infraestrutura do PB-06 (`database.py` ou `database.js`) é o único autorizado a fazer commit e fica fora da busca: `grep -rnE "commit\(\)|COMMIT" src/repositories src/controllers --exclude="database.*"`.
3. Regressão por HTTP: pedido válido retorna o mesmo status e corpo do baseline; quantidade acima do estoque e produto inexistente retornam o mesmo erro de antes.
```bash
curl -s -X POST http://localhost:PORT/orders -H "Content-Type: application/json" \
  -d '{"user_id":1,"items":[{"product_id":1,"qty":999999}]}'
```

---

## PB-09 — Queries N+1 (AP-09)
**Descrição:** uma query inicial retorna N registros e, para cada um, é executada outra query (às vezes em dois níveis: pedido, itens, produto), em vez de um JOIN ou carga em lote. O número de queries cresce linearmente com o volume. Viola a responsabilidade do Repository de escolher a estratégia de carga (seções 2.7 e 7 de `mvc-architecture.md`). Aplicar quando o número de queries crescer com o número de registros listados.

**Problema (código)**

Python/Flask:
```python
orders = conn.execute("SELECT * FROM orders").fetchall()
for order in orders:
    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order["id"],)).fetchall()   # 1 por pedido
    for item in items:
        product = conn.execute("SELECT name FROM products WHERE id = ?", (item["product_id"],)).fetchone()  # 1 por item
```

Node/Express:
```javascript
const orders = await db.all("SELECT * FROM orders");
for (const order of orders) {
  order.items = await db.all("SELECT * FROM order_items WHERE order_id = ?", [order.id]);   // await dentro do for
}
```

Java/JPA: associação `LAZY` percorrida em loop. PHP: `mysqli_query` dentro de `foreach`.

**Correção (código)**

Camada de destino: **Repository**. Uma única query com `LEFT JOIN` (ou duas queries em lote com `IN`), agrupando em memória e preservando a ordem. A mesma função atende "todos" e "por usuário" (reduz duplicação, PB-11). `LEFT JOIN` mantém registros sem filhos.

Python/Flask (`repositories/order_repository.py`):
```python
def list_with_items(self, conn, user_id=None):
    query = """
        SELECT o.id, o.user_id, o.status, o.total,
               i.product_id, i.qty, i.unit_price, p.name AS product_name
        FROM orders o
        LEFT JOIN order_items i ON i.order_id = o.id
        LEFT JOIN products p ON p.id = i.product_id"""
    params = ()
    if user_id is not None:
        query += " WHERE o.user_id = ?"
        params = (user_id,)
    query += " ORDER BY o.id, i.id"

    orders = {}
    for row in conn.execute(query, params):
        order = orders.setdefault(row["id"], {"id": row["id"], "user_id": row["user_id"],
                                              "status": row["status"], "total": row["total"], "items": []})
        if row["product_id"] is not None:
            order["items"].append({"product_id": row["product_id"], "product_name": row["product_name"],
                                   "qty": row["qty"], "unit_price": row["unit_price"]})
    return list(orders.values())
```

Node/Express (`repositories/order.repository.js`):
```javascript
async listWithItems(db, userId) {
  let sql = `SELECT o.id, o.user_id, o.status, o.total,
                    i.product_id, i.qty, i.unit_price, p.name AS product_name
             FROM orders o
             LEFT JOIN order_items i ON i.order_id = o.id
             LEFT JOIN products p ON p.id = i.product_id`;
  const params = [];
  if (userId !== undefined) { sql += " WHERE o.user_id = ?"; params.push(userId); }
  sql += " ORDER BY o.id, i.id";

  const orders = new Map();
  for (const row of await db.all(sql, params)) {
    if (!orders.has(row.id)) orders.set(row.id, { id: row.id, user_id: row.user_id, status: row.status, total: row.total, items: [] });
    if (row.product_id !== null) orders.get(row.id).items.push({ product_id: row.product_id, product_name: row.product_name, qty: row.qty, unit_price: row.unit_price });
  }
  return [...orders.values()];
}
```

Java/JPA: `JOIN FETCH` ou `@EntityGraph`. PHP: um `JOIN` único e agrupamento em PHP.

Se o produto relacionado puder não existir e o contrato exigir um texto padrão (por exemplo "Desconhecido"), aplique-o no Repository ou no Serializer sem nova consulta.

**Como validar**
1. O número de queries independe do tamanho da listagem:
```python
def test_uma_query(conn_com_varios_pedidos):
    consultas = []
    conn_com_varios_pedidos.set_trace_callback(consultas.append)
    OrderRepository().list_with_items(conn_com_varios_pedidos)
    assert len(consultas) == 1
```
(Node: contar as chamadas de um `db` falso/espião; esperado 1 chamada.)
2. Resultado idêntico ao baseline (mesma ordem, mesmos campos, listas vazias para registros sem filhos): `diff -r baseline depois`.
3. Padrão proibido (resultado esperado: nenhuma linha): `grep -nE "for .*:\s*$" -A3 src/repositories/*.py | grep execute` e, em Node, `await` de query dentro de `for`/`map` em `src/repositories`.

---

## PB-10 — Validação ausente e tratamento genérico de erros (AP-10)
**Descrição:** entradas não são validadas (tipo, formato, existência, unicidade) de forma consistente, e as exceções são capturadas em cada handler com `catch` genérico devolvendo a mensagem interna ao cliente. Viola as responsabilidades do Controller (validar formato na borda) e dos Middlewares (handler global de erros), seções 2.4, 2.9 e 5.6 de `mvc-architecture.md`. Aplicar quando entradas não forem validadas de forma consistente ou quando exceções forem capturadas de forma genérica e devolverem detalhe interno ao cliente.

**Problema (código)**

Python/Flask:
```python
def create_product():
    try:
        data = request.get_json()
        if data["price"] < 0:                       # TypeError se price for string; data None quebra
            return jsonify({"error": "preço negativo"}), 400
        ...
    except Exception as e:
        print("ERRO: " + str(e))
        return jsonify({"error": str(e)}), 500      # vaza detalhe interno; repetido em todo handler

def update_product(id):                             # sem as validações do create
    data = request.get_json()
    ...
```

Node/Express:
```javascript
app.post("/products", async (req, res) => {
  try {
    if (req.body.price < 0) return res.status(400).send("preço negativo");
    ...
  } catch (e) {
    res.status(500).send(e.message);                // vaza detalhe interno
  }
});
```

Java/Spring: `catch (Exception e)` retornando `e.getMessage()`. PHP: `die(mysqli_error($conn))`.

**Correção (código)**

Camadas de destino: **Controller** (validação de formato na borda, via validator compartilhado), **exceptions/** (exceções de domínio) e **Middlewares** (handler global que mapeia exceção para status HTTP, registra o detalhe no log e devolve mensagem genérica em erro inesperado).

Python/Flask:
```python
# exceptions/errors.py
class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ValidationError(AppError):   status_code, code = 400, "VALIDATION_ERROR"
class UnauthorizedError(AppError): status_code, code = 401, "UNAUTHORIZED"
class ForbiddenError(AppError):    status_code, code = 403, "FORBIDDEN"
class NotFoundError(AppError):     status_code, code = 404, "NOT_FOUND"
class ConflictError(AppError):     status_code, code = 409, "CONFLICT"

# middlewares/error_middleware.py
import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException
logger = logging.getLogger(__name__)

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": {"code": err.code, "message": err.message}}), err.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            return err
        logger.exception("Erro não tratado")        # detalhe só no log
        return jsonify({"error": {"code": "INTERNAL_ERROR", "message": "Erro interno do servidor"}}), 500

# validators/product_validator.py (reutilizado por create e update)
def validate_product(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")
    for field in ("name", "price"):
        if field not in data:
            raise ValidationError(f"{field} é obrigatório")
    if isinstance(data["price"], bool) or not isinstance(data["price"], (int, float)):
        raise ValidationError("price deve ser numérico")
    if data["price"] < 0:
        raise ValidationError("price não pode ser negativo")
    return data

# controllers/product_controller.py (sem try/except)
def create(self):
    data = validate_product(request.get_json(silent=True))
    return jsonify({"data": {"id": self._service.create(**data)}}), 201
```

Node/Express:
```javascript
// exceptions/errors.js
class AppError extends Error { constructor(message, status, code) { super(message); this.status = status; this.code = code; } }
class ValidationError extends AppError { constructor(m) { super(m, 400, "VALIDATION_ERROR"); } }
class NotFoundError extends AppError { constructor(m) { super(m, 404, "NOT_FOUND"); } }

// middlewares/error.middleware.js (registrado por último)
const errorMiddleware = (err, req, res, next) => {
  if (err instanceof AppError) return res.status(err.status).json({ error: { code: err.code, message: err.message } });
  logger.error({ err }, "Erro não tratado");               // detalhe só no log
  res.status(500).json({ error: { code: "INTERNAL_ERROR", message: "Erro interno do servidor" } });
};

// validators/product.validator.js
function validateProduct(body) {
  if (!body || typeof body !== "object") throw new ValidationError("Dados inválidos");
  if (typeof body.price !== "number" || Number.isNaN(body.price)) throw new ValidationError("price deve ser numérico");
  if (body.price < 0) throw new ValidationError("price não pode ser negativo");
  return body;
}

// controllers/product.controller.js (Express 5 repassa erros assíncronos; no Express 4 use um wrapper asyncHandler)
create = async (req, res) => {
  const data = validateProduct(req.body);
  res.status(201).json({ data: { id: await this.service.create(data) } });
};
```

Java/Spring: `@RestControllerAdvice` com `@ExceptionHandler`. PHP: `set_exception_handler` central.

**Decisão humana:** (a) unicidade de campos como e-mail: se adotada, o Service lança `ConflictError` (409), mas bancos existentes podem ter duplicatas; (b) alinhar a validação de atualização à de criação é mudança intencional se hoje o update aceita entradas que o create rejeita; (c) respostas para recurso inexistente (404 em vez de sucesso silencioso); (d) formato do corpo de erro: os exemplos adotam o envelope `{"error": {"code", "message"}}` da seção 5.6 de `mvc-architecture.md`. Se o contrato atual dos clientes for `{"error": "<mensagem>"}`, a troca é mudança intencional de formato: declare-a no relatório (AP-10) e confirme com o usuário antes da Fase 3.

**Como validar**
1. Entradas inválidas retornam 4xx com mensagem clara, não 500 com texto de exceção (endpoint hipotético):
```bash
curl -s -w " [%{http_code}]\n" -X POST http://localhost:PORT/products -H "Content-Type: application/json" -d '{"name":"x","price":"abc"}'
curl -s -w " [%{http_code}]\n" -X POST http://localhost:PORT/products                       # corpo ausente
curl -s -w " [%{http_code}]\n" -X PUT  http://localhost:PORT/products/999999 -H "Content-Type: application/json" -d '{"name":"x","price":1}'
# esperado: 400, 400 e 404, com corpo {"error": {"code": "...", "message": "..."}}
```
2. Nenhum detalhe interno vaza (resultado esperado: nenhuma linha): `grep -rnE "str\(e\)|e\.message|getMessage\(\)" src/controllers` e `grep -rnE "except Exception|catch \(" src/controllers`.
3. Erro inesperado: simule uma exceção no Service (monkeypatch/mock) e verifique que a resposta tem apenas a mensagem genérica com status 500 e que o stack trace foi para o log.
4. Regressão: requisições válidas mantêm status e corpo do baseline.

---

## PB-11 — Código duplicado (AP-11)
**Descrição:** o mesmo trecho de lógica (montagem do dicionário de uma entidade, listagens quase idênticas, validações repetidas entre criar e atualizar) é copiado em vários pontos. Viola o DRY (seção 4.2 de `mvc-architecture.md`): uma mudança de schema precisa ser replicada em todos os lugares, com risco de divergência. A formatação de saída pertence à View (Serializer). Aplicar quando o mesmo trecho de montagem, listagem ou validação aparecer em mais de um ponto e a diferença couber em um parâmetro.

**Problema (código)**

Python/Flask:
```python
# o mesmo dicionário, copiado em três funções de acesso a dados
result.append({"id": row["id"], "name": row["name"], "price": row["price"], "created_at": row["created_at"]})

# listar todos e listar por usuário: corpo igual, muda só o WHERE
def list_orders(conn): ...
def list_orders_by_user(conn, user_id): ...
```

Node/Express:
```javascript
res.json({ id: p.id, name: p.name, price: p.price, createdAt: p.created_at });   // repetido em vários handlers
```

Java/Spring: DTOs convertidos manualmente em vários métodos. PHP: `while ($row = fetch())` repetido com a mesma montagem.

**Correção (código)**

Camada de destino: **View (Serializer)** para a formatação, **Validator/Service** para validações e regras compartilhadas, e uma função de Repository parametrizada para listagens que diferem só no filtro. Os serializers selecionam e formatam campos; não consultam o banco nem têm regra.

Python/Flask (`serializers/product_serializer.py`):
```python
def product_to_dict(product):
    return {"id": product["id"], "name": product["name"],
            "price": product["price"], "created_at": product["created_at"]}


def products_to_list(products):
    return [product_to_dict(p) for p in products]
```
```python
# controller: um ponto de formatação por recurso
return jsonify({"data": products_to_list(self._service.list())}), 200
```

Node/Express (`serializers/product.serializer.js`):
```javascript
const productToDto = (p) => ({ id: p.id, name: p.name, price: p.price, createdAt: p.created_at });
const productsToList = (list) => list.map(productToDto);
module.exports = { productToDto, productsToList };

// controller
res.json({ data: productsToList(await this.service.list()) });
```

Listagens que diferem só no filtro viram uma função com parâmetro opcional (ver `list_with_items(conn, user_id=None)` no PB-09). Validações repetidas entre criar e atualizar viram um validator único (PB-10). Campos sensíveis (hash de senha) nunca entram no serializer (PB-03). Atenção: DRY trata de duplicação de conhecimento; trechos que apenas se parecem não precisam ser unificados.

Java/Spring: um mapper único Entity para DTO (MapStruct ou método estático). PHP: uma função `serializeProduct($row)`.

**Como validar**
1. A montagem existe uma única vez (esperado: uma ocorrência por chave, dentro de `serializers/`):
```bash
grep -rn '"created_at": ' src/ | grep -v serializers || echo "OK: montagem só nos serializers"
```
2. Regressão: `diff -r baseline depois` sem diferenças (exceto mudanças intencionais de PB-03, como a ausência da senha).
3. Teste do contrato de saída: o serializer devolve exatamente o conjunto de campos esperado.
```python
def test_product_to_dict_campos():
    row = {k: None for k in ("id", "name", "price", "created_at")}
    assert set(product_to_dict(row)) == set(row)
```

---

## PB-12 — Uso de APIs deprecated ou obsoletas (AP-12)
**Descrição:** o código usa funções, classes, parâmetros ou bibliotecas marcados como deprecated, removidos ou sem manutenção na versão em uso, existindo um equivalente moderno. Viola a evolutibilidade (seção 7 de `mvc-architecture.md`) e quebra em upgrades. A severidade segue a tabela de ajuste do catálogo. Aplicar somente quando a versão declarada nos arquivos de dependência (`requirements.txt`, `package.json`, `pom.xml`, `composer.json`) comprovar a depreciação ou a remoção e existir substituto documentado. Sem versão fixa ou sem verificação, registrar "não confirmado" e não aplicar. Os exemplos abaixo são genéricos e ilustrativos, e não representam achado de nenhum projeto específico.

**Problema (código)**

Python/Flask:
```python
from datetime import datetime
created_at = datetime.utcnow()            # deprecated desde o Python 3.12

@app.before_first_request                 # removido no Flask 2.3
def init():
    init_db()
```

Node/Express:
```javascript
const buf = new Buffer("texto");          // deprecated: usar Buffer.from
require("fs").exists(filePath, (ok) => {});    // deprecated: usar fs.promises.access
const bodyParser = require("body-parser");     // desnecessário no Express 4.16+
app.use(bodyParser.json());
```

Java: `new Integer(x)`. PHP: `mysql_connect()` (removido no PHP 7).

**Correção (código)**

Camada de destino: a mesma em que o uso aparece (Service, Repository, entry point). Substituição pelo equivalente documentado.

Python/Flask:
```python
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)   # datetime "aware": isoformat() passa a incluir "+00:00"

def create_app(config=None):
    ...
    init_db(database)                     # inicialização explícita no composition root (PB-07)
```

Node/Express:
```javascript
const buf = Buffer.from("texto");
const ok = await require("fs").promises.access(filePath).then(() => true, () => false);
app.use(express.json());                  // sem dependência extra
```

Java: `Integer.valueOf(x)`. PHP: PDO ou `mysqli` com prepared statements.

**Item "não confirmado" não é alterado.** Se a depreciação não foi confirmada pela versão declarada (por exemplo, `Model.query.get()` sem o SQLAlchemy pinado, ou `datetime.utcnow()` sem versão do Python), a substituição não é aplicada, mesmo que pareça inofensiva e devolva o mesmo resultado. Só se aplica com a versão confirmada ou com decisão explícita do usuário, e então entra em `Intentional changes`.

**Decisão humana:** atualizar a versão fixada de uma dependência e aceitar mudanças visíveis ao cliente (por exemplo, o formato de um timestamp serializado) são decisões do usuário.

**Como validar**
1. Promova avisos de depreciação a erro ao importar a aplicação e ao rodar os testes (resultado esperado: nenhum aviso):
```bash
python -W error::DeprecationWarning -c "from app import create_app; create_app()"
python -W error::DeprecationWarning -m pytest -q
node --throw-deprecation src/server.js        # ou: NODE_OPTIONS=--throw-deprecation npm test
```
2. Busca do padrão antigo (resultado esperado: nenhuma linha): `grep -rnE "utcnow\(|before_first_request|new Buffer\(|fs\.exists\(" src/`.
3. Confirme a versão declarada antes de afirmar a depreciação (por exemplo `grep -iE "^flask" requirements.txt` ou a chave `dependencies` do `package.json`). Sem versão fixa, o achado fica como "não confirmado".
4. Os endpoints respondem como no baseline.

---

## PB-13 — Magic numbers, strings soltas e nomenclatura ruim (AP-13)
**Descrição:** valores literais com significado de negócio (status, categorias, faixas e percentuais, limites de tamanho, versão) espalhados e repetidos, sem nome. Viola o DRY e a legibilidade (seção 5.5 de `mvc-architecture.md`: constantes e enums em vez de valores mágicos). Mudar uma regra exige caçar literais em vários arquivos e camadas. Aplicar quando o mesmo literal com significado de negócio aparecer em mais de um arquivo ou camada.

**Problema (código)**

Python/Flask:
```python
if new_status not in ["pending", "approved", "shipped", "cancelled"]:     # lista literal na função
    ...
valid_categories = ["books", "toys", "general"]                           # outra lista literal
conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")      # mesmo literal em outra camada
if revenue > 10000:
    discount = revenue * 0.1
elif revenue > 5000:
    discount = revenue * 0.05
elif revenue > 1000:
    discount = revenue * 0.02
if len(name) < 2 or len(name) > 200:
    ...
```

Node/Express:
```javascript
if (!["pending", "approved", "shipped", "cancelled"].includes(status)) { ... }
if (revenue > 10000) discount = revenue * 0.1;
else if (revenue > 5000) discount = revenue * 0.05;
else if (revenue > 1000) discount = revenue * 0.02;
```

Java: ausência de `enum` ou `static final`. PHP: literais em condições e queries.

**Correção (código)**

Camada de destino: **`constants/`** (seção 6 de `mvc-architecture.md`), um único local por valor. Enums para conjuntos fechados, constantes nomeadas para limites e taxas.

Python/Flask (`constants/order.py` e `constants/product.py`):
```python
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"


ORDER_STATUSES = tuple(s.value for s in OrderStatus)
DISCOUNT_BANDS = ((10000, 0.10), (5000, 0.05), (1000, 0.02))     # (limite exclusivo, taxa)

VALID_CATEGORIES = ("books", "toys", "general")
NAME_MIN_LEN = 2
NAME_MAX_LEN = 200
```
```python
# uso: o status vai como parâmetro vinculado, usando .value (não literal no SQL)
conn.execute("SELECT COUNT(*) FROM orders WHERE status = ?", (OrderStatus.PENDING.value,))
if new_status not in ORDER_STATUSES:
    raise ValidationError("Status inválido")
```

Node/Express (`constants/order.js`):
```javascript
const OrderStatus = Object.freeze({ PENDING: "pending", APPROVED: "approved", SHIPPED: "shipped", CANCELLED: "cancelled" });
const ORDER_STATUSES = Object.values(OrderStatus);
const DISCOUNT_BANDS = [[10000, 0.10], [5000, 0.05], [1000, 0.02]];
const NAME_MIN_LEN = 2;
const NAME_MAX_LEN = 200;
module.exports = { OrderStatus, ORDER_STATUSES, DISCOUNT_BANDS, NAME_MIN_LEN, NAME_MAX_LEN };

// uso
if (!ORDER_STATUSES.includes(status)) throw new ValidationError("Status inválido");
```

Java: `public enum OrderStatus { PENDING, APPROVED }` e `public static final int NAME_MAX_LEN = 200;`. PHP: constantes de classe (`const STATUS_PENDING = 'pending';`).

Mensagens que listam valores (por exemplo, "Válidas: [...]") devem ser geradas a partir da constante mantendo o texto original. Literais de DDL (`DEFAULT 'pending'`) fazem parte do esquema e podem permanecer, com comentário apontando para a constante. **Decisão humana:** se faixas e taxas de negócio passam a ser configuráveis (ambiente ou tabela) em vez de constantes.

**Nomenclatura (parte b do AP-13)**

Renomeie variáveis locais, parâmetros e funções internas para nomes que revelem o conteúdo, no idioma do domínio do projeto. **Nunca renomeie o que faz parte de um contrato externo:** chaves de corpo JSON, parâmetros de query, cabeçalhos, rotas, colunas do banco e nomes exportados que outros sistemas consomem. Só o identificador local muda; a chave do contrato continua a mesma.

Node/Express:
```javascript
// antes
let u = req.body.usr;
let cid = req.body.c_id;
let cc = req.body.card;

// depois: o contrato do corpo (usr, c_id, card) não muda, só as variáveis locais
const userName = req.body.usr;
const courseId = req.body.c_id;
const cardNumber = req.body.card;
```

Python/Flask:
```python
# antes
def calc(d, t):
    r = d * t
    return r

# depois
def calculate_total(unit_price, quantity):
    return unit_price * quantity
```

Faça a renomeação junto da extração de cada camada (ou como último bloco), com a aplicação funcionando antes e depois. Não renomeie o que a convenção do framework ou da linguagem já consagra (`req`, `res`, `next`, `db`, `cb`, `i`, `e` em captura de exceção).

**Como validar**
1. Os literais existem só em `constants/` e no DDL (resultado esperado: nenhuma linha fora desses lugares):
```bash
grep -rnE "\"(pending|approved|shipped|cancelled)\"|'(pending|approved|shipped|cancelled)'" src/ \
  | grep -vE "constants/|schema|migrations" || echo "OK: sem status solto"
```
2. Mesmos valores aceitos e mesma mensagem de erro de antes (endpoint hipotético):
```bash
for s in pending approved shipped cancelled; do
  curl -s -o /dev/null -w "$s -> %{http_code}\n" -X PUT http://localhost:PORT/orders/1/status \
    -H "Content-Type: application/json" -d "{\"status\":\"$s\"}"
done                                              # esperado: 2xx para todos
curl -s -w " [%{http_code}]\n" -X PUT http://localhost:PORT/orders/1/status -H "Content-Type: application/json" -d '{"status":"x"}'   # esperado: 400
```
3. Testes de fronteira da regra (por exemplo, descontos do PB-05) continuam passando usando as constantes; respostas iguais ao baseline.
4. Nomenclatura: nenhuma variável de 1 ou 2 letras fora das exceções (resultado esperado: nenhuma linha). Exemplos: `grep -rnE "\b(let|const|var)\s+[a-z]{1,2}\b" src/` (Node) e `grep -rnE "^\s*[a-z]{1,2}\s*=[^=]" src/ app/` (Python), descartando contadores de laço e `e`/`err`. As respostas continuam iguais ao baseline, porque renomear identificadores locais não altera nenhum contrato.

---

## PB-14 — Logging por print e código morto (AP-14)
**Descrição:** `print`/`console.log` usados como mecanismo de log e de notificação, sem nível, timestamp ou contexto, além de imports, variáveis e configurações que nunca são usados. Viola a convenção de logging configurado (seção 5.7 de `mvc-architecture.md`) e a higiene de manutenção. Dificulta o diagnóstico em produção e adiciona ruído à leitura. Aplicar quando houver `print`/`console.log` usado como log ou notificação, ou imports, variáveis ou configurações sem uso.

**Problema (código)**

Python/Flask:
```python
import os                                     # nunca usado
import sqlite3                                # nunca usado neste arquivo

def create_user():
    try:
        ...
        print("Usuário criado: " + email)     # sem nível, com dado pessoal
        ...
    except Exception as e:
        print("ERRO: " + str(e))

app.config["SOME_SETTING"] = "x"              # definida e nunca lida
```

Node/Express:
```javascript
const fs = require("fs");                     // sem uso
console.log("Usuário criado: " + email);
console.log("Servidor iniciado");
```

Java: `System.out.println` e imports não utilizados. PHP: `echo`/`var_dump` em fluxo de produção.

**Correção (código)**

Camada de destino: **Middlewares/logging** (configuração central) com uso por módulo em Controllers e Services; remoção de código morto em qualquer camada. Use formatação tardia (argumentos do logger, não concatenação), níveis adequados e nenhum dado sensível (senha, token, dado pessoal) nas mensagens.

Python/Flask:
```python
# config/logging_config.py
import logging

def configure_logging(level="INFO"):
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# no composition root: configure_logging(config.LOG_LEVEL)   # LOG_LEVEL vem do ambiente (PB-02)

# uso em services/controllers
import logging
logger = logging.getLogger(__name__)

logger.info("Usuário criado: id=%s", user_id)       # id, não e-mail
logger.warning("Tentativa de login falhou")
# erros inesperados: o handler global (PB-10) usa logger.exception(...)
```

Node/Express (exemplo com `pino`; `winston` é equivalente):
```javascript
// config/logger.js (o nível vem da Config, PB-02; o módulo não lê o ambiente)
const pino = require("pino");
const createLogger = (config) => pino({ level: config.logLevel });
module.exports = { createLogger };

// composition root (PB-07): const logger = createLogger(config);  e o logger é injetado em services e middlewares

// uso (logger recebido por injeção)
logger.info({ userId }, "Usuário criado");
logger.warn("Tentativa de login falhou");
```

Java: SLF4J (`private static final Logger log = LoggerFactory.getLogger(X.class);`). PHP: `monolog` ou `error_log()`.

Código morto: remover imports sem uso, variáveis e configurações nunca lidas, e mensagens de "envio" que apenas imprimem. Antes de remover uma configuração, confirme que ela não é usada em outra camada (por exemplo, uma chave usada para assinar tokens após PB-03).

**Decisão humana:** destino dos logs (stdout, arquivo, JSON, agregador) e nível por ambiente; se mensagens de "envio" de e-mail/SMS/push serão mantidas como log, removidas ou substituídas por integração real; se dados pessoais podem aparecer em logs.

**Como validar**
1. Nenhum `print`/`console.log` fora de scripts utilitários (resultado esperado: nenhuma linha):
```bash
grep -rnE "^\s*print\(|console\.log\(" src/ app/ 2>/dev/null
```
2. Linter de código morto (resultado esperado: sem avisos de import/variável não usados):
```bash
python -m pyflakes src/        # ou: ruff check --select F401,F841 src/
npx eslint --rule '{"no-unused-vars":"error"}' src/
```
3. O log tem nível, data e contexto: suba a aplicação com `LOG_LEVEL=INFO`, chame um endpoint e confira o formato da linha emitida.
4. Nenhum dado sensível nos logs: execute login e criação de usuário e verifique que senha, token e e-mail não aparecem (`grep -iE "password|senha|token" <saída de log>`).
5. Os endpoints respondem como no baseline; remover `print` e código morto não altera nenhuma resposta HTTP.
