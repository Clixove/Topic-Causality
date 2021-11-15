from django.contrib import admin
from .models import *


@admin.register(DecompositionContent)
class DecompositionContentAdmin(admin.ModelAdmin):
    list_display = ['task', 'kept_dimension', 'eps', 'class_num']
    autocomplete_fields = ['task']
    search_fields = ['task']


@admin.register(Influence)
class InfluenceAdmin(admin.ModelAdmin):
    list_display = ['task']
    autocomplete_fields = ['task']
    search_fields = ['task']


@admin.register(EventTimeSeriesGenerator)
class EventTimeSeriesGeneratorAdmin(admin.ModelAdmin):
    list_display = ['task', 'time_points', 'influence_shrink_ratio']
    autocomplete_fields = ['task']
    search_fields = ['task']
