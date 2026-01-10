from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.conf import settings
import json
from .models import Query, Response
from .agents import ResearchAssistantAgent

agent = ResearchAssistantAgent(settings.VECTOR_DB_PATH)

def index(request):
    """Render the main frontend page"""
    return render(request, 'index.html')

@csrf_exempt
@require_http_methods(["POST"])
def process_query(request):
    """Process a research query through the agentic RAG system"""
    try:
        data = json.loads(request.body)
        query_text = data.get('query', '')
        
        if not query_text:
            return JsonResponse({'error': 'Query is required'}, status=400)
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        query_obj = Query.objects.create(
            query_text=query_text,
            user_ip=ip
        )
        
        result = agent.process_query(query_text)
        
        query_obj.is_safe = result['is_safe']
        query_obj.safety_issues = '; '.join(result['safety_issues'])
        query_obj.save()
        
        if result['iterations']:
            last_iteration = result['iterations'][-1]
            Response.objects.create(
                query=query_obj,
                maker_response=result['iterations'][0]['maker_answer'],
                checker_feedback=last_iteration['checker_feedback'],
                final_response=result['final_answer'],
                is_approved=result['approved'],
                iteration_count=len(result['iterations'])
            )
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'agent': 'Research Assistant Agent',
        'version': '1.0'
    })