const PaymentStatus = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
});

const APPROVED_CARD_PREFIX = '4';
const DEFAULT_PASSWORD = '123456';
const SEED_USER_PASSWORD = '123';

module.exports = { PaymentStatus, APPROVED_CARD_PREFIX, DEFAULT_PASSWORD, SEED_USER_PASSWORD };
