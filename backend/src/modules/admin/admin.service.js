const fs = require("fs/promises");
const path = require("path");

const db = require("../../config/db");
const pythonApi = require("../../config/pythonApi");
const ApiError = require("../../utils/apiError");


async function getRegularUsers() {
    const [rows] = await db.execute(
        `
        SELECT id, name, email, role, created_at
        FROM users
        WHERE role = ?
        ORDER BY created_at DESC
        `,
        ["user"],
    );

    return rows;
}


function resolveOwnedPdf(filePath, userId) {
    const uploadRoot = path.resolve(
        process.env.PDF_UPLOAD_PATH || "data/papers",
    );
    const userRoot = path.resolve(uploadRoot, String(userId));
    const resolvedFile = path.resolve(filePath);
    const relativePath = path.relative(userRoot, resolvedFile);

    if (
        !relativePath
        || relativePath.startsWith("..")
        || path.isAbsolute(relativePath)
    ) {
        throw new ApiError(500, "Unsafe stored PDF path");
    }

    return resolvedFile;
}


async function deleteRegularUser(userId, adminId) {
    if (userId === adminId) {
        throw new ApiError(403, "Admin accounts cannot be deleted");
    }

    const [users] = await db.execute(
        "SELECT id, role FROM users WHERE id = ? LIMIT 1",
        [userId],
    );
    const user = users[0];

    if (!user) {
        throw new ApiError(404, "User not found");
    }

    if (user.role !== "user") {
        throw new ApiError(403, "Admin accounts cannot be deleted");
    }

    const [documents] = await db.execute(
        "SELECT id, file_path FROM documents WHERE user_id = ?",
        [userId],
    );

    // Complete external cleanup first. Any failure keeps all MySQL ownership rows.
    for (const document of documents) {
        await pythonApi.delete(
            `/internal/documents/${document.id}`,
            { params: { user_id: userId } },
        );
    }

    for (const document of documents) {
        const pdfPath = resolveOwnedPdf(document.file_path, userId);
        try {
            await fs.rm(pdfPath, { force: true });
        } catch (error) {
            throw new ApiError(
                500,
                "PDF cleanup failed; user was not deleted",
            );
        }
    }

    const connection = await db.getConnection();

    try {
        await connection.beginTransaction();
        const [lockedUsers] = await connection.execute(
            "SELECT role FROM users WHERE id = ? FOR UPDATE",
            [userId],
        );

        if (!lockedUsers[0]) {
            throw new ApiError(404, "User not found");
        }

        if (lockedUsers[0].role !== "user") {
            throw new ApiError(403, "Admin accounts cannot be deleted");
        }

        await connection.execute(
            "DELETE FROM chat_messages WHERE user_id = ?",
            [userId],
        );
        await connection.execute(
            "DELETE FROM chat_sessions WHERE user_id = ?",
            [userId],
        );
        await connection.execute(
            "DELETE FROM documents WHERE user_id = ?",
            [userId],
        );
        await connection.execute(
            "DELETE FROM users WHERE id = ? AND role = ?",
            [userId, "user"],
        );
        await connection.commit();
    } catch (error) {
        await connection.rollback();
        throw error;
    } finally {
        connection.release();
    }

    return { message: "User deleted successfully" };
}


module.exports = { deleteRegularUser, getRegularUsers };
