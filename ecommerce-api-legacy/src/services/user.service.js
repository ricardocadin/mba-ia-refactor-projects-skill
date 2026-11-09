class UserService {
    constructor({ db, userModel }) {
        this.db = db;
        this.users = userModel;
    }

    async deleteUser(id) {
        await this.db.transaction((tx) => this.users.deleteById(tx, id));
    }
}

module.exports = { UserService };
