const { PaymentStatus } = require('../constants/payment');
const { Messages } = require('../constants/messages');

class ReportService {
    constructor({ db, reportModel }) {
        this.db = db;
        this.reports = reportModel;
    }

    // Relatório financeiro: receita por curso (só pagamentos PAID) e alunos matriculados.
    async financialReport() {
        const rows = await this.db.transaction((tx) => this.reports.listCourseEnrollmentRows(tx));

        const courses = new Map();
        for (const row of rows) {
            if (!courses.has(row.course_id)) {
                courses.set(row.course_id, { title: row.course_title, revenue: 0, students: [] });
            }
            if (row.enrollment_id === null) continue;

            const course = courses.get(row.course_id);
            if (row.payment_status === PaymentStatus.PAID) course.revenue += row.payment_amount;
            course.students.push({
                name: row.user_name !== null ? row.user_name : Messages.UNKNOWN_STUDENT,
                paid: row.payment_amount !== null ? row.payment_amount : 0,
            });
        }
        return [...courses.values()];
    }
}

module.exports = { ReportService };
