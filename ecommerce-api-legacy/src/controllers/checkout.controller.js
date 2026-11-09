const { validateCheckout } = require('../validators/checkout.validator');
const { checkoutResponse } = require('../views/checkout.view');

class CheckoutController {
    constructor(checkoutService) {
        this.checkoutService = checkoutService;
    }

    checkout = async (req, res) => {
        const input = validateCheckout(req.body);
        const result = await this.checkoutService.execute(input);
        res.status(200).json(checkoutResponse(result));
    };
}

module.exports = { CheckoutController };
