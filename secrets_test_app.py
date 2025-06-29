import streamlit as st
import os

st.set_page_config(page_title="Teste de Secrets", layout="wide")

st.title("🧪 Teste de Leitura do secrets.toml")

st.write(f"Caminho do diretório de trabalho atual: `{os.getcwd()}`")
st.write(f"Caminho do arquivo do app: `{os.path.abspath(__file__)}`")
st.write(f"Caminho esperado do .streamlit/: `{os.path.abspath(os.path.join(os.getcwd(), '.streamlit'))}`")

st.divider()

st.subheader("Conteúdo de st.secrets:")
try:
    st.write(st.secrets)
    
    # <<< CORREÇÃO APLICADA AQUI: Acesso defensivo usando .get() >>>
    connections_data = st.secrets.get("connections")
    
    if connections_data:
        gsheets_data = connections_data.get("gsheets")
        
        if gsheets_data:
            st.success("🎉 Chave 'connections.gsheets' encontrada em st.secrets!")
            
            # Agora tentamos acessar 'test_key'
            test_value = gsheets_data.get("test_key")
            if test_value:
                st.info(f"Valor de 'test_key': **{test_value}**")
            else:
                st.error("❌ Chave 'test_key' NÃO encontrada dentro de 'connections.gsheets'.")
        else:
            st.error("❌ Chave 'gsheets' NÃO encontrada dentro de 'connections'.")
            st.warning("Isso indica que a seção '[connections.gsheets]' no secrets.toml pode estar vazia ou malformada.")
    else:
        st.error("❌ Chave 'connections' NÃO encontrada em st.secrets.")
        st.warning("Isso significa que o arquivo secrets.toml não está sendo lido corretamente ou a seção 'connections' está ausente.")

except Exception as e:
    st.exception(e)
    st.error("Ocorreu um erro inesperado ao acessar st.secrets. Por favor, verifique a formatação do secrets.toml.")

st.divider()
st.info("Verifique os caminhos acima. O arquivo `.streamlit/secrets.toml` deve estar na raiz do seu projeto.")