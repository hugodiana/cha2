# Dentro do novo arquivo: teste_auth.py

import streamlit as st
import streamlit_authenticator as stauth

# Configuração mínima com um usuário falso
config = {
    'credentials': {'usernames': {}},
    'cookie': {'name': 'teste_cookie', 'key': 'chave_teste', 'expiry_days': 30},
}

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

st.title("Teste de Registro de Usuário")

# Esta é a parte que queremos testar
try:
    if authenticator.register_user(fields={'Form name': 'Formulário de Teste', 'Username': 'Usuário', 'Name':'Nome', 'Password':'Senha'}):
        st.success('Usuário de teste registrado com sucesso!')
except Exception as e:
    st.error(f"Ocorreu um erro ao tentar renderizar o formulário de registro:")
    st.error(e)