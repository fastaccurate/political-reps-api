import requests
from bs4 import BeautifulSoup
import psycopg2
import psycopg2.extras
import os
import time
import logging
from fake_useragent import UserAgent
from retrying import retry
from dotenv import load_dotenv
import json
from typing import List, Dict, Optional, Tuple

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class BaseScraper:
    """Base class for web scraping government representative data"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_agent = UserAgent()
        self.session = requests.Session()
        self.db_connection = None
        self.setup_session()
        self.connect_database()
        
    def setup_session(self):
        """Configure requests session with headers and timeouts"""
        self.session.headers.update({
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Set timeout for all requests
        self.session.timeout = 30
        
    def connect_database(self):
        """Establish database connection"""
        try:
            self.db_connection = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'political_reps_db'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                port=os.getenv('DB_PORT', '5432')
            )
            self.db_connection.autocommit = False
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            raise
    
    @retry(stop_max_attempt_number=3, wait_fixed=2000)
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> requests.Response:
        """Make HTTP request with retry logic"""
        try:
            # Rotate user agent for each request
            self.session.headers['User-Agent'] = self.user_agent.random
            
            if method.upper() == 'GET':
                response = self.session.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = self.session.post(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise
    
    def parse_html(self, html_content: str, parser: str = 'html.parser') -> BeautifulSoup:
        """Parse HTML content with BeautifulSoup"""
        return BeautifulSoup(html_content, parser)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text data"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = ' '.join(text.strip().split())
        return cleaned
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        import re
        if not text:
            return None
            
        # Pattern for US phone numbers
        phone_pattern = r'(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})'
        match = re.search(phone_pattern, text)
        return match.group(1) if match else None
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address from text"""
        import re
        if not text:
            return None
            
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def insert_geography(self, geography_data: Dict) -> int:
        """Insert geography data and return ID"""
        cursor = self.db_connection.cursor()
        
        try:
            insert_query = """
                INSERT INTO geography (
                    zip_code, city, state, state_name, county, 
                    congressional_district, latitude, longitude
                ) VALUES (
                    %(zip_code)s, %(city)s, %(state)s, %(state_name)s, 
                    %(county)s, %(congressional_district)s, %(latitude)s, %(longitude)s
                )
                ON CONFLICT (zip_code) DO UPDATE SET
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    state_name = EXCLUDED.state_name,
                    county = EXCLUDED.county,
                    congressional_district = EXCLUDED.congressional_district,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """
            
            cursor.execute(insert_query, geography_data)
            geo_id = cursor.fetchone()[0]
            self.db_connection.commit()
            
            return geo_id
            
        except Exception as e:
            self.db_connection.rollback()
            self.logger.error(f"Error inserting geography data: {e}")
            raise
        finally:
            cursor.close()
    
    def insert_representative(self, rep_data: Dict) -> int:
        """Insert representative data and return ID"""
        cursor = self.db_connection.cursor()
        
        try:
            # Check if representative already exists (by name and title)
            check_query = """
                SELECT id FROM representatives 
                WHERE name = %(name)s AND title = %(title)s
            """
            cursor.execute(check_query, rep_data)
            existing = cursor.fetchone()
            
            if existing:
                # Update existing representative
                rep_id = existing[0]
                update_query = """
                    UPDATE representatives SET
                        party = %(party)s,
                        branch = %(branch)s,
                        office_type = %(office_type)s,
                        phone = %(phone)s,
                        email = %(email)s,
                        website = %(website)s,
                        photo_url = %(photo_url)s,
                        address_line1 = %(address_line1)s,
                        address_line2 = %(address_line2)s,
                        address_city = %(address_city)s,
                        address_state = %(address_state)s,
                        address_zip = %(address_zip)s,
                        term_start = %(term_start)s,
                        term_end = %(term_end)s,
                        is_active = %(is_active)s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %(id)s
                """
                rep_data['id'] = rep_id
                cursor.execute(update_query, rep_data)
            else:
                # Insert new representative
                insert_query = """
                    INSERT INTO representatives (
                        name, title, party, branch, office_type, phone, email, 
                        website, photo_url, address_line1, address_line2, 
                        address_city, address_state, address_zip, term_start, 
                        term_end, is_active
                    ) VALUES (
                        %(name)s, %(title)s, %(party)s, %(branch)s, %(office_type)s, 
                        %(phone)s, %(email)s, %(website)s, %(photo_url)s, 
                        %(address_line1)s, %(address_line2)s, %(address_city)s, 
                        %(address_state)s, %(address_zip)s, %(term_start)s, 
                        %(term_end)s, %(is_active)s
                    ) RETURNING id
                """
                cursor.execute(insert_query, rep_data)
                rep_id = cursor.fetchone()[0]
            
            self.db_connection.commit()
            return rep_id
            
        except Exception as e:
            self.db_connection.rollback()
            self.logger.error(f"Error inserting representative data: {e}")
            raise
        finally:
            cursor.close()
    
    def create_geography_mapping(self, rep_id: int, geo_id: int, jurisdiction_level: str):
        """Create mapping between representative and geography"""
        cursor = self.db_connection.cursor()
        
        try:
            mapping_query = """
                INSERT INTO rep_geography_map (
                    representative_id, geography_id, jurisdiction_level
                ) VALUES (%s, %s, %s)
                ON CONFLICT (representative_id, geography_id) DO UPDATE SET
                    jurisdiction_level = EXCLUDED.jurisdiction_level
            """
            
            cursor.execute(mapping_query, (rep_id, geo_id, jurisdiction_level))
            self.db_connection.commit()
            
        except Exception as e:
            self.db_connection.rollback()
            self.logger.error(f"Error creating geography mapping: {e}")
            raise
        finally:
            cursor.close()
    
    def respect_rate_limit(self, delay: float = None):
        """Add delay between requests to be respectful"""
        if delay is None:
            delay = float(os.getenv('SCRAPER_DELAY_MS', '2000')) / 1000
        
        time.sleep(delay)
    
    def close_connection(self):
        """Close database connection"""
        if self.db_connection:
            self.db_connection.close()
            self.logger.info("Database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()
        
    # Abstract methods to be implemented by subclasses
    def scrape_representatives(self, zip_code: str) -> List[Dict]:
        """Abstract method to scrape representatives for a ZIP code"""
        raise NotImplementedError("Subclass must implement scrape_representatives method")
    
    def validate_zip_code(self, zip_code: str) -> bool:
        """Validate ZIP code format"""
        import re
        return bool(re.match(r'^\d{5}$', zip_code))