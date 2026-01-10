from django.contrib import admin
from .models import Query, Response

@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    list_display = ('id', 'query_preview', 'is_safe', 'user_ip', 'timestamp')
    list_filter = ('is_safe', 'timestamp')
    search_fields = ('query_text', 'user_ip')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def query_preview(self, obj):
        """Show first 100 characters of query"""
        return obj.query_text[:100] + '...' if len(obj.query_text) > 100 else obj.query_text
    query_preview.short_description = 'Query'
    
    fieldsets = (
        ('Query Information', {
            'fields': ('query_text', 'user_ip', 'timestamp')
        }),
        ('Safety Validation', {
            'fields': ('is_safe', 'safety_issues'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'query_preview', 'is_approved', 'iteration_count', 'timestamp')
    list_filter = ('is_approved', 'iteration_count', 'timestamp')
    search_fields = ('query__query_text', 'final_response')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def query_preview(self, obj):
        """Show related query preview"""
        return obj.query.query_text[:80] + '...' if len(obj.query.query_text) > 80 else obj.query.query_text
    query_preview.short_description = 'Related Query'
    
    fieldsets = (
        ('Query Reference', {
            'fields': ('query',)
        }),
        ('Maker-Checker Process', {
            'fields': ('maker_response', 'checker_feedback', 'iteration_count', 'is_approved')
        }),
        ('Final Output', {
            'fields': ('final_response', 'timestamp')
        }),
    )