from typing import Dict, Any, List
from loguru import logger

from app.agents.base import BaseAgent


class PlannerAgent(BaseAgent):
    """Agent responsible for creating execution plans based on user prompts."""
    
    def __init__(self, model: str = "gpt-4"):
        super().__init__(model=model)
    
    async def execute(self, prompt: str) -> Dict[str, Any]:
        """
        Create a detailed execution plan for web data mining based on user prompt.
        
        Args:
            prompt: User's query describing what data they want to collect
            
        Returns:
            Dict containing the execution plan with search strategies, target sites, etc.
        """
        system_prompt = """
        You are an expert web data mining planner. Given a user query, create a comprehensive
        plan for discovering and extracting relevant data from the web.
        
        Your plan should include:
        1. Target website categories and types
        2. Search strategies and keywords
        3. Expected data structures and schemas
        4. Quality criteria for data selection
        5. Estimated scope and complexity
        
        Return your response as a JSON object with the following structure:
        {
            "summary": "Brief description of the data mining objective",
            "target_categories": ["category1", "category2", ...],
            "search_strategies": [
                {
                    "method": "search_engine",
                    "keywords": ["keyword1", "keyword2", ...],
                    "target_sites": ["site1.com", "site2.com", ...]
                }
            ],
            "expected_data_types": ["tables", "lists", "text", "structured_data"],
            "schema_hints": {
                "field1": "description",
                "field2": "description"
            },
            "quality_criteria": ["criteria1", "criteria2", ...],
            "estimated_urls": 50,
            "complexity": "low|medium|high"
        }
        """
        
        planning_prompt = f"""
        Create a comprehensive web data mining plan for the following request:
        
        "{prompt}"
        
        Consider:
        - What types of websites would have this information
        - What search terms would find relevant pages
        - What data structures to expect (tables, lists, etc.)
        - How to validate data quality
        - Realistic scope for automated extraction
        
        Provide a detailed JSON plan following the specified format.
        """
        
        try:
            logger.info(f"Planning data mining strategy for: {prompt}")
            response = self._call_llm(planning_prompt, system_prompt)
            plan = self._parse_json_response(response)
            
            logger.info(f"Generated plan with {plan.get('estimated_urls', 0)} estimated URLs")
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            raise ValueError(f"Failed to create execution plan: {e}")
