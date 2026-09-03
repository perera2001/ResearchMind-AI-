const chatService = require("./chat.service");
const ApiError = require("../../utils/apiError");


async function chat(request, response, next) {
    try {
        const question = request.body.question?.trim();
        const sessionId = request.body.session_id ?? null;
        const documentIds = request.body.document_ids ?? null;

        if (!question) {
            throw new ApiError(400, "Question is required");
        }

        if (
            sessionId !== null
            && (!Number.isInteger(sessionId) || sessionId < 1)
        ) {
            throw new ApiError(400, "Invalid session ID");
        }

        if (
            documentIds !== null
            && (
                !Array.isArray(documentIds)
                || !documentIds.length
                || documentIds.some(
                    (id) => !Number.isInteger(id) || id < 1,
                )
            )
        ) {
            throw new ApiError(
                400,
                "document_ids must be a non-empty array of valid IDs",
            );
        }

        const result = await chatService.sendMessage(
            question,
            sessionId,
            request.user.id,
            documentIds === null
                ? null
                : [...new Set(documentIds)],
        );

        return response.json(result);
    } catch (error) {
        return next(error);
    }
}


async function listSessions(request, response, next) {
    try {
        const sessions = await chatService.getSessions(
            request.user.id,
        );

        return response.json(sessions);
    } catch (error) {
        return next(error);
    }
}


async function getSession(request, response, next) {
    try {
        const sessionId = Number(request.params.sessionId);

        if (!Number.isInteger(sessionId) || sessionId < 1) {
            throw new ApiError(400, "Invalid session ID");
        }

        const session = await chatService.getSession(
            sessionId,
            request.user.id,
        );

        return response.json(session);
    } catch (error) {
        return next(error);
    }
}


async function deleteSession(request, response, next) {
    try {
        const sessionId = Number(request.params.sessionId);

        if (!Number.isInteger(sessionId) || sessionId < 1) {
            throw new ApiError(400, "Invalid session ID");
        }

        const result = await chatService.deleteSession(
            sessionId,
            request.user.id,
        );

        return response.json(result);
    } catch (error) {
        return next(error);
    }
}


module.exports = {
    chat,
    deleteSession,
    getSession,
    listSessions,
};
