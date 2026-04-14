from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.db import connection
from datetime import datetime
from .forms import UploadForm
from .models import Register
from io import TextIOWrapper
from decimal import Decimal
import pandas as pd
import csv


def reconcile_home(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            file = request.FILES['file']

            total = process_file(file)

            request.session['total_registros'] = total

            return redirect('reconcile:filter_by_period')

    else:
        form = UploadForm()

    return render(request, 'pages/reconcile_home.html', {'form': form})


def process_file(file):
    df = pd.read_csv(TextIOWrapper(file, encoding='utf-8'))

    registers = []

    for _, row in df.iterrows():
        registers.append(
            Register(
                company_id=row.get('company_id'),
                issue_date=datetime.strptime(row.get('issue_date'), "%d/%m/%Y").date(),
                debit_account=row.get('debit_account'),
                credit_account=row.get('credit_account'),
                description=row.get('description'),
                value=Decimal(str(row.get('value')).replace(',', '.'))
            )
        )

    Register.objects.bulk_create(registers)

    return len(registers)


def filter_by_period(request):
    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    company_id,
                    SUM(
                        CASE
                            WHEN CAST(debit_account AS INTEGER) > CAST(credit_account AS INTEGER)
                            THEN -ABS(value)
                            ELSE ABS(value)
                        END
                    ) AS total_value,
                    MIN(issue_date) AS earliest_date,
                    CASE 
                        WHEN SUM(
                            CASE
                                WHEN CAST(debit_account AS INTEGER) > CAST(credit_account AS INTEGER)
                                THEN -ABS(value)
                                ELSE ABS(value)
                            END
                        ) = 0 THEN 'ZEROED'
                        ELSE 'OPEN'
                    END AS status
                FROM reconcile_register
                WHERE issue_date BETWEEN %s AND %s
                GROUP BY company_id
                ORDER BY company_id
            """, [start_date, end_date])

            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            for r in results:
                r['total_value'] = float(r['total_value']) if r['total_value'] is not None else 0
                r['earliest_date'] = str(r['earliest_date']) if r['earliest_date'] else ''
                
        request.session['results'] = results

        return render(request, 'pages/reconcile_results.html', {
            'results': results
        })

    return render(request, 'pages/reconcile_get_data.html')


def reconcile_process(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT
                company_id,
                SUM(
                    CASE
                        WHEN CAST(debit_account AS INTEGER) > CAST(credit_account AS INTEGER)
                        THEN -ABS(value)
                        ELSE ABS(value)
                    END
                ) AS total_value,
                MIN(issue_date) AS earliest_date,
                CASE 
                    WHEN SUM(
                        CASE
                            WHEN CAST(debit_account AS INTEGER) > CAST(credit_account AS INTEGER)
                            THEN -ABS(value)
                            ELSE ABS(value)
                        END
                    ) = 0 THEN 'ZEROED'
                    ELSE 'OPEN'
                END AS status
            FROM reconcile_register
            GROUP BY company_id
            ORDER BY company_id
        """)

        columns = [col[0] for col in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]

    request.session['results'] = results

    return render(request, 'pages/reconcile_results.html', {
        'results': results
    })


def reconcile_results(request):
    results = request.session.get('results', [])
    return render(request, 'pages/reconcile_results.html', {'results': results})


def export_csv(request):
    results = request.session.get('results', [])

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reconciliation.csv"'

    writer = csv.writer(response)

    # Cabeçalho
    writer.writerow(['Company ID', 'Value', 'Earliest Date', 'Status'])

    # Dados
    for r in results:
        writer.writerow([
            r['company_id'],
            r['total_value'],
            r['earliest_date'],
            r['status']
        ])

    return response

def process_again(request):
    request.session.flush()
    return redirect('reconcile:reconcile_home')