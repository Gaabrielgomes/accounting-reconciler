from django.db import models

# Create your models here.
class Supplier(models.Model):
    id = models.AutoField(serialize=True, primary_key=True)
    associated_company = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    cpf_cnpj = models.IntegerField(null=True, blank=True)


class Register(models.Model):
    class RegisterType(models.TextChoices):
        INBOUND = "IN"
        OUTBOUND = "OUT"  

    id = models.AutoField(serialize=True, primary_key=True)
    company_id = models.IntegerField()
    issue_date = models.DateField()
    text = models.TextField(max_length=100)
    register_type = models.TextField(
        max_length=3, 
        choices=RegisterType, 
        default=RegisterType.INBOUND
    )

