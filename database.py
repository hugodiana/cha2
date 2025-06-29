import streamlit as st
import pandas as pd
import gspread 
import json 

# <<< LINHA DE DEBUG PARA O CAMINHO DO MÓDULO GSPREAD >>>
# Esta linha vai mostrar o caminho de onde o módulo gspread está sendo carregado
st.sidebar.write(f"DEBUG Gspread Module Path: {gspread.__file__}")
# <<< FIM DA LINHA DE DEBUG >>>

# Função para conectar à planilha
def connect_to_sheet():
    """
    Conecta ao Google Sheet 'ChaDeBebe_DB' autenticando diretamente com gspread
    usando as credenciais de st.secrets.
    """
    try:
        # Acesso defensivo às credenciais de st.secrets
        connections = st.secrets.get("connections")
        if not connections:
            raise KeyError("Seção 'connections' ausente em st.secrets.")
        
        gsheets_creds = connections.get("gsheets")
        if not gsheets_creds:
            raise KeyError("Seção 'connections.gsheets' ausente em st.secrets.")
        
        creds = {
            "type": gsheets_creds.get("type"),
            "project_id": gsheets_creds.get("project_id"),
            "private_key_id": gsheets_creds.get("private_key_id"),
            "private_key": gsheets_creds.get("private_key"),
            "client_email": gsheets_creds.get("client_email"),
            "client_id": gsheets_creds.get("client_id"),
            "auth_uri": gsheets_creds.get("auth_uri"),
            "token_uri": gsheets_creds.get("token_uri"),
            "auth_provider_x509_cert_url": gsheets_creds.get("auth_provider_x509_cert_url"),
            "client_x509_cert_url": gsheets_creds.get("client_x509_cert_url")
        }
        
        # Garante que a private_key não seja None antes de usar
        if not creds.get("private_key"):
            raise ValueError("private_key não encontrada ou está vazia nas credenciais.")

        gc = gspread.service_account_from_dict(creds)
        
        # <<< LINHAS DE DEBUG AQUI (dentro da função) >>>
        # Estas linhas mostram o tipo do objeto 'gc' e se ele tem o método 'open'
        st.sidebar.write(f"DEBUG Gspread: Tipo do objeto 'gc': {type(gc)}")
        st.sidebar.write(f"DEBUG Gspread: 'gc' tem 'open'? {'open' in dir(gc)}")
        # <<< FIM DAS LINHAS DE DEBUG >>>

        # <<< A CORREÇÃO CRUCIAL AQUI: open_by_name foi alterado para open >>>
        sheet = gc.open("ChaDeBebe_DB") 
        return sheet
    except (KeyError, ValueError) as e:
        st.error(f"Erro de configuração no .streamlit/secrets.toml: {e}")
        st.info("Verifique se a seção `[connections.gsheets]` e todas as chaves dentro dela estão corretas e completas.")
        st.stop()
    except Exception as e:
        st.error(f"Erro ao conectar ou abrir a planilha: {e}")
        st.info("Verifique se o nome da planilha 'ChaDeBebe_DB' está exato e se as credenciais "
                "em .streamlit/secrets.toml (seção [connections.gsheets]) estão corretas.")
        st.stop() 

# --- Funções para gerenciar usuários (aba 'usuarios') ---
def fetch_all_users(sheet):
    """
    Busca todos os usuários da aba 'usuarios'.
    Retorna um DataFrame pandas.
    """
    try:
        worksheet = sheet.worksheet("usuarios")
        data = worksheet.get_all_records()
        if not data:
            return pd.DataFrame(columns=['username', 'email', 'name', 'password'])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao buscar usuários da planilha: {e}")
        return pd.DataFrame(columns=['username', 'email', 'name', 'password'])

def update_users(sheet, users_df):
    """
    Atualiza todos os usuários na aba 'usuarios' com o DataFrame fornecido.
    """
    try:
        worksheet = sheet.worksheet("usuarios")
        worksheet.clear()
        worksheet.update([users_df.columns.values.tolist()] + users_df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao atualizar usuários na planilha: {e}")

# --- Funções para gerenciar dados do evento (aba 'eventos') ---
def get_evento_atual(sheet, username):
    """
    Busca as informações do evento para o usuário logado.
    """
    try:
        worksheet = sheet.worksheet("eventos")
        data = worksheet.get_all_records()
        eventos_df = pd.DataFrame(data)
        if not eventos_df.empty and username in eventos_df['username'].values:
            return eventos_df[eventos_df['username'] == username].iloc[0].to_dict()
        return None 
    except Exception as e:
        st.error(f"Erro ao buscar informações do evento: {e}")
        return None

def set_evento_atual(sheet, username, event_data):
    """
    Define ou atualiza as informações do evento para o usuário logado.
    """
    try:
        worksheet = sheet.worksheet("eventos")
        all_events_data = worksheet.get_all_records()
        eventos_df = pd.DataFrame(all_events_data)

        eventos_df = eventos_df[eventos_df['username'] != username]

        new_event_df = pd.DataFrame([{"username": username, **event_data}])
        
        if all_events_data:
            final_df = pd.concat([eventos_df, new_event_df], ignore_index=True)
            final_df = final_df[worksheet.row_values(1)] 
        else:
            final_df = new_event_df
            
        worksheet.clear()
        worksheet.update([final_df.columns.values.tolist()] + final_df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao salvar informações do evento: {e}")

# --- Funções para gerenciar Convidados (aba 'convidados') ---
def get_convidados(sheet, username):
    try:
        worksheet = sheet.worksheet("convidados")
        data = worksheet.get_all_records()
        convidados_df = pd.DataFrame(data)
        if not convidados_df.empty and username in convidados_df['username'].values:
            return eval(convidados_df[convidados_df['username'] == username]['lista_convidados'].iloc[0])
        return []
    except Exception as e:
        st.error(f"Erro ao buscar convidados: {e}")
        return []

def set_convidados(sheet, username, convidados_list):
    try:
        worksheet = sheet.worksheet("convidados")
        all_convidados = worksheet.get_all_records()
        convidados_df = pd.DataFrame(all_convidados)

        if username in convidados_df['username'].values:
            convidados_df.loc[convidados_df['username'] == username, 'lista_convidados'] = str(convidados_list)
        else:
            new_row = pd.DataFrame([{'username': username, 'lista_convidados': str(convidados_list)}])
            convidados_df = pd.concat([convidados_df, new_row], ignore_index=True)
        
        worksheet.clear()
        worksheet.update([convidados_df.columns.values.tolist()] + convidados_df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao salvar convidados: {e}")


# --- Funções para Checklist (aba 'checklist') ---
def get_checklist(sheet, username):
    try:
        worksheet = sheet.worksheet("checklist")
        data = worksheet.get_all_records()
        checklist_df = pd.DataFrame(data)
        if not checklist_df.empty and username in checklist_df['username'].values:
            row = checklist_df[checklist_df['username'] == username].iloc[0]
            tarefas = eval(row['tarefas'])
            status = eval(row['status'])
            return tarefas, status
        return [], []
    except Exception as e:
        st.error(f"Erro ao buscar checklist: {e}")
        return [], []

def set_checklist(sheet, username, tarefas, status):
    try:
        worksheet = sheet.worksheet("checklist")
        all_checklist = worksheet.get_all_records()
        checklist_df = pd.DataFrame(all_checklist)

        if username in checklist_df['username'].values:
            checklist_df.loc[checklist_df['username'] == username, 'tarefas'] = str(tarefas)
            checklist_df.loc[checklist_df['username'] == username, 'status'] = str(status)
        else:
            new_row = pd.DataFrame([{'username': username, 'tarefas': str(tarefas), 'status': str(status)}])
            checklist_df = pd.concat([checklist_df, new_row], ignore_index=True)
        
        worksheet.clear()
        worksheet.update([checklist_df.columns.values.tolist()] + checklist_df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao salvar checklist: {e}")

# --- Funções para Gastos (aba 'gastos') ---
def get_gastos(sheet, username):
    try:
        worksheet = sheet.worksheet("gastos")
        data = worksheet.get_all_records()
        gastos_df = pd.DataFrame(data)
        if not gastos_df.empty and username in gastos_df['username'].values:
            user_gastos_str = gastos_df[gastos_df['username'] == username]['gastos_json'].iloc[0]
            if user_gastos_str:
                return pd.read_json(user_gastos_str)
        return pd.DataFrame(columns=['descricao', 'valor', 'forma_pagamento'])
    except Exception as e:
        st.error(f"Erro ao buscar gastos: {e}")
        return pd.DataFrame(columns=['descricao', 'valor', 'forma_pagamento'])

def set_gastos(sheet, username, gastos_df):
    try:
        worksheet = sheet.worksheet("gastos")
        all_gastos = worksheet.get_all_records()
        main_gastos_df = pd.DataFrame(all_gastos)

        gastos_json_str = gastos_df.to_json(orient="records")

        if username in main_gastos_df['username'].values:
            main_gastos_df.loc[main_gastos_df['username'] == username, 'gastos_json'] = gastos_json_str
        else:
            new_row = pd.DataFrame([{'username': username, 'gastos_json': gastos_json_str}])
            main_gastos_df = pd.concat([main_gastos_df, new_row], ignore_index=True)
        
        worksheet.clear()
        worksheet.update([main_gastos_df.columns.values.tolist()] + main_gastos_df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao salvar gastos: {e}")

# --- Função para Orçamento (aba 'orcamento') ---
def get_orcamento(sheet, username):
    try:
        worksheet = sheet.worksheet("orcamento")
        data = worksheet.get_all_records()
        orcamento_df = pd.DataFrame(data)
        if not orcamento_df.empty and username in orcamento_df['username'].values:
            return float(orcamento_df[orcamento_df['username'] == username]['valor_orcamento'].iloc[0])
        return 0.0
    except Exception as e:
        st.error(f"Erro ao buscar orçamento: {e}")
        return 0.0

def set_orcamento(sheet, username, valor_orcamento):
    try:
        worksheet = sheet.worksheet("orcamento")
        all_orcamento = worksheet.get_all_records()
        orcamento_df = pd.DataFrame(all_orcamento)

        if username in orcamento_df['username'].values:
            orcamento_df.loc[orcamento_df['username'] == username, 'valor_orcamento'] = valor_orcamento
        else:
            new_row = pd.DataFrame([{'username': username, 'valor_orcamento': valor_orcamento}])
            orcamento_df = pd.concat([orcamento_df, new_row], ignore_index=True)
        
        worksheet.clear()
        worksheet.update([orcamento_df.columns.values.tolist()] + orcamento_df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao salvar orçamento: {e}")

# --- Funções para Sugestões (aba 'sugestoes') ---
def get_sugestoes(sheet, username):
    try:
        worksheet = sheet.worksheet("sugestoes")
        data = worksheet.get_all_records()
        sugestoes_df = pd.DataFrame(data)
        if not sugestoes_df.empty and username in sugestoes_df['username'].values:
            user_sugestoes_str = sugestoes_df[sugestoes_df['username'] == username]['sugestoes_json'].iloc[0]
            if user_sugestoes_str:
                return pd.read_json(user_sugestoes_str)
        return pd.DataFrame(columns=['item', 'detalhes'])
    except Exception as e:
        st.error(f"Erro ao buscar sugestões: {e}")
        return pd.DataFrame(columns=['item', 'detalhes'])

def set_sugestoes(sheet, username, sugestoes_df):
    try:
        worksheet = sheet.worksheet("sugestoes")
        all_sugestoes = worksheet.get_all_records()
        main_sugestoes_df = pd.DataFrame(all_sugestoes)

        sugestoes_json_str = sugestoes_df.to_json(orient="records")

        if username in main_sugestoes_df['username'].values:
            main_sugestoes_df.loc[main_sugestoes_df['username'] == username, 'sugestoes_json'] = sugestoes_json_str
        else:
            new_row = pd.DataFrame([{'username': username, 'sugestoes_json': sugestoes_json_str}])
            main_sugestoes_df = pd.concat([main_sugestoes_df, new_row], ignore_index=True)
        
        worksheet.clear()
        worksheet.update([main_sugestoes_df.columns.values.tolist()] + main_sugestoes_df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao salvar sugestões: {e}")

# --- Funções para Brincadeiras (aba 'brincadeiras') ---
def get_brincadeiras(sheet, username):
    try:
        worksheet = sheet.worksheet("brincadeiras")
        data = worksheet.get_all_records()
        brincadeiras_df = pd.DataFrame(data)
        if not brincadeiras_df.empty and username in brincadeiras_df['username'].values:
            user_brincadeiras_str = brincadeiras_df[brincadeiras_df['username'] == username]['brincadeiras_json'].iloc[0]
            if user_brincadeiras_str:
                return pd.read_json(user_brincadeiras_str)
        return pd.DataFrame(columns=['nome', 'regras'])
    except Exception as e:
        st.error(f"Erro ao buscar brincadeiras: {e}")
        return pd.DataFrame(columns=['nome', 'regras'])

def set_brincadeiras(sheet, username, brincadeiras_df):
    try:
        worksheet = sheet.worksheet("brincadeiras")
        all_brincadeiras = worksheet.get_all_records()
        main_brincadeiras_df = pd.DataFrame(all_brincadeiras)

        brincadeiras_json_str = brincadeiras_df.to_json(orient="records")

        if username in main_brincadeiras_df['username'].values:
            main_brincadeiras_df.loc[main_brincadeiras_df['username'] == username, 'brincadeiras_json'] = brincadeiras_json_str
        else:
            new_row = pd.DataFrame([{'username': username, 'brincadeiras_json': brincadeiras_json_str}])
            main_brincadeiras_df = pd.concat([main_brincadeiras_df, new_row], ignore_index=True)
        
        worksheet.clear()
        worksheet.update([main_brincadeiras_df.columns.values.tolist()] + main_brincadeiras_df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao salvar brincadeiras: {e}")

# --- Funções para Presentes (aba 'presentes') ---
def get_presentes(sheet, username):
    try:
        worksheet = sheet.worksheet("presentes")
        data = worksheet.get_all_records()
        presentes_df = pd.DataFrame(data)
        if not presentes_df.empty and username in presentes_df['username'].values:
            user_presentes_str = presentes_df[presentes_df['username'] == username]['presentes_json'].iloc[0]
            if user_presentes_str:
                return pd.read_json(user_presentes_str)
        return pd.DataFrame(columns=['convidado', 'presente', 'agradecimento_enviado'])
    except Exception as e:
        st.error(f"Erro ao buscar presentes: {e}")
        return pd.DataFrame(columns=['convidado', 'presente', 'agradecimento_enviado'])

def set_presentes(sheet, username, presentes_df):
    try:
        worksheet = sheet.worksheet("presentes")
        all_presentes = worksheet.get_all_records()
        main_presentes_df = pd.DataFrame(all_presentes)

        presentes_json_str = presentes_df.to_json(orient="records")

        if username in main_presentes_df['username'].values:
            main_presentes_df.loc[main_presentes_df['username'] == username, 'presentes_json'] = presentes_json_str
        else:
            new_row = pd.DataFrame([{'username': username, 'presentes_json': presentes_json_str}])
            main_presentes_df = pd.concat([main_presentes_df, new_row], ignore_index=True)
        
        worksheet.clear()
        worksheet.update([main_presentes_df.columns.values.tolist()] + main_presentes_df.values.tolist())
    except Exception as e:
        st.error(f"Erro ao salvar presentes: {e}")

# --- Função para resetar todos os dados de um usuário (em todas as abas) ---
def reset_all_data_for_user(sheet, username):
    try:
        abas_para_resetar = ["eventos", "convidados", "checklist", "gastos", 
                             "orcamento", "sugestoes", "brincadeiras", "presentes"]

        for aba_name in abas_para_resetar:
            worksheet = sheet.worksheet(aba_name)
            all_data = worksheet.get_all_records()
            df = pd.DataFrame(all_data)

            df_filtered = df[df['username'] != username]

            worksheet.clear()
            if not df_filtered.empty:
                worksheet.update([df_filtered.columns.values.tolist()] + df_filtered.values.tolist())
            else:
                worksheet.update([df.columns.values.tolist()]) 
        
        st.success(f"Todos os dados para o usuário '{username}' foram resetados com sucesso.")

    except Exception as e:
        st.error(f"Erro ao resetar dados do usuário: {e}")