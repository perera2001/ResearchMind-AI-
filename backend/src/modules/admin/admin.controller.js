const adminService = require("./admin.service");
const ApiError = require("../../utils/apiError");


async function listUsers(request, response, next) {
    try {
        return response.json(await adminService.getRegularUsers());
    } catch (error) {
        return next(error);
    }
}


async function deleteUser(request, response, next) {
    try {
        const userId = Number(request.params.userId);

        if (!Number.isInteger(userId) || userId < 1) {
            throw new ApiError(400, "Invalid user ID");
        }

        return response.json(
            await adminService.deleteRegularUser(
                userId,
                request.user.id,
            ),
        );
    } catch (error) {
        return next(error);
    }
}


module.exports = { deleteUser, listUsers };
