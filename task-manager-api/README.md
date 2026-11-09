# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Após a refatoração, segue o padrão MVC: `config/`, `routes/`, `controllers/`, `views/`, `services/`, `models/`, `validators/`, `middlewares/`, `exceptions/` e `constants/`, com `app.py` como composition root.

## Como rodar

```bash
pip install -r requirements.txt
cp .env.example .env        # defina SECRET_KEY (ou use APP_DEBUG=1 em desenvolvimento)
python seed.py
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000` (o padrão é só local e sem debug; ajuste `HOST`, `PORT` e `APP_DEBUG` no `.env`; o CORS não aceita nenhuma origem de navegador por padrão, liste as permitidas em `CORS_ORIGINS`). O `seed.py` popula o banco SQLite (`instance/tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Autenticação

`POST /login` devolve um token assinado. As rotas `DELETE /tasks/<id>` e `DELETE /categories/<id>` exigem `Authorization: Bearer <token>`; `PUT /users/<id>` e `DELETE /users/<id>` exigem token de um usuário `admin`. As demais rotas continuam abertas.
