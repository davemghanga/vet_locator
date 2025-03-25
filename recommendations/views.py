from django.shortcuts import render
from django.conf import settings
import google.generativeai as genai
from .models import UserProblem
from django.contrib.auth.decorators import login_required
import re

def clean_recommendation_text(text):
    """
    Clean and format the recommendation text
    """
    # Remove excessive asterisks and clean up formatting
    text = re.sub(r'\*{2,}', '', text)
    
    # Replace section headings with emojified versions
    section_map = {
        'Most Likely Causes:': '🔍 Likely Causes:',
        'Top 3 Immediate Actions:': '⚠️ Immediate Actions:',
        'Warning Signs:': '🚨 Warning Signs:',
        'Care Instructions:': '❤️ Care Tips:',
        'Important Notes:': '📝 Important Notes:'
    }
    
    for original, replacement in section_map.items():
        text = text.replace(original, replacement)
    
    # Custom filtering functions
    def split_lines(value):
        return [line.strip() for line in value.split('\n') if line.strip()]
    
    def is_section_header(line):
        emojis = ['🔍', '⚠️', '🚨', '❤️', '📝']
        return (line.endswith(':') and 
                any(emoji in line for emoji in emojis))
    
    def is_not_empty(line):
        return (line.strip() and 
                not is_section_header(line) and 
                not line.startswith('-'))
    
    # Process lines
    processed_lines = []
    lines = split_lines(text)
    for line in lines:
        if is_section_header(line):
            processed_lines.append(f'\n{line}\n')
        elif is_not_empty(line):
            processed_lines.append(f'• {line}')
    
    return '\n'.join(processed_lines)

@login_required(login_url='login')
def recommend_solution(request):
    recommendation = None
    error_message = None
    
    if request.method == "POST":
        problem_description = request.POST.get("problem")
        
        # More structured and concise prompt
        context_input = f"""Pet Health Consultation Request:
        Problem: {problem_description}

        Please provide a comprehensive yet concise recommendation:
        Most Likely Causes:
        - List the potential reasons for the symptoms

        Top 3 Immediate Actions:
        - Suggest practical steps the pet owner can take

        Warning Signs:
        - Highlight critical symptoms that require immediate vet attention

        Care Instructions:
        - Provide specific care guidance

        Use a compassionate, clear, and informative tone."""

        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        try:
            response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                contents=context_input
            )
            
            # Clean and format recommendation
            recommendation = clean_recommendation_text(response.text)

            # Save to database
            UserProblem.objects.create(
                user=request.user,
                problem_description=problem_description,
                recommendation=recommendation
            )

        except Exception as e:
            error_message = f"Unable to generate recommendation. Please try again."
            # Optional: log the error for debugging
            print(f"Recommendation Error: {str(e)}")

    user_problems = UserProblem.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'recommendations.html', {
        'recommendation': recommendation,
        'error_message': error_message,
        'user_problems': user_problems
    })