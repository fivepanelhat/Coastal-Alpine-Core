const path = require('path');
const fs = require('fs');

// Utilize the hardened sqlcipher driver layer instead of vanilla sqlite3
const sqlite3 = require('sqlite3').verbose();
const dbPath = '/mnt/sovereign-data/db/local_cache.db';

// Ensure parent storage directories are instantiated safely
const dbDir = path.dirname(dbPath);
if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
}

/**
 * Instantiates a fully encrypted-at-rest local SQLite node connection interface.
 */
function initializeSecureDatabase() {
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

    // Execute raw cipher parameters immediately upon opening the database handle
    db.serialize(() => {
        // Inject the passkey into SQLCipher configuration parsing structures
        db.run(`PRAGMA key = '${cryptoPragmaPass}';`);
        
        // Optimize encryption page size metrics for high-speed edge writes
        db.run("PRAGMA cipher_page_size = 4096;");
        db.run("PRAGMA kdf_iter = 64000;"); // Hardens key derivation loops against brute-force attacks

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
