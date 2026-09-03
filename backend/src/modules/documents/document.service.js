const crypto = require("crypto");
const fs = require("fs/promises");
const path = require("path");

const db = require("../../config/db");
const pythonApi = require("../../config/pythonApi");
const ApiError = require("../../utils/apiError");


async function findDuplicateDocument(userId, fileName) {
    const [rows] = await db.execute(
        `
        SELECT id
        FROM documents
        WHERE user_id = ? AND file_name = ?
        LIMIT 1
        `,
        [userId, fileName],
    );

    return rows[0] || null;
}


async function findDocument(documentId, userId) {
    const [rows] = await db.execute(
        `
        SELECT
            id,
            user_id,
            file_name,
            file_path,
            status,
            page_count,
            chunk_count,
            uploaded_at
        FROM documents
        WHERE id = ? AND user_id = ?
        LIMIT 1
        `,
        [documentId, userId],
    );

    return rows[0] || null;
}


async function uploadDocument(file, userId) {
    const existingDocument = await findDuplicateDocument(
        userId,
        file.originalname,
    );

    if (existingDocument) {
        throw new ApiError(409, "This PDF is already uploaded");
    }

    const uploadRoot = path.resolve(
        process.env.PDF_UPLOAD_PATH || "data/papers",
    );
    const userFolder = path.join(uploadRoot, String(userId));
    const safeFileName = path.basename(file.originalname);
    const storedFileName = `${crypto.randomUUID()}_${safeFileName}`;
    const filePath = path.join(userFolder, storedFileName);

    await fs.mkdir(userFolder, { recursive: true });
    await fs.writeFile(filePath, file.buffer);

    let documentId;

    try {
        const [result] = await db.execute(
            `
            INSERT INTO documents (
                user_id,
                file_name,
                file_path,
                status,
                page_count,
                chunk_count
            )
            VALUES (?, ?, ?, 'processing', 0, 0)
            `,
            [userId, safeFileName, filePath],
        );

        documentId = result.insertId;

        const form = new FormData();
        const pdf = new Blob(
            [file.buffer],
            {
                type: file.mimetype,
            },
        );

        form.append("file", pdf, safeFileName);
        form.append("user_id", String(userId));
        form.append("document_id", String(documentId));
        form.append("file_name", safeFileName);
        form.append("file_path", filePath);

        const aiResponse = await pythonApi.post(
            "/internal/documents/process",
            form,
        );

        await db.execute(
            `
            UPDATE documents
            SET status = ?, page_count = ?, chunk_count = ?
            WHERE id = ? AND user_id = ?
            `,
            [
                aiResponse.data.status,
                aiResponse.data.page_count,
                aiResponse.data.chunk_count,
                documentId,
                userId,
            ],
        );

        return findDocument(documentId, userId);
    } catch (error) {
        if (documentId) {
            await pythonApi.delete(
                `/internal/documents/${documentId}`,
                {
                    params: {
                        user_id: userId,
                    },
                },
            ).catch(() => {});

            await db.execute(
                "DELETE FROM documents WHERE id = ? AND user_id = ?",
                [documentId, userId],
            );
        }

        await fs.rm(filePath, { force: true });
        throw error;
    }
}


async function getDocuments(userId) {
    const [rows] = await db.execute(
        `
        SELECT
            id,
            user_id,
            file_name,
            file_path,
            status,
            page_count,
            chunk_count,
            uploaded_at
        FROM documents
        WHERE user_id = ?
        ORDER BY uploaded_at DESC
        `,
        [userId],
    );

    return rows;
}


async function deleteDocument(documentId, userId) {
    const document = await findDocument(documentId, userId);

    if (!document) {
        throw new ApiError(404, "Document not found");
    }

    await pythonApi.delete(
        `/internal/documents/${documentId}`,
        {
            params: {
                user_id: userId,
            },
        },
    );

    await fs.rm(document.file_path, { force: true });

    await db.execute(
        "DELETE FROM documents WHERE id = ? AND user_id = ?",
        [documentId, userId],
    );

    return {
        message: "Document deleted successfully",
    };
}


module.exports = {
    deleteDocument,
    getDocuments,
    uploadDocument,
};
