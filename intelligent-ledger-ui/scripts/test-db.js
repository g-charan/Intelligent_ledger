// Quick DB tester: reads DATABASE_URL from .env.local and runs a test query
const fs = require("fs");
const path = require("path");
const { Pool } = require("pg");

function loadDatabaseUrl() {
  const envPath = path.resolve(__dirname, "..", ".env.local");
  if (!fs.existsSync(envPath)) throw new Error(".env.local not found");
  const content = fs.readFileSync(envPath, "utf8");
  const m = content.match(/^[\s\"]*DATABASE_URL\s*=\s*\"?(.*?)\"?\s*$/m);
  if (!m) throw new Error("DATABASE_URL not found in .env.local");
  return m[1];
}

async function main() {
  const connectionString = loadDatabaseUrl();
  console.log("Using DB:", connectionString.replace(/:[^:@]+@/, ":*****@"));

  const pool = new Pool({ connectionString, max: 5 });

  try {
    const res = await pool.query(
      `SELECT id, status, amount, raw_text, transaction_timestamp
       FROM transactions
       ORDER BY transaction_timestamp DESC
       LIMIT 10;`,
    );

    console.log("rows:", res.rowCount);
    console.log(JSON.stringify(res.rows, null, 2));
  } catch (err) {
    console.error("Query error:", err);
    process.exitCode = 2;
  } finally {
    await pool.end();
  }
}

main();
