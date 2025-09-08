const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();

const db = require('./models/database');
const { requestLogger } = require('./middleware/validation');

// Import route modules
const representativesRoutes = require('./routes/representatives');

const app = express();
const PORT = process.env.PORT || 3000;
const API_VERSION = process.env.API_VERSION || 'v1';

// Security middleware
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'"],
            scriptSrc: ["'self'"],
            imgSrc: ["'self'", "data:", "https:"],
        },
    },
    hsts: {
        maxAge: 31536000,
        includeSubDomains: true,
        preload: true
    }
}));

// CORS configuration
const corsOptions = {
    origin: process.env.NODE_ENV === 'production' 
        ? ['https://yourdomain.com'] 
        : ['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:3001'],
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Content-Type', 'Authorization'],
    credentials: true
};

app.use(cors(corsOptions));

// Logging middleware
app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));
app.use(requestLogger);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Trust proxy (for production deployment)
app.set('trust proxy', 1);

// Health check endpoint
app.get('/health', async (req, res) => {
    try {
        // Test database connection
        await db.query('SELECT 1');
        
        res.status(200).json({
            status: 'OK',
            message: 'Political Representatives API is running',
            timestamp: new Date().toISOString(),
            version: API_VERSION,
            uptime: process.uptime(),
            database: 'connected'
        });
    } catch (error) {
        res.status(503).json({
            status: 'ERROR',
            message: 'Service unavailable - database connection failed',
            timestamp: new Date().toISOString(),
            database: 'disconnected'
        });
    }
});

// API information endpoint
app.get('/', (req, res) => {
    res.json({
        name: 'Political Representatives API',
        version: API_VERSION,
        description: 'API that returns political representative details for U.S. ZIP codes',
        author: 'Your Name',
        documentation: {
            endpoints: {
                health: '/health',
                representatives: `/api/${API_VERSION}/representatives?zip={zipcode}`,
                representative_detail: `/api/${API_VERSION}/representatives/{id}`,
                search: `/api/${API_VERSION}/representatives/search?name={name}`
            },
            parameters: {
                zip: 'Required 5-digit ZIP code',
                include_inactive: 'Optional: include inactive representatives (true/false)',
                branch: 'Optional: filter by branch (federal, state, local)'
            }
        },
        sample_requests: [
            `/api/${API_VERSION}/representatives?zip=11354`,
            `/api/${API_VERSION}/representatives?zip=20301&branch=federal`,
            `/api/${API_VERSION}/representatives/search?name=Schumer`
        ],
        data_sources: [
            'house.gov',
            'congress.gov',
            'state government websites'
        ],
        timestamp: new Date().toISOString()
    });
});

// Mount API routes
app.use(`/api/${API_VERSION}/representatives`, representativesRoutes);

// Database stats endpoint (for demo purposes)
app.get('/stats', async (req, res) => {
    try {
        const stats = await db.query(`
            SELECT 
                (SELECT COUNT(*) FROM geography) as zip_codes,
                (SELECT COUNT(*) FROM representatives) as representatives,
                (SELECT COUNT(*) FROM rep_geography_map) as mappings,
                (SELECT COUNT(*) FROM representatives WHERE is_active = true) as active_reps,
                (SELECT COUNT(DISTINCT branch) FROM representatives) as branches
        `);
        
        const branchStats = await db.query(`
            SELECT branch, COUNT(*) as count 
            FROM representatives 
            WHERE is_active = true 
            GROUP BY branch 
            ORDER BY count DESC
        `);
        
        res.json({
            database_statistics: stats.rows[0],
            representatives_by_branch: branchStats.rows,
            timestamp: new Date().toISOString()
        });
        
    } catch (error) {
        console.error('Stats query error:', error);
        res.status(500).json({
            error: 'Unable to fetch statistics',
            timestamp: new Date().toISOString()
        });
    }
});

// 404 handler for undefined routes
app.use('*', (req, res) => {
    res.status(404).json({
        error: 'Route not found',
        message: `The requested route ${req.originalUrl} does not exist`,
        availableEndpoints: [
            '/',
            '/health',
            '/stats',
            `/api/${API_VERSION}/representatives`
        ],
        timestamp: new Date().toISOString()
    });
});

// Global error handling middleware
app.use((err, req, res, next) => {
    console.error('Error occurred:', {
        message: err.message,
        stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
        url: req.url,
        method: req.method,
        timestamp: new Date().toISOString()
    });

    // Database connection errors
    if (err.code === 'ECONNREFUSED' || err.code === '28P01') {
        return res.status(503).json({
            error: 'Service temporarily unavailable',
            message: 'Database connection failed',
            timestamp: new Date().toISOString()
        });
    }

    // Validation errors
    if (err.name === 'ValidationError') {
        return res.status(422).json({
            error: 'Validation failed',
            message: err.message,
            timestamp: new Date().toISOString()
        });
    }

    // Default error response
    const status = err.status || err.statusCode || 500;
    const message = err.message || 'Internal Server Error';

    res.status(status).json({
        error: {
            message: message,
            status: status,
            ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
        },
        timestamp: new Date().toISOString()
    });
});

// Start server function
const startServer = async () => {
    try {
        // Test database connection
        await db.testConnection();
        
        // Start server
        const server = app.listen(PORT, () => {
            console.log(`🚀 Political Representatives API Server started`);
            console.log(`📍 Server running on port ${PORT}`);
            console.log(`🌐 Environment: ${process.env.NODE_ENV || 'development'}`);
            console.log(`📊 Health check: http://localhost:${PORT}/health`);
            console.log(`📖 API docs: http://localhost:${PORT}/`);
            console.log(`⚡ API endpoint: http://localhost:${PORT}/api/${API_VERSION}/representatives`);
            console.log(`📈 Statistics: http://localhost:${PORT}/stats`);
            console.log(`🐍 To run scraper: npm run scrape`);
        });

        return server;
    } catch (error) {
        console.error('Failed to start server:', error);
        process.exit(1);
    }
};

// Handle graceful shutdown
const gracefulShutdown = async (signal) => {
    console.log(`\n🛑 Received ${signal}. Starting graceful shutdown...`);
    
    try {
        // Close database connections
        await db.closePool();
        console.log('✅ Database connections closed');
        
        console.log('✅ Server shut down gracefully');
        process.exit(0);
    } catch (error) {
        console.error('❌ Error during shutdown:', error);
        process.exit(1);
    }
};

// Listen for shutdown signals
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    gracefulShutdown('uncaughtException');
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    gracefulShutdown('unhandledRejection');
});

// Start the server if this file is run directly
if (require.main === module) {
    startServer();
}

module.exports = app;