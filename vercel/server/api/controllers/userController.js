const admin = require("../services/firebaseService");
const generateApiKey = require("../utils/generateApiKey");
const { hashPassword, comparePassword } = require("../utils/hashPassword");

// REGISTER
exports.registerUser = async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password)
    return res.status(400).json({ error: "Email y contraseña son requeridos" });

  try {
    const db = admin.firestore();
    const usersRef = db.collection("users");
    const existing = await usersRef.where("email", "==", email).get();

    if (!existing.empty)
      return res.status(409).json({ error: "Este usuario ya existe" });

    const hashedPassword = await hashPassword(password);
    const apiKey = generateApiKey();

    const user = { email, password: hashedPassword, apiKey };
    await usersRef.add(user);

    res.status(201).json({ email, apiKey });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Error en el servidor" });
  }
};

// LOGIN
exports.loginUser = async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password)
    return res.status(400).json({ error: "Email y contraseña son requeridos" });

  try {
    const db = admin.firestore();
    const usersRef = db.collection("users");
    const snapshot = await usersRef.where("email", "==", email).get();

    if (snapshot.empty)
      return res.status(401).json({ error: "Credenciales inválidas" });

    const userDoc = snapshot.docs[0];
    const user = userDoc.data();

    const match = await comparePassword(password, user.password);
    if (!match)
      return res.status(401).json({ error: "Credenciales inválidas" });

    res.status(200).json({ email: user.email, apiKey: user.apiKey });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: "Error en el servidor" });
  }
};
