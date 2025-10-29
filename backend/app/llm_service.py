"""
LLM Service for Failure Analysis
Generates natural language summaries of DAG failures using LLM APIs.
"""

import httpx
from typing import List, Dict, Any, Optional
from loguru import logger
from app.config import settings


class LLMService:
    """Service for interacting with LLM APIs to analyze DAG failures."""
    
    def __init__(self):
        self.provider = (settings.llm_provider or "openai").lower()
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model or "gpt-4o-mini"
        self.enabled = settings.llm_enabled and bool(self.api_key)
        
        if not self.enabled:
            logger.warning("LLM service disabled or API key not configured")
        else:
            logger.info(f"LLM service initialized: provider={self.provider}, model={self.model}")
    
    async def analyze_failures(
        self, 
        failed_dags: List[Dict[str, Any]], 
        failed_runs: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Analyze failed DAGs and generate summary, categories, and action items.
        
        Args:
            failed_dags: List of DAG information with failure details
            failed_runs: Dict mapping dag_id to list of failed runs
            
        Returns:
            Dict with summary, categories, action_items
        """
        if not self.enabled:
            return {
                "summary": "LLM analysis disabled. Please configure LLM_API_KEY.",
                "categories": [],
                "action_items": [],
                "error": "LLM_NOT_CONFIGURED"
            }
        
        # Build context for LLM
        context = self._build_failure_context(failed_dags, failed_runs)
        
        # Generate analysis using LLM
        try:
            if self.provider == "openai":
                return await self._analyze_with_openai(context)
            elif self.provider == "azure_openai":
                return await self._analyze_with_azure_openai(context)
            elif self.provider == "anthropic":
                return await self._analyze_with_anthropic(context)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            return {
                "summary": f"Analysis failed: {str(e)}",
                "categories": [],
                "action_items": [],
                "error": str(e)
            }
    
    def _build_failure_context(
        self, 
        failed_dags: List[Dict[str, Any]], 
        failed_runs: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Build structured context string for LLM analysis."""
        
        context_parts = []
        context_parts.append("# Airflow DAG Failure Analysis Request\n")
        context_parts.append(f"Total failed DAGs: {len(failed_dags)}\n")
        context_parts.append(f"Total failed runs: {sum(len(runs) for runs in failed_runs.values())}\n\n")
        
        context_parts.append("## Failed DAGs Summary:\n")
        for dag in failed_dags:
            dag_id = dag.get('dag_id', 'unknown')
            domain = dag.get('domain_tag', 'untagged')
            failed_count = dag.get('failed_count', 0)
            description = dag.get('description', 'No description')
            
            context_parts.append(f"\n### {dag_id}")
            context_parts.append(f"- Domain: {domain}")
            context_parts.append(f"- Failed runs: {failed_count}")
            context_parts.append(f"- Description: {description}")
            
            # Add recent failure information
            if dag_id in failed_runs:
                runs = failed_runs[dag_id][:3]  # Last 3 failures
                context_parts.append(f"- Recent failures:")
                for run in runs:
                    exec_date = run.get('execution_date', 'unknown')
                    state = run.get('state', 'unknown')
                    context_parts.append(f"  * {exec_date}: {state}")
        
        return "\n".join(context_parts)
    
    async def _analyze_with_openai(self, context: str) -> Dict[str, Any]:
        """Analyze failures using OpenAI API."""
        
        system_prompt = """You are an expert Airflow data engineer analyzing DAG failures. 
Your task is to analyze failed DAG runs and provide:
1. A concise executive summary (2-3 sentences)
2. Categories of failures (group similar failures)
3. Specific action items to resolve the issues

Be direct, actionable, and prioritize by impact."""

        user_prompt = f"""{context}

Please analyze these failures and provide:

1. **Summary**: A brief executive summary of the overall failure situation
2. **Categories**: Group failures into categories (e.g., "Data Quality Issues", "Infrastructure Failures", "Configuration Errors")
3. **Action Items**: Specific steps to resolve these issues, prioritized by impact

Format your response as JSON:
{{
  "summary": "Your executive summary here",
  "categories": [
    {{
      "name": "Category Name",
      "count": number_of_dags,
      "dag_ids": ["dag1", "dag2"],
      "description": "What's causing this category of failures"
    }}
  ],
  "action_items": [
    {{
      "priority": "high|medium|low",
      "title": "Action title",
      "description": "Detailed action description",
      "affected_dags": ["dag1", "dag2"]
    }}
  ]
}}"""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON response
            import json
            analysis = json.loads(content)
            
            return analysis
    
    async def _analyze_with_azure_openai(self, context: str) -> Dict[str, Any]:
        """Analyze failures using Azure OpenAI API."""
        
        if not settings.azure_openai_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT not configured")
        if not settings.azure_openai_deployment_name:
            raise ValueError("AZURE_OPENAI_DEPLOYMENT_NAME not configured")
        
        system_prompt = """You are an expert Airflow data engineer analyzing DAG failures. 
Your task is to analyze failed DAG runs and provide:
1. A concise executive summary (2-3 sentences)
2. Categories of failures (group similar failures)
3. Specific action items to resolve the issues

Be direct, actionable, and prioritize by impact."""

        user_prompt = f"""{context}

Please analyze these failures and provide:

1. **Summary**: A brief executive summary of the overall failure situation
2. **Categories**: Group failures into categories (e.g., "Data Quality Issues", "Infrastructure Failures", "Configuration Errors")
3. **Action Items**: Specific steps to resolve these issues, prioritized by impact

Format your response as JSON:
{{
  "summary": "Your executive summary here",
  "categories": [
    {{
      "name": "Category Name",
      "count": number_of_dags,
      "dag_ids": ["dag1", "dag2"],
      "description": "What's causing this category of failures"
    }}
  ],
  "action_items": [
    {{
      "priority": "high|medium|low",
      "title": "Action title",
      "description": "Detailed action description",
      "affected_dags": ["dag1", "dag2"]
    }}
  ]
}}"""

        # Azure OpenAI endpoint format
        endpoint = settings.azure_openai_endpoint.rstrip('/')
        api_version = settings.azure_openai_api_version
        deployment_name = settings.azure_openai_deployment_name
        
        url = f"{endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
        
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON response
            import json
            analysis = json.loads(content)
            
            return analysis
    
    async def _analyze_with_anthropic(self, context: str) -> Dict[str, Any]:
        """Analyze failures using Anthropic Claude API."""
        
        system_prompt = """You are an expert Airflow data engineer analyzing DAG failures. 
Your task is to analyze failed DAG runs and provide:
1. A concise executive summary (2-3 sentences)
2. Categories of failures (group similar failures)
3. Specific action items to resolve the issues

Be direct, actionable, and prioritize by impact.

Always respond with valid JSON in this exact format:
{
  "summary": "Your executive summary here",
  "categories": [
    {
      "name": "Category Name",
      "count": number_of_dags,
      "dag_ids": ["dag1", "dag2"],
      "description": "What's causing this category of failures"
    }
  ],
  "action_items": [
    {
      "priority": "high|medium|low",
      "title": "Action title",
      "description": "Detailed action description",
      "affected_dags": ["dag1", "dag2"]
    }
  ]
}"""

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": [
                {
                    "role": "user",
                    "content": context
                }
            ],
            "temperature": 0.3
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["content"][0]["text"]
            
            # Parse JSON response
            import json
            analysis = json.loads(content)
            
            return analysis


# Global service instance
llm_service = LLMService()
