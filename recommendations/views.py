from django.shortcuts import render
from django.conf import settings
import google.generativeai as genai
from .models import UserProblem  # Import your model
from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def recommend_solution(request):
    recommendation = None
    error_message = None
    
    if request.method == "POST":
        problem_description = request.POST.get("problem")
        
        # More structured prompt
        context_input = f"""My dog has the following problem: {problem_description}. 
        Please provide a recommendation in the following format:
        1. Possible Causes (list the most common causes)
        2. Initial Steps to Take (what the owner should do first)
        3. Warning Signs (when to see a vet)
        4. Care Instructions (if applicable)
        5. Important Notes
        
        Please structure the response with clear headings and bullet points."""

        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        try:
            response = genai.GenerativeModel("gemini-2.0-flash").generate_content(
                contents=context_input
            )
            recommendation = response.text

            # Save to database
            UserProblem.objects.create(
                user=request.user,
                problem_description=problem_description,
                recommendation=recommendation
            )

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"

    user_problems = UserProblem.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'recommendations.html', {
        'recommendation': recommendation,
        'error_message': error_message,
        'user_problems': user_problems
    })