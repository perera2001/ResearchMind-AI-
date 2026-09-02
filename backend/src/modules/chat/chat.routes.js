const express = require("express");

const chatController = require("./chat.controller");
const authenticate = require("../../middleware/auth.middleware");


const router = express.Router();

router.use(authenticate);

router.post("/", chatController.chat);
router.get("/sessions", chatController.listSessions);
router.get("/sessions/:sessionId", chatController.getSession);
router.delete("/sessions/:sessionId", chatController.deleteSession);


module.exports = router;
