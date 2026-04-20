const express = require("express");
const router = express.Router();
const { searchArticles } = require("../controllers/searchController");
const apiKeyMiddleware = require("../middlewares/apiKeyMiddleware");
//Llama a la ruta para hacer las búsquedas
router.get("/", apiKeyMiddleware, searchArticles);

module.exports = router;
