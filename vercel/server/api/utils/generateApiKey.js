const crypto = require("crypto");
//Modulo para generar una key aleatoria
function generateApiKey() {
  return crypto.randomBytes(16).toString("hex").toUpperCase();
}

module.exports = generateApiKey;
