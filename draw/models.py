from django.db import models


class Task(models.Model):
    """Task and it's status of proccessing - creating a shot of map."""
    id = models.AutoField(primary_key=True)
    year = models.CharField(max_length=5)
    depart = models.CharField(max_length=30)
    sz = models.CharField(max_length=200)
    dateTime_added = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)

    def __str__(self):
        """Return a string representation of the model."""
        return f"{self.sz}"
