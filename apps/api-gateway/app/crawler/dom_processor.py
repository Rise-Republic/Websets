from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup, Tag
from loguru import logger
import re


class DOMProcessor:
    """Utility class for processing and analyzing DOM content."""
    
    def __init__(self):
        self.soup = None
    
    def load_html(self, html_content: str) -> None:
        """Load HTML content for processing."""
        self.soup = BeautifulSoup(html_content, 'html.parser')
    
    def extract_metadata(self) -> Dict[str, Any]:
        """Extract page metadata from HTML."""
        if not self.soup:
            raise ValueError("No HTML content loaded")
        
        metadata = {}
        
        # Basic metadata
        title_tag = self.soup.find('title')
        metadata['title'] = title_tag.get_text(strip=True) if title_tag else None
        
        # Meta tags
        meta_tags = self.soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[f"meta_{name}"] = content
        
        # Language
        html_tag = self.soup.find('html')
        if html_tag:
            metadata['language'] = html_tag.get('lang')
        
        # Canonical URL
        canonical = self.soup.find('link', rel='canonical')
        if canonical:
            metadata['canonical_url'] = canonical.get('href')
        
        return metadata
    
    def find_data_tables(self) -> List[Dict[str, Any]]:
        """Find and analyze data tables in the document."""
        if not self.soup:
            raise ValueError("No HTML content loaded")
        
        tables = []
        
        for table in self.soup.find_all('table'):
            table_data = self._analyze_table(table)
            if table_data['is_data_table']:
                tables.append(table_data)
        
        return tables
    
    def _analyze_table(self, table: Tag) -> Dict[str, Any]:
        """Analyze a table element to determine if it contains data."""
        
        rows = table.find_all('tr')
        if len(rows) < 2:  # Need header + at least one data row
            return {'is_data_table': False}
        
        # Check for headers
        header_row = rows[0]
        headers = header_row.find_all(['th', 'td'])
        
        # Analyze data consistency
        data_rows = rows[1:]
        if not data_rows:
            return {'is_data_table': False}
        
        # Check column consistency
        expected_cols = len(headers)
        consistent_columns = all(
            len(row.find_all(['td', 'th'])) == expected_cols
            for row in data_rows[:10]  # Check first 10 rows
        )
        
        # Extract sample data
        sample_data = []
        for i, row in enumerate(data_rows[:5]):  # First 5 rows
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            sample_data.append(row_data)
        
        return {
            'is_data_table': consistent_columns and len(data_rows) >= 2,
            'row_count': len(data_rows),
            'column_count': expected_cols,
            'headers': [h.get_text(strip=True) for h in headers],
            'sample_data': sample_data,
            'table_html': str(table)[:2000]  # Truncated for storage
        }
    
    def find_structured_lists(self) -> List[Dict[str, Any]]:
        """Find structured lists that might contain data."""
        if not self.soup:
            raise ValueError("No HTML content loaded")
        
        lists = []
        
        # Process unordered and ordered lists
        for list_elem in self.soup.find_all(['ul', 'ol']):
            list_data = self._analyze_list(list_elem)
            if list_data['is_structured']:
                lists.append(list_data)
        
        # Process definition lists
        for dl in self.soup.find_all('dl'):
            dl_data = self._analyze_definition_list(dl)
            if dl_data['is_structured']:
                lists.append(dl_data)
        
        return lists
    
    def _analyze_list(self, list_elem: Tag) -> Dict[str, Any]:
        """Analyze a list element for structured data."""
        
        items = list_elem.find_all('li', recursive=False)
        
        if len(items) < 3:  # Need at least 3 items to be interesting
            return {'is_structured': False}
        
        # Check for consistent structure
        sample_items = []
        has_nested_structure = False
        
        for item in items[:10]:  # Analyze first 10 items
            item_text = item.get_text(strip=True)
            
            # Check for nested elements
            nested_elements = item.find_all(['a', 'span', 'div', 'p'])
            if nested_elements:
                has_nested_structure = True
            
            sample_items.append({
                'text': item_text[:200],  # Truncate
                'has_links': bool(item.find_all('a')),
                'nested_elements': len(nested_elements)
            })
        
        return {
            'is_structured': len(items) >= 3,
            'type': list_elem.name,
            'item_count': len(items),
            'has_nested_structure': has_nested_structure,
            'sample_items': sample_items,
            'list_html': str(list_elem)[:2000]
        }
    
    def _analyze_definition_list(self, dl: Tag) -> Dict[str, Any]:
        """Analyze a definition list for structured data."""
        
        terms = dl.find_all('dt')
        definitions = dl.find_all('dd')
        
        if len(terms) < 2 or len(definitions) < 2:
            return {'is_structured': False}
        
        pairs = []
        for i, term in enumerate(terms[:10]):
            term_text = term.get_text(strip=True)
            
            # Find corresponding definition
            definition = None
            if i < len(definitions):
                definition = definitions[i].get_text(strip=True)
            
            pairs.append({
                'term': term_text[:100],
                'definition': definition[:200] if definition else None
            })
        
        return {
            'is_structured': True,
            'type': 'definition_list',
            'pair_count': len(terms),
            'sample_pairs': pairs,
            'list_html': str(dl)[:2000]
        }
    
    def extract_text_content(self, clean: bool = True) -> str:
        """Extract clean text content from the document."""
        if not self.soup:
            raise ValueError("No HTML content loaded")
        
        # Remove script and style elements
        for script in self.soup(["script", "style"]):
            script.decompose()
        
        text = self.soup.get_text()
        
        if clean:
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def find_contact_info(self) -> Dict[str, List[str]]:
        """Extract contact information from the page."""
        if not self.soup:
            raise ValueError("No HTML content loaded")
        
        text = self.extract_text_content()
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Phone pattern (basic)
        phone_pattern = r'[\+]?[1-9]?[\d\s\-\(\)]{10,}'
        phones = re.findall(phone_pattern, text)
        
        # Clean phone numbers
        clean_phones = []
        for phone in phones:
            cleaned = re.sub(r'[^\d\+]', '', phone)
            if 10 <= len(cleaned) <= 15:  # Reasonable phone number length
                clean_phones.append(phone.strip())
        
        return {
            'emails': list(set(emails)),  # Remove duplicates
            'phones': list(set(clean_phones))
        }
    
    def get_page_statistics(self) -> Dict[str, Any]:
        """Get general statistics about the page content."""
        if not self.soup:
            raise ValueError("No HTML content loaded")
        
        # Count various elements
        stats = {
            'total_text_length': len(self.extract_text_content()),
            'paragraph_count': len(self.soup.find_all('p')),
            'heading_count': len(self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            'link_count': len(self.soup.find_all('a')),
            'image_count': len(self.soup.find_all('img')),
            'table_count': len(self.soup.find_all('table')),
            'list_count': len(self.soup.find_all(['ul', 'ol', 'dl'])),
            'form_count': len(self.soup.find_all('form')),
            'div_count': len(self.soup.find_all('div'))
        }
        
        return stats
