from django.db import models

class Query(models.Model):
    query_text = models.TextField()
    user_ip = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_safe = models.BooleanField(default=True)
    safety_issues = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']

class Response(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE, related_name='responses')
    maker_response = models.TextField()
    checker_feedback = models.TextField(blank=True)
    final_response = models.TextField()
    is_approved = models.BooleanField(default=False)
    iteration_count = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']