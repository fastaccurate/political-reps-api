const express = require('express');
const router = express.Router();
const db = require('../models/database');
const { createValidator, rateLimit, asyncHandler } = require('../middleware/validation');

// Apply rate limiting to all routes in this router
router.use(rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    maxRequests: 100,
    message: 'Too many requests to representatives API, please try again later'
}));

/**
 * GET /representatives
 * Returns political representatives for a given ZIP code
 * Query Parameters:
 *   - zip (required): 5-digit ZIP code
 *   - include_inactive (optional): Include inactive representatives (default: false)
 *   - branch (optional): Filter by branch (federal, state, local)
 */
router.get('/', 
    createValidator('zipQuery', 'query'),
    asyncHandler(async (req, res) => {
        const { zip, include_inactive = 'false', branch } = req.query;
        
        try {
            // Get geography data for the ZIP code
            const geoQuery = `
                SELECT 
                    id, zip_code, city, state, state_name, 
                    county, congressional_district, latitude, longitude
                FROM geography 
                WHERE zip_code = $1
            `;
            
            const geoResult = await db.query(geoQuery, [zip]);

            if (geoResult.rows.length === 0) {
                return res.status(404).json({
                    error: 'ZIP code not found',
                    message: `No data available for ZIP code ${zip}`,
                    suggestion: 'Please verify the ZIP code or try a nearby area',
                    timestamp: new Date().toISOString()
                });
            }

            const geography = geoResult.rows[0];

            // Build representatives query with optional filters
            let repQuery = `
                SELECT 
                    r.id, r.name, r.title, r.party, r.branch, r.office_type,
                    r.phone, r.email, r.website, r.photo_url,
                    r.address_line1, r.address_line2, r.address_city, 
                    r.address_state, r.address_zip,
                    r.term_start, r.term_end, r.is_active,
                    rgm.jurisdiction_level
                FROM representatives r
                JOIN rep_geography_map rgm ON r.id = rgm.representative_id
                WHERE rgm.geography_id = $1
            `;

            const queryParams = [geography.id];
            let paramCounter = 2;

            // Add filters based on query parameters
            if (include_inactive !== 'true') {
                repQuery += ` AND r.is_active = true`;
            }

            if (branch) {
                repQuery += ` AND r.branch = $${paramCounter}`;
                queryParams.push(branch);
                paramCounter++;
            }

            repQuery += ` ORDER BY 
                CASE r.branch 
                    WHEN 'federal' THEN 1 
                    WHEN 'state' THEN 2 
                    WHEN 'local' THEN 3 
                END, 
                r.name`;

            const repResult = await db.query(repQuery, queryParams);

            // Format response
            const representatives = repResult.rows.map(rep => ({
                id: rep.id,
                name: rep.name,
                title: rep.title,
                party: rep.party,
                branch: rep.branch,
                office_type: rep.office_type,
                contact: {
                    phone: rep.phone,
                    email: rep.email,
                    website: rep.website
                },
                address: rep.address_line1 ? {
                    line1: rep.address_line1,
                    line2: rep.address_line2,
                    city: rep.address_city,
                    state: rep.address_state,
                    zip: rep.address_zip
                } : null,
                photo_url: rep.photo_url,
                term: {
                    start: rep.term_start,
                    end: rep.term_end
                },
                is_active: rep.is_active,
                jurisdiction_level: rep.jurisdiction_level
            }));

            // Group representatives by branch for better organization
            const groupedReps = {
                federal: representatives.filter(rep => rep.branch === 'federal'),
                state: representatives.filter(rep => rep.branch === 'state'),
                local: representatives.filter(rep => rep.branch === 'local')
            };

            const response = {
                zip: geography.zip_code,
                location: {
                    city: geography.city,
                    state: geography.state,
                    state_name: geography.state_name,
                    county: geography.county,
                    congressional_district: geography.congressional_district,
                    coordinates: geography.latitude && geography.longitude ? {
                        latitude: parseFloat(geography.latitude),
                        longitude: parseFloat(geography.longitude)
                    } : null
                },
                representatives: {
                    count: representatives.length,
                    by_branch: {
                        federal: groupedReps.federal,
                        state: groupedReps.state,
                        local: groupedReps.local
                    },
                    all: representatives
                },
                meta: {
                    timestamp: new Date().toISOString(),
                    include_inactive: include_inactive === 'true',
                    branch_filter: branch || 'all'
                }
            };

            res.json(response);

        } catch (error) {
            console.error('Database error in representatives route:', error);
            res.status(500).json({
                error: 'Internal server error',
                message: 'Unable to fetch representatives data',
                timestamp: new Date().toISOString()
            });
        }
    })
);

/**
 * GET /representatives/:id
 * Get detailed information about a specific representative
 */
router.get('/:id', 
    asyncHandler(async (req, res) => {
        const { id } = req.params;

        if (!id || isNaN(parseInt(id))) {
            return res.status(400).json({
                error: 'Invalid representative ID',
                message: 'Representative ID must be a valid number',
                timestamp: new Date().toISOString()
            });
        }

        try {
            const query = `
                SELECT 
                    r.*,
                    array_agg(
                        json_build_object(
                            'zip_code', g.zip_code,
                            'city', g.city,
                            'state', g.state,
                            'congressional_district', g.congressional_district
                        )
                    ) as served_areas
                FROM representatives r
                LEFT JOIN rep_geography_map rgm ON r.id = rgm.representative_id
                LEFT JOIN geography g ON rgm.geography_id = g.id
                WHERE r.id = $1
                GROUP BY r.id
            `;

            const result = await db.query(query, [parseInt(id)]);

            if (result.rows.length === 0) {
                return res.status(404).json({
                    error: 'Representative not found',
                    message: `No representative found with ID ${id}`,
                    timestamp: new Date().toISOString()
                });
            }

            const rep = result.rows[0];
            
            const response = {
                id: rep.id,
                name: rep.name,
                title: rep.title,
                party: rep.party,
                branch: rep.branch,
                office_type: rep.office_type,
                contact: {
                    phone: rep.phone,
                    email: rep.email,
                    website: rep.website
                },
                address: rep.address_line1 ? {
                    line1: rep.address_line1,
                    line2: rep.address_line2,
                    city: rep.address_city,
                    state: rep.address_state,
                    zip: rep.address_zip
                } : null,
                photo_url: rep.photo_url,
                term: {
                    start: rep.term_start,
                    end: rep.term_end
                },
                is_active: rep.is_active,
                served_areas: rep.served_areas.filter(area => area.zip_code !== null),
                created_at: rep.created_at,
                updated_at: rep.updated_at
            };

            res.json(response);

        } catch (error) {
            console.error('Database error in representative detail route:', error);
            res.status(500).json({
                error: 'Internal server error',
                message: 'Unable to fetch representative details',
                timestamp: new Date().toISOString()
            });
        }
    })
);

/**
 * GET /representatives/search
 * Search representatives by name or other criteria
 */
router.get('/search', 
    asyncHandler(async (req, res) => {
        const { 
            name, 
            party, 
            branch, 
            state,
            limit = 20,
            offset = 0 
        } = req.query;

        if (!name && !party && !branch && !state) {
            return res.status(400).json({
                error: 'Search criteria required',
                message: 'Please provide at least one search parameter (name, party, branch, or state)',
                timestamp: new Date().toISOString()
            });
        }

        try {
            let query = `
                SELECT DISTINCT
                    r.id, r.name, r.title, r.party, r.branch, r.office_type,
                    r.phone, r.email, r.website, r.is_active,
                    COUNT(*) OVER() as total_count
                FROM representatives r
                LEFT JOIN rep_geography_map rgm ON r.id = rgm.representative_id
                LEFT JOIN geography g ON rgm.geography_id = g.id
                WHERE r.is_active = true
            `;

            const queryParams = [];
            let paramCounter = 1;

            if (name) {
                query += ` AND r.name ILIKE $${paramCounter}`;
                queryParams.push(`%${name}%`);
                paramCounter++;
            }

            if (party) {
                query += ` AND r.party ILIKE $${paramCounter}`;
                queryParams.push(`%${party}%`);
                paramCounter++;
            }

            if (branch) {
                query += ` AND r.branch = $${paramCounter}`;
                queryParams.push(branch);
                paramCounter++;
            }

            if (state) {
                query += ` AND g.state = $${paramCounter}`;
                queryParams.push(state.toUpperCase());
                paramCounter++;
            }

            query += ` ORDER BY r.name LIMIT $${paramCounter} OFFSET $${paramCounter + 1}`;
            queryParams.push(parseInt(limit), parseInt(offset));

            const result = await db.query(query, queryParams);

            const response = {
                results: result.rows.map(rep => ({
                    id: rep.id,
                    name: rep.name,
                    title: rep.title,
                    party: rep.party,
                    branch: rep.branch,
                    office_type: rep.office_type,
                    contact: {
                        phone: rep.phone,
                        email: rep.email,
                        website: rep.website
                    },
                    is_active: rep.is_active
                })),
                pagination: {
                    total: result.rows.length > 0 ? parseInt(result.rows[0].total_count) : 0,
                    limit: parseInt(limit),
                    offset: parseInt(offset),
                    has_more: result.rows.length === parseInt(limit)
                },
                search_criteria: {
                    name: name || null,
                    party: party || null,
                    branch: branch || null,
                    state: state || null
                },
                timestamp: new Date().toISOString()
            };

            res.json(response);

        } catch (error) {
            console.error('Database error in representatives search:', error);
            res.status(500).json({
                error: 'Internal server error',
                message: 'Unable to perform search',
                timestamp: new Date().toISOString()
            });
        }
    })
);

module.exports = router;