class AppError extends Error {
    constructor(status, message, options) {
        super(message, options);
        this.status = status;
    }
}

module.exports = { AppError };
