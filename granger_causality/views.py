import json
import pickle

import numpy as np
from django import forms
from django.contrib.auth.decorators import permission_required
from django.http.response import HttpResponseForbidden, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.timezone import now
from statsmodels.tools.sm_exceptions import InfeasibleTestError
from statsmodels.tsa.stattools import grangercausalitytests

from task_manager.views import ChooseTask
from .models import *


class SearchUser(forms.Form):
    task = forms.ModelChoiceField(Task.objects.all(), widget=forms.HiddenInput())
    username = forms.CharField(
        widget=forms.TextInput({'class': 'form-control'}), label='用户',
        help_text='用以搜索因果关系的参与者, 搜索内容是帖子数据集中的"用户编号"字段的值. 搜索方式是用户编号必须包含搜索词.'
    )


class GCConfig(forms.Form):
    task = forms.ModelChoiceField(Task.objects.all(), widget=forms.HiddenInput())
    max_lag = forms.IntegerField(min_value=1, widget=forms.NumberInput({'class': 'form-control'}), label='最大滞后阶')
    event = forms.ChoiceField(
        widget=forms.Select({'class': 'from-control form-select'}), label='事件编号', choices=[],
    )
    username = forms.ChoiceField(
        widget=forms.Select({'class': 'form-control form-select'}), label='用户', choices=[],
        help_text='必须先在上一个表单提交搜索, 才能获得选项.'
    )
    direction = forms.BooleanField(
        label='分析方向', required=False,
        widget=forms.Select(
            {'class': 'form-control form-select'},
            choices=[(True, "对其他用户施加影响(主动方)"), (False, "受到其他用户的影响(被动方)")]
        )
    )
    n_results = forms.IntegerField(
        label='最大结果数量 (可选)', required=False,
        widget=forms.NumberInput({'class': 'form-control'}),
        min_value=1, help_text='返回最显著的"最大结果数量"个结果. 如果空白, 则返回所有结果.'
    )

    def load_choices(self, task, username):
        clusters_detail = json.loads(task.decompositioncontent.clusters_detail)
        self.fields['event'].choices = [(x['label'], '事件' + str(x['label'])) for x in clusters_detail]
        with open(task.eventtimeseriesgenerator.user_list.path, "rb") as f:
            user_list = pickle.load(f)
        self.fields['username'].choices = [(x, x) for x in user_list if username in x]

    def load_choices_no_searching(self, task):
        clusters_detail = json.loads(task.decompositioncontent.clusters_detail)
        self.fields['event'].choices = [(x['label'], '事件' + str(x['label'])) for x in clusters_detail]
        with open(task.eventtimeseriesgenerator.user_list.path, "rb") as f:
            user_list = pickle.load(f)
        self.fields['username'].choices = [(x, x) for x in user_list]


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_granger_causality(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    context = {"task_id": task.id, "gc_config": GCConfig()}
    search_user = SearchUser()
    search_user.fields['task'].initial = task
    context['search_user'] = search_user
    return render(req, "task/add-14.html", context)


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
@require_POST
@csrf_exempt
def get_gc_config(req):
    search_user = SearchUser(req.POST)
    if not search_user.is_valid():
        return HttpResponseForbidden()
    task = search_user.cleaned_data['task']
    if (task.user != req.user) or task.busy:
        return HttpResponseForbidden()
    task.busy = True
    task.save()
    try:
        gc = GrangerCausality.objects.get(task=task)
    except GrangerCausality.DoesNotExist:
        gc = GrangerCausality(task=task)
        gc.save()
    try:
        gc_config = GCConfig({
            'task': task, 'max_lag': gc.max_lag, 'event': gc.current_event,
            'username': gc.current_user, 'direction': gc.direction
        })
        gc_config.load_choices(task, search_user.cleaned_data['username'])
    except Exception as e:
        task.busy = False
        task.save()
        return HttpResponse('读取所需数据时发生错误. ' + e.__str__())
    task.busy = False
    task.save()
    return HttpResponse(gc_config.as_p())


@permission_required("task_manager.change_task", login_url="/main?color=danger&message=没有编辑任务的权限.")
@require_POST
@csrf_exempt
def exe_granger_causality(req):
    gc_config = GCConfig(req.POST)
    try:
        task = Task.objects.get(id=req.POST['task'], user=req.user, busy=False)
    except Task.DoesNotExist:
        return render(req, 'gc/errors.html', {'error_message': '任务繁忙或不存在.'})
    gc_config.load_choices_no_searching(task)
    if not gc_config.is_valid():
        return render(req, 'gc/errors.html', {'error_message': '提交入口错误.'})
    task.busy = True
    task.current_step = 15
    task.save()
    try:
        with open(task.eventtimeseriesgenerator.event_ts.path, 'rb') as f:
            event_ts = pickle.load(f)
        gc = task.grangercausality
        gc.max_lag = max_lag = gc_config.cleaned_data['max_lag']
        gc.current_event = gc_config.cleaned_data['event']  # "k" must place before "gc.current_event"
        gc.current_user = gc_config.cleaned_data['username']
        gc.direction = gc_config.cleaned_data['direction']
        gc.save()
        with open(task.eventtimeseriesgenerator.user_list.path, "rb") as f:
            user_list = pickle.load(f)
        assert event_ts.shape[0] == user_list.shape[0], "用户列表和事件的时间序列中, 用户的数量不同, 所以无法完成Granger因果检验."
        i = np.argwhere(user_list == gc.current_user)[0, 0]
        k = int(gc.current_event)
        gc_results = []
        for j in range(user_list.shape[0]):
            if j == i:
                continue
            try:
                if gc.direction:
                    gc_all = grangercausalitytests(event_ts[[j, i], :, k].T, max_lag, verbose=False)
                else:
                    gc_all = grangercausalitytests(event_ts[[i, j], :, k].T, max_lag, verbose=False)
            except InfeasibleTestError:
                continue
            gc_results.append({
                'username': user_list[j],
                'stats': [gc_all[lag][0]['ssr_ftest'] for lag in range(1, max_lag + 1)],
            })
        gc_results = sorted(gc_results, key=lambda x: x['stats'][-1][1])
        n = gc_config.cleaned_data['n_results']
        if n:
            gc_results = gc_results[:n]
    except Exception as e:
        task.busy = False
        task.current_step = 14
        task.save()
        return render(req, 'gc/errors.html', {'error_message': 'Granger因果检验时发生错误. ' + e.__str__()})
    task.busy = False
    task.current_step = 14
    task.save()
    return render(req, 'gc/stats.html', {'gc_results': gc_results, 'max_lag': max_lag, 'timestamp': now()})
