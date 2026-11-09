const sqlite3 = require('sqlite3');

function createTransactionContext(conn) {
    return {
        all: (sql, params = []) => new Promise((resolve, reject) => {
            conn.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        }),
        get: (sql, params = []) => new Promise((resolve, reject) => {
            conn.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        }),
        run: (sql, params = []) => new Promise((resolve, reject) => {
            conn.run(sql, params, function onRun(err) {
                if (err) return reject(err);
                return resolve({ lastID: this.lastID, changes: this.changes });
            });
        }),
    };
}

class Database {
    constructor(filename) {
        this.conn = new sqlite3.Database(filename);
        this.context = createTransactionContext(this.conn);
        this.queue = Promise.resolve();
    }

    // Executa `work` dentro de BEGIN/COMMIT, com ROLLBACK em qualquer erro.
    // As unidades de trabalho são serializadas porque há uma única conexão.
    transaction(work) {
        const result = this.queue.then(async () => {
            await this.context.run('BEGIN');
            try {
                const value = await work(this.context);
                await this.context.run('COMMIT');
                return value;
            } catch (err) {
                await this.context.run('ROLLBACK').catch(() => {});
                throw err;
            }
        });
        this.queue = result.catch(() => {});
        return result;
    }

    close() {
        return new Promise((resolve, reject) => {
            this.conn.close((err) => (err ? reject(err) : resolve()));
        });
    }
}

module.exports = { Database };
