from django import forms
from django.contrib.auth.decorators import permission_required
from django.core.files.base import ContentFile
from django.http.response import FileResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from task_manager.models import Column
from task_manager.views import ChooseTask
from .models import *


class SetVariable(forms.Form):
    task = forms.ModelChoiceField(
        Task.objects.all(),
        widget=forms.HiddenInput(),
    )
    is_datetime = forms.ModelChoiceField(
        Column.objects.all(),
        label='选择代表时间的变量', empty_label='',
        widget=forms.Select({'class': 'form-control form-select'}),
    )
    is_user_id = forms.ModelChoiceField(
        Column.objects.all(),
        label='选择代表用户编号的变量', empty_label='',
        widget=forms.Select({'class': 'form-control form-select'}),
    )
    is_text = forms.ModelChoiceField(
        Column.objects.all(),
        label='选择代表帖子正文的变量', empty_label='',
        widget=forms.Select({'class': 'form-control form-select'})
    )
    is_interaction = forms.ModelMultipleChoiceField(
        Column.objects.all(),
        label='选择代表互动指标的多个变量',
        widget=forms.SelectMultiple({'class': 'form-control form-select', 'style': 'height: 12rem;'}),
        help_text='按住 Control 键或 Mac 上的 Command 键来选择多项.'
    )

    def load_choices(self, task):
        self.fields['task'].initial = task
        corresponding_columns = Column.objects.filter(task=task)
        self.fields['is_datetime'].queryset = corresponding_columns
        self.fields['is_user_id'].queryset = corresponding_columns
        self.fields['is_interaction'].queryset = corresponding_columns
        self.fields['is_text'].queryset = corresponding_columns


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_set_variables(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    set_variable = SetVariable()
    set_variable.load_choices(task)
    context = {
        'set_variable_sheet': set_variable,
        'task_id': task.id,
    }
    return render(req, "task/add-3.html", context)


@permission_required("task_manager.change_task", login_url="/main?color=danger&message=没有编辑任务的权限.")
@csrf_exempt
@require_POST
def exe_set_variables(req):
    set_variable = SetVariable(req.POST)
    if not set_variable.is_valid():
        return redirect('/task/list?color=danger&message=提交入口错误.')
    task = set_variable.cleaned_data['task']
    if task.user != req.user:
        return redirect('/task/list?color=danger&message=任务不存在.')
    if task.busy:
        return redirect(f'/task/add-3?index={task.id}&color=danger&message=任务繁忙.')
    set_variable.load_choices(task)
    if not set_variable.is_valid():
        return redirect(f'/task/add-3?index={task.id}color=danger&message=提交入口错误.')
    task.busy = True
    task.current_step = 4
    task.save()
    for col in Column.objects.filter(task=task):
        col.is_datetime = col == set_variable.cleaned_data['is_datetime']
        col.is_user_id = col == set_variable.cleaned_data['is_user_id']
        col.is_interaction = col in set_variable.cleaned_data['is_interaction']
        col.is_text = col == set_variable.cleaned_data['is_text']
        col.save()
    posts = pd.read_pickle(task.posts.path)
    try:
        col_user_id = Column.objects.get(task=task, is_user_id=True)
        col_datetime = Column.objects.get(task=task, is_datetime=True)
    except Column.DoesNotExist:
        return redirect(f'/task/add-3?index={task.id}&color=danger&message=变量未选定.')
    t_trend, u_trend = draw_descriptive_statistics_figures(posts, col_user_id.name, col_datetime.name)
    try:
        dep_stats = DescriptiveStatistics.objects.get(task=task)
    except DescriptiveStatistics.DoesNotExist:
        dep_stats = DescriptiveStatistics(task=task)
        dep_stats.save()
    intermediate_file_handler = ContentFile(t_trend)
    dep_stats.time_trending.delete()
    dep_stats.time_trending.save(f'task_{task.id}_time_trending.png', intermediate_file_handler)
    intermediate_file_handler = ContentFile(u_trend)
    dep_stats.user_trending.delete()
    dep_stats.user_trending.save(f'task_{task.id}_user_trending.png', intermediate_file_handler)
    task.current_step = 5
    task.busy = False
    task.save()
    return redirect(f'/task/add-5?index={task.id}')


@permission_required("task_manager.view_task")
def view_time_trending_figures(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return HttpResponseForbidden()
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return HttpResponseForbidden()
    # -------------- choose task end   --------------
    try:
        return FileResponse(task.descriptivestatistics.time_trending)
    except DescriptiveStatistics.DoesNotExist:
        return HttpResponseForbidden()


@permission_required("task_manager.view_task")
def view_user_trending_figures(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return HttpResponseForbidden()
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return HttpResponseForbidden()
    # -------------- choose task end   --------------
    try:
        return FileResponse(task.descriptivestatistics.user_trending)
    except DescriptiveStatistics.DoesNotExist:
        return HttpResponseForbidden()
