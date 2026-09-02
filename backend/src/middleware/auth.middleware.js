const jwt = require("jsonwebtoken");

const ApiError = require("../utils/apiError");


function authenticate(request, response, next) {
    const authorization = request.headers.authorization;

    if (!authorization || !authorization.startsWith("Bearer ")) {
        return next(new ApiError(401, "Authentication required"));
    }

    const token = authorization.slice(7);

    try {
        const payload = jwt.verify(
            token,
            process.env.JWT_SECRET,
        );

        request.user = {
            id: Number(payload.user_id),
            email: payload.email,
        };

        return next();
    } catch (error) {
        return next(new ApiError(401, "Invalid or expired token"));
    }
}


module.exports = authenticate;
