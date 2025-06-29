import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import streamlit as st

# Nome da planilha no Google Sheets
SHEET_NAME = 'ChaDeBebe_DB'

def connect_to_sheet():
    try:
        creds_dict = st.secrets["connections"]["gsheets"]

        # Corrige a formatação da chave privada
        private_key = creds_dict["private_key"].replace("\\n", "\n")

        credentials_info = {
            "type": creds_dict["type"],
            "project_id": creds_dict["project_id"],
            "private_key_id": creds_dict["private_key_id"],
            "private_key": private_key,
            "client_email": creds_dict["client_email"],
            "client_id": creds_dict["client_id"],
            "auth_uri": creds_dict["auth_uri"],
            "token_uri": creds_dict["token_uri"],
            "auth_provider_x509_cert_url": creds_dict["auth_provider_x509_cert_url"],
            "client_x509_cert_url": creds_dict["client_x509_cert_url"]
        }

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SHEET_NAME)
        worksheet = spreadsheet.get_worksheet(0)  # seleciona a primeira aba
        return worksheet

    except Exception as e:
        st.error(f"Erro ao conectar à planilha: {e}")
        return None


def fetch_all_users(worksheet):
    try:
        records = worksheet.get_all_records()
        if not records:
            return pd.DataFrame(columns=['username', 'email', 'name', 'password'])
        df = pd.DataFrame(records)
        for col in ['username', 'email', 'name', 'password']:
            if col not in df.columns:
                df[col] = ""
        return df[['username', 'email', 'name', 'password']]
    except Exception as e:
        st.error(f"Erro ao buscar usuários: {e}")
        return pd.DataFrame(columns=['username', 'email', 'name', 'password'])


def update_users(worksheet, users_df):
    try:
        users_df = users_df.fillna("")
        worksheet.clear()
        worksheet.update([users_df.columns.values.tolist()] + users_df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar usuários: {e}")
        return False


def get_evento_atual(worksheet, username):
    try:
        records = worksheet.get_all_records()
        if not records:
            return {}
        df = pd.DataFrame(records)
        if 'username' not in df.columns:
            return {}
        user_evento = df[df['username'] == username]
        if user_evento.empty:
            return {}
        row = user_evento.iloc[0]
        return {
            "nome_bebe": row.get("nome_bebe", ""),
            "sexo_bebe": row.get("sexo_bebe", ""),
            "data_cha": row.get("data_cha", ""),
        }
    except Exception as e:
        st.error(f"Erro ao buscar evento: {e}")
        return {}


def set_evento_atual(worksheet, username, evento_data):
    try:
        records = worksheet.get_all_records()
        if not records:
            df = pd.DataFrame(columns=["username","nome_bebe","sexo_bebe","data_cha","email","name","password"])
        else:
            df = pd.DataFrame(records)

        if 'username' not in df.columns:
            df = pd.DataFrame(columns=["username","nome_bebe","sexo_bebe","data_cha","email","name","password"])

        idx = df.index[df['username'] == username].tolist()

        if not idx:
            nova_linha = {
                "username": username,
                "nome_bebe": evento_data.get("nome_bebe", ""),
                "sexo_bebe": evento_data.get("sexo_bebe", ""),
                "data_cha": evento_data.get("data_cha", ""),
                "email": "",
                "name": "",
                "password": "",
            }
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            i = idx[0]
            df.at[i, "nome_bebe"] = evento_data.get("nome_bebe", "")
            df.at[i, "sexo_bebe"] = evento_data.get("sexo_bebe", "")
            df.at[i, "data_cha"] = evento_data.get("data_cha", "")

        df = df.fillna("")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Erro ao salvar evento: {e}")
        return False


def get_convidados(worksheet, username):
    try:
        records = worksheet.get_all_records()
        if not records:
            return []
        df = pd.DataFrame(records)
        if 'username' not in df.columns or 'convidados' not in df.columns:
            return []
        convidados_str = df.loc[df['username'] == username, 'convidados'].values
        if convidados_str.size == 0 or not convidados_str[0]:
            return []
        return convidados_str[0].split(',')
    except Exception as e:
        st.error(f"Erro ao obter convidados: {e}")
        return []


def set_convidados(worksheet, username, convidados_list):
    try:
        records = worksheet.get_all_records()
        if not records:
            df = pd.DataFrame(columns=["username", "convidados"])
        else:
            df = pd.DataFrame(records)

        if 'username' not in df.columns:
            df['username'] = ""
        if 'convidados' not in df.columns:
            df['convidados'] = ""

        idx = df.index[df['username'] == username].tolist()
        convidados_str = ",".join(convidados_list)
        if not idx:
            nova_linha = {"username": username, "convidados": convidados_str}
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            i = idx[0]
            df.at[i, "convidados"] = convidados_str
        df = df.fillna("")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Erro ao salvar convidados: {e}")
        return False


def get_checklist(worksheet, username):
    try:
        records = worksheet.get_all_records()
        if not records:
            return [], []
        df = pd.DataFrame(records)
        if 'username' not in df.columns or 'checklist_tarefas' not in df.columns or 'checklist_status' not in df.columns:
            return [], []
        tarefas_str = df.loc[df['username'] == username, 'checklist_tarefas'].values
        status_str = df.loc[df['username'] == username, 'checklist_status'].values
        tarefas = tarefas_str[0].split(';') if tarefas_str.size > 0 and tarefas_str[0] else []
        status = list(map(int, status_str[0].split(';'))) if status_str.size > 0 and status_str[0] else []
        return tarefas, status
    except Exception as e:
        st.error(f"Erro ao obter checklist: {e}")
        return [], []


def set_checklist(worksheet, username, tarefas, status):
    try:
        records = worksheet.get_all_records()
        if not records:
            df = pd.DataFrame(columns=["username", "checklist_tarefas", "checklist_status"])
        else:
            df = pd.DataFrame(records)

        if 'username' not in df.columns:
            df['username'] = ""
        if 'checklist_tarefas' not in df.columns:
            df['checklist_tarefas'] = ""
        if 'checklist_status' not in df.columns:
            df['checklist_status'] = ""

        tarefas_str = ';'.join(tarefas)
        status_str = ';'.join(map(str, status))
        idx = df.index[df['username'] == username].tolist()
        if not idx:
            nova_linha = {"username": username, "checklist_tarefas": tarefas_str, "checklist_status": status_str}
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            i = idx[0]
            df.at[i, "checklist_tarefas"] = tarefas_str
            df.at[i, "checklist_status"] = status_str
        df = df.fillna("")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Erro ao salvar checklist: {e}")
        return False


def get_orcamento(worksheet, username):
    try:
        records = worksheet.get_all_records()
        if not records:
            return 0.0
        df = pd.DataFrame(records)
        if 'username' not in df.columns or 'orcamento' not in df.columns:
            return 0.0
        orcamento = df.loc[df['username'] == username, 'orcamento'].values
        return float(orcamento[0]) if orcamento.size > 0 and orcamento[0] else 0.0
    except Exception as e:
        st.error(f"Erro ao obter orçamento: {e}")
        return 0.0


def set_orcamento(worksheet, username, orcamento):
    try:
        records = worksheet.get_all_records()
        if not records:
            df = pd.DataFrame(columns=["username", "orcamento"])
        else:
            df = pd.DataFrame(records)

        if 'username' not in df.columns:
            df['username'] = ""
        if 'orcamento' not in df.columns:
            df['orcamento'] = 0.0

        idx = df.index[df['username'] == username].tolist()
        if not idx:
            nova_linha = {"username": username, "orcamento": orcamento}
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            i = idx[0]
            df.at[i, "orcamento"] = orcamento
        df = df.fillna("")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Erro ao salvar orçamento: {e}")
        return False


def get_gastos(worksheet, username):
    try:
        records = worksheet.get_all_records()
        if not records:
            return pd.DataFrame(columns=['descricao', 'valor', 'forma_pagamento'])
        df = pd.DataFrame(records)
        if 'username' not in df.columns or 'gastos' not in df.columns:
            return pd.DataFrame(columns=['descricao', 'valor', 'forma_pagamento'])
        gastos_str = df.loc[df['username'] == username, 'gastos'].values
        if gastos_str.size == 0 or not gastos_str[0]:
            return pd.DataFrame(columns=['descricao', 'valor', 'forma_pagamento'])
        return pd.read_json(gastos_str[0])
    except Exception as e:
        st.error(f"Erro ao obter gastos: {e}")
        return pd.DataFrame(columns=['descricao', 'valor', 'forma_pagamento'])


def set_gastos(worksheet, username, gastos_df):
    try:
        records = worksheet.get_all_records()
        if not records:
            df = pd.DataFrame(columns=["username", "gastos"])
        else:
            df = pd.DataFrame(records)

        if 'username' not in df.columns:
            df['username'] = ""
        if 'gastos' not in df.columns:
            df['gastos'] = ""

        gastos_json = gastos_df.to_json(orient='records')
        idx = df.index[df['username'] == username].tolist()
        if not idx:
            nova_linha = {"username": username, "gastos": gastos_json}
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            i = idx[0]
            df.at[i, "gastos"] = gastos_json
        df = df.fillna("")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Erro ao salvar gastos: {e}")
        return False


def get_presentes(worksheet, username):
    try:
        records = worksheet.get_all_records()
        if not records:
            return pd.DataFrame(columns=['convidado', 'presente', 'agradecimento_enviado'])
        df = pd.DataFrame(records)
        if 'username' not in df.columns or 'presentes' not in df.columns:
            return pd.DataFrame(columns=['convidado', 'presente', 'agradecimento_enviado'])
        presentes_str = df.loc[df['username'] == username, 'presentes'].values
        if presentes_str.size == 0 or not presentes_str[0]:
            return pd.DataFrame(columns=['convidado', 'presente', 'agradecimento_enviado'])
        return pd.read_json(presentes_str[0])
    except Exception as e:
        st.error(f"Erro ao obter presentes: {e}")
        return pd.DataFrame(columns=['convidado', 'presente', 'agradecimento_enviado'])


def set_presentes(worksheet, username, presentes_df):
    try:
        records = worksheet.get_all_records()
        if not records:
            df = pd.DataFrame(columns=["username", "presentes"])
        else:
            df = pd.DataFrame(records)

        if 'username' not in df.columns:
            df['username'] = ""
        if 'presentes' not in df.columns:
            df['presentes'] = ""

        presentes_json = presentes_df.to_json(orient='records')
        idx = df.index[df['username'] == username].tolist()
        if not idx:
            nova_linha = {"username": username, "presentes": presentes_json}
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            i = idx[0]
            df.at[i, "presentes"] = presentes_json
        df = df.fillna("")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Erro ao salvar presentes: {e}")
        return False


def get_sugestoes(worksheet, username):
    try:
        records = worksheet.get_all_records()
        if not records:
            return pd.DataFrame(columns=['item', 'detalhes'])
        df = pd.DataFrame(records)
        if 'username' not in df.columns or 'sugestoes' not in df.columns:
            return pd.DataFrame(columns=['item', 'detalhes'])
        sugestoes_str = df.loc[df['username'] == username, 'sugestoes'].values
        if sugestoes_str.size == 0 or not sugestoes_str[0]:
            return pd.DataFrame(columns=['item', 'detalhes'])
        return pd.read_json(sugestoes_str[0])
    except Exception as e:
        st.error(f"Erro ao obter sugestões: {e}")
        return pd.DataFrame(columns=['item', 'detalhes'])


def set_sugestoes(worksheet, username, sugestoes_df):
    try:
        records = worksheet.get_all_records()
        if not records:
            df = pd.DataFrame(columns=["username", "sugestoes"])
        else:
            df = pd.DataFrame(records)

        if 'username' not in df.columns:
            df['username'] = ""
        if 'sugestoes' not in df.columns:
            df['sugestoes'] = ""

        sugestoes_json = sugestoes_df.to_json(orient='records')
        idx = df.index[df['username'] == username].tolist()
        if not idx:
            nova_linha = {"username": username, "sugestoes": sugestoes_json}
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            i = idx[0]
            df.at[i, "sugestoes"] = sugestoes_json
        df = df.fillna("")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Erro ao salvar sugestões: {e}")
        return False


def get_brincadeiras(worksheet, username):
    try:
        records = worksheet.get_all_records()
        if not records:
            return pd.DataFrame(columns=['nome', 'regras'])
        df = pd.DataFrame(records)
        if 'username' not in df.columns or 'brincadeiras' not in df.columns:
            return pd.DataFrame(columns=['nome', 'regras'])
        brincadeiras_str = df.loc[df['username'] == username, 'brincadeiras'].values
        if brincadeiras_str.size == 0 or not brincadeiras_str[0]:
            return pd.DataFrame(columns=['nome', 'regras'])
        return pd.read_json(brincadeiras_str[0])
    except Exception as e:
        st.error(f"Erro ao obter brincadeiras: {e}")
        return pd.DataFrame(columns=['nome', 'regras'])


def set_brincadeiras(worksheet, username, brincadeiras_df):
    try:
        records = worksheet.get_all_records()
        if not records:
            df = pd.DataFrame(columns=["username", "brincadeiras"])
        else:
            df = pd.DataFrame(records)

        if 'username' not in df.columns:
            df['username'] = ""
        if 'brincadeiras' not in df.columns:
            df['brincadeiras'] = ""

        brincadeiras_json = brincadeiras_df.to_json(orient='records')
        idx = df.index[df['username'] == username].tolist()
        if not idx:
            nova_linha = {"username": username, "brincadeiras": brincadeiras_json}
            df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
        else:
            i = idx[0]
            df.at[i, "brincadeiras"] = brincadeiras_json
        df = df.fillna("")
        worksheet.clear()
        worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Erro ao salvar brincadeiras: {e}")
        return False


def reset_all_data_for_user(worksheet, username):
    try:
        records = worksheet.get_all_records()
        if not records:
            return True
        df = pd.DataFrame(records)
        if 'username' not in df.columns:
            return True
        idx = df.index[df['username'] == username].tolist()
        if idx:
            i = idx[0]
            # Apaga todas as colunas exceto username, email, name, password
            for col in df.columns:
                if col not in ['username', 'email', 'name', 'password']:
                    if df[col].dtype == object:
                        df.at[i, col] = ""
                    else:
                        df.at[i, col] = 0
            df = df.fillna("")
            worksheet.clear()
            worksheet.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except Exception as e:
        st.error(f"Erro ao resetar dados: {e}")
        return False
