const { Pool } = require('pg');
require('dotenv').config();

// Database connection configuration
const dbConfig = {
    user: process.env.DB_USER || 'postgres',
    host: process.env.DB_HOST || 'localhost',
    database: process.env.DB_NAME || 'political_reps_db',
    password: process.env.DB_PASSWORD,
    port: process.env.DB_PORT || 5432,
    // Connection pool settings
    max: 20, // Maximum number of clients in pool
    idleTimeoutMillis: 30000, // How long a client is allowed to remain idle
    connectionTimeoutMillis: 2000, // How long to wait when connecting
};

// Create connection pool
const pool = new Pool(dbConfig);

// Handle pool errors
pool.on('error', (err, client) => {
    console.error('Unexpected error on idle client', err);
    process.exit(-1);
});

// Test database connection
const testConnection = async () => {
    try {
        const client = await pool.connect();
        const result = await client.query('SELECT NOW()');
        console.log('Database connected successfully at:', result.rows[0].now);
        client.release();
    } catch (err) {
        console.error('Database connection error:', err);
        throw err;
    }
};

// Query wrapper with error handling
const query = async (text, params = []) => {
    const start = Date.now();
    try {
        const result = await pool.query(text, params);
        const duration = Date.now() - start;
        
        if (process.env.NODE_ENV === 'development') {
            console.log('Executed query', { text, duration, rows: result.rowCount });
        }
        
        return result;
    } catch (error) {
        console.error('Database query error:', error);
        throw error;
    }
};

// Transaction wrapper
const transaction = async (callback) => {
    const client = await pool.connect();
    try {
        await client.query('BEGIN');
        const result = await callback(client);
        await client.query('COMMIT');
        return result;
    } catch (error) {
        await client.query('ROLLBACK');
        throw error;
    } finally {
        client.release();
    }
};

// Graceful shutdown
const closePool = async () => {
    try {
        await pool.end();
        console.log('Database pool closed');
    } catch (err) {
        console.error('Error closing database pool:', err);
    }
};

// Handle process termination
process.on('SIGINT', closePool);
process.on('SIGTERM', closePool);

module.exports = {
    pool,
    query,
    transaction,
    testConnection,
    closePool
};