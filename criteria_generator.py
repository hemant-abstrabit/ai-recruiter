import json
import os
from dotenv import load_dotenv
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

            Your task is to deeply analyze the following Job Description (JD) and generate a structured set of **selection criteria** that will be used to evaluate candidate resumes.

            You must:
            - Identify both **explicitly stated** and **implicitly expected** skills, experiences, or qualities that a strong candidate should demonstrate for this role.
            - Assign a **"Must-Have: Yes/No"** flag to each, based on whether the criterion is essential or simply desirable.
            - Assign a **weight (%)** to each, reflecting its relative importance in the role.
            - Provide a clear and detailed **description** of what should be visible in a resume to demonstrate each criterion (e.g., tools, certifications, years of experience, domain exposure, soft skills, etc.).

            Think like an experienced recruiter:
            - What would you expect from top candidates even if not directly mentioned in the JD?
            - Include domain-specific soft skills, work styles, or team collaboration expectations if relevant.
            - Differentiate between mission-critical requirements and value-adding qualities.

            ---

            Job Description:
            {jd_text}

            Additional Instructions (optional):
            {user_guidance}

            ---

            Output Format:

            Return a JSON array. Strictly follow this exact format:
            [
            {{
                "name": "Skill/Experience/Quality Name",
                "must_have": "Yes/No",
                "weight": "X%",
                "description": "Explain how this should be demonstrated in the resume. Include tools, technologies, or evidence you expect to find."
            }},
            ...
            ]

            Ensure the total of all weights is close to 100%. Do not include any explanations outside the JSON array.
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
        required_keys = ['name', 'must_have', 'weight', 'description']
        
        if not criteria:
            raise ValueError("No criteria generated")
        
        for i, criterion in enumerate(criteria):
            if not isinstance(criterion, dict):
                raise ValueError(f"Criterion {i+1} is not a dictionary")
            
            for key in required_keys:
                if key not in criterion:
                    raise ValueError(f"Missing '{key}' in criterion {i+1}")
            
            # Validate must_have field
            if criterion['must_have'] not in ['Yes', 'No']:
                raise ValueError(f"Invalid must_have value in criterion {i+1}: {criterion['must_have']}")
            
            # Validate weight format
            weight_str = criterion['weight']
            if not weight_str.endswith('%'):
                raise ValueError(f"Weight must end with '%' in criterion {i+1}")
            
            try:
                weight_value = float(weight_str[:-1])
                if weight_value < 0 or weight_value > 100:
                    raise ValueError(f"Weight must be between 0-100% in criterion {i+1}")
            except ValueError:
                raise ValueError(f"Invalid weight format in criterion {i+1}")
        
        return criteria
    
    def format_criteria_for_display(self, criteria: List[Dict]) -> str:
        """Format criteria for display purposes."""
        if not criteria:
            return "No criteria generated"
        
        formatted = []
        total_weight = 0
        
        for i, criterion in enumerate(criteria, 1):
            weight_value = float(criterion['weight'][:-1])
            total_weight += weight_value
            
            formatted.append(f"""
**{i}. {criterion['name']}**
- Must-Have: {criterion['must_have']}
- Weight: {criterion['weight']}
- Description: {criterion['description']}
""")
        
        result = "\n".join(formatted)
        result += f"\n\n**Total Weight: {total_weight:.1f}%**"
        
        return result