"""Script para popular o banco com dados iniciais"""
from app import create_app
from constants.task import STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING
from constants.user import ROLE_ADMIN, ROLE_MANAGER, ROLE_USER
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import datetime, timedelta

def seed_data():
    app = create_app()
    with app.app_context():

        Task.query.delete()
        User.query.delete()
        Category.query.delete()
        db.session.commit()

        u1 = User()
        u1.name = 'João Silva'
        u1.email = 'joao@email.com'
        u1.set_password('1234')
        u1.role = ROLE_ADMIN
        db.session.add(u1)

        u2 = User()
        u2.name = 'Maria Santos'
        u2.email = 'maria@email.com'
        u2.set_password('abcd')
        u2.role = ROLE_USER
        db.session.add(u2)

        u3 = User()
        u3.name = 'Pedro Oliveira'
        u3.email = 'pedro@email.com'
        u3.set_password('pass')
        u3.role = ROLE_MANAGER
        db.session.add(u3)

        db.session.commit()

        c1 = Category()
        c1.name = 'Backend'
        c1.description = 'Tarefas de backend'
        c1.color = '#3498db'
        db.session.add(c1)

        c2 = Category()
        c2.name = 'Frontend'
        c2.description = 'Tarefas de frontend'
        c2.color = '#2ecc71'
        db.session.add(c2)

        c3 = Category()
        c3.name = 'DevOps'
        c3.description = 'Tarefas de infraestrutura'
        c3.color = '#e74c3c'
        db.session.add(c3)

        c4 = Category()
        c4.name = 'Bug'
        c4.description = 'Correção de bugs'
        c4.color = '#e67e22'
        db.session.add(c4)

        db.session.commit()

        tasks_data = [
            {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': STATUS_PENDING, 'priority': 1, 'user_id': u1.id, 'category_id': c1.id, 'due_date': datetime.utcnow() - timedelta(days=3)},
            {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': STATUS_IN_PROGRESS, 'priority': 2, 'user_id': u2.id, 'category_id': c2.id, 'due_date': datetime.utcnow() + timedelta(days=5)},
            {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': STATUS_DONE, 'priority': 2, 'user_id': u3.id, 'category_id': c3.id, 'tags': 'devops,ci,github'},
            {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': STATUS_PENDING, 'priority': 1, 'user_id': u1.id, 'category_id': c4.id, 'due_date': datetime.utcnow() - timedelta(days=1)},
            {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': STATUS_PENDING, 'priority': 3, 'user_id': u1.id, 'category_id': c1.id, 'due_date': datetime.utcnow() + timedelta(days=10)},
            {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': STATUS_PENDING, 'priority': 2, 'user_id': u2.id, 'category_id': c1.id},
            {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': STATUS_CANCELLED, 'priority': 4, 'user_id': u3.id, 'category_id': c1.id},
            {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': STATUS_IN_PROGRESS, 'priority': 3, 'user_id': u2.id, 'category_id': c1.id, 'tags': 'refactor,tech-debt'},
            {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': STATUS_PENDING, 'priority': 4, 'user_id': u3.id, 'category_id': c3.id, 'due_date': datetime.utcnow() + timedelta(days=20)},
            {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': STATUS_PENDING, 'priority': 3, 'user_id': u1.id, 'category_id': c1.id, 'tags': 'improvement,validation'},
        ]

        for td in tasks_data:
            t = Task()
            t.title = td['title']
            t.description = td['description']
            t.status = td['status']
            t.priority = td['priority']
            t.user_id = td['user_id']
            t.category_id = td['category_id']
            if 'due_date' in td:
                t.due_date = td['due_date']
            if 'tags' in td:
                t.tags = td['tags']
            db.session.add(t)

        db.session.commit()
        print("Seed concluído com sucesso!")
        print(f"  {User.query.count()} usuários")
        print(f"  {Category.query.count()} categorias")
        print(f"  {Task.query.count()} tasks")

if __name__ == '__main__':
    seed_data()
