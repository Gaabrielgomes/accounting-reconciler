import os
import json
import pandas as pd
from pathlib import Path
import decimal
from datetime import datetime

def format_decimal(value):
    try:
        value = decimal.Decimal(str(value))
        return value.quantize(decimal.Decimal('0.00'), rounding=decimal.ROUND_DOWN)
    except (decimal.InvalidOperation, TypeError):
        return decimal.Decimal('0.00')

def parse_date(date_value):
    try:
        if isinstance(date_value, str):
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    date_value = datetime.strptime(date_value, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                raise ValueError("Date format not recognized")
        
        elif isinstance(date_value, datetime):
            date_value = date_value.date()

        return date_value.strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Error converting date '{date_value}': {str(e)}")
        return None

dir_name = input("Folder name with archives of reconciliation: ")
base_path = Path(__file__).parent.parent.resolve()
archives_dir = os.path.join(base_path, "archives")
total_path = os.path.join(archives_dir, dir_name)

if not os.path.exists(total_path):
    print(f"Path '{total_path}' not found.")
    exit()

tuples = []
not_found_tuples = []

for directory_number in os.listdir(total_path):
    directory_path = os.path.join(total_path, directory_number)
    archive_file = os.path.join(directory_path, "archive.json")

    if os.path.isdir(directory_path) and os.path.exists(archive_file):
        with open(archive_file, "r", encoding="utf-8") as archive:
            try:
                data = json.load(archive)
            except json.JSONDecodeError as error:
                print(f"Error loading JSON in {archive_file}: {error}")
                continue

        for supplier, supplier_data in data.items():
            if supplier == "NOT_FOUND":
                i_counter = 0
                for key, value in supplier_data.items():
                    if key.startswith("history_"):
                        history = value
                        i_counter += 1
                    if key.startswith("value_"):
                        value_data = value
                        i_counter += 1
                    if key.startswith("date_"):
                        date_data = str(parse_date(value))
                        i_counter += 1

                    if i_counter != 0 and (i_counter % 3) == 0:
                        not_found_tuples.append((directory_number, history, value_data, date_data))
            
            else:
                for invoice, details in supplier_data.items():
                    if not isinstance(details, dict):
                        continue

                    result = format_decimal(details.get("result"))
                    debit = str(details.get("debit", ""))
                    credit = str(details.get("credit", ""))
                    max_date = str(details.get("max_date", ""))
                    min_date = str(details.get("min_date", ""))

                    if max_date == "":
                        max_date = str(parse_date(details.get("date")))
                    
                    tuples.append((directory_number, supplier, invoice, max_date, min_date, debit, credit, result))

# Criação dos DataFrames
dataframe = pd.DataFrame(tuples, columns=["FILIAL", "IDENTIFICACAO", "NOTA", "DATA_MAX", "DATA_MIN", "DEBITO", "CREDITO", "RESULTADO"])
not_found_dataframe = pd.DataFrame(not_found_tuples, columns=["FILIAL", "HISTORICO", "VALOR", "DATA"])

# Exportação dos DataFrames
pathname = input("Name the archive to save and export: ")
export_path = os.path.join(base_path, "export", f"{pathname}.xlsx")
os.makedirs(os.path.dirname(export_path), exist_ok=True)

with pd.ExcelWriter(export_path, engine="openpyxl") as writer:
    dataframe.to_excel(writer, index=False, sheet_name="Dados")
    not_found_dataframe.to_excel(writer, index=False, sheet_name="Não Encontrados")
    
    workbook = writer.book

    for sheet_name in ["Dados", "Não Encontrados"]:
        worksheet = workbook[sheet_name]
        
        for col in worksheet.columns:
            max_length = 0
            col_letter = col[0].column_letter
            
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            adjusted_width = max_length + 2
            worksheet.column_dimensions[col_letter].width = adjusted_width

print(f"Archive '{export_path}' exported with success.")
