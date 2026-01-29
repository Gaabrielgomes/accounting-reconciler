import pandas as pd
import os
import json
from connection import connect_database
import queries as queries
from tkinter import messagebox

connection = connect_database()
cursor = connection.cursor()

try:
    cursor.execute(queries.enterprises_suppliers)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    joined_tables = pd.DataFrame.from_records(rows, columns=columns)

except Exception as error:
    messagebox.showinfo("Erro", f"{str(error)}")
finally:
    cursor.close()

json_dir = "../json"
os.makedirs(json_dir, exist_ok=True)

for row in joined_tables.itertuples(index=False):
    json_path = os.path.join(json_dir, f"{str(row.codigo_empresa)}.json")

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                data = {"enterprise_info": {}}
    else:
        data = {
            "enterprise_info": {
                "apelido_empresa": str(row.apelido_empresa),
                "razao_empresa": str(row.razao_empresa),
                "cnpj_cpf_empresa": str(row.cnpj_cpf_empresa)
            }
        }

    data[str(row.codigo_fornecedor)] = {
        "nome_fornecedor": str(row.nome_fornecedor),
        "cnpj_cpf_fornecedor": str(row.cnpj_cpf_fornecedor)
    }

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
