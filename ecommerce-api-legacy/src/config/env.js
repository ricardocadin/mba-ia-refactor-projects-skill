const DEFAULT_PORT = 3000;
const DEFAULT_LOG_LEVEL = 'info';
const DATABASE_PATH = ':memory:';

function loadConfig(env = process.env) {
    return {
        port: Number(env.PORT || DEFAULT_PORT),
        adminToken: env.ADMIN_TOKEN || null,
        logLevel: env.LOG_LEVEL || DEFAULT_LOG_LEVEL,
        databasePath: DATABASE_PATH,
    };
}

module.exports = { loadConfig };
