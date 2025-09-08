const Joi = require('joi');

// Validation schemas for different endpoints
const schemas = {
    zipQuery: Joi.object({
        zip: Joi.string()
            .pattern(/^\d{5}$/)
            .required()
            .messages({
                'string.pattern.base': 'ZIP code must be exactly 5 digits',
                'any.required': 'ZIP code is required'
            })
    }),
    
    representativeBody: Joi.object({
        name: Joi.string().min(2).max(200).required(),
        title: Joi.string().min(2).max(100).required(),
        party: Joi.string().max(50).optional(),
        branch: Joi.string().valid('federal', 'state', 'local').required(),
        office_type: Joi.string().max(100).optional(),
        phone: Joi.string().pattern(/^[\d\s\-\(\)\+]+$/).optional(),
        email: Joi.string().email().optional(),
        website: Joi.string().uri().optional(),
        photo_url: Joi.string().uri().optional(),
        address_line1: Joi.string().max(200).optional(),
        address_line2: Joi.string().max(200).optional(),
        address_city: Joi.string().max(100).optional(),
        address_state: Joi.string().length(2).optional(),
        address_zip: Joi.string().max(10).optional(),
        term_start: Joi.date().optional(),
        term_end: Joi.date().optional(),
        is_active: Joi.boolean().default(true)
    }),

    geographyBody: Joi.object({
        zip_code: Joi.string().pattern(/^\d{5}$/).required(),
        city: Joi.string().max(100).optional(),
        state: Joi.string().length(2).required(),
        state_name: Joi.string().max(50).optional(),
        county: Joi.string().max(100).optional(),
        congressional_district: Joi.string().max(3).optional(),
        latitude: Joi.number().min(-90).max(90).optional(),
        longitude: Joi.number().min(-180).max(180).optional()
    })
};

// Generic validation middleware factory
const createValidator = (schemaName, source = 'body') => {
    return (req, res, next) => {
        const schema = schemas[schemaName];
        
        if (!schema) {
            return res.status(500).json({
                error: 'Internal server error - invalid validation schema',
                timestamp: new Date().toISOString()
            });
        }

        // Determine which part of request to validate
        let dataToValidate;
        switch (source) {
            case 'query':
                dataToValidate = req.query;
                break;
            case 'params':
                dataToValidate = req.params;
                break;
            case 'headers':
                dataToValidate = req.headers;
                break;
            default:
                dataToValidate = req.body;
        }

        // Perform validation
        const { error, value } = schema.validate(dataToValidate, {
            abortEarly: false,
            stripUnknown: true,
            convert: true
        });

        if (error) {
            const errorDetails = error.details.map(detail => ({
                field: detail.path.join('.'),
                message: detail.message,
                value: detail.context?.value
            }));

            return res.status(422).json({
                error: 'Validation failed',
                details: errorDetails,
                timestamp: new Date().toISOString()
            });
        }

        // Replace original data with validated/sanitized data
        switch (source) {
            case 'query':
                req.query = value;
                break;
            case 'params':
                req.params = value;
                break;
            case 'headers':
                req.headers = value;
                break;
            default:
                req.body = value;
        }

        next();
    };
};

// Rate limiting middleware (simple implementation)
const rateLimitStore = new Map();

const rateLimit = (options = {}) => {
    const {
        windowMs = 15 * 60 * 1000, // 15 minutes
        maxRequests = 100,
        message = 'Too many requests, please try again later'
    } = options;

    return (req, res, next) => {
        const clientIP = req.ip || req.connection.remoteAddress;
        const now = Date.now();
        const windowStart = now - windowMs;

        // Clean up old entries
        const clientRequests = rateLimitStore.get(clientIP) || [];
        const validRequests = clientRequests.filter(timestamp => timestamp > windowStart);

        // Check if limit exceeded
        if (validRequests.length >= maxRequests) {
            return res.status(429).json({
                error: message,
                retryAfter: Math.ceil(windowMs / 1000),
                timestamp: new Date().toISOString()
            });
        }

        // Add current request
        validRequests.push(now);
        rateLimitStore.set(clientIP, validRequests);

        next();
    };
};

// Request logging middleware
const requestLogger = (req, res, next) => {
    const start = Date.now();
    
    // Override res.end to capture response time
    const originalEnd = res.end;
    res.end = function(...args) {
        const duration = Date.now() - start;
        
        console.log(`${req.method} ${req.originalUrl} - ${res.statusCode} - ${duration}ms - ${req.ip}`);
        
        originalEnd.apply(this, args);
    };

    next();
};

// Error handling for async route handlers
const asyncHandler = (fn) => {
    return (req, res, next) => {
        Promise.resolve(fn(req, res, next)).catch(next);
    };
};

module.exports = {
    schemas,
    createValidator,
    rateLimit,
    requestLogger,
    asyncHandler
};