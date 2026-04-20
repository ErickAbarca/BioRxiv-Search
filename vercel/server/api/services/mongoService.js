const { MongoClient } = require("mongodb");
//Conexión a Mongo
let client;

async function getMongoClient() {
  if (!client) {
    client = new MongoClient(process.env.MONGODB_URI);
    await client.connect();
    console.log("MongoDB client connected");
  }
  return client;
}

module.exports = { getMongoClient };