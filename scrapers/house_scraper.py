from base_scraper import BaseScraper
from typing import List, Dict
import re

class HouseRepresentativeScraper(BaseScraper):
    """Scraper for House of Representatives data from house.gov"""
    
    def __init__(self):
        super().__init__()
        self.house_lookup_url = "https://ziplook.house.gov/htbin/findrep_house"
        self.house_member_url = "https://www.house.gov/representatives"
        
    def scrape_representatives(self, zip_code: str) -> List[Dict]:
        """Scrape House representative data for a ZIP code"""
        if not self.validate_zip_code(zip_code):
            self.logger.error(f"Invalid ZIP code format: {zip_code}")
            return []
            
        try:
            representatives = []
            
            # Get House representative from ZIP lookup
            house_rep = self.get_house_rep_by_zip(zip_code)
            if house_rep:
                representatives.append(house_rep)
            
            # Get senators for the state
            if house_rep and 'state' in house_rep:
                senators = self.get_senators_by_state(house_rep['state'])
                representatives.extend(senators)
            
            return representatives
            
        except Exception as e:
            self.logger.error(f"Error scraping representatives for {zip_code}: {e}")
            return []
    
    def get_house_rep_by_zip(self, zip_code: str) -> Dict:
        """Get House representative using ZIP code lookup"""
        try:
            # First try the official ZIP lookup service
            data = {
                'ZIP': zip_code,
                'Submit': 'FIND YOUR REP'
            }
            
            response = self.make_request(
                self.house_lookup_url, 
                method='POST', 
                data=data,
                allow_redirects=True
            )
            
            soup = self.parse_html(response.content)
            
            # Parse representative information from response
            rep_info = self.parse_house_lookup_response(soup, zip_code)
            
            if rep_info:
                return rep_info
            
            # Fallback: Try to get representative info from sample data
            return self.get_sample_house_rep(zip_code)
            
        except Exception as e:
            self.logger.error(f"Error getting House rep for {zip_code}: {e}")
            return self.get_sample_house_rep(zip_code)
    
    def parse_house_lookup_response(self, soup, zip_code: str) -> Dict:
        """Parse House lookup response HTML"""
        try:
            # Look for representative information in various possible structures
            rep_data = {}
            
            # Try to find representative name and district
            # The structure may vary, so we try multiple selectors
            
            # Look for links to representative pages
            rep_links = soup.find_all('a', href=re.compile(r'/representatives/'))
            
            for link in rep_links:
                if link.text and len(link.text.strip()) > 0:
                    name = self.clean_text(link.text)
                    
                    # Extract district from URL or surrounding text
                    href = link.get('href', '')
                    district_match = re.search(r'district[/-]?(\d+)', href, re.IGNORECASE)
                    
                    if district_match:
                        district = district_match.group(1).zfill(2)
                    else:
                        district = "00"  # Default if not found
                    
                    # Determine state from ZIP code (simplified mapping)
                    state = self.get_state_from_zip(zip_code)
                    
                    rep_data = {
                        'name': name,
                        'title': f'U.S. House Rep, {state}-{district}',
                        'party': '',  # Would need additional scraping
                        'branch': 'federal',
                        'office_type': 'House Representative',
                        'phone': '',
                        'email': '',
                        'website': f"https://www.house.gov{href}" if href.startswith('/') else href,
                        'photo_url': '',
                        'address_line1': '',
                        'address_line2': '',
                        'address_city': '',
                        'address_state': state,
                        'address_zip': '',
                        'term_start': None,
                        'term_end': None,
                        'is_active': True,
                        'state': state,
                        'district': district
                    }
                    break
            
            return rep_data
            
        except Exception as e:
            self.logger.error(f"Error parsing House lookup response: {e}")
            return {}
    
    def get_sample_house_rep(self, zip_code: str) -> Dict:
        """Get sample House representative data for demo purposes"""
        # Sample data for common ZIP codes for demonstration
        sample_data = {
            '11354': {
                'name': 'Grace Meng',
                'title': 'U.S. House Rep, NY-6',
                'party': 'Democratic',
                'branch': 'federal',
                'office_type': 'House Representative',
                'phone': '(202) 225-2601',
                'email': '',
                'website': 'https://meng.house.gov',
                'photo_url': '',
                'address_line1': '2209 Rayburn House Office Building',
                'address_line2': '',
                'address_city': 'Washington',
                'address_state': 'DC',
                'address_zip': '20515',
                'term_start': None,
                'term_end': None,
                'is_active': True,
                'state': 'NY',
                'district': '06'
            },
            '20301': {
                'name': 'Eleanor Holmes Norton',
                'title': 'U.S. House Delegate, DC-At Large',
                'party': 'Democratic',
                'branch': 'federal',
                'office_type': 'House Delegate',
                'phone': '(202) 225-8050',
                'email': '',
                'website': 'https://norton.house.gov',
                'photo_url': '',
                'address_line1': '2136 Rayburn House Office Building',
                'address_line2': '',
                'address_city': 'Washington',
                'address_state': 'DC',
                'address_zip': '20515',
                'term_start': None,
                'term_end': None,
                'is_active': True,
                'state': 'DC',
                'district': '00'
            },
            '90210': {
                'name': 'Brad Sherman',
                'title': 'U.S. House Rep, CA-30',
                'party': 'Democratic',
                'branch': 'federal',
                'office_type': 'House Representative',
                'phone': '(202) 225-5911',
                'email': '',
                'website': 'https://sherman.house.gov',
                'photo_url': '',
                'address_line1': '2181 Rayburn House Office Building',
                'address_line2': '',
                'address_city': 'Washington',
                'address_state': 'DC',
                'address_zip': '20515',
                'term_start': None,
                'term_end': None,
                'is_active': True,
                'state': 'CA',
                'district': '30'
            }
        }
        
        return sample_data.get(zip_code, {})
    
    def get_senators_by_state(self, state: str) -> List[Dict]:
        """Get senators for a given state"""
        # Sample senators data for demonstration
        senators_data = {
            'NY': [
                {
                    'name': 'Chuck Schumer',
                    'title': 'U.S. Senator, NY',
                    'party': 'Democratic',
                    'branch': 'federal',
                    'office_type': 'Senator',
                    'phone': '(202) 224-6542',
                    'email': '',
                    'website': 'https://www.schumer.senate.gov',
                    'photo_url': '',
                    'address_line1': '322 Hart Senate Office Building',
                    'address_line2': '',
                    'address_city': 'Washington',
                    'address_state': 'DC',
                    'address_zip': '20510',
                    'term_start': None,
                    'term_end': None,
                    'is_active': True
                },
                {
                    'name': 'Kirsten Gillibrand',
                    'title': 'U.S. Senator, NY',
                    'party': 'Democratic',
                    'branch': 'federal',
                    'office_type': 'Senator',
                    'phone': '(202) 224-4451',
                    'email': '',
                    'website': 'https://www.gillibrand.senate.gov',
                    'photo_url': '',
                    'address_line1': '478 Russell Senate Office Building',
                    'address_line2': '',
                    'address_city': 'Washington',
                    'address_state': 'DC',
                    'address_zip': '20510',
                    'term_start': None,
                    'term_end': None,
                    'is_active': True
                }
            ],
            'CA': [
                {
                    'name': 'Dianne Feinstein',
                    'title': 'U.S. Senator, CA',
                    'party': 'Democratic',
                    'branch': 'federal',
                    'office_type': 'Senator',
                    'phone': '(202) 224-3841',
                    'email': '',
                    'website': 'https://www.feinstein.senate.gov',
                    'photo_url': '',
                    'address_line1': '331 Hart Senate Office Building',
                    'address_line2': '',
                    'address_city': 'Washington',
                    'address_state': 'DC',
                    'address_zip': '20510',
                    'term_start': None,
                    'term_end': None,
                    'is_active': True
                },
                {
                    'name': 'Alex Padilla',
                    'title': 'U.S. Senator, CA',
                    'party': 'Democratic',
                    'branch': 'federal',
                    'office_type': 'Senator',
                    'phone': '(202) 224-3553',
                    'email': '',
                    'website': 'https://www.padilla.senate.gov',
                    'photo_url': '',
                    'address_line1': '112 Hart Senate Office Building',
                    'address_line2': '',
                    'address_city': 'Washington',
                    'address_state': 'DC',
                    'address_zip': '20510',
                    'term_start': None,
                    'term_end': None,
                    'is_active': True
                }
            ],
            'DC': []  # DC has no voting senators
        }
        
        return senators_data.get(state, [])
    
    def get_state_from_zip(self, zip_code: str) -> str:
        """Get state abbreviation from ZIP code (simplified mapping)"""
        # Simplified ZIP to state mapping for common demo ZIP codes
        zip_to_state = {
            '11354': 'NY',  # Flushing, NY
            '20301': 'DC',  # Washington, DC
            '90210': 'CA',  # Beverly Hills, CA
        }
        
        # For production, you would use a comprehensive ZIP code database
        return zip_to_state.get(zip_code, 'XX')
    
    def get_state_governors(self, state: str) -> List[Dict]:
        """Get governor information for a state"""
        governors_data = {
            'NY': {
                'name': 'Kathy Hochul',
                'title': 'Governor, New York',
                'party': 'Democratic',
                'branch': 'state',
                'office_type': 'Governor',
                'phone': '(518) 474-8390',
                'email': '',
                'website': 'https://www.governor.ny.gov',
                'photo_url': '',
                'address_line1': 'NYS State Capitol Building',
                'address_line2': '',
                'address_city': 'Albany',
                'address_state': 'NY',
                'address_zip': '12224',
                'term_start': None,
                'term_end': None,
                'is_active': True
            },
            'CA': {
                'name': 'Gavin Newsom',
                'title': 'Governor, California',
                'party': 'Democratic',
                'branch': 'state',
                'office_type': 'Governor',
                'phone': '(916) 445-2841',
                'email': '',
                'website': 'https://www.gov.ca.gov',
                'photo_url': '',
                'address_line1': '1303 10th Street, Suite 1173',
                'address_line2': '',
                'address_city': 'Sacramento',
                'address_state': 'CA',
                'address_zip': '95814',
                'term_start': None,
                'term_end': None,
                'is_active': True
            }
        }
        
        governor = governors_data.get(state)
        return [governor] if governor else []