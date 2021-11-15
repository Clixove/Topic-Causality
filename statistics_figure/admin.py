from django.contrib import admin
from .models import *


@admin.register(DescriptiveStatistics)
class DescriptiveStatistics(admin.ModelAdmin):
    pass
