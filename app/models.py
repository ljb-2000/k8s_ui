from django.db import models


class Project(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    use_rc = models.CharField(max_length=30)
    jenkins_job_name = models.CharField(max_length=30)
    description = models.CharField(max_length=30)
    def __unicode__(self):
        return self.name