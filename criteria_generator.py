import json
import os
import google.generativeai as genai
from typing import List, Dict, Optional


class CriteriaGenerator:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the criteria generator with Gemini API."""
        try:
            # Use provided API key or fall back to environment variable
            key = api_key or os.getenv('GEMINI_API_KEY')
            if not key:
                raise ValueError("No API key provided. Set GEMINI_API_KEY environment variable or provide key directly.")
            
            genai.configure(api_key=key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        except Exception as e:
            raise Exception(f"Failed to initialize Gemini model: {str(e)}")
    
    def generate_criteria(self, job_role: str, jd_text: str, user_guidance: str = "") -> List[Dict]:
        """
        Generate selection criteria based on job role and description.
        
        Args:
            job_role (str): Job role/title
            jd_text (str): Job description text
            user_guidance (str): Additional instructions from user
            
        Returns:
            List[Dict]: List of selection criteria
        """
        if not jd_text or not jd_text.strip():
            raise ValueError("Job description cannot be empty")
        
        if not job_role or not job_role.strip():
            raise ValueError("Job role cannot be empty")
        
        prompt = f""" 
You are an expert AI recruitment analyst. 
 
Your task is to thoroughly analyze the following Job Description (JD) and generate a structured set of **selection criteria** for evaluating candidate resumes. 
 
You must: 
- Identify both **explicitly stated** and **implicitly expected** skills, experiences, or qualities. 
- For each criterion, assign one of the following **priority categories**: 
    - "Must-Have": Essential and required for the role. 
    - "Nice-to-Have": Not required but valuable and relevant. 
    - "Bonus Advantage": Extra qualities that make a candidate stand out, even if not asked for. 
    - "Red Flag": Situations that indicate a candidate should be disqualified (e.g., missing a mandatory qualification). 
- Provide a detailed **description** of what should be demonstrated in a resume for this criterion (e.g., tools used, certifications, years of experience, types of projects, soft skills, domains, etc.). 
 
Think like a senior recruiter: 
- What makes a candidate clearly qualified? 
- What would strengthen their case? 
- What might be a concern or reason for exclusion? 
 
--- 
 
Job Description: 
{jd_text} 
 
Additional Instructions (optional): 
{user_guidance} 
 
--- 
 
Output Format: 
 
Return a JSON array. Strictly follow this format for each criterion: 
 
[ 
  {{ 
    "name": "Skill/Experience/Quality Name", 
    "priority": "Must-Have / Nice-to-Have / Bonus Advantage / Red Flag", 
    "description": "Explain how this should be demonstrated in the resume. Include tools, technologies, years of experience, certifications, or types of work." 
  }}, 
  ... 
] 
 
Return only the JSON array. Do not include any explanation or commentary outside the array. 
"""
        try:
            response = self.model.generate_content(prompt)
            criteria_json = self._extract_json_from_response(response.text)
            validated_criteria = self._validate_criteria(criteria_json)
            return validated_criteria
            
        except Exception as e:
            raise Exception(f"Error generating criteria: {str(e)}")
    
    def _extract_json_from_response(self, response_text: str) -> List[Dict]:
        """Extract JSON from the model response."""
        try:
            # Find JSON array in the response
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON array found in response")
            
            json_str = response_text[start_idx:end_idx]
            criteria = json.loads(json_str)
            
            if not isinstance(criteria, list):
                raise ValueError("Response is not a JSON array")
                
            return criteria
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing response: {str(e)}")
    
    def _validate_criteria(self, criteria: List[Dict]) -> List[Dict]:
        """Validate the structure of generated criteria."""
        required_keys = ['name', 'priority', 'description']
        valid_priorities = ['Must-Have', 'Nice-to-Have', 'Bonus Advantage', 'Red Flag']
        
        if not criteria:
            raise ValueError("No criteria generated")
        
        for i, criterion in enumerate(criteria):
            if not isinstance(criterion, dict):
                raise ValueError(f"Criterion {i+1} is not a dictionary")
            
            for key in required_keys:
                if key not in criterion:
                    raise ValueError(f"Missing '{key}' in criterion {i+1}")
            
            # Validate priority field
            if criterion['priority'] not in valid_priorities:
                raise ValueError(f"Invalid priority value in criterion {i+1}: {criterion['priority']}. Must be one of: {', '.join(valid_priorities)}")
        
        return criteria
    
    def format_criteria_for_display(self, criteria: List[Dict]) -> str:
        """Format criteria for display purposes."""
        if not criteria:
            return "No criteria generated"
        
        formatted = []
        priority_counts = {}
        
        for i, criterion in enumerate(criteria, 1):
            priority = criterion['priority']
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            formatted.append(f"""
**{i}. {criterion['name']}**
- Priority: {criterion['priority']}
- Description: {criterion['description']}
""")
        
        result = "\n".join(formatted)
        
        # Add summary
        result += "\n\n**Summary:**\n"
        for priority, count in priority_counts.items():
            result += f"- {priority}: {count} criteria\n"
        
        return result