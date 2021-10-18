import os
from django import forms

PATH_TO_DIR = "/home/user/python_projects/"


class TaskForm(forms.Form):
    blank_choice = (('', '----Выберите значение----'), )
    # CHOICES = tuple((item, item) for item in os.listdir("/mnt/billing/")
    #                if os.path.isdir(os.path.join("/mnt/billing/", item)))
    CHOICES = tuple((item, item) for item in os.listdir(PATH_TO_DIR)
                    if os.path.isdir(os.path.join(PATH_TO_DIR, item)))
    yearField = forms.ChoiceField(choices=blank_choice + CHOICES,
                                  label="Выберите год:")
    departField = forms.ChoiceField(choices=blank_choice,
                                    label="Выберите подразделение:")
    szField = forms.ChoiceField(choices=blank_choice,
                                label="Выберите служ. записку:")
