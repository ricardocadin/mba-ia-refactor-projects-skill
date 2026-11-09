const { AppError } = require('../errors/app-error');
const { Messages } = require('../constants/messages');
const { PaymentStatus, DEFAULT_PASSWORD } = require('../constants/payment');

class CheckoutService {
    constructor({ db, userModel, courseModel, enrollmentModel, paymentModel, auditLogModel,
        passwordService, paymentService, logger }) {
        this.db = db;
        this.users = userModel;
        this.courses = courseModel;
        this.enrollments = enrollmentModel;
        this.payments = paymentModel;
        this.auditLogs = auditLogModel;
        this.passwords = passwordService;
        this.paymentGateway = paymentService;
        this.logger = logger;
    }

    async execute({ name, email, password, courseId, card }) {
        // Etapa 1: curso e usuário. O usuário novo é gravado (e confirmado) antes da checagem
        // do cartão, como no comportamento original: cartão recusado não desfaz o cadastro.
        const { course, userId } = await this.db.transaction(async (tx) => {
            const found = await this.courses.findActiveById(tx, courseId);
            if (!found) throw new AppError(404, Messages.COURSE_NOT_FOUND);

            const user = await this.users.findByEmail(tx, email);
            if (user) return { course: found, userId: user.id };

            const passwordHash = await this.passwords.hash(password || DEFAULT_PASSWORD);
            try {
                const createdId = await this.users.create(tx, { name, email, passwordHash });
                return { course: found, userId: createdId };
            } catch (err) {
                throw new AppError(500, Messages.USER_CREATE_ERROR, { cause: err });
            }
        });

        const status = this.paymentGateway.authorize(card);
        if (status === PaymentStatus.DENIED) throw new AppError(400, Messages.PAYMENT_DENIED);

        // Etapa 2: matrícula, pagamento e auditoria de forma atômica.
        const enrollmentId = await this.db.transaction(async (tx) => {
            let createdEnrollmentId;
            try {
                createdEnrollmentId = await this.enrollments.create(tx, userId, courseId);
            } catch (err) {
                throw new AppError(500, Messages.ENROLLMENT_ERROR, { cause: err });
            }
            try {
                await this.payments.create(tx, { enrollmentId: createdEnrollmentId, amount: course.price, status });
            } catch (err) {
                throw new AppError(500, Messages.PAYMENT_ERROR, { cause: err });
            }
            await this.auditLogs.create(tx, `Checkout curso ${courseId} por ${userId}`);
            return createdEnrollmentId;
        });

        this.logger.info(`Checkout concluído: curso=${course.id} usuario=${userId} matricula=${enrollmentId}`);
        return { enrollmentId };
    }
}

module.exports = { CheckoutService };
