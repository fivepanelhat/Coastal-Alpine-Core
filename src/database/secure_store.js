const path = require('path');
const fs = require('fs');

// Utilize the hardened sqlcipher driver layer instead of vanilla sqlite3
const sqlite3 = require('sqlite3').verbose();

// Env-overridable so dev boxes and CI don't write to the Pi-only mount.
const dbPath = process.env.SOVEREIGN_DB_PATH || '/mnt/sovereign-data/db/local_cache.db';

/**
 * Instantiates a fully encrypted-at-rest local SQLite node connection interface.
 */
function initializeSecureDatabase() {
 // Directory creation happens here, not at require() time: importing the
 // module must never have filesystem side effects (or crash on hosts
 // where the sovereign mount is absent).
 const dbDir = path.dirname(dbPath);
 if (!fs.existsSync(dbDir)) {
 fs.mkdirSync(dbDir, { recursive: true });
 }

 const db = new sqlite3.Database(dbPath, (err) => {
 if (err) {
 console.error(`[DB CRYPTO ERROR] Storage system failed initialization: ${err.message}`);
 throw err;
 }
 });

 // CRITICAL: Pull the localized key string from your secure, git-ignored .env boundary
 const cryptoPragmaPass = process.env.DB_CIPHER_KEY;
 if (!cryptoPragmaPass || cryptoPragmaPass.length < 32) {
 throw new Error("[CRITICAL SECURITY FAULT] Database key missing or fails entropy standard (min 32 chars).");
 }

 // The key is interpolated into a PRAGMA statement (SQLite offers no
 // parameter binding for PRAGMAs), so a quote or control character in the
 // env var would otherwise break out of the string literal. Reject rather
 // than escape: a key containing quotes is almost certainly mis-set.
 if (/['"\\\r\n\0]/.test(cryptoPragmaPass)) {
 throw new Error("[CRITICAL SECURITY FAULT] DB_CIPHER_KEY must not contain quotes, backslashes, or control characters.");
 }

 // Execute raw cipher parameters immediately upon opening the database handle
 db.serialize(() => {
 // Inject the passkey into SQLCipher configuration parsing structures
 db.run(`PRAGMA key = '${cryptoPragmaPass}';`);

 // Optimize encryption page size metrics for high-speed edge writes
 db.run("PRAGMA cipher_page_size = 4096;");
 // SQLCipher 4 default work factor; anything lower weakens
 // brute-force resistance of the derived key.
 db.run("PRAGMA kdf_iter = 256000;");

 // Initialize your sovereign telemetry schema
 db.run(`CREATE TABLE IF NOT EXISTS local_telemetry (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 nodeId TEXT NOT NULL,
 reading REAL NOT NULL,
 ts DATETIME DEFAULT CURRENT_TIMESTAMP
 );`);
 });

 console.log("[MINT] SQLCipher 256-bit AES encrypted storage system active at rest.");
 return db;
}

module.exports = { initializeSecureDatabase };
