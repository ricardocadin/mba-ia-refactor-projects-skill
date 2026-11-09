# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

## Configuração

Variáveis de ambiente (veja `.env.example`):

| Variável | Padrão | Uso |
|---|---|---|
| `PORT` | `3000` | Porta HTTP |
| `ADMIN_TOKEN` | (vazio) | Token das rotas administrativas, enviado como `Authorization: Bearer <token>`. Sem ele, as rotas respondem 401 |
| `LOG_LEVEL` | `info` | `error`, `warn`, `info` ou `debug` |

## Estrutura (MVC)

```
src/
├── app.js            # entry point e composition root
├── config/           # env.js (variáveis de ambiente), logger.js
├── constants/        # status de pagamento, mensagens
├── routes/           # mapeamento método + caminho -> controller
├── controllers/      # leitura da requisição e resposta HTTP
├── validators/       # validação da entrada
├── services/         # regras de negócio (checkout, relatório, senha)
├── models/           # acesso a dados (SQL parametrizado) e schema
├── views/            # formato das respostas JSON
├── middlewares/      # autenticação admin, tratador global de erros
└── errors/           # AppError
```

Exemplos de requisições estão em `api.http`.
