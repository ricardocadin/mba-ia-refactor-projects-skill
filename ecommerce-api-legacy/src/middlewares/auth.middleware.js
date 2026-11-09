const crypto = require('crypto');
const { AppError } = require('../errors/app-error');
const { Messages } = require('../constants/messages');

const BEARER_PREFIX = 'Bearer ';

function digest(value) {
    return crypto.createHash('sha256').update(value).digest();
}

// Exige "Authorization: Bearer <ADMIN_TOKEN>". Sem ADMIN_TOKEN configurado, nega sempre.
function requireAdmin(adminToken) {
    return (req, res, next) => {
        const header = req.headers.authorization || '';
        const provided = header.startsWith(BEARER_PREFIX) ? header.slice(BEARER_PREFIX.length) : '';
        const authorized = Boolean(adminToken) && Boolean(provided)
            && crypto.timingSafeEqual(digest(provided), digest(adminToken));
        if (!authorized) return next(new AppError(401, Messages.UNAUTHORIZED));
        return next();
    };
}

module.exports = { requireAdmin };
