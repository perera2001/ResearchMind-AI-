const db = require("../../config/db");
const pythonApi = require("../../config/pythonApi");
const ApiError = require("../../utils/apiError");


async function findSession(sessionId, userId) {
    const [rows] = await db.execute(
        `
        SELECT id, user_id, title, created_at, updated_at
        FROM chat_sessions
        WHERE id = ? AND user_id = ?
        LIMIT 1
        `,
        [sessionId, userId],
    );

    return rows[0] || null;
}


async function getHistory(sessionId, userId) {
    const [rows] = await db.execute(
        `
        SELECT role, content
        FROM chat_messages
        WHERE session_id = ? AND user_id = ?
        ORDER BY created_at ASC, id ASC
        `,
        [sessionId, userId],
    );

    return rows;
}


async function getUserDocuments(userId) {
    const [rows] = await db.execute(
        `
        SELECT
            id AS document_id,
            file_name AS source,
            file_path
        FROM documents
        WHERE user_id = ? AND status = 'processed'
        ORDER BY uploaded_at ASC, id ASC
        `,
        [userId],
    );

    return rows;
}


async function sendMessage(question, sessionId, userId) {
    let currentSessionId = sessionId;

    if (currentSessionId === null) {
        const [result] = await db.execute(
            `
            INSERT INTO chat_sessions (user_id, title)
            VALUES (?, ?)
            `,
            [userId, question.slice(0, 80)],
        );

        currentSessionId = result.insertId;
    } else {
        const session = await findSession(currentSessionId, userId);

        if (!session) {
            throw new ApiError(404, "Chat session not found");
        }
    }

    const chatHistory = await getHistory(
        currentSessionId,
        userId,
    );
    const documents = await getUserDocuments(userId);

    await db.execute(
        `
        INSERT INTO chat_messages (
            session_id,
            user_id,
            role,
            content,
            sources
        )
        VALUES (?, ?, 'user', ?, NULL)
        `,
        [currentSessionId, userId, question],
    );

    const aiResponse = await pythonApi.post(
        "/internal/chat",
        {
            user_id: userId,
            question,
            chat_history: chatHistory,
            documents,
        },
    );

    await db.execute(
        `
        INSERT INTO chat_messages (
            session_id,
            user_id,
            role,
            content,
            sources
        )
        VALUES (?, ?, 'assistant', ?, ?)
        `,
        [
            currentSessionId,
            userId,
            aiResponse.data.answer,
            JSON.stringify(aiResponse.data.sources),
        ],
    );

    await db.execute(
        `
        UPDATE chat_sessions
        SET updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
        `,
        [currentSessionId, userId],
    );

    return {
        session_id: currentSessionId,
        ...aiResponse.data,
    };
}


async function getSessions(userId) {
    const [rows] = await db.execute(
        `
        SELECT id, title, created_at, updated_at
        FROM chat_sessions
        WHERE user_id = ?
        ORDER BY updated_at DESC, id DESC
        `,
        [userId],
    );

    return rows;
}


async function getSession(sessionId, userId) {
    const session = await findSession(sessionId, userId);

    if (!session) {
        throw new ApiError(404, "Chat session not found");
    }

    const [messages] = await db.execute(
        `
        SELECT id, session_id, role, content, sources, created_at
        FROM chat_messages
        WHERE session_id = ? AND user_id = ?
        ORDER BY created_at ASC, id ASC
        `,
        [sessionId, userId],
    );

    return {
        session: {
            id: session.id,
            title: session.title,
            created_at: session.created_at,
            updated_at: session.updated_at,
        },
        messages: messages.map((message) => ({
            ...message,
            sources: message.sources
                ? JSON.parse(message.sources)
                : null,
        })),
    };
}


async function deleteSession(sessionId, userId) {
    const session = await findSession(sessionId, userId);

    if (!session) {
        throw new ApiError(404, "Chat session not found");
    }

    const connection = await db.getConnection();

    try {
        await connection.beginTransaction();
        await connection.execute(
            `
            DELETE FROM chat_messages
            WHERE session_id = ? AND user_id = ?
            `,
            [sessionId, userId],
        );
        await connection.execute(
            `
            DELETE FROM chat_sessions
            WHERE id = ? AND user_id = ?
            `,
            [sessionId, userId],
        );
        await connection.commit();
    } catch (error) {
        await connection.rollback();
        throw error;
    } finally {
        connection.release();
    }

    return {
        message: "Chat session deleted successfully",
    };
}


module.exports = {
    deleteSession,
    getSession,
    getSessions,
    sendMessage,
};
