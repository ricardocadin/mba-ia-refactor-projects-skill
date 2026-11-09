"""Composition root: cria as dependências concretas, conecta as camadas e registra as rotas."""
from flask import Flask
from flask_cors import CORS

from src.config.logging_config import configure_logging
from src.config.settings import Config
from src.constants.aplicacao import APP_VERSION
from src.controllers.admin_controller import AdminController
from src.controllers.health_controller import HealthController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.usuario_controller import UsuarioController
from src.middlewares.error_middleware import register_error_handlers
from src.models.admin_model import AdminModel
from src.models.database import Database
from src.models.health_model import HealthModel
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.relatorio_model import RelatorioModel
from src.models.schema import init_database
from src.models.usuario_model import UsuarioModel
from src.routes.admin_routes import build_admin_blueprint
from src.routes.health_routes import build_health_blueprint
from src.routes.pedido_routes import build_pedido_blueprint
from src.routes.produto_routes import build_produto_blueprint
from src.routes.usuario_routes import build_usuario_blueprint
from src.services.admin_service import AdminService
from src.services.auth_service import AuthService
from src.services.health_service import HealthService
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.usuario_service import UsuarioService


def create_app(config=None):
    config = config or Config()
    configure_logging(config.LOG_LEVEL)

    app = Flask(__name__)
    app.config.update(DEBUG=config.DEBUG)
    CORS(app)

    database = Database(config.DATABASE_URL)
    init_database(database)

    # Models (acesso a dados, sem estado)
    produto_model = ProdutoModel()
    pedido_model = PedidoModel()
    usuario_model = UsuarioModel()

    # Services (regras de negócio e transações)
    auth_service = AuthService(config.SECRET_KEY, config.TOKEN_MAX_AGE)
    produto_service = ProdutoService(database, produto_model)
    usuario_service = UsuarioService(database, usuario_model)
    pedido_service = PedidoService(database, pedido_model, produto_model, usuario_model, NotificacaoService())
    relatorio_service = RelatorioService(database, RelatorioModel())
    admin_service = AdminService(database, AdminModel())
    health_service = HealthService(database, HealthModel())

    # Controllers e rotas
    app.register_blueprint(build_produto_blueprint(ProdutoController(produto_service)))
    app.register_blueprint(build_usuario_blueprint(UsuarioController(usuario_service, auth_service)))
    app.register_blueprint(
        build_pedido_blueprint(PedidoController(pedido_service), RelatorioController(relatorio_service))
    )
    app.register_blueprint(build_admin_blueprint(AdminController(admin_service), auth_service))
    app.register_blueprint(
        build_health_blueprint(HealthController(health_service, APP_VERSION, config.ENVIRONMENT))
    )

    register_error_handlers(app)
    return app
