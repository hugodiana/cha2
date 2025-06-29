import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime
import database

st.set_page_config(page_title="Organizador de Chá de Bebê", layout="wide")

def hash_passwords(passwords):
    """Gera hashes das senhas para armazenar."""
    hasher = stauth.Hasher(passwords)
    return hasher.generate()

try:
    # Conecta planilha e busca usuários
    sheet = database.connect_to_sheet()
    users_df = database.fetch_all_users(sheet)
    users_dict = {}

    # Prepara dicionário para autenticação
    if not users_df.empty:
        for _, row in users_df.iterrows():
            users_dict[row['username']] = {
                'name': row['name'],
                'email': row['email'],
                'password': row['password']
            }

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

        # Formulário de registro customizado para poder pegar a senha em texto plano
        with st.form("registro_form"):
            new_username = st.text_input("Usuário")
            new_name = st.text_input("Nome")
            new_email = st.text_input("Email")
            new_password = st.text_input("Senha", type="password")
            confirmar_senha = st.text_input("Confirme a senha", type="password")
            submit_button = st.form_submit_button("Registrar")

        if submit_button:
            if not new_username or not new_password or not new_name or not new_email:
                st.error("Preencha todos os campos.")
            elif new_password != confirmar_senha:
                st.error("As senhas não coincidem.")
            elif new_username in users_dict:
                st.error("Usuário já existe.")
            else:
                # Gerar hash da senha
                hashed_pwd = hash_passwords([new_password])[0]

                # Adicionar novo usuário no dict
                users_dict[new_username] = {
                    'name': new_name,
                    'email': new_email,
                    'password': hashed_pwd
                }

                # Atualizar planilha
                new_users_list = []
                for uname, details in users_dict.items():
                    details['username'] = uname
                    new_users_list.append(details)
                new_users_df = pd.DataFrame(new_users_list)
                final_users_df = new_users_df[['username', 'email', 'name', 'password']]
                success = database.update_users(sheet, final_users_df)

                if success:
                    st.success("Usuário registrado com sucesso! Faça login com suas credenciais.")
                    st.experimental_rerun()
                else:
                    st.error("Erro ao salvar usuário.")

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
                    st.success(f"⏳ Faltam {dias_restantes} dia(s) para o grande dia!")
                else:
                    st.warning("📅 A data do chá já passou.")
            except Exception:
                pass

        if not evento or not isinstance(evento, dict) or not evento.get('nome_bebe'):
            st.header("✨ Vamos configurar seu chá de bebê!")
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
                        st.experimental_rerun()

        else:
            nomes_bebes = evento.get('nome_bebe', '')
            st.title(f"👶 Chá de Bebê de {nomes_bebes}")
            st.divider()

            paginas = [
                "📅 Painel Principal", "👥 Convidados", "✅ Checklist", "💸 Gastos",
                "🏳️ Presentes", "💡 Sugestões", "🎲 Brincadeiras", "⚙️ Configurações"
            ]
            pagina = st.sidebar.radio("Ir para:", paginas)

            # Você pode implementar as páginas aqui conforme seu código

            if pagina == "⚙️ Configurações":
                st.header("⚙️ Configurações")
                st.warning("⚠️ Apagar todos os dados do evento.")
                confirm = st.checkbox("Confirmo apagar todos os dados.")
                if confirm:
                    if st.button("Apagar e reiniciar"):
                        try:
                            database.reset_all_data_for_user(sheet, username)
                            st.success("Dados apagados! Redirecionando...")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Erro ao apagar dados: {e}")

except Exception as e:
    st.error(f"Erro na inicialização do app: {e}")
    st.info("Verifique as credenciais e configuração do Google Sheets.")
