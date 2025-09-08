-- Political Representatives Database Schema
-- Drop tables if they exist (for fresh setup)
DROP TABLE IF EXISTS rep_geography_map CASCADE;
DROP TABLE IF EXISTS representatives CASCADE;
DROP TABLE IF EXISTS geography CASCADE;

-- Create geography table for ZIP code and location data
CREATE TABLE geography (
    id SERIAL PRIMARY KEY,
    zip_code VARCHAR(5) NOT NULL UNIQUE,
    city VARCHAR(100),
    state VARCHAR(2) NOT NULL,
    state_name VARCHAR(50),
    county VARCHAR(100),
    congressional_district VARCHAR(3),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create representatives table for political representatives
CREATE TABLE representatives (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    title VARCHAR(100) NOT NULL,
    party VARCHAR(50),
    branch VARCHAR(20) NOT NULL CHECK (branch IN ('federal', 'state', 'local')),
    office_type VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(200),
    website VARCHAR(500),
    photo_url VARCHAR(500),
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    address_city VARCHAR(100),
    address_state VARCHAR(2),
    address_zip VARCHAR(10),
    term_start DATE,
    term_end DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create mapping table between geography and representatives
CREATE TABLE rep_geography_map (
    id SERIAL PRIMARY KEY,
    representative_id INTEGER NOT NULL REFERENCES representatives(id) ON DELETE CASCADE,
    geography_id INTEGER NOT NULL REFERENCES geography(id) ON DELETE CASCADE,
    jurisdiction_level VARCHAR(20) NOT NULL CHECK (jurisdiction_level IN ('federal', 'state', 'local')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(representative_id, geography_id)
);

-- Create indexes for performance optimization
CREATE INDEX idx_geography_zip ON geography(zip_code);
CREATE INDEX idx_geography_state ON geography(state);
CREATE INDEX idx_geography_district ON geography(congressional_district);
CREATE INDEX idx_representatives_name ON representatives(name);
CREATE INDEX idx_representatives_branch ON representatives(branch);
CREATE INDEX idx_representatives_active ON representatives(is_active);
CREATE INDEX idx_map_geography ON rep_geography_map(geography_id);
CREATE INDEX idx_map_representative ON rep_geography_map(representative_id);
CREATE INDEX idx_map_jurisdiction ON rep_geography_map(jurisdiction_level);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updating updated_at columns
CREATE TRIGGER update_geography_updated_at 
    BEFORE UPDATE ON geography 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_representatives_updated_at 
    BEFORE UPDATE ON representatives 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO geography (zip_code, city, state, state_name, county, congressional_district) VALUES
('11354', 'Flushing', 'NY', 'New York', 'Queens', '06'),
('20301', 'Washington', 'DC', 'District of Columbia', 'District of Columbia', '00'),
('90210', 'Beverly Hills', 'CA', 'California', 'Los Angeles', '30');

-- Insert sample representatives
INSERT INTO representatives (name, title, party, branch, office_type, website, is_active) VALUES
('Grace Meng', 'U.S. House Rep, NY-6', 'Democratic', 'federal', 'House Representative', 'https://meng.house.gov', true),
('Chuck Schumer', 'U.S. Senator, NY', 'Democratic', 'federal', 'Senator', 'https://www.schumer.senate.gov', true),
('Kirsten Gillibrand', 'U.S. Senator, NY', 'Democratic', 'federal', 'Senator', 'https://www.gillibrand.senate.gov', true),
('Kathy Hochul', 'Governor, New York', 'Democratic', 'state', 'Governor', 'https://www.governor.ny.gov', true);

-- Create mappings for sample data
INSERT INTO rep_geography_map (representative_id, geography_id, jurisdiction_level) VALUES
-- NY representatives for Flushing, NY (11354)
(1, 1, 'federal'), -- Grace Meng
(2, 1, 'federal'), -- Chuck Schumer
(3, 1, 'federal'), -- Kirsten Gillibrand
(4, 1, 'state');   -- Kathy Hochul

-- Verify the setup
SELECT 'Geography records:' as info, COUNT(*) as count FROM geography
UNION ALL
SELECT 'Representative records:' as info, COUNT(*) as count FROM representatives
UNION ALL
SELECT 'Mapping records:' as info, COUNT(*) as count FROM rep_geography_map;