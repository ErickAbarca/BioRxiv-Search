const { getMongoClient } = require("../services/mongoService");

//Busqueda de articulos
exports.searchArticles = async (req, res) => {
  try {
    const { q } = req.query;
    if (!q) {
      return res.status(400).json({ error: "Query parameter 'q' is required" });
    }

    const client = await getMongoClient();
    const collection = client.db("prueba_proyecto").collection("documents");//conexión a la BD

    const results = await collection.aggregate([
      {
        $search: {
          index: "default_1",//nombre del index
          text: {
            query: q, //consulta de búsqueda
            path: ["title", "abstract"]
          },
          highlight: {
            path: ["title", "abstract"]
          }
        }
      },
      {
        $addFields: {
          rel_date: {
            $cond: [
              { $eq: [{ $type: "$rel_date" }, "date"] },
              "$rel_date",
              {
                $dateFromString: {
                  dateString: "$rel_date",
                  format: "%d/%m/%Y"// le damos el formato de fecha
                }
              }
            ]
          }
        }
      },
      {
        $facet: {
          results: [
            {
              $project: {
                _id: 1,
                title: 1,
                abstract: 1,
                link: 1,
                doi: 1,
                category: 1,
                rel_date: 1,
                entities: 1,
                type: 1,
                authors: 1,
                score: { $meta: "searchScore" },// puntuación de búsqueda
                highlights: { $meta: "searchHighlights" }// guardar los fragmentos destacados
              }
            }
          ],
          category_facet: [
            {
              $group: {
                _id: "$category",
                count: { $sum: 1 }
              }
            }
          ],
          date_facet: [
            {
              $bucket: {
                groupBy: "$rel_date",
                boundaries: [
                  new Date("2020-01-01"),
                  new Date("2021-01-01"),
                  new Date("2022-01-01"),
                  new Date("2023-01-01"),
                  new Date("2024-01-01"),
                  new Date("2025-01-01")
                ],
                default: "Other",
                output: { count: { $sum: 1 } }
              }
            }
          ],
          entities_facet: [
            { $unwind: "$entities" },
            {
              $group: {
                _id: "$entities",
                count: { $sum: 1 }
              }
            }
          ],
          type_facet: [
            {
              $group: {
                _id: "$type",
                count: { $sum: 1 }
              }
            }
          ],
          author_name_facet: [
            { $unwind: "$authors" },
            {
              $group: {
                _id: "$authors.author_name",
                count: { $sum: 1 }
              }
            }
          ],
          author_inst_facet: [
            { $unwind: "$authors" },
            { $unwind: "$authors.author_inst" },
            {
              $group: {
                _id: "$authors.author_inst",
                count: { $sum: 1 }
              }
            }
          ]
        }
      }
    ]).toArray();

    if (!results || results.length === 0) {
      return res.status(404).json({ error: "No results found" });
    }

    res.status(200).json(results[0]);
  } catch (err) {
    console.error("Search error:", err);
    res.status(500).json({ error: "Search failed", details: err.message });
  }
};