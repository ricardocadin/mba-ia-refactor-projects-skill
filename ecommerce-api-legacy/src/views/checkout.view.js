const { Messages } = require('../constants/messages');

function checkoutResponse({ enrollmentId }) {
    return { msg: Messages.CHECKOUT_SUCCESS, enrollment_id: enrollmentId };
}

module.exports = { checkoutResponse };
