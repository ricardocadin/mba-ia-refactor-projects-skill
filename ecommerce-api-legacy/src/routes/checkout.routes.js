const { Router } = require('express');
const { asyncHandler } = require('../middlewares/async-handler');

function buildCheckoutRouter(controller) {
    const router = Router();
    router.post('/api/checkout', asyncHandler(controller.checkout));
    return router;
}

module.exports = { buildCheckoutRouter };
