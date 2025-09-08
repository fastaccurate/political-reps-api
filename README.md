# Political Representatives API

A prototype API that returns political representative details for U.S. ZIP codes, built for the Civic Tracker technical challenge.

## 🎯 Project Overview

This API allows users to query political representatives (federal, state, and local) for any given U.S. ZIP code. The system includes a web scraping agent that automatically fetches representative data from official government sources and stores it in a PostgreSQL database.

## 🏗️ Architecture

- **API Backend**: Node.js with Express.js
- **Database**: PostgreSQL with properly normalized schema
- **Web Scraping**: Python with BeautifulSoup and Requests
- **Data Sources**: Official government websites (house.gov, congress.gov, state sites)
- **Validation**: Joi middleware for input validation
- **Security**: Helmet, CORS, rate limiting

## 📋 Prerequisites

- Node.js 16.0+
- Python 3.8+
- PostgreSQL 12+
- Git

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/political-reps-api.git
cd political-reps-api
```

### 2. Database Setup
```bash
# Create PostgreSQL database
createdb political_reps_db

# Run schema setup
psql -U postgres -d political_reps_db -f database/schema.sql
```

### 3. Install Dependencies

#### Backend (Node.js)
```bash
npm install
```

#### Scrapers (Python)
```bash
cd scrapers
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cd ..
```

### 4. Environment Configuration
```bash
# Copy and edit environment file
cp .env.example .env

# Edit .env with your database credentials:
# DB_PASSWORD=your_password_here
```

### 5. Run the Scrapers (Data Population)
```bash
# Run demo scraping for sample ZIP codes
npm run scrape

# Or run manually with Python:
cd scrapers
python main_scraper.py --demo
```

### 6. Start the API Server
```bash
# Development mode with auto-restart
npm run dev

# Production mode
npm start
```

## 📡 API Endpoints

### Health Check
```
GET /health
```
Returns API status and database connectivity.

### API Information
```
GET /
```
Returns API documentation and available endpoints.

### Get Representatives by ZIP Code
```
GET /api/v1/representatives?zip={zipcode}
```

**Parameters:**
- `zip` (required): 5-digit ZIP code
- `include_inactive` (optional): Include inactive representatives (default: false)
- `branch` (optional): Filter by branch (federal, state, local)

**Example Request:**
```bash
curl "http://localhost:3000/api/v1/representatives?zip=11354"
```

**Example Response:**
```json
{
  "zip": "11354",
  "location": {
    "city": "Flushing",
    "state": "NY",
    "state_name": "New York",
    "congressional_district": "06"
  },
  "representatives": {
    "count": 4,
    "by_branch": {
      "federal": [
        {
          "name": "Grace Meng",
          "title": "U.S. House Rep, NY-6",
          "party": "Democratic",
          "branch": "federal",
          "contact": {
            "phone": "(202) 225-2601",
            "website": "https://meng.house.gov"
          }
        }
      ],
      "state": [
        {
          "name": "Kathy Hochul",
          "title": "Governor, New York",
          "party": "Democratic",
          "branch": "state"
        }
      ]
    }
  }
}
```

### Get Representative Details
```
GET /api/v1/representatives/{id}
```

### Search Representatives
```
GET /api/v1/representatives/search?name={name}&party={party}&branch={branch}
```

### Database Statistics
```
GET /stats
```

## 🗃️ Database Schema

The system uses three main tables:

- **geography**: ZIP code location data (zip_code, city, state, congressional_district)
- **representatives**: Political representative information (name, title, party, contact info)
- **rep_geography_map**: Many-to-many relationship mapping

## 🔧 Development Scripts

```bash
npm run dev          # Start development server with auto-reload
npm start           # Start production server
npm run setup-db    # Initialize database schema
npm run scrape      # Run web scraping agent

# Python scraper options:
cd scrapers
python main_scraper.py --demo                    # Demo with sample ZIPs
python main_scraper.py --zip 11354              # Single ZIP code
python main_scraper.py --zip-file ziplist.txt   # Batch from file
```

## 🧪 Testing the API

### Sample ZIP Codes Available:
- `11354` - Flushing, NY (Grace Meng, Chuck Schumer, Kirsten Gillibrand, Kathy Hochul)
- `20301` - Washington, DC (Eleanor Holmes Norton) 
- `90210` - Beverly Hills, CA (Brad Sherman, Dianne Feinstein, Alex Padilla, Gavin Newsom)

### Test Commands:
```bash
# Basic representative lookup
curl "http://localhost:3000/api/v1/representatives?zip=11354"

# Filter by branch
curl "http://localhost:3000/api/v1/representatives?zip=11354&branch=federal"

# Search by name
curl "http://localhost:3000/api/v1/representatives/search?name=Schumer"

# Health check
curl "http://localhost:3000/health"

# API statistics
curl "http://localhost:3000/stats"
```

## 🐍 Web Scraping System

The Python scraping system includes:

- **BaseScraper**: Abstract base class with database connectivity and common utilities
- **HouseRepresentativeScraper**: Scrapes house.gov and related sources
- **RepresentativeDataProcessor**: Orchestrates scraping and data processing

### Scraper Features:
- Respectful rate limiting with delays between requests
- User agent rotation to avoid detection  
- Retry logic for failed requests
- Data validation and normalization
- Duplicate detection and removal
- Comprehensive error handling and logging

### Running Custom Scrapes:
```bash
cd scrapers

# Process specific ZIP codes
python main_scraper.py --zip 10001 --verbose

# Process from file
echo "10001\n10002\n10003" > ziplist.txt
python main_scraper.py --zip-file ziplist.txt

# View detailed logs
tail -f scraper.log
```

## 🔒 Security & Performance Features

- **Input Validation**: Joi schemas for all API inputs
- **Rate Limiting**: Prevents API abuse (100 requests/15 minutes)
- **Security Headers**: Helmet.js for security best practices
- **CORS**: Configured for cross-origin requests
- **Database Connection Pooling**: Efficient database resource management
- **Error Handling**: Comprehensive error responses with appropriate HTTP codes
- **Logging**: Request/response logging with Morgan and custom middleware

## 🚢 Deployment Ready

The application includes production-ready features:

- Environment-based configuration
- Graceful shutdown handling
- Health check endpoints
- Error tracking and logging
- Database connection monitoring
- Process management with PM2 support

## 📊 Current Status

### ✅ Completed Features
- [x] Complete database schema with sample data
- [x] RESTful API with comprehensive endpoints  
- [x] Input validation and error handling
- [x] Python web scraping system
- [x] Rate limiting and security middleware
- [x] Comprehensive documentation
- [x] Production-ready server configuration
- [x] Sample data for 3 ZIP codes

### 🎥 Demo Video

A demonstration video showing:
1. API endpoints working with sample ZIP codes
2. Database schema and data relationships  
3. Python scraping system in action
4. Design decisions and architecture explanation

**Video Link**: [Upload to Google Drive and include link here]

## 🔮 Future Enhancements

For production deployment, additional features could include:

- **Authentication & Authorization**: API keys or OAuth
- **Caching Layer**: Redis for improved performance  
- **Comprehensive Testing**: Unit, integration, and API tests
- **CI/CD Pipeline**: Automated testing and deployment
- **Monitoring**: Application performance monitoring
- **Data Freshness**: Automated scraping schedules
- **Geographic Expansion**: Support for all U.S. ZIP codes
- **Advanced Search**: Full-text search capabilities
- **API Versioning**: Multiple API versions support

## 🤝 Technical Decisions

### Database Design
- **PostgreSQL**: Chosen for ACID compliance and complex queries
- **Normalized Schema**: Separate tables for geography, representatives, and mappings
- **Indexing Strategy**: Optimized for ZIP code lookups and searches

### API Architecture  
- **Express.js**: Lightweight, fast, and well-documented
- **Joi Validation**: Schema-based validation with detailed error messages
- **Modular Routes**: Separation of concerns with dedicated route files

### Web Scraping Approach
- **BeautifulSoup**: Reliable HTML parsing with good error handling
- **Respectful Scraping**: Rate limiting and user agent rotation
- **Data Quality**: Validation, normalization, and duplicate removal

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Repository

**GitHub**: [https://github.com/yourusername/political-reps-api](https://github.com/yourusername/political-reps-api)

---

Built with ❤️ for the Civic Tracker technical challenge.
