from flask import Flask
from flask_cors import CORS

from config.logging_config import configure_logging
from config.settings import Config
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.system_controller import SystemController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.auth_middleware import AuthMiddleware
from middlewares.error_middleware import register_error_handlers
from models.category_model import CategoryModel
from models.task_model import TaskModel
from models.user_model import UserModel
from routes.category_routes import build_category_blueprint
from routes.report_routes import build_report_blueprint
from routes.system_routes import build_system_blueprint
from routes.task_routes import build_task_blueprint
from routes.user_routes import build_user_blueprint
from services.auth_service import AuthService
from services.category_service import CategoryService
from services.report_service import ReportService
from services.task_service import TaskService
from services.user_service import UserService


def create_app(config=None):
    """Composition root: unico lugar que cria e conecta as implementacoes concretas."""
    config = config or Config()
    configure_logging(config.LOG_LEVEL)

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    CORS(app, origins=config.CORS_ORIGINS)
    db.init_app(app)

    task_model = TaskModel()
    user_model = UserModel()
    category_model = CategoryModel()

    auth_service = AuthService(config.SECRET_KEY, config.TOKEN_MAX_AGE)
    auth = AuthMiddleware(auth_service)

    task_service = TaskService(task_model, user_model, category_model)
    user_service = UserService(user_model, task_model, auth_service)
    category_service = CategoryService(category_model, task_model)
    report_service = ReportService(task_model, user_model, category_model)

    app.register_blueprint(build_system_blueprint(SystemController()))
    app.register_blueprint(build_task_blueprint(TaskController(task_service), auth))
    app.register_blueprint(build_user_blueprint(UserController(user_service), auth))
    app.register_blueprint(build_category_blueprint(CategoryController(category_service), auth))
    app.register_blueprint(build_report_blueprint(ReportController(report_service)))
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app_config = Config()
    create_app(app_config).run(debug=app_config.DEBUG, host=app_config.HOST, port=app_config.PORT)
