# Arquivo: gerar_senha.py
import streamlit_authenticator as stauth

# ❗ IMPORTANTE: Coloque a senha que você deseja usar aqui dentro das aspas
senha_que_voce_quer = "Ah240911**" # Ex: "minhasenha123"

hashed_password = stauth.Hasher([senha_que_voce_quer]).generate()
print("Sua senha criptografada é:")
print(hashed_password[0])