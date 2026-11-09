class UserModel {
    async findByEmail(tx, email) {
        return tx.get('SELECT id FROM users WHERE email = ?', [email]);
    }

    async create(tx, { name, email, passwordHash }) {
        const { lastID } = await tx.run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [name, email, passwordHash]);
        return lastID;
    }

    async deleteById(tx, id) {
        await tx.run('DELETE FROM users WHERE id = ?', [id]);
    }
}

module.exports = { UserModel };
