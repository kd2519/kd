from django.contrib import admin
from .models import EEGRecord, EEGDataPoint

@admin.register(EEGRecord)
class EEGRecordAdmin(admin.ModelAdmin):
    list_display = ('recording_id', 'name', 'start_time', 'end_time', 'data_count')
    search_fields = ('name', 'recording_id')

@admin.register(EEGDataPoint)
class EEGDataPointAdmin(admin.ModelAdmin):
    list_display = ('recording', 'time', 'delta', 'theta', 'alpha')
    list_filter = ('recording',)