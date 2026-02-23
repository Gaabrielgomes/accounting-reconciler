from django.db import models


class Client(models.Model):
    
    id = models.AutoField(serialize=True, primary_key=True)
    name = models.CharField(max_length=100)
    register_date = models.DateField()
    cpf_cnpj = models.IntegerField(null=True, blank=True)


# Create your models here.
class Supplier(models.Model):
    
    id = models.AutoField(serialize=True, primary_key=True)
    associated_company = models.IntegerField()
    name = models.CharField(max_length=100)
    cpf_cnpj = models.IntegerField(null=True, blank=True)


class Register(models.Model):
    
    class RegisterType(models.TextChoices):
        INBOUND = "INBOUND"
        OUTBOUND = "OUTBOUND"

    id = models.AutoField(serialize=True, primary_key=True)
    company_id = models.IntegerField()
    issue_date = models.DateField()
    debit_account = models.CharField(max_length=100, default="")
    credit_account = models.CharField(max_length=100, default="")
    description = models.TextField(max_length=100)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    register_type = models.TextField(
        choices=RegisterType,
        null=True
    )
