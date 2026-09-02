const express = require("express");
const multer = require("multer");

const documentController = require("./document.controller");
const authenticate = require("../../middleware/auth.middleware");
const ApiError = require("../../utils/apiError");


const router = express.Router();

const upload = multer({
    storage: multer.memoryStorage(),
    limits: {
        fileSize: 25 * 1024 * 1024,
    },
    fileFilter: (request, file, callback) => {
        if (
            file.mimetype !== "application/pdf"
            && !file.originalname.toLowerCase().endsWith(".pdf")
        ) {
            return callback(
                new ApiError(400, "Only PDF files are allowed"),
            );
        }

        return callback(null, true);
    },
});

router.use(authenticate);

router.post(
    "/upload",
    upload.single("file"),
    documentController.upload,
);
router.get("/", documentController.list);
router.delete("/:id", documentController.remove);


module.exports = router;
