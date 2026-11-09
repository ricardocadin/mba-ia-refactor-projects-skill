const { AppError } = require('../errors/app-error');
const { Messages } = require('../constants/messages');

// Tratador global de erros (registrado por último).
function errorMiddleware(logger) {
    return (err, req, res, next) => {
        if (err instanceof AppError) return res.status(err.status).send(err.message);

        // Erros 4xx do próprio Express (ex.: JSON malformado) mantêm o tratamento padrão.
        if (err && err.status >= 400 && err.status < 500) return next(err);

        logger.error(err && err.stack ? err.stack : String(err));
        if (res.headersSent) return next(err);
        return res.status(500).send(Messages.INTERNAL_ERROR);
    };
}

module.exports = { errorMiddleware };
