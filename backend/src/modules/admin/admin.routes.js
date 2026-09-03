const express = require("express");

const adminController = require("./admin.controller");
const authenticate = require("../../middleware/auth.middleware");
const authorizeAdmin = require("../../middleware/admin.middleware");


const router = express.Router();

router.use(authenticate, authorizeAdmin);
router.get("/users", adminController.listUsers);
router.delete("/users/:userId", adminController.deleteUser);


module.exports = router;
