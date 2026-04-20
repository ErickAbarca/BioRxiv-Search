const admin = require("../services/firebaseService");

//modulo de middleware para validar la API Key

// verifica si la API Key es válida (esta en la base de datos)
module.exports = async function (req, res, next) {
  const apiKey = req.headers["x-api-key"];

  if (!apiKey) {
    return res.status(401).json({ error: "Falta API Key" });
  }

  try {
    const db = admin.firestore();
    const snapshot = await db.collection("users").where("apiKey", "==", apiKey).get();

    if (snapshot.empty) {
      return res.status(403).json({ error: "API Key inválida" });
    }

    const userData = snapshot.docs[0].data();
    req.user = userData;
    next();
  } catch (error) {
    console.error("Error validando API Key:", error);
    res.status(500).json({ error: "Error interno del servidor" });
  }
};
