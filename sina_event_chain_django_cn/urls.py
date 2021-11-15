"""sina_event_chain_django_cn URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
import my_login.views as v1
import task_manager.views as v2
import statistics_figure.views as v3
import bert.views as v4
import events_time_series.views as v5
import granger_causality.views as v6

urlpatterns = [
    path('admin/', admin.site.urls),
    # my login
    path('my_login/view', v1.view_login),
    path('my_login/add', v1.add_login),
    path('my_login/delete', v1.delete_login),
    path('my_login/register', v1.view_register),
    path('my_login/register/add', v1.add_register),
    path('my_login/register/confirm/<str:invitation_code>', v1.add_user),
    # task manager
    path('main', v2.view_main),
    path('task/list', v2.view_tasks),
    path('task/delete', v2.delete_task),
    path('task/add-1', v2.view_add_task),
    path('task/add-2', v2.add_task),
    path('task/add-5', v2.view_descriptive_statistics),
    # statistics figure
    path('task/add-3', v3.view_set_variables),
    path('task/add-4', v3.exe_set_variables),
    path('stats_fig/time_trending', v3.view_time_trending_figures),
    path('stats_fig/user_trending', v3.view_user_trending_figures),
    # BERT
    path('task/add-6', v4.exe_bert),
    # event time series
    path('task/add-7', v5.exe_pca),
    path('task/add-8', v5.view_pca),
    path('event_ts/explained_variance_ratio', v5.view_pca_figure),
    path('event_ts/adjust_pca_x_range', v5.adjust_pca_x_range),
    path('task/add-9', v5.exe_knn),
    path('task/add-10', v5.view_clustering),
    path('event_ts/knn', v5.view_knn_figure),
    path('task/add-11', v5.exe_clustering),
    path('event_ts/influence', v5.view_influence_figure),
    path('task/add-12', v5.view_event_ts),
    path('task/add-13', v5.exe_event_ts),
    # granger causality
    path('task/add-14', v6.view_granger_causality),
    path('gc/get_gc_config', v6.get_gc_config),
    path('task/add-15', v6.exe_granger_causality),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
