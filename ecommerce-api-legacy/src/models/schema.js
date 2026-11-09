const { PaymentStatus } = require('../constants/payment');

async function initializeSchema(db, { seedUserPasswordHash }) {
    await db.transaction(async (tx) => {
        await tx.run('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
        await tx.run('CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
        await tx.run('CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)');
        await tx.run('CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)');
        await tx.run('CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

        await tx.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            ['Leonan', 'leonan@fullcycle.com.br', seedUserPasswordHash]);
        await tx.run('INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)',
            ['Clean Architecture', 997.00, 1, 'Docker', 497.00, 1]);
        await tx.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [1, 1]);
        await tx.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [1, 997.00, PaymentStatus.PAID]);
    });
}

module.exports = { initializeSchema };
