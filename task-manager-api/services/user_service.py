import logging

from exceptions.errors import ConflictError, ForbiddenError, NotFoundError, PersistenceError, UnauthorizedError
from models.transaction import transaction
from models.user import User
from validators.user_validator import validate_email_format, validate_password_length, validate_role

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, user_model, task_model, auth_service):
        self._users = user_model
        self._tasks = task_model
        self._auth = auth_service

    def list_users(self):
        """Devolve [(usuario, quantidade de tasks)] com uma unica consulta de contagem."""
        counts = self._tasks.count_by_user()
        return [(user, counts.get(user.id, (0, 0))[0]) for user in self._users.list_all()]

    def get_user(self, user_id):
        user = self._users.find_by_id(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')
        return user

    def get_user_tasks(self, user_id):
        return self._tasks.list_by_user(user_id)

    def create_user(self, fields):
        if self._users.find_by_email(fields['email']):
            raise ConflictError('Email já cadastrado')
        validate_role(fields['role'])

        user = User()
        user.name = fields['name']
        user.email = fields['email']
        user.set_password(fields['password'])
        user.role = fields['role']

        try:
            with transaction():
                self._users.add(user)
        except Exception as err:
            raise PersistenceError('Erro ao criar usuário') from err

        logger.info('Usuário criado: id=%s', user.id)
        return user

    def update_user(self, user, data):
        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            validate_email_format(data['email'])
            existing = self._users.find_by_email(data['email'])
            if existing and existing.id != user.id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']

        if 'password' in data:
            validate_password_length(data['password'], 'Senha muito curta')
            user.set_password(data['password'])

        if 'role' in data:
            validate_role(data['role'])
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        try:
            with transaction():
                pass
        except Exception as err:
            raise PersistenceError('Erro ao atualizar') from err

        return user

    def delete_user(self, user_id):
        user = self.get_user(user_id)
        try:
            with transaction():
                self._tasks.delete_by_user(user_id)
                self._users.delete(user)
        except Exception as err:
            raise PersistenceError('Erro ao deletar') from err
        logger.info('Usuário deletado: id=%s', user_id)

    def login(self, email, password):
        user = self._users.find_by_email(email)
        if not user:
            raise UnauthorizedError('Credenciais inválidas')
        if not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        if user.has_legacy_password_hash():
            self._upgrade_password_hash(user, password)

        return user, self._auth.issue_token(user)

    def _upgrade_password_hash(self, user, password):
        try:
            with transaction():
                user.set_password(password)
            logger.info('Hash de senha atualizado: user_id=%s', user.id)
        except Exception:
            logger.warning('Falha ao atualizar o hash de senha: user_id=%s', user.id, exc_info=True)
