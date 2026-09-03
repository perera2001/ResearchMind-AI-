const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

const db = require("../../config/db");


async function findUserByEmail(email) {
    const [rows] = await db.execute(
        `
        SELECT id, name, email, password, role, created_at
        FROM users
        WHERE email = ?
        LIMIT 1
        `,
        [email],
    );

    return rows[0] || null;
}


async function findUserById(userId) {
    const [rows] = await db.execute(
        `
        SELECT id, name, email, role, created_at
        FROM users
        WHERE id = ?
        LIMIT 1
        `,
        [userId],
    );

    return rows[0] || null;
}


async function createUser(name, email, password) {
    const passwordHash = await bcrypt.hash(password, 12);

    const [result] = await db.execute(
        `
        INSERT INTO users (name, email, password, role)
        VALUES (?, ?, ?, 'user')
        `,
        [name, email, passwordHash],
    );

    return findUserById(result.insertId);
}


function createToken(user) {
    return jwt.sign(
        {
            user_id: user.id,
            email: user.email,
            role: user.role,
        },
        process.env.JWT_SECRET,
        {
            expiresIn: process.env.JWT_EXPIRES_IN || "2h",
        },
    );
}


module.exports = {
    createToken,
    createUser,
    findUserByEmail,
    findUserById,
};
