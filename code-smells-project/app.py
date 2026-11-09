"""Entry point da aplicação: `python app.py`. A montagem das camadas fica em src/app.py (composition root)."""
import logging

from src.app import create_app
from src.config.settings import Config

if __name__ == "__main__":
    config = Config()
    app = create_app(config)
    logging.getLogger(__name__).info("Servidor iniciado em http://%s:%s", config.HOST, config.PORT)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
