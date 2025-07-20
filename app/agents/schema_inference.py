from typing import Dict, Any, List, Optional
from loguru import logger
from bs4 import BeautifulSoup

from app.agents.base import BaseAgent


class SchemaInferenceAgent(BaseAgent):
    """Agent responsible for inferring data schemas from crawled content."""
    
    def __init__(self, model: str = "gpt-4"):
        super().__init__(model=model)
    
    async def execute(self, html_content: str, url: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Infer data schema and extract structured data from HTML content.
        
        Args:
            html_content: Raw HTML content from crawled page
            url: Source URL for context
            plan: Original execution plan for guidance
            
        Returns:
            Dict containing inferred schema and extracted data
        """
        try:
            # Parse HTML and extract structured elements
            soup = BeautifulSoup(html_content, 'html.parser')
            structured_elements = self._identify_structured_elements(soup)
            
            if not structured_elements:
                logger.warning(f"No structured elements found in {url}")
                return {"schema": None, "data": [], "confidence": 0.0}
            
            # Generate schema using LLM
            schema = await self._infer_schema(structured_elements, url, plan)
            
            # Extract data based on schema
            extracted_data = await self._extract_data(structured_elements, schema, plan)
            
            confidence = self._calculate_confidence(extracted_data, schema)
            
            return {
                "schema": schema,
                "data": extracted_data,
                "confidence": confidence,
                "source_url": url,
                "extraction_method": "llm_inference"
            }
            
        except Exception as e:
            logger.error(f"Schema inference failed for {url}: {e}")
            return {"schema": None, "data": [], "confidence": 0.0, "error": str(e)}
    
    def _identify_structured_elements(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Identify tables, lists, and other structured elements in HTML."""
        elements = []
        
        # Extract tables
        for table in soup.find_all('table'):
            elements.append({
                "type": "table",
                "element": str(table),
                "text_content": table.get_text(strip=True)[:1000]  # Limit size
            })
        
        # Extract structured lists
        for ul in soup.find_all(['ul', 'ol']):
            if len(ul.find_all('li')) > 2:  # Only meaningful lists
                elements.append({
                    "type": "list",
                    "element": str(ul),
                    "text_content": ul.get_text(strip=True)[:1000]
                })
        
        # Extract definition lists
        for dl in soup.find_all('dl'):
            elements.append({
                "type": "definition_list",
                "element": str(dl),
                "text_content": dl.get_text(strip=True)[:1000]
            })
        
        # Extract structured divs (common in modern websites)
        for div in soup.find_all('div', class_=True):
            class_names = ' '.join(div.get('class', []))
            if any(keyword in class_names.lower() for keyword in ['card', 'item', 'entry', 'record', 'row']):
                if len(div.get_text(strip=True)) > 50:  # Has meaningful content
                    elements.append({
                        "type": "structured_div",
                        "element": str(div),
                        "text_content": div.get_text(strip=True)[:1000]
                    })
        
        return elements[:10]  # Limit to most relevant elements
    
    async def _infer_schema(self, elements: List[Dict[str, Any]], url: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to infer the data schema from structured elements."""
        
        system_prompt = """
        You are an expert data schema analyst. Analyze HTML elements and infer
        a JSON schema for structured data extraction.
        
        Your schema should:
        1. Identify the main entity type
        2. Define key fields with appropriate data types
        3. Handle nested or repeated structures
        4. Include field descriptions and validation rules
        
        Return a JSON schema object:
        {
            "entity_type": "company|person|product|event|etc",
            "description": "What this data represents",
            "fields": {
                "field_name": {
                    "type": "string|number|boolean|array|object",
                    "description": "Field description",
                    "required": true|false,
                    "format": "url|email|date|etc (optional)"
                }
            },
            "array_fields": ["field_name1", "field_name2"],
            "nested_objects": {
                "field_name": {
                    "subfield1": {"type": "string", "description": "..."},
                    "subfield2": {"type": "number", "description": "..."}
                }
            }
        }
        """
        
        elements_summary = "\n\n".join([
            f"Element {i+1} ({elem['type']}):\n{elem['text_content'][:500]}"
            for i, elem in enumerate(elements)
        ])
        
        inference_prompt = f"""
        Analyze the following HTML elements from {url} and infer a data schema:
        
        Original Query Context: {plan.get('summary', '')}
        Expected Data Types: {', '.join(plan.get('expected_data_types', []))}
        Schema Hints: {plan.get('schema_hints', {})}
        
        HTML Elements:
        {elements_summary}
        
        Infer a comprehensive schema that captures the structured data
        represented in these elements. Focus on the most repeating and
        consistent patterns.
        """
        
        try:
            response = self._call_llm(inference_prompt, system_prompt)
            schema = self._parse_json_response(response)
            return schema
            
        except Exception as e:
            logger.error(f"Schema inference failed: {e}")
            return {"entity_type": "unknown", "fields": {}, "description": "Schema inference failed"}
    
    async def _extract_data(self, elements: List[Dict[str, Any]], schema: Dict[str, Any], plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract structured data based on inferred schema."""
        
        system_prompt = """
        You are a data extraction expert. Given HTML elements and a schema,
        extract structured data that matches the schema.
        
        Rules:
        1. Extract all records that match the schema
        2. Handle missing fields gracefully
        3. Clean and normalize data values
        4. Maintain data consistency
        5. Skip incomplete or invalid records
        
        Return a JSON array of extracted records:
        [
            {
                "field1": "value1",
                "field2": "value2",
                ...
            }
        ]
        """
        
        elements_html = "\n\n".join([
            f"Element {i+1} ({elem['type']}):\n{elem['element'][:2000]}"
            for i, elem in enumerate(elements)
        ])
        
        extraction_prompt = f"""
        Extract structured data from these HTML elements using the provided schema:
        
        Schema:
        {schema}
        
        HTML Elements:
        {elements_html}
        
        Extract all valid records that match the schema. Clean and normalize
        the data values. Skip records with missing required fields.
        """
        
        try:
            response = self._call_llm(extraction_prompt, system_prompt)
            data = self._parse_json_response(response)
            
            # Ensure it's a list
            if isinstance(data, dict):
                data = [data]
            
            return data
            
        except Exception as e:
            logger.error(f"Data extraction failed: {e}")
            return []
    
    def _calculate_confidence(self, data: List[Dict[str, Any]], schema: Dict[str, Any]) -> float:
        """Calculate confidence score for extracted data quality."""
        if not data:
            return 0.0
        
        required_fields = [
            field for field, props in schema.get('fields', {}).items()
            if props.get('required', False)
        ]
        
        if not required_fields:
            return 0.7  # Medium confidence if no required fields
        
        total_score = 0.0
        for record in data:
            record_score = sum(1 for field in required_fields if record.get(field))
            total_score += record_score / len(required_fields)
        
        return min(1.0, total_score / len(data))