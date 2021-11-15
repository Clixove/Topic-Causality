import pandas as pd
from django.contrib.auth.decorators import permission_required
from django.core.files.base import ContentFile
from django.shortcuts import redirect
import pickle
from .models import *
from task_manager.models import AsyncErrorMessage
from task_manager.views import ChooseTask
import tensorflow_hub as hub
import tensorflow_text
import numpy as np

batch_size = 500
pre_processor = hub.KerasLayer("bert_models/bert_zh_preprocess_3")
encoder = hub.KerasLayer("bert_models/bert_zh_L-12_H-768_A-12_3")


@permission_required("task_manager.change_task", login_url="/main?color=danger&message=没有编辑任务的权限.")
def exe_bert(req):
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
    task.current_step = 6
    task.save()

    try:
        posts = pd.read_pickle(task.posts.path)
        name_text = task.column_set.get(is_text=True).name
        content = posts[name_text].astype('str').values.tolist()
        content_container = np.empty(shape=(0, 768))  # match BERT model: H-768

        for i in range(posts.shape[0] // batch_size):
            sub_content = content[i * batch_size:(i + 1) * batch_size]
            processed_content = pre_processor(sub_content)
            tokenized_content = encoder(processed_content)['pooled_output']
            content_container = np.vstack([content_container, tokenized_content.numpy()])
        i = posts.shape[0] // batch_size
        sub_content = content[i * batch_size:]
        processed_content = pre_processor(sub_content)
        tokenized_content = encoder(processed_content)['pooled_output']
        content_container = np.vstack([content_container, tokenized_content.numpy()])
    except Exception as e:
        task.current_step = 5
        task.busy = False
        task.save()
        new_error = AsyncErrorMessage(
            user=req.user, task=task, current_step=6, error_message=f'BERT-3模型运行时发生错误. {e}'
        )
        new_error.save()
        return
    intermediate_file_handler = ContentFile(pickle.dumps(content_container))
    try:
        bert_instance = BERT.objects.get(task=task)
    except BERT.DoesNotExist:
        bert_instance = BERT(task=task)
        bert_instance.save()
    bert_instance.text_features.delete()
    bert_instance.text_features.save(f'task_{task.id}_content.pkl', intermediate_file_handler)
    task.current_step = 7  # change "current step" before "busy", forbidden visiting when "current step = 6".
    task.busy = False
    task.save()
    return redirect(f'/task/add-7?index={task.id}')
