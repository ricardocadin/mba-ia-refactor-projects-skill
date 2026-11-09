const express = require('express');

const { loadConfig } = require('./config/env');
const { createLogger } = require('./config/logger');
const { SEED_USER_PASSWORD } = require('./constants/payment');

const { Database } = require('./models/database');
const { initializeSchema } = require('./models/schema');
const { UserModel } = require('./models/user.model');
const { CourseModel } = require('./models/course.model');
const { EnrollmentModel } = require('./models/enrollment.model');
const { PaymentModel } = require('./models/payment.model');
const { AuditLogModel } = require('./models/audit-log.model');
const { ReportModel } = require('./models/report.model');

const { PasswordService } = require('./services/password.service');
const { PaymentService } = require('./services/payment.service');
const { CheckoutService } = require('./services/checkout.service');
const { ReportService } = require('./services/report.service');
const { UserService } = require('./services/user.service');

const { CheckoutController } = require('./controllers/checkout.controller');
const { ReportController } = require('./controllers/report.controller');
const { UserController } = require('./controllers/user.controller');

const { buildCheckoutRouter } = require('./routes/checkout.routes');
const { buildAdminRouter } = require('./routes/admin.routes');
const { requireAdmin } = require('./middlewares/auth.middleware');
const { errorMiddleware } = require('./middlewares/error.middleware');

// Composition root: cria as implementações concretas, conecta as camadas e inicia o servidor.
async function main() {
    const config = loadConfig();
    const logger = createLogger(config.logLevel);

    const db = new Database(config.databasePath);
    const passwordService = new PasswordService();
    await initializeSchema(db, { seedUserPasswordHash: await passwordService.hash(SEED_USER_PASSWORD) });

    const userModel = new UserModel();
    const checkoutService = new CheckoutService({
        db,
        userModel,
        courseModel: new CourseModel(),
        enrollmentModel: new EnrollmentModel(),
        paymentModel: new PaymentModel(),
        auditLogModel: new AuditLogModel(),
        passwordService,
        paymentService: new PaymentService(),
        logger,
    });
    const reportService = new ReportService({ db, reportModel: new ReportModel() });
    const userService = new UserService({ db, userModel });

    const app = express();
    app.use(express.json());
    app.use(buildCheckoutRouter(new CheckoutController(checkoutService)));
    app.use(buildAdminRouter({
        reportController: new ReportController(reportService),
        userController: new UserController(userService),
        requireAdmin: requireAdmin(config.adminToken),
    }));
    app.use(errorMiddleware(logger));

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

main().catch((err) => {
    process.stderr.write(`Falha ao iniciar a aplicação: ${err.stack}\n`);
    process.exit(1);
});
