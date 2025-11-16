"""
Gemini-based evaluator - Evaluates agent responses using Gemini
"""
import json
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

from .config import GEMINI_API_KEY, GEMINI_EVAL_MODEL


EVALUATION_PROMPT = """
You are an AI evaluator for a personal assistant system. Your job is to evaluate the quality of an agent's response to a user query.

**User Query:**
{query}

**Agent Response:**
{response}

**Agent Category:** {category}
**Agent Name:** {agent_name}

**Additional Context:**
{metadata}

Evaluate the response based on:
1. **Correctness**: Does it address the query correctly?
2. **Completeness**: Is the response complete and thorough?
3. **Clarity**: Is it clear and easy to understand?
4. **Helpfulness**: Is it actually helpful to the user?

Provide your evaluation in JSON format with exactly these 3 fields:

{{
  "status": "pass" or "fail",
  "justification": "Brief explanation of why it passed or failed (2-3 sentences)",
  "improvements": "Specific suggestions for improvement (2-3 bullet points)"
}}

Be strict but fair. A "pass" means the response is good enough to be helpful. A "fail" means significant issues that would confuse or mislead the user.
"""


class GeminiEvaluator:
    """Evaluates agent responses using Gemini"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_EVAL_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0.3,  # Lower temperature for consistent evaluation
            convert_system_message_to_human=True,
            request_timeout=30  # 30 second timeout for Gemini
        )
    
    async def evaluate(
        self,
        query: str,
        response: str,
        agent_name: str,
        category: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate an agent response
        
        Returns:
            Dict with: status, justification, improvements, score
        """
        try:
            # Format prompt
            prompt = EVALUATION_PROMPT.format(
                query=query,
                response=response,
                agent_name=agent_name,
                category=category,
                metadata=json.dumps(metadata, indent=2)
            )
            
            # Get evaluation from Gemini
            result = await self.llm.ainvoke(prompt)
            evaluation_text = result.content
            
            # Parse JSON response
            # Try to extract JSON from markdown code blocks if present
            if "```json" in evaluation_text:
                json_start = evaluation_text.find("```json") + 7
                json_end = evaluation_text.find("```", json_start)
                evaluation_text = evaluation_text[json_start:json_end].strip()
            elif "```" in evaluation_text:
                json_start = evaluation_text.find("```") + 3
                json_end = evaluation_text.find("```", json_start)
                evaluation_text = evaluation_text[json_start:json_end].strip()
            
            evaluation = json.loads(evaluation_text)
            
            # Normalize fields to strings (Gemini sometimes returns arrays)
            if isinstance(evaluation.get("justification"), list):
                evaluation["justification"] = " ".join(evaluation["justification"])
            if isinstance(evaluation.get("improvements"), list):
                evaluation["improvements"] = "\n".join(evaluation["improvements"])
            
            # Add score based on status
            evaluation["score"] = 1.0 if evaluation["status"] == "pass" else 0.0
            
            return evaluation
        
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini response: {e}")
            print(f"Response: {evaluation_text}")
            
            # Fallback response
            return {
                "status": "error",
                "justification": f"Failed to parse evaluation: {str(e)}",
                "improvements": "Could not generate improvements due to parsing error",
                "score": 0.0
            }
        
        except Exception as e:
            print(f"Evaluation error: {e}")
            return {
                "status": "error",
                "justification": f"Evaluation failed: {str(e)}",
                "improvements": "Could not evaluate due to error",
                "score": 0.0
            }
    
    def evaluate_sync(
        self,
        query: str,
        response: str,
        agent_name: str,
        category: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synchronous version of evaluate"""
        try:
            prompt = EVALUATION_PROMPT.format(
                query=query,
                response=response,
                agent_name=agent_name,
                category=category,
                metadata=json.dumps(metadata, indent=2)
            )
            
            result = self.llm.invoke(prompt)
            evaluation_text = result.content
            
            # Parse JSON
            if "```json" in evaluation_text:
                json_start = evaluation_text.find("```json") + 7
                json_end = evaluation_text.find("```", json_start)
                evaluation_text = evaluation_text[json_start:json_end].strip()
            elif "```" in evaluation_text:
                json_start = evaluation_text.find("```") + 3
                json_end = evaluation_text.find("```", json_start)
                evaluation_text = evaluation_text[json_start:json_end].strip()
            
            evaluation = json.loads(evaluation_text)
            
            # Normalize fields to strings (Gemini sometimes returns arrays)
            if isinstance(evaluation.get("justification"), list):
                evaluation["justification"] = " ".join(evaluation["justification"])
            if isinstance(evaluation.get("improvements"), list):
                evaluation["improvements"] = "\n".join(evaluation["improvements"])
            
            evaluation["score"] = 1.0 if evaluation["status"] == "pass" else 0.0
            
            return evaluation
        
        except Exception as e:
            print(f"Evaluation error: {e}")
            return {
                "status": "error",
                "justification": f"Evaluation failed: {str(e)}",
                "improvements": "Could not evaluate due to error",
                "score": 0.0
            }

