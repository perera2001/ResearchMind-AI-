const bcrypt = require("bcryptjs");

const authService = require("./auth.service");
const ApiError = require("../../utils/apiError");


async function register(request, response, next) {
    try {
        const name = request.body.name?.trim();
        const email = request.body.email?.trim().toLowerCase();
        const password = request.body.password;

        if (!name || !email || !password) {
            throw new ApiError(400, "Name, email, and password are required");
        }

        if (password.length < 8) {
            throw new ApiError(400, "Password must contain at least 8 characters");
        }

        const existingUser = await authService.findUserByEmail(email);

        if (existingUser) {
            throw new ApiError(409, "Email already registered");
        }

        const user = await authService.createUser(
            name,
            email,
            password,
        );

        return response.status(201).json({
            message: "User registered successfully",
            user,
        });
    } catch (error) {
        if (error.code === "ER_DUP_ENTRY") {
            return next(new ApiError(409, "Email already registered"));
        }

        return next(error);
    }
}


async function login(request, response, next) {
    try {
        const email = request.body.email?.trim().toLowerCase();
        const password = request.body.password;

        if (!email || !password) {
            throw new ApiError(400, "Email and password are required");
        }

        const user = await authService.findUserByEmail(email);

        if (!user || !await bcrypt.compare(password, user.password)) {
            throw new ApiError(401, "Invalid email or password");
        }

        const token = authService.createToken(user);

        return response.json({
            access_token: token,
            token_type: "bearer",
            user: {
                id: user.id,
                name: user.name,
                email: user.email,
                created_at: user.created_at,
            },
        });
    } catch (error) {
        return next(error);
    }
}


async function me(request, response, next) {
    try {
        const user = await authService.findUserById(request.user.id);

        if (!user) {
            throw new ApiError(404, "User not found");
        }

        return response.json(user);
    } catch (error) {
        return next(error);
    }
}


module.exports = {
    login,
    me,
    register,
};
