const db = require("../config/db");
const ApiError = require("../utils/apiError");


async function authorizeAdmin(request, response, next) {
    try {
        if (request.user.role !== "admin") {
            throw new ApiError(403, "Admin access required");
        }

        const [rows] = await db.execute(
            "SELECT id, role FROM users WHERE id = ? LIMIT 1",
            [request.user.id],
        );
        const user = rows[0];

        if (!user) {
            throw new ApiError(401, "Authentication required");
        }

        if (user.role !== "admin" || user.role !== request.user.role) {
            throw new ApiError(403, "Admin access required");
        }

        return next();
    } catch (error) {
        return next(error);
    }
}


module.exports = authorizeAdmin;
