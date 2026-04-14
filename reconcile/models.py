from django.db import models


# Create your models here.
class Register(models.Model):
    id = models.AutoField(serialize=True, primary_key=True)
    company_id = models.IntegerField()
    issue_date = models.DateField()
    debit_account = models.CharField(max_length=100, default="")
    credit_account = models.CharField(max_length=100, default="")
    description = models.TextField(max_length=100)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    