import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime
import database

st.set_page_config(page_title="Organizador de Chá de Bebê", layout="wide")

def try_rerun():
    try:
        st.experimental_rerun()
    except AttributeError:
        # fallback caso experimental_rerun não exista
        st.experimental_singleton.clear()
        st.experimental_memo.clear()
        st.stop()

try:
    # Conecta planilha e busca usuários
    sheet = database.connect_to_sheet()
    users_df = database.fetch_all_users(sheet)
    users_dict = users_df.set_index('username').to_dict('index') if not users_df.empty else {}

    config = {
        'credentials': {'usernames': users_dict},
        'cookie': {'name': 'cha_de_bebe_cookie', 'key': 'uma_chave_secreta_qualquer', 'expiry_days': 30},
    }

    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )

    name, authentication_status, username = authenticator.login("Acessar Organizador", "main")

    if authentication_status is False:
        st.error('Usuário ou senha incorreto.')

    elif authentication_status is None:
        st.warning('Por favor, digite seu usuário e senha para entrar, ou registre-se abaixo.')
        try:
            if authenticator.register_user("Registrar Novo Usuário", preauthorization=False):
                new_users_list = []
                for uname, details in config['credentials']['usernames'].items():
                    details['username'] = uname
                    new_users_list.append(details)
                new_users_df = pd.DataFrame(new_users_list)
                if not new_users_df.empty:
                    final_users_df = new_users_df[['username', 'email', 'name', 'password']]
                    database.update_users(sheet, final_users_df)
                st.success('Usuário registrado com sucesso! Por favor, faça o login com suas novas credenciais.')
        except Exception as e:
            st.error(f"Erro no registro: {e}")

    else:
        st.sidebar.write(f'Bem-vindo(a) **{name}**!')
        authenticator.logout('Sair', 'sidebar')

        evento = database.get_evento_atual(sheet, username)

        if evento and isinstance(evento, dict) and evento.get('data_cha'):
            try:
                data_evento = datetime.fromisoformat(evento['data_cha']).date()
                hoje = datetime.today().date()
                dias_restantes = (data_evento - hoje).days
                if dias_restantes >= 0:
                    st.success(f"\u23F3 Faltam {dias_restantes} dia(s) para o grande dia!")
                else:
                    st.warning("\ud83d\uddd3\ufe0f A data do chá já passou.")
            except Exception:
                pass

        if not evento or not isinstance(evento, dict) or not evento.get('nome_bebe'):
            st.header("\u2728 Vamos configurar seu chá de bebê!")
            with st.form("form_evento"):
                nome_bebe = st.text_input("Nome do bebê:")
                sexo_bebe = st.selectbox("Sexo do bebê:", ["Menina", "Menino", "Prefiro não informar"])
                data_nao_definida = st.checkbox("Ainda não defini a data do chá")
                data_cha = st.date_input("Data do Chá:", disabled=data_nao_definida, min_value=datetime.today())

                if st.form_submit_button("Salvar e Continuar"):
                    if not nome_bebe:
                        st.error("Preencha o nome do bebê.")
                    else:
                        evento_data = {
                            "nome_bebe": nome_bebe.strip(),
                            "sexo_bebe": sexo_bebe,
                            "data_cha": data_cha.isoformat() if not data_nao_definida else ""
                        }
                        database.set_evento_atual(sheet, username, evento_data)
                        st.success("Evento salvo!")
                        try_rerun()

        else:
            nomes_bebes = evento.get('nome_bebe', '')
            st.title(f"\ud83d\udc76 Chá de Bebê de {nomes_bebes}")
            st.divider()

            paginas = [
                "\ud83d\uddd3\ufe0f Painel Principal", "\ud83d\udc65 Convidados", "\u2705 Checklist", "\ud83d\udcb8 Gastos",
                "\ud83c\udff1 Presentes", "\ud83d\udca1 Sugestões", "\ud83c\udfb2 Brincadeiras", "\u2699\ufe0f Configurações"
            ]
            pagina = st.sidebar.radio("Ir para:", paginas)

            if pagina == "\ud83d\uddd3\ufe0f Painel Principal":
                # Conteúdo da página principal
                pass

            elif pagina == "\ud83d\udc65 Convidados":
                # Conteúdo convidados
                pass

            elif pagina == "\u2705 Checklist":
                # Conteúdo checklist
                pass

            elif pagina == "\ud83d\udcb8 Gastos":
                # Conteúdo gastos
                pass

            elif pagina == "\ud83c\udff1 Presentes":
                # Conteúdo presentes
                pass

            elif pagina == "\ud83d\udca1 Sugestões":
                # Conteúdo sugestões
                pass

            elif pagina == "\ud83c\udfb2 Brincadeiras":
                # Conteúdo brincadeiras
                pass

            elif pagina == "\u2699\ufe0f Configurações":
                st.header("\u2699\ufe0f Configurações")
                st.warning("\u26a0\ufe0f Apagar todos os dados do evento.")
                confirm = st.checkbox("Confirmo apagar todos os dados.")
                if confirm:
                    if st.button("Apagar e reiniciar"):
                        try:
                            database.reset_all_data_for_user(sheet, username)
                            st.success("Dados apagados! Redirecionando...")
                            try_rerun()
                        except Exception as e:
                            st.error(f"Erro ao apagar dados: {e}")

except Exception as e:
    st.error(f"Erro na inicialização do app: {e}")
    st.info("Verifique as credenciais e configuração do Google Sheets.")
