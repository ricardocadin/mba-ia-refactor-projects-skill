const crypto = require('crypto');

const KEY_LENGTH = 64;
const SALT_BYTES = 16;

function scrypt(password, salt) {
    return new Promise((resolve, reject) => {
        crypto.scrypt(password, salt, KEY_LENGTH, (err, key) => (err ? reject(err) : resolve(key)));
    });
}

class PasswordService {
    async hash(plain) {
        const salt = crypto.randomBytes(SALT_BYTES);
        const key = await scrypt(plain, salt);
        return `scrypt$${salt.toString('hex')}$${key.toString('hex')}`;
    }
}

module.exports = { PasswordService };
