"""Casos de uso de usuários: cadastro com hash de senha e autenticação."""
import logging

from werkzeug.security import check_password_hash, generate_password_hash

from src.constants.usuario import TIPO_CLIENTE
from src.exceptions.errors import ConflictError

logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, database, usuario_model):
        self._db = database
        self._model = usuario_model

    def listar(self):
        with self._db.transaction() as conn:
            return self._model.listar_todos(conn)

    def buscar(self, usuario_id):
        with self._db.transaction() as conn:
            return self._model.buscar_por_id(conn, usuario_id)

    def criar(self, nome, email, senha):
        with self._db.transaction() as conn:
            if self._model.listar_por_email(conn, email):
                raise ConflictError("Email já cadastrado")
            usuario_id = self._model.criar(conn, nome, email, generate_password_hash(senha), TIPO_CLIENTE)
        logger.info("Usuário criado: id=%s", usuario_id)
        return usuario_id

    def autenticar(self, email, senha):
        """Devolve o usuário se a senha confere; caso contrário, None."""
        with self._db.transaction() as conn:
            candidatos = self._model.listar_por_email(conn, email)
        for usuario in candidatos:
            if check_password_hash(usuario["senha"], senha):
                logger.info("Login bem-sucedido: id=%s", usuario["id"])
                return usuario
        logger.warning("Tentativa de login falhou")
        return None
