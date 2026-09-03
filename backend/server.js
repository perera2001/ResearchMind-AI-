require("dotenv").config();

const cors = require("cors");
const express = require("express");
const multer = require("multer");

const db = require("./src/config/db");
const authRoutes = require("./src/modules/auth/auth.routes");
const documentRoutes = require("./src/modules/documents/document.routes");
const chatRoutes = require("./src/modules/chat/chat.routes");
const adminRoutes = require("./src/modules/admin/admin.routes");
const ensureAdminUser = require("./src/modules/admin/admin.seed");
const ApiError = require("./src/utils/apiError");


const app = express();

app.use(cors());
app.use(express.json());

app.get("/health", async (request, response, next) => {
    try {
        await db.query("SELECT 1");

        response.json({
            status: "ok",
            service: "ResearchMind Node.js Backend",
        });
    } catch (error) {
        next(error);
    }
});

app.use("/api/auth", authRoutes);
app.use("/api/documents", documentRoutes);
app.use("/api/chat", chatRoutes);
app.use("/api/admin", adminRoutes);

app.use((request, response, next) => {
    next(new ApiError(404, "Route not found"));
});

app.use((error, request, response, next) => {
    if (error instanceof multer.MulterError) {
        return response.status(400).json({
            message: error.message,
        });
    }

    if (error.response) {
        return response.status(error.response.status).json({
            message:
                error.response.data?.detail
                || error.response.data?.message
                || "AI service request failed",
        });
    }

    const statusCode = error.statusCode || 500;

    return response.status(statusCode).json({
        message:
            statusCode === 500
                ? "Internal server error"
                : error.message,
    });
});

const port = Number(process.env.PORT || 5000);

async function startServer() {
    try {
        await db.query("SELECT 1");
        await ensureAdminUser();

        app.listen(port, "127.0.0.1", () => {
            console.log(
                `ResearchMind backend running at http://127.0.0.1:${port}`,
            );
        });
    } catch (error) {
        console.error(`Backend startup failed: ${error.message}`);
        await db.end().catch(() => {});
        process.exit(1);
    }
}


startServer();
