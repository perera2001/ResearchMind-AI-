const documentService = require("./document.service");
const ApiError = require("../../utils/apiError");


function toPublicDocument(document) {
    return {
        id: document.id,
        file_name: document.file_name,
        status: document.status,
        page_count: document.page_count,
        chunk_count: document.chunk_count,
        uploaded_at: document.uploaded_at,
    };
}


async function upload(request, response, next) {
    try {
        const legacyFile = request.files?.file?.[0];
        const batchFiles = request.files?.files || [];

        if (legacyFile && batchFiles.length) {
            throw new ApiError(
                400,
                "Use either file or files, not both",
            );
        }

        const files = legacyFile
            ? [legacyFile]
            : batchFiles;

        if (!files.length) {
            throw new ApiError(400, "PDF file is required");
        }

        const documents = [];
        const errors = [];

        for (const file of files) {
            try {
                const document = await documentService.uploadDocument(
                    file,
                    request.user.id,
                );
                documents.push(toPublicDocument(document));
            } catch (error) {
                errors.push({
                    file_name: file.originalname,
                    status: error.statusCode || 500,
                    message: error.statusCode
                        ? error.message
                        : "PDF upload failed",
                });
            }
        }

        if (legacyFile) {
            if (errors.length) {
                throw new ApiError(
                    errors[0].status,
                    errors[0].message,
                );
            }

            return response.status(201).json(documents[0]);
        }

        return response.status(errors.length ? 207 : 201).json({
            documents,
            errors,
        });
    } catch (error) {
        return next(error);
    }
}


async function list(request, response, next) {
    try {
        const documents = await documentService.getDocuments(
            request.user.id,
        );

        return response.json(
            documents.map(toPublicDocument),
        );
    } catch (error) {
        return next(error);
    }
}


async function remove(request, response, next) {
    try {
        const documentId = Number(request.params.id);

        if (!Number.isInteger(documentId) || documentId < 1) {
            throw new ApiError(400, "Invalid document ID");
        }

        const result = await documentService.deleteDocument(
            documentId,
            request.user.id,
        );

        return response.json(result);
    } catch (error) {
        return next(error);
    }
}


module.exports = {
    list,
    remove,
    upload,
};
