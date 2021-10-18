from draw import procloc
import os

from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import JsonResponse
from .forms import TaskForm
from .models import Task

PATH_TO_DIR = "/home/user/python_projects/"


def index(request):
    """Main page."""
    if request.method != "POST":
        # No data submitted, create a blank form.
        form = TaskForm()
    else:
        # POST data submitted; process data.
        form = TaskForm(data=request.POST)
        year = request.POST.get('yearField')
        depart = request.POST.get('departField')
        sz = request.POST.get('szField')
        form.fields['yearField'].choices = [(year, year)]
        form.fields['departField'].choices = [(depart, depart)]
        form.fields['szField'].choices = [(sz, sz)]
        if form.is_valid():
            taskObj = Task()
            taskObj.year = form.cleaned_data['yearField']
            taskObj.depart = form.cleaned_data['departField']
            taskObj.sz = form.cleaned_data['szField']
            taskObj.status = "Добавленa в очередь на обработку"
            taskObj.save()
            return redirect('draw:tasks')

    # Display a blank or invalid form.
    context = {'form': form}
    return render(request, 'draw/index.html', context)


def get_departments(request):
    """Process the request for depart field."""
    year = request.GET.get('year')
    fullPath = os.path.join(PATH_TO_DIR, year)
    depart_list = [
        item for item in os.listdir(fullPath)
        if os.path.isdir(os.path.join(fullPath, item))
    ]
    # return JsonResponse({'data': depart_list})
    return render(request, 'draw/departs_dropdown_list_options.html',
                  {'departs': depart_list})


def get_sz(request):
    """Using ajax-request to load sz."""
    year = request.GET.get('year')
    depart = request.GET.get('depart')
    fullPath = os.path.join(PATH_TO_DIR, year, depart)
    sz_list = [
        item for item in os.listdir(fullPath)
        if os.path.isdir(os.path.join(fullPath, item))
    ]
    return render(request, 'draw/sz_dropdown_list_options.html',
                  {'sz': sz_list})


def tasks(request):
    """Check the status of task, then if needed call the procloc functions
    to process the bill files and render locations.
    Show all tasks and it's status of proccessing."""

    tasks = Task.objects.order_by('-dateTime_added')
    if (tasks is not None):
        for task in tasks:
            if task.status == "Добавленa в очередь на обработку":
                task.status = "Обрабатывается"
                task.save()
                path = os.path.join(PATH_TO_DIR, task.year, task.depart,
                                    task.sz)
                procloc.start(path)
                task.status = "Завершена."
                task.save()

    context = {'tasks': tasks}
    return render(request, 'draw/tasks.html', context)
