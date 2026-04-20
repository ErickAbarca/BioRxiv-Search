const express = require("express");
const app = express();
const cors = require("cors");
require("dotenv").config();

app.use(cors());
app.use(express.json());

app.get("/", (req, res) => res.send("API corriendo..."));

app.use("/api/users", require("./routes/users"));//Ruta para el registro y login de usuarios
app.use("/api/search", require("./routes/search"));// Ruta para la búsqueda de articulos

module.exports = app;
