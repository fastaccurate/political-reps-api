#!/usr/bin/env python3
"""
Main scraper orchestrator for Political Representatives API
Handles scraping from multiple sources and data processing
"""

import sys
import argparse
import logging
from typing import List, Dict
from house_scraper import HouseRepresentativeScraper
from base_scraper import BaseScraper

class RepresentativeDataProcessor:
    """Main class to orchestrate scraping and data processing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scrapers = {
            'house': HouseRepresentativeScraper()
        }
        
    def process_zip_code(self, zip_code: str) -> Dict:
        """Process a single ZIP code through all scrapers"""
        self.logger.info(f"Processing ZIP code: {zip_code}")
        
        results = {
            'zip_code': zip_code,
            'representatives': [],
            'geography': {},
            'success': False,
            'errors': []
        }
        
        try:
            # Validate ZIP code format
            if not self.validate_zip_code(zip_code):
                results['errors'].append(f"Invalid ZIP code format: {zip_code}")
                return results
            
            # Get geography data
            geography_data = self.get_geography_data(zip_code)
            if not geography_data:
                results['errors'].append(f"Could not determine geography for ZIP code: {zip_code}")
                return results
            
            results['geography'] = geography_data
            
            # Scrape representatives from all sources
            all_representatives = []
            
            for scraper_name, scraper in self.scrapers.items():
                try:
                    self.logger.info(f"Using {scraper_name} scraper for {zip_code}")
                    reps = scraper.scrape_representatives(zip_code)
                    
                    if reps:
                        all_representatives.extend(reps)
                        self.logger.info(f"{scraper_name} scraper found {len(reps)} representatives")
                    else:
                        self.logger.warning(f"{scraper_name} scraper found no representatives")
                        
                    # Respect rate limiting between scraper calls
                    scraper.respect_rate_limit()
                    
                except Exception as e:
                    error_msg = f"Error in {scraper_name} scraper: {e}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            # Process and deduplicate representatives
            processed_reps = self.process_representatives(all_representatives)
            results['representatives'] = processed_reps
            
            # Store data in database
            if processed_reps:
                self.store_data(results)
                results['success'] = True
                self.logger.info(f"Successfully processed {len(processed_reps)} representatives for {zip_code}")
            else:
                results['errors'].append("No representatives found after processing")
            
        except Exception as e:
            error_msg = f"Error processing ZIP code {zip_code}: {e}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def get_geography_data(self, zip_code: str) -> Dict:
        """Get geography data for a ZIP code"""
        # Sample geography data for demo ZIP codes
        geography_mapping = {
            '11354': {
                'zip_code': zip_code,
                'city': 'Flushing',
                'state': 'NY',
                'state_name': 'New York',
                'county': 'Queens',
                'congressional_district': '06',
                'latitude': 40.7598,
                'longitude': -73.8303
            },
            '20301': {
                'zip_code': zip_code,
                'city': 'Washington',
                'state': 'DC',
                'state_name': 'District of Columbia',
                'county': 'District of Columbia',
                'congressional_district': '00',
                'latitude': 38.9072,
                'longitude': -77.0369
            },
            '90210': {
                'zip_code': zip_code,
                'city': 'Beverly Hills',
                'state': 'CA',
                'state_name': 'California',
                'county': 'Los Angeles',
                'congressional_district': '30',
                'latitude': 34.0901,
                'longitude': -118.4065
            }
        }
        
        return geography_mapping.get(zip_code, {})
    
    def process_representatives(self, representatives: List[Dict]) -> List[Dict]:
        """Process and deduplicate representatives"""
        # Remove duplicates based on name and title
        seen = set()
        processed = []
        
        for rep in representatives:
            if not rep or 'name' not in rep or 'title' not in rep:
                continue
                
            key = (rep['name'].lower().strip(), rep['title'].lower().strip())
            
            if key not in seen:
                seen.add(key)
                
                # Ensure all required fields are present
                processed_rep = self.normalize_representative_data(rep)
                processed.append(processed_rep)
        
        return processed
    
    def normalize_representative_data(self, rep: Dict) -> Dict:
        """Normalize representative data to ensure consistency"""
        normalized = {
            'name': rep.get('name', '').strip(),
            'title': rep.get('title', '').strip(),
            'party': rep.get('party', '').strip(),
            'branch': rep.get('branch', 'federal').lower(),
            'office_type': rep.get('office_type', '').strip(),
            'phone': rep.get('phone', '').strip(),
            'email': rep.get('email', '').strip(),
            'website': rep.get('website', '').strip(),
            'photo_url': rep.get('photo_url', '').strip(),
            'address_line1': rep.get('address_line1', '').strip(),
            'address_line2': rep.get('address_line2', '').strip(),
            'address_city': rep.get('address_city', '').strip(),
            'address_state': rep.get('address_state', '').strip(),
            'address_zip': rep.get('address_zip', '').strip(),
            'term_start': rep.get('term_start'),
            'term_end': rep.get('term_end'),
            'is_active': rep.get('is_active', True)
        }
        
        # Convert empty strings to None for database storage
        for key, value in normalized.items():
            if isinstance(value, str) and not value:
                normalized[key] = None
        
        return normalized
    
    def store_data(self, results: Dict):
        """Store scraped data in the database"""
        scraper = self.scrapers['house']  # Use any scraper for database access
        
        try:
            # Insert geography data
            geo_id = scraper.insert_geography(results['geography'])
            
            # Insert representatives and create mappings
            for rep_data in results['representatives']:
                rep_id = scraper.insert_representative(rep_data)
                scraper.create_geography_mapping(
                    rep_id, 
                    geo_id, 
                    rep_data['branch']
                )
            
            self.logger.info(f"Successfully stored data for ZIP {results['zip_code']}")
            
        except Exception as e:
            self.logger.error(f"Error storing data: {e}")
            raise
    
    def validate_zip_code(self, zip_code: str) -> bool:
        """Validate ZIP code format"""
        import re
        return bool(re.match(r'^\d{5}$', zip_code))
    
    def process_multiple_zip_codes(self, zip_codes: List[str]) -> List[Dict]:
        """Process multiple ZIP codes"""
        results = []
        
        for i, zip_code in enumerate(zip_codes):
            self.logger.info(f"Processing {i+1}/{len(zip_codes)}: {zip_code}")
            
            try:
                result = self.process_zip_code(zip_code)
                results.append(result)
                
                # Add delay between ZIP codes to be respectful
                if i < len(zip_codes) - 1:  # Don't sleep after the last one
                    import time
                    time.sleep(3)
                    
            except Exception as e:
                self.logger.error(f"Failed to process ZIP code {zip_code}: {e}")
                results.append({
                    'zip_code': zip_code,
                    'success': False,
                    'errors': [str(e)]
                })
        
        return results
    
    def cleanup(self):
        """Clean up resources"""
        for scraper in self.scrapers.values():
            scraper.close_connection()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Scrape political representative data')
    parser.add_argument('--zip', '-z', help='Single ZIP code to process')
    parser.add_argument('--zip-file', '-f', help='File containing ZIP codes (one per line)')
    parser.add_argument('--demo', '-d', action='store_true', help='Run demo with sample ZIP codes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    processor = RepresentativeDataProcessor()
    
    try:
        if args.demo:
            # Demo mode with sample ZIP codes
            demo_zips = ['11354', '20301', '90210']
            print(f"Running demo with ZIP codes: {demo_zips}")
            results = processor.process_multiple_zip_codes(demo_zips)
            
        elif args.zip:
            # Single ZIP code mode
            print(f"Processing ZIP code: {args.zip}")
            result = processor.process_zip_code(args.zip)
            results = [result]
            
        elif args.zip_file:
            # File mode
            try:
                with open(args.zip_file, 'r') as f:
                    zip_codes = [line.strip() for line in f if line.strip()]
                print(f"Processing {len(zip_codes)} ZIP codes from file")
                results = processor.process_multiple_zip_codes(zip_codes)
            except FileNotFoundError:
                print(f"Error: File {args.zip_file} not found")
                return 1
                
        else:
            # No arguments provided
            parser.print_help()
            return 1
        
        # Print summary
        successful = sum(1 for r in results if r.get('success', False))
        total = len(results)
        
        print(f"\nScraping completed:")
        print(f"  Total ZIP codes processed: {total}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {total - successful}")
        
        if args.verbose:
            for result in results:
                status = "✓" if result.get('success', False) else "✗"
                rep_count = len(result.get('representatives', []))
                print(f"  {status} {result['zip_code']}: {rep_count} representatives")
                
                if result.get('errors'):
                    for error in result['errors']:
                        print(f"    Error: {error}")
        
        return 0
        
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
        return 1
        
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.exception("Fatal error occurred")
        return 1
        
    finally:
        processor.cleanup()

if __name__ == '__main__':
    sys.exit(main())