const express = require("express");
const router = express.Router();
const { registerUser, loginUser } = require("../controllers/userController");
//Divide la ruta para cada acción
router.post("/register", registerUser);
router.post("/login", loginUser);

module.exports = router;
