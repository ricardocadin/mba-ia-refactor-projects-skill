const { AppError } = require('../errors/app-error');
const { Messages } = require('../constants/messages');

const DIGITS_ONLY = /^\d+$/;

function badRequest() {
    return new AppError(400, Messages.BAD_REQUEST);
}

function isValidCourseId(value) {
    return (typeof value === 'number' && Number.isInteger(value))
        || (typeof value === 'string' && DIGITS_ONLY.test(value));
}

// Valida o corpo do checkout e devolve os dados já nomeados.
function validateCheckout(body) {
    const { usr, eml, pwd, c_id: courseId, card } = body || {};

    if (!usr || !eml || !courseId || !card) throw badRequest();
    if (typeof usr !== 'string' || typeof eml !== 'string' || typeof card !== 'string') throw badRequest();
    if (!isValidCourseId(courseId)) throw badRequest();
    if (pwd && typeof pwd !== 'string') throw badRequest();

    return { name: usr, email: eml, password: pwd, courseId, card };
}

module.exports = { validateCheckout };
