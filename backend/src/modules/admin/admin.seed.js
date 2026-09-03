const bcrypt = require("bcryptjs");

const db = require("../../config/db");
const ApiError = require("../../utils/apiError");


function getAdminConfig() {
    const name = process.env.ADMIN_NAME?.trim();
    const email = process.env.ADMIN_EMAIL?.trim().toLowerCase();
    const password = process.env.ADMIN_PASSWORD;

    if (!name || !email || !password || !password.trim()) {
        throw new Error(
            "ADMIN_NAME, ADMIN_EMAIL, and ADMIN_PASSWORD are required",
        );
    }

    return { name, email, password };
}


async function ensureAdminUser() {
    const { name, email, password } = getAdminConfig();
    const [rows] = await db.execute(
        "SELECT id, password, role FROM users WHERE email = ? LIMIT 1",
        [email],
    );
    const existingUser = rows[0];

    if (existingUser && existingUser.role !== "admin") {
        throw new ApiError(
            409,
            "Configured admin email belongs to a regular user",
        );
    }

    const passwordHash = await bcrypt.hash(password, 12);

    if (!existingUser) {
        await db.execute(
            `
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, 'admin')
            `,
            [name, email, passwordHash],
        );
        return;
    }

    const passwordMatches = await bcrypt.compare(
        password,
        existingUser.password,
    );

    await db.execute(
        `
        UPDATE users
        SET name = ?, password = ?, role = 'admin'
        WHERE id = ?
        `,
        [
            name,
            passwordMatches ? existingUser.password : passwordHash,
            existingUser.id,
        ],
    );
}


module.exports = ensureAdminUser;
