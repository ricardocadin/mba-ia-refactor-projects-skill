const { Messages } = require('../constants/messages');

class UserController {
    constructor(userService) {
        this.userService = userService;
    }

    remove = async (req, res) => {
        await this.userService.deleteUser(req.params.id);
        res.send(Messages.USER_DELETED);
    };
}

module.exports = { UserController };
