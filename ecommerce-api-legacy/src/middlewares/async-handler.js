// Express 4 não repassa rejeições de handlers assíncronos ao tratador de erros.
const asyncHandler = (handler) => (req, res, next) => {
    Promise.resolve(handler(req, res, next)).catch(next);
};

module.exports = { asyncHandler };
