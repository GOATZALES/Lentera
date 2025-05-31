# ai_services/admin.py
from django.contrib import admin
from .models import AiForecastRequestLog, AiModelPerformanceFeedback, RegionalRiskAnalysisResult

@admin.register(AiForecastRequestLog)
class AiForecastRequestLogAdmin(admin.ModelAdmin):
    list_display = ('caller_reference_id', 'service_type', 'ai_model_name_used', 'processing_status', 'requested_at', 'completed_at')
    list_filter = ('service_type', 'processing_status', 'ai_model_name_used', 'requested_at')
    search_fields = ('caller_reference_id', 'input_payload_json', 'parsed_ai_output_json')
    readonly_fields = ('requested_at', 'completed_at')

@admin.register(AiModelPerformanceFeedback)
class AiModelPerformanceFeedbackAdmin(admin.ModelAdmin):
    list_display = ('ai_request_log_id', 'get_caller_reference', 'overall_accuracy_score', 'feedback_provided_at', 'accuracy_calculated_at')
    list_filter = ('feedback_provided_at', 'accuracy_calculated_at')
    search_fields = ('ai_request_log__caller_reference_id', 'qualitative_feedback')
    autocomplete_fields = ['ai_request_log']

    def ai_request_log_id(self, obj):
        return obj.ai_request_log.id
    ai_request_log_id.short_description = "AI Request Log ID"
    
    def get_caller_reference(self, obj):
        return obj.ai_request_log.caller_reference_id
    get_caller_reference.short_description = "Caller Reference"

@admin.register(RegionalRiskAnalysisResult)
class RegionalRiskAnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('caller_reference_id', 'risk_level_predicted', 'ai_model_name_used', 'analyzed_at')
    list_filter = ('risk_level_predicted', 'ai_model_name_used', 'analyzed_at')
    search_fields = ('caller_reference_id', 'input_data_summary_text')