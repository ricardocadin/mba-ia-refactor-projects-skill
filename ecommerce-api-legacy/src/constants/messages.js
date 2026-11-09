const Messages = Object.freeze({
    BAD_REQUEST: 'Bad Request',
    COURSE_NOT_FOUND: 'Curso não encontrado',
    PAYMENT_DENIED: 'Pagamento recusado',
    USER_CREATE_ERROR: 'Erro ao criar usuário',
    ENROLLMENT_ERROR: 'Erro Matrícula',
    PAYMENT_ERROR: 'Erro Pagamento',
    CHECKOUT_SUCCESS: 'Sucesso',
    USER_DELETED: 'Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.',
    UNAUTHORIZED: 'Unauthorized',
    INTERNAL_ERROR: 'Erro interno do servidor',
    UNKNOWN_STUDENT: 'Unknown',
});

module.exports = { Messages };
