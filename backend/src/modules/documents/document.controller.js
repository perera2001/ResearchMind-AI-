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
        if (!request.file) {
            throw new ApiError(400, "PDF file is required");
        }

        const document = await documentService.uploadDocument(
            request.file,
            request.user.id,
        );

        return response.status(201).json(
            toPublicDocument(document),
        );
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
