const { PaymentStatus, APPROVED_CARD_PREFIX } = require('../constants/payment');

class PaymentService {
    // Regra de aprovação do pagamento (gateway simulado): cartões que começam com "4" são aprovados.
    authorize(card) {
        return card.startsWith(APPROVED_CARD_PREFIX) ? PaymentStatus.PAID : PaymentStatus.DENIED;
    }
}

module.exports = { PaymentService };
