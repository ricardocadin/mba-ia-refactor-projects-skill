class AuditLogModel {
    async create(tx, action) {
        await tx.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
    }
}

module.exports = { AuditLogModel };
