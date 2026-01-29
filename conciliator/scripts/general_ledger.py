import pandas as pd
import os
import tkinter as tk
from tkinter import messagebox, filedialog
from connection import connect_database
import queries as queries
from openpyxl import Workbook

# Conectando ao banco de dados
connection = connect_database()

# Função para encerrar o programa
def close_application():
    action_block.quit()
    action_block.destroy()
    exit()

# Escolher o caminho do arquivo para salvamento
def choose_file_path():
    tk.Tk().withdraw()  # Oculta a janela principal do tkinter
    file_path = filedialog.askdirectory(title="Escolha o local de salvamento do arquivo")
    return file_path

# Função para realizar a consulta com os parâmetros fornecidos
def execute_query():
    try:
        start_date = input_start.get()
        end_date = input_end.get()
        client_identifier = input_client.get()

        if ',' not in client_identifier and not client_identifier.isnumeric():
            client_identifier = '%' + client_identifier + '%'
            client_cursor = connection.cursor()
            try:
                client_cursor.execute(queries.get_client, (client_identifier))
                results = client_cursor.fetchall()
                result_columns = [col[0] for col in client_cursor.description]
                obtained_codes = pd.DataFrame.from_records(results, columns=result_columns)
                clients = [f'{code}' for code in list(obtained_codes['codi_emp'])]
                add_variables = ', '.join('?' for code in clients)
            except Exception as search_error:
                messagebox.showinfo("Erro", f"{str(search_error)}")
            finally:
                client_cursor.close()
        else:
            clients = input_client.get()

        account_number = input_account_number.get()  # Obtendo o número da conta (opcional)

        # Verifica se a conta está preenchida
        if account_number == "":
            account_type = str(input_account_type.get()) + '%'  # Obtendo o tipo de conta
            parameters = (*clients, start_date, end_date, account_type, *clients, start_date, end_date, account_type)
            query = queries.general_ledger.replace("IN (?)", f"IN ({add_variables})")
        else:
            parameters = (*clients, start_date, end_date, account_number, *clients, start_date, end_date, account_number)
            query = queries.basic_ledger.replace("IN (?)", f"IN ({add_variables})")

        # Consulta de saldo
        balance_cursor = connection.cursor()

        try:
            if account_number == "":
                balance_query = queries.get_balance_by_account_type.replace("IN (?)", f"IN ({add_variables})")
                balance_cursor.execute(balance_query, (*clients, start_date, account_type, *clients, start_date, account_type))
            else:
                balance_query = queries.get_balance.replace("IN (?)", f"IN ({add_variables})")
                balance_cursor.execute(balance_query, (*clients, start_date, account_number, *clients, start_date, account_number))

            balance_row = balance_cursor.fetchone()
            if balance_row:
                balance = balance_row[0]
                if balance is None:
                    balance = 0
                    print("Não foi possível obter o saldo anterior ao período ou o saldo anterior é zero.")

        except Exception as error:
            print(str(error))
        finally:
            balance_cursor.close()

        # Consulta ao Banco
        cursor = connection.cursor()
        cursor.execute(query, parameters)

        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        data_frame = pd.DataFrame.from_records(rows, columns=columns)

        if not data_frame.empty:
            debit = data_frame["VALOR"][data_frame["VALOR"] > 0].sum()
            credit = data_frame["VALOR"][data_frame["VALOR"] < 0].sum()
            current_balance = balance - (debit - credit)
            print(data_frame)
            print(f'SALDO ANTERIOR: {balance}\nDÉBITO: {debit}\nCRÉDITO: {credit}\nSALDO ATUAL: {current_balance}')

            # Exporta os dados se necessário
            export_data(data_frame, debit, credit, balance, current_balance)
            return data_frame
        else:
            messagebox.showinfo("Info", "Nenhum dado encontrado.")

    except Exception as query_error:
        print(str(query_error))
        messagebox.showerror("Erro", f"Erro ao executar a consulta: {str(query_error)}")
        return None

# Função para exportar os dados
def export_data(data_frame, debit, credit, balance, current_balance):
    export = messagebox.askyesno("Exportar", "Consulta efetuada com sucesso. Deseja exportar/salvar os dados?")
    if export:
        # Janela para escolher o formato do arquivo e o nome do arquivo
        export_window = tk.Toplevel(action_block)
        export_window.title("Opções de Exportação")

        # Seleção do formato do arquivo
        tk.Label(export_window, text="Formato do arquivo:").grid(row=0, column=0, padx=10, pady=5)
        file_format_var = tk.StringVar(value="Selecionar")
        tk.OptionMenu(export_window, file_format_var, "excel", "csv").grid(row=0, column=1, padx=10, pady=5)

        # Entrada para o nome do arquivo
        tk.Label(export_window, text="Nome do arquivo:").grid(row=1, column=0, padx=10, pady=5)
        input_file_name = tk.Entry(export_window)
        input_file_name.grid(row=1, column=1, padx=10, pady=5)

        # Função interna para salvar o arquivo
        def save_file():
            file_format = file_format_var.get()
            file_name = input_file_name.get()

            if file_name == "":
                messagebox.showerror("Erro", "Nome do arquivo não pode ser vazio.")
                return

            export_path = choose_file_path()
            if file_format == "excel":
                file_name += ".xlsx"
                complete_export_path = os.path.join(export_path, file_name)

                new_workbook = Workbook()
                sheet = new_workbook.active

                sheet.append(data_frame.columns.tolist())
                for row in data_frame.itertuples(index=False, name=None):
                    sheet.append(row)

                sheet['G1'] = 'SALDO ANTERIOR'
                sheet['G2'] = 'DÉBITO'
                sheet['G3'] = 'CRÉDITO'
                sheet['G4'] = 'SALDO ATUAL'
                sheet['H1'] = balance
                sheet['H2'] = debit
                sheet['H3'] = credit
                sheet['H4'] = current_balance

                new_workbook.save(complete_export_path)
                messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n'{complete_export_path}'")
                export_window.destroy()

            elif file_format == "csv":
                file_name += ".csv"
                complete_export_path = os.path.join(export_path, file_name)
                data_frame.to_csv(complete_export_path, index=False)
                messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n'{complete_export_path}'")
                export_window.destroy()

            else:
                messagebox.showerror("Erro", "Formato inválido. Escolha 'excel' ou 'csv'.")

        # Botão para confirmar a exportação
        save_button = tk.Button(export_window, text="Salvar", command=save_file)
        save_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)
    else:
        messagebox.showinfo("Cancelado", "Exportação cancelada.")

# Função para abrir a janela de instruções
def show_instructions():
    instructions_window = tk.Toplevel(action_block)
    instructions_window.title("Instruções de Uso")
    instructions_text = tk.Text(instructions_window, wrap="word")
    instructions_text.insert(tk.END, "1. Digite a data de início e de fim, inserindo também as barras '/'.\n\n")
    instructions_text.insert(tk.END, "2. Digite o nome do cliente ou os códigos de cada uma das empresas que deseja analisar.\n\n")
    instructions_text.insert(tk.END, "3. Digite o número da conta específica da qual o razão deve ser extraído.\n\n")
    instructions_text.insert(tk.END, "4. Se desejar fazer uma extração por tipo de conta tais como ativo, passivo e resultado, deixar o número específico de conta em branco e selecionar qual tipo de conta na caixa de seleção.\n\n")
    instructions_text.insert(tk.END, "5. Ao finalizar a consulta, você pode exportar os dados para um arquivo Excel ou CSV. Basta selecionar o tipo de arquivo, escrever o nome que o arquivo terá e o local de salvamento.\n\n")
    instructions_text.config(state=tk.DISABLED)
    instructions_text.pack(padx=10, pady=10)


# Criação da interface gráfica
if connection:
    action_block = tk.Tk()
    action_block.title("Consulta de Razão")

    # Para encerrar
    action_block.protocol("WM_DELETE_WINDOW", close_application)

    # Entradas para as datas
    tk.Label(action_block, text="Data inicial (DD/MM/AAAA):").grid(row=0, column=0, padx=10, pady=5)
    input_start = tk.Entry(action_block)
    input_start.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(action_block, text="Data final (DD/MM/AAAA):").grid(row=1, column=0, padx=10, pady=5)
    input_end = tk.Entry(action_block)
    input_end.grid(row=1, column=1, padx=10, pady=5)

    # Entrada para o nome ou código do cliente
    tk.Label(action_block, text="Cliente (código ou nome/razão social):").grid(row=3, column=0, padx=10, pady=5)
    input_client = tk.Entry(action_block)
    input_client.grid(row=3, column=1, padx=10, pady=5)

    # Entrada para o número da conta
    tk.Label(action_block, text="Número da conta:").grid(row=4, column=0, padx=10, pady=5)
    input_account_number = tk.Entry(action_block)
    input_account_number.grid(row=4, column=1, padx=10, pady=5)

    # Seleção do tipo de conta
    tk.Label(action_block, text="Tipo de conta [1(ATIVO)/2(PASSIVO)/3(RESULTADO)]:").grid(row=5, column=0, padx=10, pady=5)
    input_account_type = tk.IntVar(value="Selecionar")
    account_type_menu = tk.OptionMenu(action_block, input_account_type, "1", "2", "3")
    account_type_menu.grid(row=5, column=1, padx=10, pady=5)

    # Botão para realizar a consulta
    query_button = tk.Button(action_block, text="Consultar", command=execute_query)
    query_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

    # Botão para abrir as instruções de uso
    instructions_button = tk.Button(action_block, text="Instruções")
    instructions_button.grid(row=6, column=1, padx=10, pady=10)

    # Botão para abrir as instruções de uso
    instructions_button = tk.Button(action_block, text="Instruções", command=show_instructions)
    instructions_button.grid(row=6, column=1, padx=10, pady=10)

    action_block.mainloop()
else:
    messagebox.showinfo("Erro", "Falha ao conectar ao banco de dados.")
