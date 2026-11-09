"""Notificações de negócio. Hoje apenas registradas em log; a integração real (e-mail, SMS, push)
fica para uma decisão futura."""
import logging

logger = logging.getLogger(__name__)


class NotificacaoService:
    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Notificação (e-mail/SMS/push): pedido %s criado para o usuário %s", pedido_id, usuario_id)

    def pedido_aprovado(self, pedido_id):
        logger.info("Notificação: pedido %s aprovado, preparar envio", pedido_id)

    def pedido_cancelado(self, pedido_id):
        logger.info("Notificação: pedido %s cancelado", pedido_id)
