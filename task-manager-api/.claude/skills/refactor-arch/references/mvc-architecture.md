# Arquitetura MVC (Model-View-Controller) - Documento de Referência

> **REGRAS OBRIGATÓRIAS - LEIA ANTES DE QUALQUER AÇÃO**
>
> 1. Este documento é **SOMENTE REFERÊNCIA**. Ele, por si só, **não deve alterar** nenhuma estrutura de pastas, código-fonte, dependências, configurações ou itens semelhantes em nenhum projeto.
> 2. Qualquer refatoração baseada neste documento **EXIGE a aprovação EXPLÍCITA do usuário** antes de ser executada. O agente deve **apresentar as mudanças propostas** (arquivos afetados, movimentações, novas camadas, riscos) e **aguardar a aprovação** antes de modificar qualquer coisa.
> 3. Na ausência de aprovação explícita, o agente deve limitar-se a analisar, diagnosticar e propor.

---

## Sumário

1. [Descrição](#1-descrição)
2. [Camadas](#2-camadas)
3. [Dependência](#3-dependência)
4. [Princípios que sustentam a arquitetura](#4-princípios-que-sustentam-a-arquitetura)
5. [Nomenclaturas e convenções](#5-nomenclaturas-e-convenções)
6. [Estrutura de Pastas / Diretórios](#6-estrutura-de-pastas--diretórios)
7. [Relação com anti-patterns](#7-relação-com-anti-patterns)

---

## 1. Descrição

### 1.1 O que é MVC

MVC (Model-View-Controller) é um padrão arquitetural que separa uma aplicação em três papéis com responsabilidades distintas:

| Papel | Pergunta que responde | Resumo |
|---|---|---|
| **Model** | "O que o sistema sabe e quais regras ele obedece?" | Dados, entidades e regras do domínio |
| **View** | "Como o resultado é apresentado?" | Representação da saída para o consumidor |
| **Controller** | "Quem recebe o pedido e coordena a resposta?" | Intermediário entre entrada, Model e View |

### 1.2 Origem

O padrão foi formulado por Trygve Reenskaug no fim da década de 1970, no Xerox PARC, durante o trabalho com Smalltalk, com o objetivo de aproximar o modelo mental do usuário do modelo digital existente no computador. Ao longo das décadas foi adaptado para interfaces desktop, web server-side (Rails, Django, Spring MVC, Laravel, ASP.NET MVC) e APIs. Existem muitas variações (MVP, MVVM, MVC "de servidor web"), e as interpretações diferem entre frameworks. Este documento descreve a interpretação **pragmática para aplicações web e APIs**.

### 1.3 Objetivo

- **Separar responsabilidades**: cada parte do código tem um motivo claro para existir e para mudar.
- **Facilitar manutenção e evolução**: alterar o formato da resposta não deve exigir mexer em regras de negócio, nem trocar o banco deve exigir mexer em rotas.
- **Melhorar testabilidade**: regras de negócio testáveis sem servidor HTTP e sem banco real.
- **Permitir trabalho paralelo** entre pessoas e times em camadas diferentes.
- **Reduzir duplicação** concentrando cada regra em um único lugar.

### 1.4 MVC em aplicações com interface renderizada (server-side)

```
Requisição --> Controller --> Model (dados/regras)
                   |
                   +--> View (template HTML) --> Resposta HTML
```

### 1.5 MVC em APIs REST

Em uma API REST não há template HTML. A **View** passa a ser a **camada de serialização/resposta**: a parte responsável por transformar objetos de domínio em uma representação para o cliente (geralmente JSON) e por definir o contrato de saída.

| Conceito MVC clássico | Equivalente em API REST |
|---|---|
| View (template) | Serializer, Presenter, DTO de resposta, Resource, ViewModel, schema de saída |
| Controller | Handler/endpoint que traduz HTTP em chamadas ao domínio e devolve a resposta |
| Model | Entidades, regras de domínio e (na prática) serviços e repositórios que as sustentam |
| Roteamento | Tabela de rotas que associa método + caminho a um controller |

```
Cliente HTTP
   |  (JSON/HTTP)
   v
Rotas --> Controller --> Service --> Repository --> Banco de dados
              |             |             |
              |             v             v
              |           Model <---------+
              v
   View (Serializer/DTO) --> Resposta JSON + status HTTP
```

Pontos importantes para APIs:

- O contrato de saída (campos, nomes, formatos, envelope de erro) pertence à View. O Model **não** deve ser devolvido "cru" quando isso expõe campos internos (ex.: hash de senha).
- DTOs de **entrada** (validação de payload) ficam na borda (controller/schema), antes de chegar ao domínio.
- Códigos de status HTTP são decisão da camada de apresentação (controller/View), nunca do Model ou do Repository.

---

## 2. Camadas

### 2.1 Visão geral

Na prática, MVC "puro" (3 papéis) costuma ser complementado por camadas de apoio, para evitar que o Controller ou o Model virem depósitos de código:

| Camada | Papel |
|---|---|
| Routes / Entry point | Mapear URLs e métodos HTTP para controllers; inicializar a aplicação |
| Controller | Orquestrar a requisição: ler entrada, chamar Service, escolher a resposta |
| View (Serializer/DTO) | Formatar a saída |
| Service | Regras de negócio e orquestração de casos de uso |
| Model | Entidades e invariantes do domínio |
| Repository | Acesso a dados (consultas, persistência) |
| Config | Configuração e variáveis de ambiente |
| Middlewares / Error handling | Preocupações transversais: autenticação, logging, tratamento de erros |

### 2.2 Model

**Responsabilidades**
- Representar as entidades do domínio e seus atributos.
- Garantir invariantes próprias da entidade (ex.: preço não negativo, estado válido).
- Conter comportamento intrínseco à entidade (ex.: `pedido.total()`).
- Em frameworks com ORM (Active Record), mapear a entidade para a tabela.

**Não-responsabilidades**
- Não conhecer HTTP (request, response, status, headers, sessão).
- Não formatar saída para o cliente (JSON, HTML).
- Não orquestrar casos de uso que envolvem várias entidades (isso é do Service).
- Não ler variáveis de ambiente nem abrir conexões por conta própria.

### 2.3 View (Serialização / Resposta)

**Responsabilidades**
- Converter entidades/resultados em representação de saída (JSON, XML, HTML).
- Escolher quais campos expor, nomes e formatos (datas, moeda).
- Padronizar envelopes de resposta e de erro.

**Não-responsabilidades**
- Não conter regra de negócio nem tomar decisões de domínio.
- Não acessar banco de dados nem disparar consultas (risco de N+1 por lazy loading).
- Não modificar estado do sistema.

### 2.4 Controller

**Responsabilidades**
- Receber a requisição já roteada; extrair parâmetros, corpo e identidade do chamador.
- Validar o formato da entrada (ou delegar a um schema/validator).
- Chamar **um** caso de uso no Service e traduzir o resultado em resposta HTTP (status + View).
- Traduzir exceções de domínio em respostas adequadas (diretamente ou via handler global).

**Não-responsabilidades**
- Não acessar banco de dados diretamente (sem SQL, sem ORM, sem conexão).
- Não conter regras de negócio (cálculos, decisões de domínio, políticas).
- Não montar JSON "na mão" com lógica de apresentação espalhada.
- Não instanciar suas próprias dependências concretas (use injeção).

### 2.5 Routes / Entry point

**Responsabilidades**
- Declarar rotas: método HTTP + caminho -> controller/handler.
- Agrupar rotas por recurso e versão (`/api/v1/...`).
- Ponto de entrada (`main`, `app`, `server`): criar a aplicação, registrar rotas, middlewares e dependências (composition root).

**Não-responsabilidades**
- Não conter lógica de negócio nem de acesso a dados.
- Não conter regras de validação detalhadas.

### 2.6 Service (lógica de negócio)

**Responsabilidades**
- Implementar casos de uso (ex.: "criar pedido", "aplicar desconto").
- Coordenar entidades e repositórios; definir fronteiras de transação.
- Aplicar regras que envolvem mais de uma entidade ou fonte de dados.
- Lançar exceções de domínio significativas.

**Não-responsabilidades**
- Não conhecer HTTP (nada de request/response/status code).
- Não conter SQL ou detalhes de persistência.
- Não formatar saída (JSON/HTML).

### 2.7 Repository (acesso a dados)

**Responsabilidades**
- Encapsular consultas e persistência (CRUD, buscas, paginação).
- Usar consultas parametrizadas / ORM; evitar N+1 com carregamento adequado (joins, batch).
- Isolar o restante do sistema do mecanismo de armazenamento.

**Não-responsabilidades**
- Não conter regra de negócio.
- Não conhecer HTTP.
- Não devolver detalhes de infraestrutura (cursor, row bruta) para camadas superiores quando possível.

### 2.8 Config

**Responsabilidades**
- Centralizar configuração (porta, URL do banco, chaves, flags) lida de variáveis de ambiente ou de arquivos externos ao código.
- Fornecer valores tipados e com padrões seguros para desenvolvimento.

**Não-responsabilidades**
- Não conter segredos versionados no repositório.
- Não conter lógica de negócio.

### 2.9 Middlewares e tratamento de erros

**Responsabilidades**
- Preocupações transversais: autenticação/autorização, logging de requisições, CORS, rate limiting, correlação de requisições.
- Handler global de erros: mapear exceções para respostas padronizadas e registrar logs.

**Não-responsabilidades**
- Não conter regra de negócio de um caso de uso específico.
- Não engolir exceções silenciosamente nem vazar stack traces ao cliente.

### 2.10 Tabela resumo: o que pertence / o que NÃO pertence

| Camada | Pertence aqui | NÃO deve estar aqui |
|---|---|---|
| **Routes / Entry point** | Mapeamento método+caminho -> controller; registro de middlewares; composition root | Regra de negócio, SQL, formatação de resposta |
| **Controller** | Leitura de params/body, validação de formato, chamada ao Service, escolha de status HTTP | SQL/ORM, cálculos de negócio, conexão com banco, segredos |
| **View (Serializer/DTO)** | Seleção e formatação de campos, envelope de resposta/erro | Regra de negócio, consultas, mutação de estado |
| **Service** | Casos de uso, regras entre entidades, transações, exceções de domínio | Objetos HTTP, SQL, JSON de resposta |
| **Model** | Entidades, invariantes, comportamento intrínseco | HTTP, serialização para o cliente, orquestração de casos de uso |
| **Repository** | Consultas parametrizadas, persistência, mapeamento row <-> entidade | Regras de negócio, HTTP, validação de payload |
| **Config** | Leitura de variáveis de ambiente, constantes de configuração | Segredos versionados, lógica de negócio |
| **Middlewares / Erros** | Autenticação, logging, CORS, handler global de exceções | Regras de um caso de uso, acesso direto a dados de domínio |

---

## 3. Dependência

### 3.1 Regra central

As dependências fluem **de fora para dentro**: da borda (HTTP) em direção ao domínio e aos dados. Camadas internas **não conhecem** camadas externas.

```
                +------------------------+
                |   Routes / Entry point |
                +-----------+------------+
                            |
                            v
 Middlewares -->  +---------+---------+  --> View (Serializer/DTO)
                  |    Controller     |
                  +---------+---------+
                            |
                            v
                  +---------+---------+
                  |      Service      |
                  +----+---------+----+
                       |         |
                       v         v
                 +-----+---+  +--+---------+
                 |  Model  |<-| Repository |
                 +---------+  +-----+------+
                                    |
                                    v
                              Banco de dados

 Config: lida pelo composition root e injetada onde necessário.
```

Leitura: Controller depende de Service; Service depende de Repository e Model; Repository depende de Model e do banco; Model não depende de ninguém acima dele.

### 3.2 Matriz de dependências

Linha = quem depende; coluna = de quem. `S` = permitido, `N` = proibido, `-` = não se aplica.

| Origem \ Destino | Routes | Controller | View | Service | Repository | Model | Config | Banco/IO |
|---|---|---|---|---|---|---|---|---|
| **Routes** | - | S | N | N | N | N | S | N |
| **Controller** | N | - | S | S | **N** | S (tipos/DTO) | N (injetada) | **N** |
| **View** | N | N | - | N | N | S | N | N |
| **Service** | N | N | N | - | S (via interface) | S | N (injetada) | N (via Repository) |
| **Repository** | N | N | N | N | - | S | N (injetada) | S |
| **Model** | N | N | N | N | N | - | N | N |
| **Middlewares** | N | N | N | S (ex.: auth) | N | N | S | N |

Observações:
- "N (injetada)" significa que a camada não lê a configuração por conta própria; recebe-a via construtor/parâmetro.
- Dependências de Service para Repository devem apontar para uma **abstração** (interface/contrato) quando a linguagem permitir.

### 3.3 Regras obrigatórias

1. **Controllers não acessam o banco diretamente.** Todo acesso a dados passa por Service -> Repository.
2. **Models não conhecem HTTP.** Sem request, response, status code, cookies ou sessão.
3. **Services não conhecem HTTP nem SQL.** Recebem e devolvem tipos de domínio ou DTOs simples.
4. **Repositories não contêm regras de negócio.**
5. **Views/Serializers não executam consultas** nem alteram estado.
6. **Sem dependências cíclicas** entre camadas ou módulos.
7. **Sem pular camadas** (Controller -> Repository) nem subir (Repository -> Controller).
8. **Estado compartilhado mutável global é proibido** (conexões, caches e contadores devem ser encapsulados e injetados).

### 3.4 Composition Root e Injeção de Dependências

O **composition root** é o único lugar (normalmente o entry point) onde as implementações concretas são criadas e conectadas:

```
Config --> cria conexão/pool --> cria Repository(conexão)
                                     |
                                     v
                              cria Service(repository)
                                     |
                                     v
                              cria Controller(service)
                                     |
                                     v
                              Routes registram Controller
```

Benefícios: troca de implementações sem tocar nas regras, testes com dublês (fakes/mocks), fim de `new`/instanciação espalhada e de singletons globais ocultos. A injeção pode ser manual (construtor) ou por container do framework (ex.: Spring, DI do NestJS); o princípio é o mesmo.

---

## 4. Princípios que sustentam a arquitetura

### 4.1 SOLID em MVC

| Princípio | Ideia | Como aparece em MVC |
|---|---|---|
| **S** - Single Responsibility | Um módulo tem um único motivo para mudar | Controller muda quando o contrato HTTP muda; Service quando a regra muda; Repository quando o armazenamento muda; View quando o formato de saída muda |
| **O** - Open/Closed | Aberto para extensão, fechado para modificação | Novos formatos de saída via novos serializers; novas regras via novas estratégias/serviços, sem editar controllers existentes |
| **L** - Liskov Substitution | Subtipos substituem seus tipos base sem quebrar o contrato | Um `InMemoryRepository` ou `SqlRepository` pode ser usado onde o contrato `Repository` é esperado, com o mesmo comportamento observável |
| **I** - Interface Segregation | Interfaces pequenas e específicas | Repositories por agregado (`UserRepository`, `OrderRepository`) em vez de um "DataAccess" gigante; Services focados por caso de uso/domínio |
| **D** - Dependency Inversion | Depender de abstrações, não de implementações concretas | Service depende de um contrato de Repository, injetado pelo composition root; Controller recebe o Service pronto |

### 4.2 DRY (Don't Repeat Yourself)

Cada conhecimento (regra, validação, formatação, consulta) deve ter **uma representação única**. Em MVC:
- Regra de negócio única no Service/Model, reutilizada por vários controllers.
- Serialização única por recurso na View.
- Validações comuns em schemas/validators compartilhados.
- Tratamento de erros centralizado em handler global.

Atenção: DRY trata de duplicação de **conhecimento**, não de código que apenas se parece. Abstrações prematuras têm custo.

### 4.3 Separation of Concerns (SoC)

Cada camada trata de uma preocupação: entrada/saída HTTP, regras de negócio, persistência, apresentação, configuração. Preocupações transversais (autenticação, logs, erros) ficam em middlewares, não misturadas em cada controller.

### 4.4 Arquitetura em 3 camadas e o mapeamento para MVC

| 3-Layer | Responsabilidade | Equivalente em MVC (estendido) |
|---|---|---|
| **Apresentação** | Interação com o cliente | Routes, Controller, View (Serializer/DTO), Middlewares |
| **Negócio** | Regras e casos de uso | Service, Model (entidades e invariantes) |
| **Dados** | Persistência e acesso | Repository, mapeamento ORM, banco |

```
+------------------------------------------------+
| APRESENTAÇÃO: Routes | Controller | View        |
+------------------------------------------------+
                        |
                        v
+------------------------------------------------+
| NEGÓCIO: Service | Model (regras/entidades)    |
+------------------------------------------------+
                        |
                        v
+------------------------------------------------+
| DADOS: Repository | ORM | Banco                |
+------------------------------------------------+
```

Nota: o "Model" do MVC clássico engloba, conceitualmente, negócio e dados. A separação em Service/Model/Repository é uma prática comum para manter o Model coeso e testável; ela não contradiz o MVC, apenas detalha o que o papel "Model" contém.

---

## 5. Nomenclaturas e convenções

### 5.1 Nomes por camada

Siga primeiro a convenção da linguagem/framework do projeto (snake_case, camelCase, PascalCase). Os sufixos abaixo indicam o papel.

| Camada | Classe/Módulo | Arquivo (Python) | Arquivo (Node) | Arquivo (Java) |
|---|---|---|---|---|
| Controller | `ProductController` | `product_controller.py` | `product.controller.js` ou `productController.js` | `ProductController.java` |
| Service | `ProductService` | `product_service.py` | `product.service.js` | `ProductService.java` |
| Repository | `ProductRepository` | `product_repository.py` | `product.repository.js` | `ProductRepository.java` |
| Model/Entity | `Product` | `product.py` | `product.model.js` | `Product.java` |
| View/Serializer | `ProductSerializer`, `ProductResponse` | `product_serializer.py` | `product.serializer.js` | `ProductResponse.java` (DTO) |
| Routes | - | `product_routes.py` | `product.routes.js` | (anotações no Controller ou `*Routes`) |
| Middleware | `AuthMiddleware` | `auth_middleware.py` | `auth.middleware.js` | `AuthFilter.java` |
| Exceções | `NotFoundError` | `errors.py` | `errors.js` | `NotFoundException.java` |

Mantenha **um padrão por projeto**; consistência importa mais que a escolha em si.

**Pasta da camada de dados:** nos exemplos deste documento a camada de acesso a dados aparece como `repositories/`, mas o checklist de aderência e a atividade falam em **Models**. Regra da skill: a pasta da camada de dados se chama **`models/`** (arquivos `<entidade>_model`, sem estado, com consultas parametrizadas, recebendo a conexão e sem fazer `commit`), a menos que o projeto já tenha outra convenção (por exemplo `repositories/` ou entidades ORM em `models/`), que deve ser preservada. Quando houver entidades ORM, `models/` guarda as entidades e a camada de consultas pode ficar em `repositories/`. Os nomes dos arquivos seguem o idioma do domínio do projeto (um projeto com domínio em português usa `produto_model`, não `product_model`).

### 5.2 Funções e métodos

- Use verbos que expressem a intenção: `create_order`, `findById`, `listActiveUsers`.
- Repository: `find_*`, `save`, `delete`, `exists_*` (vocabulário de dados).
- Service: verbos de negócio (`place_order`, `cancel_subscription`).
- Controller: nomes alinhados à ação HTTP (`index/list`, `show`, `create`, `update`, `destroy`).
- Booleanos: prefixos `is_`, `has_`, `can_`.

### 5.3 Exemplos curtos por linguagem

**Python**
```python
# product_repository.py
class ProductRepository:
    def __init__(self, db):
        self._db = db

    def find_by_id(self, product_id):
        return self._db.query("SELECT * FROM products WHERE id = ?", (product_id,))

# product_service.py
class ProductService:
    def __init__(self, repository):
        self._repository = repository

    def get_product(self, product_id):
        product = self._repository.find_by_id(product_id)
        if product is None:
            raise NotFoundError("Product", product_id)
        return product
```

**Node (JavaScript)**
```javascript
// product.service.js
class ProductService {
  constructor(productRepository) {
    this.productRepository = productRepository;
  }
  async getProduct(id) {
    const product = await this.productRepository.findById(id);
    if (!product) throw new NotFoundError("Product", id);
    return product;
  }
}
module.exports = { ProductService };
```

**Java**
```java
// ProductService.java
public class ProductService {
    private final ProductRepository repository;

    public ProductService(ProductRepository repository) {
        this.repository = repository;
    }

    public Product getProduct(long id) {
        return repository.findById(id)
            .orElseThrow(() -> new NotFoundException("Product", id));
    }
}
```

### 5.4 Nomenclatura de rotas

- Substantivos no **plural**, em minúsculas, com hífen para separar palavras: `/products`, `/order-items`.
- O verbo HTTP expressa a ação; evite verbos no caminho.
- Hierarquia para relações: `/users/{id}/orders`.
- Versionamento explícito: `/api/v1/...`.

| Ação | Método | Rota | Status típico |
|---|---|---|---|
| Listar | GET | `/api/v1/products` | 200 |
| Obter | GET | `/api/v1/products/{id}` | 200 / 404 |
| Criar | POST | `/api/v1/products` | 201 / 400 / 422 |
| Atualizar | PUT/PATCH | `/api/v1/products/{id}` | 200 / 404 |
| Remover | DELETE | `/api/v1/products/{id}` | 204 / 404 |

Evite: `/getProduct`, `/createProduct`, `/product/delete?id=1`.

### 5.5 Constantes e enums em vez de valores mágicos

Valores literais com significado (status, papéis, limites, taxas, tamanhos de página) devem ser constantes nomeadas ou enums, em um único lugar.

```python
# Python
class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"

MAX_PAGE_SIZE = 100
```
```javascript
// Node
const OrderStatus = Object.freeze({ PENDING: "pending", PAID: "paid" });
const MAX_PAGE_SIZE = 100;
```
```java
// Java
public enum OrderStatus { PENDING, PAID }
public static final int MAX_PAGE_SIZE = 100;
```

### 5.6 Convenções de tratamento de erros

- Definir **exceções de domínio** (`NotFoundError`, `ValidationError`, `ConflictError`, `UnauthorizedError`) lançadas por Service/Model.
- Um **handler global** mapeia exceções para status HTTP e corpo padronizado; controllers não repetem `try/catch` genérico.
- Formato de erro consistente em toda a API, por exemplo:

```json
{ "error": { "code": "PRODUCT_NOT_FOUND", "message": "Product 42 not found" } }
```

- Não vazar stack traces, SQL ou detalhes internos ao cliente; registrar-os em log.
- Nunca usar `catch` vazio ou `except: pass`.
- Validação de entrada na borda, com mensagens claras e status 400/422.

| Exceção de domínio | Status HTTP |
|---|---|
| Validação | 400 ou 422 |
| Não autenticado | 401 |
| Sem permissão | 403 |
| Não encontrado | 404 |
| Conflito | 409 |
| Erro inesperado | 500 (mensagem genérica ao cliente) |

### 5.7 Logging

Use um logger configurado (níveis, formato, destino) em vez de `print`/`console.log`/`System.out.println`. Nunca registre segredos ou dados pessoais sensíveis.

---

## 6. Estrutura de Pastas / Diretórios

### 6.1 Estrutura genérica recomendada

```
project-root/
├── src/                      # Todo o código-fonte da aplicação
│   ├── main (entry point)    # Cria a app, registra rotas/middlewares, composition root
│   ├── config/               # Leitura de variáveis de ambiente e configuração tipada
│   ├── routes/               # Mapeamento método+caminho -> controller, por recurso
│   ├── controllers/          # Orquestração HTTP: entrada -> Service -> resposta
│   ├── views/                # Serializers/Presenters/DTOs de resposta (pode ser "serializers/" ou "dto/")
│   ├── services/             # Regras de negócio e casos de uso
│   ├── models/               # Entidades e invariantes do domínio
│   ├── repositories/         # Acesso a dados (consultas, persistência)
│   ├── middlewares/          # Autenticação, logging, CORS, handler global de erros
│   ├── exceptions/           # Exceções de domínio (NotFound, Validation, ...)
│   ├── constants/            # Enums e constantes (status, papéis, limites)
│   └── utils/                # Helpers puros e sem estado, sem regra de negócio
├── tests/                    # Testes espelhando a estrutura de src/ (unit, integration)
├── migrations/               # Evolução versionada do esquema do banco (se aplicável)
├── docs/                     # Documentação adicional
├── .env.example              # Exemplo de variáveis de ambiente (sem valores secretos)
├── .gitignore                # Exclui .env, artefatos e dependências
└── README.md                 # Como instalar, configurar, executar e testar
```

Organização alternativa: **por feature/módulo** (`src/products/{controller,service,repository,model}`), útil em projetos maiores; as regras de dependência da seção 3 continuam valendo dentro e entre módulos.

Observações:
- `utils/` não deve virar depósito de lógica de negócio (risco de AP-04/AP-05).
- Em projetos pequenos, `views/` pode ser um único módulo de serializers.
- Não crie camadas vazias só por simetria; adote o que o projeto realmente precisa, mantendo as regras de dependência.

### 6.2 Variante Flask (Python)

```
app/
├── __init__.py               # Application factory (create_app) e composition root
├── config.py                 # Classes de configuração lidas do ambiente
├── routes/                   # Blueprints: product_routes.py, user_routes.py
├── controllers/              # Funções/classes chamadas pelos blueprints
├── serializers/              # Schemas de saída (ex.: marshmallow/pydantic/dataclasses)
├── services/                 # product_service.py
├── models/                   # Entidades (ex.: SQLAlchemy ou dataclasses)
├── repositories/             # product_repository.py
├── middlewares/              # before_request, autenticação
├── errors.py                 # Exceções de domínio + @app.errorhandler
└── extensions.py             # Instâncias de extensões (db, etc.) criadas sem estado de requisição
tests/
run.py                        # Entry point (app = create_app(); app.run())
```

### 6.3 Variante Express (Node)

```
src/
├── server.js                 # Sobe o servidor HTTP
├── app.js                    # Cria o Express, registra middlewares e rotas; composition root
├── config/                   # env.js (leitura/validação de variáveis)
├── routes/                   # product.routes.js (express.Router)
├── controllers/              # product.controller.js
├── serializers/              # product.serializer.js
├── services/                 # product.service.js
├── models/                   # product.model.js
├── repositories/             # product.repository.js
├── middlewares/              # auth.middleware.js, error.middleware.js
├── errors/                   # AppError, NotFoundError, ...
└── constants/                # order-status.js
tests/
```

### 6.4 Variante Java / Spring (resumo)

```
src/main/java/com/empresa/app/
├── Application.java          # Entry point
├── config/                   # Beans e propriedades
├── controller/               # @RestController
├── dto/                      # Request/Response DTOs (papel de View)
├── service/                  # @Service
├── repository/               # Interfaces de acesso a dados
├── model/                    # Entidades
├── exception/                # Exceções + @RestControllerAdvice
└── security/                 # Filtros de autenticação
```

Nota: em Spring, o container de DI exerce o papel de composition root.

---

## 7. Relação com anti-patterns

Mapeamento entre violações comuns, o catálogo de anti-patterns (`anti-patterns-catalog.md`) e a regra/princípio quebrado.

| ID | Anti-pattern | Camada/regra violada | Princípio quebrado | Direção de correção |
|---|---|---|---|---|
| **AP-01** | SQL injection por concatenação | Repository (consultas devem ser parametrizadas); Controller/Service não montam SQL | Segurança na camada de dados; SoC | Consultas parametrizadas/ORM, restritas ao Repository |
| **AP-02** | Segredos hardcoded/expostos | Config (segredos fora do código) | SoC; boas práticas de configuração | Variáveis de ambiente / cofre de segredos; `.env` fora do VCS |
| **AP-03** | Ausência de autenticação / credenciais em texto puro | Middlewares (auth), Service/Repository (hash de senha) | SoC; segurança | Middleware de auth; hash com algoritmo adequado para senhas |
| **AP-04** | God Class/Module | Qualquer camada com múltiplas responsabilidades | SRP; ISP | Dividir por responsabilidade (controller/service/repository) |
| **AP-05** | Lógica de negócio na camada errada | Controller, Routes, View ou Repository contendo regras | SRP; SoC; regra "Controller não tem regra" | Mover regras para Service/Model |
| **AP-06** | Estado global mutável | Dependências (item 3.3-8); Config/Repository | DIP; testabilidade | Encapsular e injetar; evitar variáveis globais mutáveis |
| **AP-07** | Acoplamento forte / quebra de camadas sem DI | Matriz de dependências (seção 3); composition root | DIP; OCP; LSP | Depender de abstrações; instanciar no composition root |
| **AP-08** | Transações ausentes ou sem rollback | Service (fronteira de transação, seção 2); Repository (executa as escritas sem fazer `commit` próprio) | SRP; integridade de dados (atomicidade) | Service abre a transação, agrupa as escritas e faz `commit`/`rollback`; efeitos de negócio (ex.: devolver estoque) executados dentro da mesma transação |
| **AP-09** | Consultas N+1 | Repository (estratégia de carga); View (acesso lazy ao serializar) | Separação Repository/View; desempenho | Joins/eager loading/consultas em lote no Repository |
| **AP-10** | Falta de validação / tratamento de erro genérico | Controller (validação de entrada); Middlewares (handler global) | SRP; SoC | Validação na borda; exceções de domínio + handler global |
| **AP-11** | Código duplicado | Qualquer camada | DRY | Extrair para Service/serializer/validator compartilhado |
| **AP-12** | APIs/recursos depreciados | Todas as camadas | Evolutibilidade | Migrar para a API suportada recomendada pela documentação oficial |
| **AP-13** | Números/strings mágicos | `constants/`, enums | DRY; legibilidade | Constantes nomeadas ou enums |
| **AP-14** | Logging via print / código morto | Middlewares (logging); higiene geral | SoC; manutenibilidade | Logger configurado; remover código não utilizado |

### Checklist rápido de aderência

- [ ] Nenhum controller importa driver de banco, ORM ou executa SQL.
- [ ] Nenhum Model/Service importa objetos de request/response.
- [ ] Toda consulta é parametrizada e fica em Repository.
- [ ] Dependências são criadas em um único composition root e injetadas.
- [ ] Respostas passam por View/Serializer; campos sensíveis não vazam.
- [ ] Erros são tratados por exceções de domínio + handler global.
- [ ] Segredos e configurações vêm do ambiente, não do código.
- [ ] Constantes/enums substituem valores mágicos.
- [ ] Logger configurado no lugar de `print`/`console.log`.

---

> **Lembrete final:** este documento orienta o diagnóstico e o desenho da arquitetura-alvo. **Nenhuma refatoração deve ser executada sem a aprovação explícita do usuário**, após a apresentação das mudanças propostas.
