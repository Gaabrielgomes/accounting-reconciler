import os
import re
import json
import queries
import decimal
import pandas as pd
from tqdm import tqdm
from datetime import datetime
from unidecode import unidecode
from connection import connect_database
from tkinter import messagebox, filedialog


def normalize(text):
    return unidecode(text).upper().strip()

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
        messagebox.showerror(title="Error", message=f"Error converting date: {e}")
        return None

def extract_invoice(row, data):
    cell = data.loc[row]['HISTORICO']
    characters = len(cell)

    conditionals1 = ("N.", "DOC.", "NFS.", "NF.", "Nº", "NFE.", "NOTA FISCAL", " N ", " NF ", "N°.")
    result = process_invoice(cell, characters, conditionals1)
    
    if result == "":
        conditionals2 = ("USO E CONSUMO", "DEVOLUÇÃO DE COMPRAS", "DEVOLUCAO DE COMPRAS")
        result = process_invoice(cell, characters, conditionals2)
    
    return result

def process_invoice(cell, characters, conditionals):
    positions = []
    for conditional in conditionals:
        if conditional in cell:
            position = cell.find(conditional) + len(conditional)
            positions.append(position)
    
    if not positions:
        return ""

    start_position = max(positions)
    counter = 0
    result = ""

    for i in range(start_position, characters):
        if cell[i].isdigit() or cell[i].isalpha():
            counter += 1
            result += cell[i]
            if counter == 9:
                break

        if i + 1 < characters and i - 2 >= 0:
            if cell[i].isdigit() and cell[i+1] in ['-', '/', '\\'] and cell[i-2].isalpha():
                break 

        if i + 1 < characters and cell[i] in ['-', '/', '\\'] and cell[i-1].isalpha():
            result = ""
        
        if i + 1 < characters and cell[i].isdigit() and cell[i-1].isdigit() and cell[i+1] == '-':
            break

        if i + 1 < characters and cell[i] in ['-', '/', '\\'] and cell[i-1].isdigit() and cell[i+1].isdigit():
            if len(result) > 0:
                break
        
        if i + 1 < characters and cell[i+1] == ',':
            break

        if i + 1 < characters and cell[i].isdigit() and cell[i+1] == ' ':
            break

        if i + 1 < characters and cell[i] == " " and cell[i+1].isdigit() and cell[i-1].isalpha():
            result = ""

        if len(result) > 0 and result[0].isalpha():
            result = ""
        
        if i + 1 < characters and cell[i+1] == '/' and cell[i+2].isalpha():
            if len(result) > 0:
                break
    return result

# Validação do arquivo de entrada
file_name = filedialog.askopenfilename(title="Archive selection", filetypes=[("Excel File", "*.xlsx")])

while not os.path.exists(os.path.join(r"..\import", file_name)):
    file_name = str(input(f"The file was not found.\nPlease provide the file name and type again: "))
file_path = os.path.join(r"..\import", file_name)

# Validação do nome da pasta
special_characters = r'[\[\]{}()*+?.,\\^$|#\s]'
pattern = re.compile(special_characters)

reconciliation_folder = input("Folder name to store reconciliation files: ")
while pattern.search(reconciliation_folder):
    reconciliation_folder = input("Invalid name.\nPlease provide another name for the reconciliation folder: ")
base_path = os.path.join(r"..\archives", reconciliation_folder)

# Criação da pasta com tratamento de erros
try:
    os.makedirs(base_path, exist_ok=True)
    print(f"Reconciliation folder created in: {base_path}")
except OSError as e:
    print(f"Error creating file: {e}")
    exit()

if not os.path.exists(file_path):
    print(f"The file '{file_name}' was not found.")
    exit()

# Validação das colunas necessárias
try:
    data = pd.read_excel(file_path)
    required_columns = ['FILIAL', 'HISTORICO', 'DATA', 'VALOR', 'DEBITO', 'CREDITO']
    if not all(col in data.columns for col in required_columns):
        print(f"Necessary columns not found in archive. Expected columns: {required_columns}")
        exit()
except Exception as e:
    print(f"Error reading Excel archive: {e}")
    exit()

total_lines = len(data)
print(f"Processing {total_lines} lines...")

# Processamento principal com tratamento de erros aprimorado
with tqdm(total=total_lines, desc="Reconciling", unit="line", colour="GREEN",
          bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
    
    for row in data.itertuples(index=True): 
        try:
            if pd.isna(row.FILIAL):
                print(f"Row {row.Index}: FILIAL is NaN. Skipping.")
                pbar.update(1)
                continue

            json_path = os.path.join(r"..\json", f"{str(int(row.FILIAL))}.json")
            found_supplier = False  
            
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as file:
                    try:
                        json_data = json.load(file)
                        if not isinstance(json_data, dict):
                            print(f"Invalid format of JSON archive: {json_path}")
                            json_data = {}
                    except json.JSONDecodeError as error:
                        print(f"Error reading JSON {json_path}: {error}")
                        json_data = {}

                for supplier_code, supplier_info in json_data.items():
                    if isinstance(supplier_info, dict) and "nome_fornecedor" in supplier_info:
                        norm_sup_name = normalize(supplier_info["nome_fornecedor"])
                        norm_history = normalize(row.HISTORICO)
                        if norm_sup_name in norm_history:
                            found_supplier = True
                            supplier_name = norm_sup_name
                            data_handler = {
                                'supplier_name': supplier_name,
                                'invoice': extract_invoice(row.Index, data),
                                'date': parse_date(row.DATA),
                                'debit': str(row.DEBITO),
                                'credit': str(row.CREDITO),
                                'value': format_decimal(row.VALOR)
                            }
                            break
            
            branch_path = os.path.join(base_path, str(int(row.FILIAL)))
            try:
                os.makedirs(branch_path, exist_ok=True)
            except OSError as e:
                print(f"Error creating file for branch {row.FILIAL}: {e}")
                pbar.update(1)
                continue
                
            archive_file = os.path.join(branch_path, "archive.json")
            
            if os.path.exists(archive_file):
                with open(archive_file, "r", encoding="utf-8") as archive:
                    try:
                        archives_data = json.load(archive)
                        if not isinstance(archives_data, dict):
                            print(f"Invalid format for archive {archive_file}")
                            archives_data = {}
                    except json.JSONDecodeError as err:
                        print(f"Error loading {archive_file}: {err}")
                        archives_data = {}
            else:
                archives_data = {}

            if not found_supplier:
                if "NOT_FOUND" not in archives_data:
                    archives_data["NOT_FOUND"] = {}

                archives_data["NOT_FOUND"][f'history_{row.Index}'] = row.HISTORICO
                archives_data["NOT_FOUND"][f'value_{row.Index}'] = str(format_decimal(row.VALOR))
                archives_data["NOT_FOUND"][f'date_{row.Index}'] = str(parse_date(row.DATA) or row.DATA)
                
                try:
                    current_result = decimal.Decimal(archives_data["NOT_FOUND"].get('result', '0'))
                    new_value = format_decimal(row.VALOR)
                    archives_data["NOT_FOUND"]['result'] = str(current_result + new_value)
                except decimal.InvalidOperation:
                    print(f"Obtained value is invalid for NOT_FOUND: {row.VALOR}")
                    archives_data["NOT_FOUND"]['result'] = str(format_decimal(row.VALOR))

                with open(archive_file, "w", encoding="utf-8") as archive:
                    json.dump(archives_data, archive, indent=4, ensure_ascii=False)
                
                pbar.update(1)
                continue
            
            if data_handler['supplier_name'] not in archives_data:
                archives_data[data_handler['supplier_name']] = {
                    data_handler['invoice']: {
                        'value_1': str(data_handler['value']),
                        'result': str(data_handler['value']),
                        'date': str(data_handler['date']),
                        'debit': str(data_handler['debit']),
                        'credit': str(data_handler['credit'])
                    }
                }
            else:
                supplier_data = archives_data[data_handler['supplier_name']]
                if not isinstance(supplier_data, dict):
                    supplier_data = {}
                    archives_data[data_handler['supplier_name']] = supplier_data
                
                if data_handler['invoice'] not in supplier_data:
                    supplier_data[data_handler['invoice']] = {
                        'value_1': str(data_handler['value']),
                        'result': str(data_handler['value']),
                        'date': str(data_handler['date']),
                        'debit': str(data_handler['debit']),
                        'credit': str(data_handler['credit'])
                    }
                else:
                    invoice_data = supplier_data[data_handler['invoice']]
                    if not isinstance(invoice_data, dict):
                        invoice_data = {}
                        supplier_data[data_handler['invoice']] = invoice_data
                    
                    try:
                        value_keys = [int(k.split("_")[1]) for k in invoice_data.keys() 
                                     if isinstance(k, str) and k.startswith("value_")]
                        next_index = max(value_keys) + 1 if value_keys else 1
                        value_key = f"value_{next_index}"
                        invoice_data[value_key] = str(data_handler['value'])
                        
                        current_result = decimal.Decimal(invoice_data.get('result', '0'))
                        new_value = data_handler['value']
                        invoice_data['result'] = str(current_result + new_value)
                    except (ValueError, decimal.InvalidOperation) as e:
                        print(f"Error processing values from invoice {data_handler['invoice']}: {e}")
                        invoice_data['result'] = str(data_handler['value'])

            with open(archive_file, "w", encoding="utf-8") as archive:
                json.dump(archives_data, archive, indent=4, ensure_ascii=False)
            
            pbar.update(1)
        
        except Exception as e:
            print(f"Error processing line {row.Index}: {str(e)}")
            pbar.update(1)
            continue

print("\nReconciliation done with success!")

# Processamento de notas em aberto
open_invoices = {}
enterprise_folders = [os.path.join(base_path, enterprise_number) 
                     for enterprise_number in os.listdir(base_path) 
                     if os.path.isdir(os.path.join(base_path, enterprise_number))]

print(f"Processing {len(enterprise_folders)} enterprises...")

with tqdm(total=len(enterprise_folders), desc="Processing invoices", unit="enterprise", colour="GREEN",
          bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
    
    for enterprise_folder in enterprise_folders:
        try:
            enterprise_number = os.path.basename(enterprise_folder)
            archive_path = os.path.join(enterprise_folder, "archive.json")
            
            if os.path.exists(archive_path):
                with open(archive_path, "r", encoding="utf-8") as file:
                    try:
                        json_data = json.load(file)
                        if not isinstance(json_data, dict):
                            print(f"Invalid format in {archive_path}")
                            pbar.update(1)
                            continue
                    except json.JSONDecodeError as err:
                        print(f"Error loading {archive_path}: {err}")
                        pbar.update(1)
                        continue
                
                for supplier, invoices in json_data.items():
                    if not isinstance(invoices, dict):
                        print(f"Warning: Unexpected data format in {archive_path}")
                        continue
                    
                    for invoice, invoice_data in invoices.items():
                        try:
                            if isinstance(invoice_data, dict) and "result" in invoice_data:
                                result = invoice_data["result"]
                                if result != "0.00":
                                    if enterprise_number not in open_invoices:
                                        open_invoices[enterprise_number] = {}

                                    if supplier not in open_invoices[enterprise_number]:
                                        open_invoices[enterprise_number][supplier] = {}

                                    if invoice not in open_invoices[enterprise_number][supplier]:
                                        open_invoices[enterprise_number][supplier][invoice] = {}

                                    open_invoices[enterprise_number][supplier][invoice] = {
                                        'result': invoice_data.get('result'),
                                        'date': invoice_data.get('date', 'N/A'),
                                        'debit': invoice_data.get('debit', 'N/A'),
                                        'credit': invoice_data.get('credit', 'N/A')
                                    }
                        except Exception as e:
                            print(f"Error processing invoice {invoice} in {archive_path}: {e}")

            pbar.update(1)
        
        except Exception as e:
            print(f"Error processing enterprise {enterprise_folder}: {e}")
            pbar.update(1)
            continue

# Salvando notas em aberto
output_file = os.path.join(base_path, "open_invoices.json")
if open_invoices:
    try:
        with open(output_file, "w", encoding="utf-8") as o_i_archive:
            json.dump(open_invoices, o_i_archive, indent=4, ensure_ascii=False)
        print(f"Second step completed. Open invoices processed and saved to {output_file}.")
    except Exception as e:
        print(f"Error saving {output_file}: {e}")
        exit()
else:
    print("Second step completed and no open invoices were found. Code will end.")
    exit()

# Reconciliação com o banco de dados
if output_file:
    print("There are open invoices that must be reconciliated")
    
    while True:
        try:
            num_acc = int(input("Set the number of the account to reconciliate: "))
            break
        except ValueError:
            print("Please, insert a valid account number")

    connection = None
    try:
        connection = connect_database()
        cursor = connection.cursor()

        with open(output_file, 'r', encoding='utf-8') as o_file:
            try:
                invoices_data = json.load(o_file)
                if not isinstance(invoices_data, dict):
                    print("Invalid format of the open invoices archive")
                    exit()
            except json.JSONDecodeError as e:
                print(f"Error reading {output_file}: {e}")
                exit()

        conditionals = []
        num_to_invoice = {}
        total_invoices = sum(len(invoices) for suppliers in invoices_data.values() for invoices in suppliers.values())

        print(f"Preparing {total_invoices} invoices for the query...")
        with tqdm(total=total_invoices, desc="Processing invoices", unit="Invoice", colour="GREEN",
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
            
            i_counter = 1
            for ent_num, suppliers in invoices_data.items():
                if not isinstance(suppliers, dict):
                    print(f"Warning: Unexpected data format in {output_file}")
                    continue
                
                for supplier, invoices in suppliers.items():
                    if not isinstance(invoices, dict):
                        print(f"Warning: Unexpected data format for supplier {supplier}")
                        continue
                    
                    for invoice, invoice_data in invoices.items():
                        try:
                            i_date = parse_date(invoice_data.get('date'))
                            if not i_date:
                                print(f"Invalid date for invoice {invoice} from supplier {supplier}")
                                pbar.update(1)
                                continue
                            
                            conditionals.append(f"""\t\t\tWHEN lancto.chis_lan LIKE ('%' || '{supplier}' || '%')\n\t\t\t\tAND lancto.chis_lan LIKE ('%' || '{invoice}' || '%')\n\t\t\t\tAND lancto.data_lan >= DATEADD(MONTH, -6, '{i_date}')\n\t\t\t\tAND contas.codi_cta = {num_acc}\n\t\t\t\tTHEN {i_counter}""")
                            
                            num_to_invoice[i_counter] = {"supplier": supplier, "invoice": invoice}
                            i_counter += 1
                            pbar.update(1)
                        
                        except Exception as e:
                            print(f"Error processing invoice {invoice} from {supplier}: {str(e)}")
                            pbar.update(1)

        if not conditionals:
            print("No valid conditions found for the query.")
            exit()

        conditionals_str = "\n".join(conditionals)
        pre_cursor = queries.search_historic.replace("CASE ?", f"CASE\n{conditionals_str}")
        pre_cursor = pre_cursor.replace("contas.codi_cta = ?", f"contas.codi_cta = {num_acc}")

        # Salvando a consulta SQL para debug
        sql_debug_path = os.path.join(base_path, "pre_cursor.sql")
        try:
            with open(sql_debug_path, 'w', encoding='utf-8') as pre_cursor_file:
                pre_cursor_file.write(pre_cursor)
        except Exception as e:
            print(f"Error saving SQL query: {e}")

        print("Executing research. Please wait...")
        try:
            cursor.execute(pre_cursor)
            historic_data = cursor.fetchall()
        except Exception as e:
            print(f"Error executing SQL query: {e}")
            exit()
        finally:
            cursor.close()
            if connection:
                connection.close()

        try:
            os.remove(sql_debug_path)
        except Exception as e:
            print(f"Warning: It wasn't possible to remove {sql_debug_path}: {e}")

        # Processando resultados
        results = []
        if not historic_data:
            print("No result found at the query.")
        else:
            print(f"Processing {len(historic_data)} results...")
            with tqdm(total=len(historic_data), desc="Processing results", unit="Line", colour="GREEN",
                      bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as bar:
                
                for historic_row in historic_data:
                    try:
                        filial, data_min, data_max, total, numero = historic_row
                        mapping = num_to_invoice.get(numero, {"supplier": "Unknown", "invoice": "Unknown"})
                        
                        results.append({
                            "FILIAL": filial,
                            "SUPPLIER": mapping["supplier"],
                            "INVOICE": mapping["invoice"],
                            "DATA_MIN": parse_date(data_min),
                            "DATA_MAX": parse_date(data_max),
                            "TOTAL": float(format_decimal(total)),
                            "NUMERO": numero
                        })
                    except Exception as e:
                        print(f"Error processing line of result: {e}")
                    finally:
                        bar.update(1)

        # Salvando resultados
        json_file_path = os.path.join(base_path, "reconciliated_invoices.json")
        try:
            with open(json_file_path, 'w', encoding='utf-8') as json_file:
                json.dump(results, json_file, indent=4)
            print(f"Third step completed. Results saved to {json_file_path}.")
        except Exception as e:
            print(f"Error saving results: {e}")
            exit()

    except Exception as e:
        print(f"Error at the reconciliation with database: {e}")
        if connection:
            connection.close()
        exit()

# Atualização final dos arquivos
if json_file_path:
    try:
        with open(json_file_path, "r", encoding="utf-8") as jsonfile:
            json_file = json.load(jsonfile)
            if not isinstance(json_file, list):
                print("Invalid format of the reconciliated results archive")
                exit()
    except Exception as e:
        print(f"Error reading {json_file_path}: {e}")
        exit()

    print(f"Updating {len(json_file)} reconciliated items...")
    with tqdm(total=len(json_file), desc="Processing reconciliations", unit="Item", colour="GREEN",
              bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar:
        
        for item in json_file:
            try:
                e_num = str(item.get("FILIAL"))
                sup = str(item.get("SUPPLIER"))
                inv = str(item.get("INVOICE"))

                if not inv or not sup:
                    pbar.update(1)
                    continue

                en_path = os.path.join(base_path, e_num, 'archive.json')
                if not os.path.exists(en_path):
                    print(f"Archive not found: {en_path}")
                    pbar.update(1)
                    continue

                with open(en_path, "r", encoding="utf-8") as ef:
                    try:
                        en_file = json.load(ef)
                        if not isinstance(en_file, dict):
                            print(f"Invalid format in {en_path}")
                            pbar.update(1)
                            continue
                    except Exception as e:
                        print(f"Error reading {en_path}: {e}")
                        pbar.update(1)
                        continue

                if sup in en_file and inv in en_file.get(sup, {}):
                    en_file[sup][inv]["result"] = item.get("TOTAL")
                    en_file[sup][inv]["max_date"] = item.get("DATA_MAX")
                    en_file[sup][inv]["min_date"] = item.get("DATA_MIN")
                    
                    if "date" in en_file[sup][inv]:
                        del en_file[sup][inv]["date"]

                with open(en_path, "w", encoding="utf-8") as ef:
                    json.dump(en_file, ef, indent=4, ensure_ascii=False)

            except Exception as e:
                print(f"Error processing item {item.get('INVOICE')}: {e}")
            pbar.update(1)

    print(f"Final step completed. Results saved to {base_path}.")