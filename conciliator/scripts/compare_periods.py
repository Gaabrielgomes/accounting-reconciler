import os
import pandas as pd
import tqdm


# Load current reconciliation data
c_r_name = str(input("Insert current reconciliation's archive name + type of archive: "))
c_r_path = os.path.join("..\\export", c_r_name)

if not os.path.exists(c_r_path):
    print(f"Path '{c_r_path}' not found.")
    exit()

current_reconciliation = pd.DataFrame(pd.read_excel(c_r_path))

c_r_list = []
with tqdm.tqdm(total=len(current_reconciliation), colour="GREEN") as pbar:
    for index, row in current_reconciliation.iterrows():
        c_r_list.append((row['FILIAL'], row['IDENTIFICACAO'], row['NOTA'], row['DATA_MAX'], row['DATA_MIN'], row['DEBITO'], row['CREDITO'], row['RESULTADO']))
        pbar.update(1)

p_r_name = str(input("Insert past reconciliation's archive name + type of archive: "))
p_r_path = os.path.join("..\\export", p_r_name)

if not os.path.exists(p_r_path):
    print(f"Path '{p_r_path}' not found.")
    exit()

past_reconciliation = pd.DataFrame(pd.read_excel(p_r_path))

p_r_list = []
with tqdm.tqdm(total=len(past_reconciliation), colour="GREEN") as pbar:
    for index, row in past_reconciliation.iterrows():
        if row.get('RESULTADO')!= 0:
            p_r_list.append((row['FILIAL'], row['IDENTIFICACAO'] , row['NOTA'], row['RESULTADO']))
        pbar.update(1)

# Merge current and past reconciliation data
merged_data = []
with tqdm.tqdm(total=len(c_r_list), colour="GREEN") as pbar:
    for c_r in c_r_list:
        pbar.update(1)
        if c_r[7] != 0:
            for p_r in p_r_list:
                if c_r[0] == p_r[0] and c_r[1] == p_r[1] and c_r[2] == p_r[2]:
                    sum = c_r[7] + p_r[3]
                    merged_data.append((c_r[0], c_r[1], c_r[2], c_r[3], c_r[4], c_r[5], c_r[6], sum))
                    continue
            else:
                merged_data.append((c_r[0], c_r[1], c_r[2], c_r[3], c_r[4], c_r[5], c_r[6], c_r[7]))
        else:
            merged_data.append((c_r[0], c_r[1], c_r[2], c_r[3], c_r[4], c_r[5], c_r[6], c_r[7]))
            continue

# Save the merged data to a new Excel file
pathname = input("Give to the new archive a name: ")
export_path = os.path.join("..\\export", f"{pathname}.xlsx")
os.makedirs(os.path.dirname(export_path), exist_ok=True)

with pd.ExcelWriter(export_path, engine="openpyxl") as writer:
    merged_data_df = pd.DataFrame(merged_data, columns=['FILIAL', 'IDENTIFICACAO', 'NOTA', 'DATA_MAX', 'DATA_MIN', 'DEBITO', 'CREDITO', 'RESULTADO'])
    merged_data_df.to_excel(writer, index=False, sheet_name="Dados obtidos")

print(f"Merged data saved successfully to {export_path}")