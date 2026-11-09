# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`, refatorada para MVC.

## Como rodar

```bash
pip install -r requirements.txt

# desenvolvimento (gera uma SECRET_KEY temporária e liga o debug)
APP_DEBUG=1 python app.py

# produção: defina a chave no ambiente
SECRET_KEY="<valor-secreto>" python app.py
```

No PowerShell: `$env:APP_DEBUG="1"; python app.py`.

A aplicação sobe em `http://127.0.0.1:5000` (veja `.env.example` para `HOST`, `PORT` e demais variáveis). O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, com produtos e usuários de exemplo (senhas gravadas com hash). Bancos antigos com senha em texto puro são migrados para hash no boot.

## Autenticação

`POST /login` devolve um `token`. A rota `POST /admin/reset-db` exige o cabeçalho `Authorization: Bearer <token>` de um usuário com `tipo = admin`. A rota `/admin/query` foi removida.

## Estrutura

```
app.py                 entry point
src/
├── app.py             composition root (create_app)
├── config/            variáveis de ambiente e logging
├── constants/         status, categorias, faixas de desconto
├── exceptions/        erros de domínio
├── middlewares/       handler global de erros e autenticação
├── models/            acesso a dados (consultas parametrizadas), esquema e seed
├── services/          regras de negócio e transações
├── validators/        validação de entrada
├── controllers/       fluxo HTTP
├── views/             serialização das respostas
└── routes/            blueprints por recurso
```
