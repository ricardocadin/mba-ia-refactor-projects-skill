const { Router } = require('express');
const { asyncHandler } = require('../middlewares/async-handler');

function buildAdminRouter({ reportController, userController, requireAdmin }) {
    const router = Router();
    router.get('/api/admin/financial-report', requireAdmin, asyncHandler(reportController.financialReport));
    router.delete('/api/users/:id', requireAdmin, asyncHandler(userController.remove));
    return router;
}

module.exports = { buildAdminRouter };
