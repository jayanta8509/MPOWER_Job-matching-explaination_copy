from flask import Flask, request, jsonify
import json
import os
from flask_cors import CORS
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Configure OpenAI
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI()

if not openai_api_key:
    print("WARNING: OPENAI_API_KEY environment variable not set. You need to set it before running this application.")

def normalize_analysis_response(analysis):
    """
    Normalize the analysis response to ensure consistent data types
    """
    normalized = {
        "match_explanation": "",
        "strengths": [],
        "gaps": [],
        "recommendations": []
    }
    
    # Ensure match_explanation is a string
    if "match_explanation" in analysis:
        if isinstance(analysis["match_explanation"], str):
            normalized["match_explanation"] = analysis["match_explanation"]
        else:
            normalized["match_explanation"] = str(analysis["match_explanation"])
    
    # Ensure strengths is an array
    if "strengths" in analysis:
        if isinstance(analysis["strengths"], list):
            normalized["strengths"] = analysis["strengths"]
        elif isinstance(analysis["strengths"], str):
            # If it's a string, split by common delimiters or make it a single item array
            if analysis["strengths"].strip():
                # Try to split by common delimiters
                strengths_str = analysis["strengths"]
                if '\n' in strengths_str:
                    normalized["strengths"] = [s.strip() for s in strengths_str.split('\n') if s.strip()]
                elif ';' in strengths_str:
                    normalized["strengths"] = [s.strip() for s in strengths_str.split(';') if s.strip()]
                elif ',' in strengths_str:
                    normalized["strengths"] = [s.strip() for s in strengths_str.split(',') if s.strip()]
                else:
                    normalized["strengths"] = [strengths_str]
        else:
            normalized["strengths"] = [str(analysis["strengths"])]
    
    # Ensure gaps is an array
    if "gaps" in analysis:
        if isinstance(analysis["gaps"], list):
            normalized["gaps"] = analysis["gaps"]
        elif isinstance(analysis["gaps"], str):
            if analysis["gaps"].strip():
                # Try to split by common delimiters
                gaps_str = analysis["gaps"]
                if '\n' in gaps_str:
                    normalized["gaps"] = [s.strip() for s in gaps_str.split('\n') if s.strip()]
                elif ';' in gaps_str:
                    normalized["gaps"] = [s.strip() for s in gaps_str.split(';') if s.strip()]
                elif ',' in gaps_str:
                    normalized["gaps"] = [s.strip() for s in gaps_str.split(',') if s.strip()]
                else:
                    normalized["gaps"] = [gaps_str]
        else:
            normalized["gaps"] = [str(analysis["gaps"])]
    
    # Ensure recommendations is an array
    if "recommendations" in analysis:
        if isinstance(analysis["recommendations"], list):
            normalized["recommendations"] = analysis["recommendations"]
        elif isinstance(analysis["recommendations"], str):
            if analysis["recommendations"].strip():
                # Try to split by common delimiters
                rec_str = analysis["recommendations"]
                if '\n' in rec_str:
                    normalized["recommendations"] = [s.strip() for s in rec_str.split('\n') if s.strip()]
                elif ';' in rec_str:
                    normalized["recommendations"] = [s.strip() for s in rec_str.split(';') if s.strip()]
                elif ',' in rec_str:
                    normalized["recommendations"] = [s.strip() for s in rec_str.split(',') if s.strip()]
                else:
                    normalized["recommendations"] = [rec_str]
        else:
            normalized["recommendations"] = [str(analysis["recommendations"])]
    
    return normalized

def analyze_job_match(data):
    """
    Use OpenAI to analyze the job match and provide an explanation
    """
    if not openai_api_key:
        return {"error": "OpenAI API key not configured. Please set the OPENAI_API_KEY environment variable."}
    
    # Format the input data for the prompt
    member_data = data.get("data", {}).get("member", {})
    job_data = data.get("data", {}).get("jobpost", {})
    match_percentage = data.get("data", {}).get("Matching_Percentage", 0)
    
    # Create a prompt for OpenAI
    prompt = f"""
You are an AI career advisor analyzing a job match. Here's the data:

JOB POSTING:
- Title: {job_data.get('JobTitle', 'N/A')}
- Required Skills: {job_data.get('Required_Skills', 'N/A')}
- Preferred Skills: {job_data.get('PreferredSkills', 'N/A')}
- Qualifications: {job_data.get('Qualifications', 'N/A')}
- Responsibilities: {job_data.get('Key_Responsibilities', 'N/A')}
- Industry: {job_data.get('Industry', 'N/A')}
- Role: {job_data.get('Role', 'N/A')}
- Location: {job_data.get('JobLocation', 'N/A')}

YOUR PROFILE:
- Headline: {member_data.get('Headline', 'N/A')}
- Technical Skills: {member_data.get('TechnicalSkillNames', 'N/A')}
- Other Skills: {member_data.get('OtherSkills', 'N/A')}
- Experience: {member_data.get('Experience', 'N/A')}
- Job Titles: {member_data.get('JobTitles', 'N/A')}
- Education: {member_data.get('Education', 'N/A')}
- Communication Skills: {member_data.get('CommunicationNames', 'N/A')}
- Leadership Skills: {member_data.get('LeadershipNames', 'N/A')}
- Critical Thinking: {member_data.get('CriticalThinkingNames', 'N/A')}
- Collaboration: {member_data.get('CollaborationNames', 'N/A')}
- Character: {member_data.get('CharacterNames', 'N/A')}
- Creativity: {member_data.get('CreativityNames', 'N/A')}
- Growth Mindset: {member_data.get('GrowthMindsetNames', 'N/A')}
- Mindfulness: {member_data.get('MindfulnessNames', 'N/A')}
- Fortitude: {member_data.get('FortitudeNames', 'N/A')}
- City: {member_data.get('CityName', 'N/A')}

MATCH RESULT:
- Match Percentage: {match_percentage}%

MATCHING ALGORITHM COMPONENTS:
1. Required Skills (30%): Job's Required Skills matched against your Technical Skills and Soft Skills (Character, Collaboration, Communication, Creativity, Critical Thinking, Fortitude, Growth Mindset, Leadership, Mindfulness) and Other Skills
2. Preferred Skills (15%): Job's Preferred Skills matched against your Technical Skills and Other Skills
3. Other Skills (10%): Job's Required & Preferred Skills matched against your Technical Skills and Other Skills
4. Qualifications (15%): Job's Qualifications matched against your Education and Experience
5. Responsibilities (15%): Job's Key Responsibilities matched against your Experience
6. Industry (5%): Job's Industry matched against your Industry experience
7. Role (5%): Job's Role matched against your Job Titles
8. Location (5%): Job's Location matched against your City

Based on the above information and matching algorithm, provide a detailed explanation of:
1. Why your profile received a {match_percentage}% match score for this job
2. Identify the strongest matching areas between your profile and the job
3. Identify skills or qualifications gaps you should work on to improve your match percentage
4. Provide 3-5 specific, actionable recommendations for how you can improve your match score

Format your response as a JSON with these keys:
- match_explanation: (string) detailed explanation text
- strengths: (array of strings) list of matching strengths
- gaps: (array of strings) list of skill/qualification gaps
- recommendations: (array of strings) list of actionable recommendations

IMPORTANT: strengths, gaps, and recommendations MUST be arrays of strings, not single strings or other formats.
"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a job matching AI assistant that provides detailed analysis of job matches."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1500,
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        try:
            analysis_text = response.choices[0].message.content
            analysis = json.loads(analysis_text)
            return normalize_analysis_response(analysis)
        except json.JSONDecodeError:
            # If response is not valid JSON, return it as plain text with correct format
            return normalize_analysis_response({
                "match_explanation": response.choices[0].message.content,
                "strengths": [],
                "gaps": [],
                "recommendations": []
            })
            
    except Exception as e:
        return {"error": f"Error analyzing job match: {str(e)}"}

@app.route('/analyze_job_match', methods=['POST'])
def analyze_match():
    """
    API endpoint to analyze job match data and provide an explanation
    """
    try:
        # Get the data from the request
        data = request.json
        
        # Make sure required data is present
        if not data or "data" not in data:
            return jsonify({"error": "Invalid data format. Missing 'data' field."}), 400
            
        # Get the analysis
        analysis = analyze_job_match(data)
        
        # Return only the analysis and matching percentage
        response = {
            "status": "success",
            "data": {
                "Matching_Percentage": data.get("data", {}).get("Matching_Percentage", 0),
                "analysis": analysis
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Check if API key is set
    if not openai_api_key:
        print("\nWARNING: OPENAI_API_KEY not set in environment variables!")
        print("To set it, run: export OPENAI_API_KEY=your_api_key_here\n")
    
    # Run the Flask app
    # app.run(host="127.0.0.1", port=7001, debug=True)
    app.run(host="0.0.0.0", port=8123, debug=True)
