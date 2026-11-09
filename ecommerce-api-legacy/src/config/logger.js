const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] !== undefined ? LEVELS[level] : LEVELS.info;

    function write(name, message) {
        if (LEVELS[name] > threshold) return;
        const stream = name === 'error' || name === 'warn' ? process.stderr : process.stdout;
        stream.write(`${new Date().toISOString()} ${name.toUpperCase()} ${message}\n`);
    }

    return {
        error: (message) => write('error', message),
        warn: (message) => write('warn', message),
        info: (message) => write('info', message),
        debug: (message) => write('debug', message),
    };
}

module.exports = { createLogger };
