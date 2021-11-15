import pickle
import io
import json
import numpy as np
import pandas as pd
from django import forms
from django.contrib.auth.decorators import permission_required
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http.response import HttpResponseForbidden, FileResponse, HttpResponse
from task_manager.views import ChooseTask
from task_manager.models import AsyncErrorMessage
from bert.models import BERT
from .models import *
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import DBSCAN

num_examples = 10


@permission_required("task_manager.change_task", login_url="/main?color=danger&message=没有编辑任务的权限.")
def exe_pca(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    if task.busy:
        return redirect('/task/list?color=danger&message=任务繁忙.')
    task.busy = True
    task.save()

    try:
        content_path = task.bert.text_features.path
    except BERT.DoesNotExist:
        new_error = AsyncErrorMessage(
            user=req.user, task=task, current_step=7, error_message='文本特征未成功保存, 无法进行主成分分析.')
        new_error.save()
        task.current_step = 5
        task.busy = False
        task.save()
        return
    try:
        with open(content_path, "rb") as f:
            content = pickle.load(f)
        pca = PCA()
        pca.fit(content)
        f, fig = io.BytesIO(), plt.figure()
        plt.plot(np.cumsum(pca.explained_variance_ratio_))
        plt.xlabel("Components Ranking")
        plt.ylabel("Explained Variance Ratio")
        fig.savefig(f, format='png')
        plt.close(fig)
    except Exception as e:
        new_error = AsyncErrorMessage(
            user=req.user, task=task, current_step=7, error_message=f'在主成分分析时发生错误. {e}')
        new_error.save()
        task.current_step = 7
        task.busy = False
        task.save()
        return
    intermediate_file_handler = ContentFile(pickle.dumps(pca))
    try:
        deco_content = DecompositionContent.objects.get(task=task)
    except DecompositionContent.DoesNotExist:
        deco_content = DecompositionContent(task=task)
        deco_content.save()
    deco_content.pca_model.delete()
    deco_content.pca_model.save(f'task_{task.id}_pca_model.pkl', intermediate_file_handler)
    intermediate_file_handler = ContentFile(f.getvalue())
    deco_content.pca_figure.delete()
    deco_content.pca_figure.save(f'task_{task.id}_pca.png', intermediate_file_handler)
    task.current_step = 8
    task.busy = False
    task.save()
    return redirect(f'/task/add-8?index={task.id}')


class PcaXRange(forms.Form):
    task = forms.ModelChoiceField(Task.objects.all(), widget=forms.HiddenInput())
    lower_bound = forms.IntegerField(min_value=0, max_value=768, widget=forms.NumberInput({'class': 'form-control'}))
    upper_bound = forms.IntegerField(min_value=0, max_value=768, widget=forms.NumberInput({'class': 'form-control'}))


class KeepDimension(forms.Form):
    task = forms.ModelChoiceField(Task.objects.all(), widget=forms.HiddenInput())
    dimension = forms.IntegerField(min_value=1, max_value=768, label='保留维度的数量 (1-768)',
                                   widget=forms.NumberInput({'class': 'form-control'}))


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_pca(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    keep_dimension = KeepDimension()
    keep_dimension.fields['task'].initial = task
    pca_x_range = PcaXRange()
    pca_x_range.fields['task'].initial = task
    context = {
        'task_id': task.id,
        'keep_dimension': keep_dimension,
        'pca_x_range': pca_x_range,
    }
    return render(req, "task/add-8.html", context)


@permission_required("task_manager.view_task")
def view_pca_figure(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return HttpResponseForbidden()
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return HttpResponseForbidden()
    # -------------- choose task end   --------------
    try:
        return FileResponse(task.decompositioncontent.pca_figure)
    except DecompositionContent.DoesNotExist:
        return HttpResponseForbidden()


@permission_required("task_manager.change_task", login_url="/main?color=danger&message=没有编辑任务的权限.")
@csrf_exempt
@require_POST
def adjust_pca_x_range(req):
    pca_x_range = PcaXRange(req.POST)
    if not pca_x_range.is_valid():
        return redirect('/task/list?color=danger&message=提交入口错误.')
    task = pca_x_range.cleaned_data['task']
    if task.user != req.user:
        return redirect('/task/list?color=danger&message=任务不存在.')
    try:
        deco_content = task.decompositioncontent
        with open(task.decompositioncontent.pca_model.path, "rb") as f:
            pca = pickle.load(f)
        f, fig = io.BytesIO(), plt.figure()
        plt.plot(np.cumsum(pca.explained_variance_ratio_))
        plt.xlim([pca_x_range.cleaned_data['lower_bound'], pca_x_range.cleaned_data['upper_bound']])
        plt.xlabel("Components Ranking")
        plt.ylabel("Explained Variance Ratio")
        fig.savefig(f, format='png')
        plt.close(fig)
    except Exception as e:
        return redirect(f'/task/add-8?index={task.id}&color=danger&message=绘图时发生错误. {e}')
    intermediate_file_handler = ContentFile(f.getvalue())
    deco_content.pca_figure.delete()
    deco_content.pca_figure.save(f'task_{task.id}_pca.png', intermediate_file_handler)
    return redirect(f'/task/add-8?index={task.id}')


@permission_required("task_manager.change_task", login_url="/main?color=danger&message=没有编辑任务的权限.")
@csrf_exempt
@require_POST
def exe_knn(req):
    kept_dimension = KeepDimension(req.POST)
    if not kept_dimension.is_valid():
        return HttpResponse('/task/list?color=danger&message=提交入口错误.')
    task = kept_dimension.cleaned_data['task']
    if task.user != req.user:
        return HttpResponse('/task/list?color=danger&message=任务不存在.')
    if task.busy:
        return HttpResponse('/task/add-8?color=danger&message=任务繁忙.')
    task.busy = True
    task.current_step = 9
    task.save()
    try:
        deco_content = task.decompositioncontent
        deco_content.kept_dimension = kept_dimension.cleaned_data['dimension']
        with open(task.bert.text_features.path, "rb") as f:
            content = pickle.load(f)
        with open(task.decompositioncontent.pca_model.path, "rb") as f:
            pca = pickle.load(f)
        decomposed_content = pca.transform(content)[:, :deco_content.kept_dimension]
        std_scaler = StandardScaler()
        std_decomposed_content = std_scaler.fit_transform(decomposed_content)
        neighbor = NearestNeighbors(n_neighbors=2 * deco_content.kept_dimension, metric='chebyshev')
        neighbor.fit(std_decomposed_content)
        distance, _ = neighbor.kneighbors(std_decomposed_content)
        nearest_distance = np.sort(distance, axis=0)[:, -1]
        f, fig = io.BytesIO(), plt.figure()
        plt.plot(nearest_distance)
        plt.ylabel("Chebyshev Distance of Nearest Neighbor")
        plt.xlabel("Node Ranking")
        fig.savefig(f, format='png')
        plt.close(fig)
    except Exception as e:
        task.busy = False
        task.current_step = 8
        task.save()
        return HttpResponse(f'/task/add-8?index={task.id}&color=danger&message=降维时发生错误. {e}')
    intermediate_file_handler = ContentFile(pickle.dumps(std_decomposed_content))
    deco_content.std_decomposed_content.delete()
    deco_content.std_decomposed_content.save(f'task_{task.id}_decomposed_content.pkl', intermediate_file_handler)
    intermediate_file_handler = ContentFile(pickle.dumps(std_scaler))
    deco_content.standard_scaler.delete()
    deco_content.standard_scaler.save(f'task_{task.id}_std_scaler.pkl', intermediate_file_handler)
    intermediate_file_handler = ContentFile(f.getvalue())
    deco_content.knn_figure.delete()
    deco_content.knn_figure.save(f'task_{task.id}_text_features_knn.png', intermediate_file_handler)
    task.current_step = 10
    task.busy = False
    task.save()
    return HttpResponse(f'/task/add-10?index={task.id}&color=success&message=成功降维.')


class SetEpsilon(forms.Form):
    task = forms.ModelChoiceField(Task.objects.all(), widget=forms.HiddenInput())
    epsilon = forms.FloatField(
        min_value=0,
        widget=forms.NumberInput({'class': 'form-control'}),
    )


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_clustering(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    set_epsilon = SetEpsilon()
    set_epsilon.fields['task'].initial = task
    context = {
        "task_id": task.id,
        "set_epsilon": set_epsilon,
    }
    return render(req, "task/add-10.html", context)


@permission_required("task_manager.view_task")
def view_knn_figure(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return HttpResponseForbidden()
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return HttpResponseForbidden()
    # -------------- choose task end   --------------
    try:
        return FileResponse(task.decompositioncontent.knn_figure)
    except DecompositionContent.DoesNotExist:
        return HttpResponseForbidden()


@permission_required("task_manager.change_task", login_url="/main?color=danger&message=没有编辑任务的权限.")
@csrf_exempt
@require_POST
def exe_clustering(req):
    set_epsilon = SetEpsilon(req.POST)
    if not set_epsilon.is_valid():
        return HttpResponse('/task/list?color=danger&message=提交入口错误.')
    task = set_epsilon.cleaned_data['task']
    if task.user != req.user:
        return HttpResponse('/task/list?color=danger&message=任务不存在.')
    if task.busy:
        return HttpResponse('/task/add-8?color=danger&message=任务繁忙.')
    task.busy = True
    task.current_step = 11
    task.save()

    try:
        deco_content = task.decompositioncontent
        deco_content.eps = set_epsilon.cleaned_data['epsilon']
        dbscan = DBSCAN(eps=deco_content.eps,
                        min_samples=2 * deco_content.kept_dimension, metric='chebyshev')
        with open(deco_content.std_decomposed_content.path, "rb") as f:
            std_decomposed_content = pickle.load(f)
        posts = pd.read_pickle(task.posts.path)
        dbscan.fit(std_decomposed_content)
        class_labels = dbscan.labels_
        deco_content.class_num = class_labels.max() + 1
        class_names, class_counts = np.unique(class_labels, return_counts=True)
        clusters_detail_dict = []
        name_text = task.column_set.get(is_text=True).name
        content_text = posts[name_text].astype('str')
        for one_class_name, one_class_count in zip(class_names, class_counts):
            sub_content = std_decomposed_content[class_labels == one_class_name, :]
            sub_content_text = content_text[class_labels == one_class_name]
            class_center = np.mean(sub_content, axis=0)
            distance = np.linalg.norm(sub_content - class_center, ord=np.inf, axis=1)
            clusters_detail_dict.append({
                'label': int(one_class_name),
                'count': int(one_class_count),
                'examples': sub_content_text.iloc[np.argsort(distance)[:num_examples]].tolist()
            })
        deco_content.clusters_detail = json.dumps(clusters_detail_dict)
        posts = pd.read_pickle(task.posts.path)
        influence = posts[['reposts', 'comments', 'likes']].astype("int32").values
        min_max_scaler = MinMaxScaler()
        influence_zipped = min_max_scaler.fit_transform(np.log(influence + 1))
        h_x = np.zeros(shape=influence_zipped.shape[1])
        assert influence_zipped.shape[0] > 0
        for i in range(influence_zipped.shape[1]):
            _, p_x = np.unique(influence_zipped[:, i], return_counts=True)
            p_x = p_x / influence_zipped.shape[0]
            h_x[i] = - np.sum(p_x * np.log(p_x))
        influence_metric = np.sum(influence_zipped * h_x, axis=1) / h_x.sum()
        f, fig = io.BytesIO(), plt.figure()
        plt.hist(influence_metric, density=True, bins=21)
        plt.xlabel("Influence metric")
        plt.ylabel("Frequency / class width")
        fig.savefig(f, format='png')
        plt.close(fig)
    except Exception as e:
        task.current_step = 10
        task.busy = False
        task.save()
        return HttpResponse(f'/task/add-10?index={task.id}&color=danger&message=聚类时发生错误. {e}')
    deco_content.save()
    intermediate_file_handler = ContentFile(pickle.dumps(dbscan))
    deco_content.dbscan_model.delete()
    deco_content.dbscan_model.save(f'task_{task.id}_dbscan_model.pkl', intermediate_file_handler)
    intermediate_file_handler = ContentFile(pickle.dumps(class_labels))
    deco_content.class_labels.delete()
    deco_content.class_labels.save(f'task_{task.id}_class_labels.pkl', intermediate_file_handler)

    try:
        influence_ins = Influence.objects.get(task=task)
    except Influence.DoesNotExist:
        influence_ins = Influence(task=task)
        influence_ins.save()
    intermediate_file_handler = ContentFile(pickle.dumps(min_max_scaler))
    influence_ins.min_max_scaler.delete()
    influence_ins.min_max_scaler.save(f'task_{task.id}_min_max_scaler.pkl', intermediate_file_handler)
    intermediate_file_handler = ContentFile(pickle.dumps(influence_metric))
    influence_ins.influence_metric.delete()
    influence_ins.influence_metric.save(f'task_{task.id}_influence_metric.pkl', intermediate_file_handler)
    intermediate_file_handler = ContentFile(f.getvalue())
    influence_ins.influence_metric_figure.delete()
    influence_ins.influence_metric_figure.save(f'task_{task.id}_influence_distribution.png', intermediate_file_handler)
    task.current_step = 12
    task.busy = False
    task.save()
    return HttpResponse(f'/task/add-12?index={task.id}&color=success&message=成功聚类.')


@permission_required("task_manager.view_task")
def view_influence_figure(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return HttpResponseForbidden()
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return HttpResponseForbidden()
    # -------------- choose task end   --------------
    try:
        return FileResponse(task.influence.influence_metric_figure)
    except DecompositionContent.DoesNotExist:
        return HttpResponseForbidden()


class SamplingTimeSeries(forms.Form):
    task = forms.ModelChoiceField(Task.objects.all(), widget=forms.HiddenInput())
    time_points = forms.IntegerField(
        min_value=100, label='等间隔采样次数',
        widget=forms.NumberInput({'class': 'form-control'}),
        help_text='大于100. 采样从帖子样本中最早的发帖时间开始, 到最晚的发帖时间结束, 将时间区间划分为"等间隔采样次数"个时间步.'
    )
    influence_shrink_ratio = forms.IntegerField(
        label='影响力衰减率', initial=1, widget=forms.NumberInput({'class': 'form-control'}),
        help_text='影响力衰减率代表影响力衰减的越快, 负值表示影响力随时间增加. 当取1时, 每过1个时间步, 影响力变成原来的约36.8%.'
    )


@permission_required("task_manager.view_task", login_url="/main?color=danger&message=没有查看任务的权限.")
def view_event_ts(req):
    # -------------- choose task start --------------
    redirect_task_sheet = ChooseTask(req.GET)
    if not redirect_task_sheet.is_valid():
        return redirect('/task/list?color=warning&message=任务不存在.')
    task = redirect_task_sheet.cleaned_data['index']
    if task.user != req.user:
        return redirect('/task/list?color=warning&message=任务不存在.')
    # -------------- choose task end   --------------
    sts = SamplingTimeSeries()
    sts.fields['task'].initial = task
    context = {
        "task_id": task.id, "sampling_time_series": sts,
    }
    try:
        if task.decompositioncontent.clusters_detail:
            context['clusters_detail'] = json.loads(task.decompositioncontent.clusters_detail)
    except Exception as e:
        context['clusters_detail'] = '在解析聚类结果时发生错误. ' + e.__str__()
    return render(req, "task/add-12.html", context)


@permission_required("task_manager.change_task", login_url="/main?color=danger&message=没有编辑任务的权限.")
@csrf_exempt
@require_POST
def exe_event_ts(req):
    sts = SamplingTimeSeries(req.POST)
    if not sts.is_valid():
        return HttpResponse('/task/list?color=danger&message=提交入口错误.')
    task = sts.cleaned_data['task']
    if task.user != req.user:
        return HttpResponse('/task/list?color=danger&message=任务不存在.')
    if task.busy:
        return HttpResponse('/task/add-8?color=danger&message=任务繁忙.')
    task.busy = True
    task.current_step = 13
    task.save()
    try:
        event_ts_generator = EventTimeSeriesGenerator.objects.get(task=task)
    except EventTimeSeriesGenerator.DoesNotExist:
        event_ts_generator = EventTimeSeriesGenerator(task=task)
    event_ts_generator.time_points = sts.cleaned_data['time_points']
    event_ts_generator.influence_shrink_ratio = sts.cleaned_data['influence_shrink_ratio']
    try:
        posts = pd.read_pickle(task.posts.path)
        name_user_id = task.column_set.get(is_user_id=True).name
        content_user_id = posts[name_user_id].astype('str')
        name_datetime = task.column_set.get(is_datetime=True).name
        content_datetime = posts[name_datetime].astype('datetime64')
        user_list = np.unique(content_user_id)
        user_dict = dict(zip(user_list, range(len(user_list))))

        start_time = np.min(content_datetime)
        end_time = np.max(content_datetime)
        time_scale = np.linspace(start_time.value, end_time.value, event_ts_generator.time_points + 1)
        time_scale = pd.to_datetime(time_scale)
        time_slicer = pd.cut(content_datetime.values, time_scale)
        time_discrete = time_slicer.codes.astype('int32')

        influence_shrink_seq = np.exp(-np.arange(
            (event_ts_generator.time_points + 1) * event_ts_generator.influence_shrink_ratio))
        event_ts = np.zeros(shape=(len(user_list), event_ts_generator.time_points + 1,
                                       task.decompositioncontent.class_num + 1))
        with open(task.decompositioncontent.class_labels.path, "rb") as f:
            class_labels = pickle.load(f)
        with open(task.influence.influence_metric.path, "rb") as f:
            influence_metric = pickle.load(f)
        for (user, topic, influence_coef, time_point) in \
                zip(content_user_id, class_labels, influence_metric, time_discrete):
            x, t, f = user_dict[user], time_point + 1, topic
            event_ts[x, t:, f] = influence_coef * influence_shrink_seq[:event_ts_generator.time_points + 1 - t]
    except Exception as e:
        task.current_step = 12
        task.busy = False
        task.save()
        return HttpResponse(f'/task/add-12?index={task.id}&color=danger&message=生成舆情的时间序列时发生错误. {e}')
    event_ts_generator.save()
    intermediate_file_handler = ContentFile(pickle.dumps(user_list))
    event_ts_generator.user_list.delete()
    event_ts_generator.user_list.save(f'task_{task.id}_user_list.pkl', intermediate_file_handler)
    intermediate_file_handler = ContentFile(pickle.dumps(event_ts))
    event_ts_generator.event_ts.delete()
    event_ts_generator.event_ts.save(f'task_{task.id}_event_ts.pkl', intermediate_file_handler)
    task.current_step = 14
    task.busy = False
    task.save()
    return HttpResponse(f'/task/add-14?index={task.id}&color=success&message=成功生成舆情的时间序列.')
