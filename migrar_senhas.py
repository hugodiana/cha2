import database
import pandas as pd
import streamlit_authenticator as stauth

def migrar_senhas():
    sheet = database.connect_to_sheet()
    users_df = database.fetch_all_users(sheet)
    if users_df.empty:
        print("Nenhum usuário encontrado na planilha.")
        return

    # Senhas atuais em texto puro
    senhas = users_df['password'].tolist()

    # Gerar hashes das senhas
    hasher = stauth.Hasher(senhas)
    senhas_hash = hasher.generate()

    # Atualiza o DataFrame com as senhas hasheadas
    users_df['password'] = senhas_hash

    # Atualiza a planilha
    sucesso = database.update_users(sheet, users_df)
    if sucesso:
        print("Migração concluída: senhas convertidas para hash e atualizadas na planilha.")
    else:
        print("Erro ao atualizar a planilha.")

if __name__ == "__main__":
    migrar_senhas()
