from typing import Dict, Any, List
from loguru import logger
import httpx
import asyncio

from app.agents.base import BaseAgent


class DiscoveryAgent(BaseAgent):
    """Agent responsible for discovering relevant URLs based on execution plan."""
    
    def __init__(self, model: str = "gpt-4"):
        super().__init__(model=model)
    
    async def execute(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Discover URLs based on the execution plan.
        
        Args:
            plan: Execution plan from PlannerAgent
            
        Returns:
            List of discovered URLs with metadata
        """
        discovered_urls = []
        
        for strategy in plan.get("search_strategies", []):
            if strategy["method"] == "search_engine":
                urls = await self._search_engine_discovery(strategy, plan)
                discovered_urls.extend(urls)
            elif strategy["method"] == "direct_sites":
                urls = await self._direct_site_discovery(strategy, plan)
                discovered_urls.extend(urls)
        
        # Prioritize and filter URLs
        filtered_urls = await self._prioritize_urls(discovered_urls, plan)
        
        logger.info(f"Discovered {len(filtered_urls)} prioritized URLs")
        return filtered_urls
    
    async def _search_engine_discovery(self, strategy: Dict[str, Any], plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Use LLM to generate relevant URLs based on search strategy."""
        
        system_prompt = """
        You are a web research expert. Given search keywords and target website categories,
        generate a list of specific URLs that would likely contain the requested data.
        
        Focus on:
        - High-authority, well-structured websites
        - Pages likely to have tabular or structured data
        - Diverse sources to avoid bias
        - Public, accessible content
        
        Return a JSON array of URL objects:
        [
            {
                "url": "https://example.com/data-page",
                "title": "Expected page title",
                "description": "Why this URL is relevant",
                "priority": 1-5,
                "expected_data_type": "table|list|text"
            }
        ]
        """
        
        discovery_prompt = f"""
        Generate specific URLs for web data extraction based on:
        
        Keywords: {', '.join(strategy.get('keywords', []))}
        Target Categories: {', '.join(plan.get('target_categories', []))}
        Objective: {plan.get('summary', '')}
        
        Target Sites (if specified): {', '.join(strategy.get('target_sites', []))}
        
        Generate 20-30 high-quality URLs that would contain structured data
        matching the search criteria. Focus on pages with tables, lists,
        directories, or other organized information.
        """
        
        try:
            response = self._call_llm(discovery_prompt, system_prompt)
            urls = self._parse_json_response(response)
            
            # Ensure it's a list
            if isinstance(urls, dict):
                urls = [urls]
            
            return urls
            
        except Exception as e:
            logger.error(f"Search engine discovery failed: {e}")
            return []
    
    async def _direct_site_discovery(self, strategy: Dict[str, Any], plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover URLs from specific target sites."""
        urls = []
        
        for site in strategy.get("target_sites", []):
            # Generate potential page URLs for the site
            site_urls = await self._generate_site_urls(site, plan)
            urls.extend(site_urls)
        
        return urls
    
    async def _generate_site_urls(self, site: str, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate potential URLs for a specific site."""
        
        system_prompt = """
        Given a website domain and data extraction objective, generate specific
        page URLs that would likely contain the target data.
        
        Consider common URL patterns like:
        - /directory/, /list/, /database/
        - Category pages, product listings
        - Data exports, reports, statistics pages
        
        Return JSON array of URL objects with metadata.
        """
        
        prompt = f"""
        Generate specific page URLs for the website: {site}
        
        Objective: {plan.get('summary', '')}
        Target Data Types: {', '.join(plan.get('expected_data_types', []))}
        
        Generate 10-15 URLs that would likely contain structured data
        relevant to the objective.
        """
        
        try:
            response = self._call_llm(prompt, system_prompt)
            urls = self._parse_json_response(response)
            
            if isinstance(urls, dict):
                urls = [urls]
            
            return urls
            
        except Exception as e:
            logger.error(f"Site URL generation failed for {site}: {e}")
            return []
    
    async def _prioritize_urls(self, urls: List[Dict[str, Any]], plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize and filter discovered URLs."""
        
        # Remove duplicates
        seen_urls = set()
        unique_urls = []
        
        for url_obj in urls:
            url = url_obj.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_urls.append(url_obj)
        
        # Sort by priority (lower number = higher priority)
        unique_urls.sort(key=lambda x: x.get("priority", 3))
        
        # Limit to reasonable number
        max_urls = min(100, plan.get("estimated_urls", 50))
        return unique_urls[:max_urls]