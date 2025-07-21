import asyncio
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger
from pathlib import Path
import aiofiles
import hashlib
from datetime import datetime

from app.config import settings
from app.storage.object_storage import get_object_storage


class BrowserCrawler:
    """Headless browser crawler using Playwright."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._playwright = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self):
        """Initialize browser instance."""
        try:
            self._playwright = await async_playwright().start()
            
            self.browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--no-first-run',
                    '--no-default-browser-check'
                ]
            )
            
            self.context = await self.browser.new_context(
                user_agent=settings.user_agent,
                viewport={'width': 1920, 'height': 1080},
                ignore_https_errors=True
            )
            
            logger.info("Browser crawler initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def stop(self):
        """Clean up browser resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self._playwright:
                await self._playwright.stop()
                
            logger.info("Browser crawler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping browser: {e}")
    
    async def crawl_url(self, url: str, job_id: str) -> Dict[str, Any]:
        """
        Crawl a single URL and return comprehensive results.
        
        Args:
            url: Target URL to crawl
            job_id: Job ID for organizing saved files
            
        Returns:
            Dict containing crawl results and metadata
        """
        if not self.context:
            raise RuntimeError("Browser not initialized. Use async context manager.")
        
        page = None
        try:
            page = await self.context.new_page()
            
            # Set up page event handlers
            await self._setup_page_handlers(page)
            
            logger.info(f"Crawling URL: {url}")
            
            # Navigate to page with timeout
            response = await page.goto(
                url,
                wait_until='domcontentloaded',
                timeout=30000
            )
            
            if not response:
                raise Exception("Failed to load page")
            
            # Wait for dynamic content
            await page.wait_for_timeout(2000)
            
            # Extract page data
            result = await self._extract_page_data(page, url, job_id)
            result['status_code'] = response.status
            result['success'] = 200 <= response.status < 400
            
            logger.info(f"Successfully crawled {url} (status: {response.status})")
            return result
            
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return {
                'url': url,
                'success': False,
                'error_message': str(e),
                'status_code': None,
                'crawled_at': datetime.utcnow().isoformat()
            }
            
        finally:
            if page:
                await page.close()
    
    async def _setup_page_handlers(self, page: Page):
        """Set up page event handlers for error tracking."""
        
        async def handle_console(msg):
            if msg.type == 'error':
                logger.warning(f"Console error: {msg.text}")
        
        async def handle_page_error(error):
            logger.warning(f"Page error: {error}")
        
        page.on('console', handle_console)
        page.on('pageerror', handle_page_error)
    
    async def _extract_page_data(self, page: Page, url: str, job_id: str) -> Dict[str, Any]:
        """Extract comprehensive data from a loaded page."""
        
        # Basic page metadata
        title = await page.title()
        
        # Meta description
        meta_desc_element = await page.query_selector('meta[name="description"]')
        meta_description = None
        if meta_desc_element:
            meta_description = await meta_desc_element.get_attribute('content')
        
        # Get full HTML content
        html_content = await page.content()
        
        # Save HTML to file
        html_file_path = await self._save_html_content(html_content, url, job_id)
        
        # Take screenshot
        screenshot_path = await self._save_screenshot(page, url, job_id)
        
        # Extract structured data hints
        structured_hints = await self._extract_structured_hints(page)
        
        return {
            'url': url,
            'title': title,
            'meta_description': meta_description,
            'html_content': html_content,
            'html_file_path': html_file_path,
            'screenshot_path': screenshot_path,
            'structured_hints': structured_hints,
            'content_length': len(html_content),
            'crawled_at': datetime.utcnow().isoformat()
        }
    
    async def _save_html_content(self, html_content: str, url: str, job_id: str) -> str:
        """Save HTML content to storage and return storage URL."""
        
        # Create filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()
        filename = f"{url_hash}.html"
        
        # Create storage key
        storage_key = f"crawled/{job_id}/{filename}"
        
        # Get object storage instance
        storage = get_object_storage()
        
        try:
            # Upload HTML content as bytes
            html_bytes = html_content.encode('utf-8')
            storage_url = await storage.upload_bytes(
                data=html_bytes,
                key=storage_key,
                content_type="text/html"
            )
            
            logger.info(f"Saved HTML content to storage: {storage_key}")
            return storage_url
            
        except Exception as e:
            logger.error(f"Failed to save HTML content to storage: {e}")
            # Fallback to local storage
            save_dir = Path(settings.data_dir) / "crawled" / job_id
            save_dir.mkdir(parents=True, exist_ok=True)
            file_path = save_dir / filename
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(html_content)
            
            return str(file_path)
    
    async def _save_screenshot(self, page: Page, url: str, job_id: str) -> str:
        """Save page screenshot and return storage URL."""
        
        # Create filename from URL hash
        url_hash = hashlib.md5(url.encode()).hexdigest()
        filename = f"{url_hash}.png"
        
        # Create storage key
        storage_key = f"screenshots/{job_id}/{filename}"
        
        # Get object storage instance
        storage = get_object_storage()
        
        try:
            # Take screenshot to bytes buffer
            screenshot_bytes = await page.screenshot(full_page=True)
            
            # Upload screenshot bytes
            storage_url = await storage.upload_bytes(
                data=screenshot_bytes,
                key=storage_key,
                content_type="image/png"
            )
            
            logger.info(f"Saved screenshot to storage: {storage_key}")
            return storage_url
            
        except Exception as e:
            logger.error(f"Failed to save screenshot to storage: {e}")
            # Fallback to local storage
            save_dir = Path(settings.data_dir) / "screenshots" / job_id
            save_dir.mkdir(parents=True, exist_ok=True)
            file_path = save_dir / filename
            
            await page.screenshot(path=str(file_path), full_page=True)
            
            return str(file_path)
    
    async def _extract_structured_hints(self, page: Page) -> Dict[str, Any]:
        """Extract hints about structured data on the page."""
        
        # Count structured elements
        table_count = await page.locator('table').count()
        list_count = await page.locator('ul, ol').count()
        form_count = await page.locator('form').count()
        
        # Check for common data patterns
        has_pagination = await page.locator('[class*="paginat"], [class*="page-"]').count() > 0
        has_filters = await page.locator('[class*="filter"], [class*="search"]').count() > 0
        
        # Extract JSON-LD structured data
        jsonld_scripts = await page.locator('script[type="application/ld+json"]').all()
        structured_data_count = len(jsonld_scripts)
        
        return {
            'table_count': table_count,
            'list_count': list_count,
            'form_count': form_count,
            'has_pagination': has_pagination,
            'has_filters': has_filters,
            'structured_data_count': structured_data_count,
            'likely_data_rich': table_count > 0 or list_count > 3
        }
    
    async def crawl_multiple_urls(self, urls: List[str], job_id: str, max_concurrent: int = None) -> List[Dict[str, Any]]:
        """Crawl multiple URLs concurrently."""
        
        if max_concurrent is None:
            max_concurrent = settings.max_concurrent_crawls
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def crawl_with_semaphore(url: str):
            async with semaphore:
                # Add delay between requests
                await asyncio.sleep(settings.request_delay_ms / 1000)
                return await self.crawl_url(url, job_id)
        
        # Execute crawls concurrently
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'url': urls[i],
                    'success': False,
                    'error_message': str(result),
                    'crawled_at': datetime.utcnow().isoformat()
                })
            else:
                processed_results.append(result)
        
        return processed_results