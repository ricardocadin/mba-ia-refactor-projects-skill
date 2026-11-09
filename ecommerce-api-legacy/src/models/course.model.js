class CourseModel {
    async findActiveById(tx, id) {
        return tx.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
    }
}

module.exports = { CourseModel };
