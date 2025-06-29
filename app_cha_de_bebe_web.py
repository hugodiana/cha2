import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime
import database 

st.set_page_config(page_title="Organizador de Chá de Bebê", layout="wide")

try:
    # --- DEBUG: O que Streamlit secrets está vendo? ---
    st.sidebar.subheader("DEBUG: st.secrets content")
    try:
        st.sidebar.write(st.secrets)
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            st.sidebar.success("Found 'connections.gsheets' in st.secrets!")
        else:
            st.sidebar.error("Could not find 'connections.gsheets' in st.secrets.")
    except Exception as debug_e:
        st.sidebar.error(f"Error accessing st.secrets for debug: {debug_e}")
    st.sidebar.divider()
    # --- FIM DEBUG ---

    # --- 1. CONFIGURAÇÃO DE AUTENTICAÇÃO ---
    sheet = database.connect_to_sheet()
    users_df = database.fetch_all_users(sheet)

    # <<< BLOCO DE DEBUG PARA DADOS DE USUÁRIO >>>
    st.sidebar.subheader("DEBUG: User Data for Authenticator")
    st.sidebar.write(f"users_df is empty: {users_df.empty}")
    st.sidebar.write(f"users_df columns: {users_df.columns.tolist()}")
    if not users_df.empty:
        st.sidebar.write(f"First 5 rows of users_df:\n{users_df.head()}")
    st.sidebar.divider()
    # <<< FIM DO BLOCO DE DEBUG >>>

    users_dict = users_df.set_index('username').to_dict('index') if not users_df.empty else {}

    # Adicionando o debug de users_dict keys AQUI, após users_dict ser definido
    st.sidebar.write(f"DEBUG: users_dict keys (usernames): {list(users_dict.keys())}")
    st.sidebar.divider()


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

    # --- 2. TELA DE LOGIN / CADASTRO ---
    name, authentication_status, username = authenticator.login(
        fields={
            'form_name': 'Acessar Organizador', 
            'username': 'Usuário', 
            'password': 'Senha', 
            'login': 'Entrar'
        }
    )

    if authentication_status == False: 
        st.error('Usuário ou senha incorreto.')
    
    if authentication_status == None:
        st.warning('Por favor, digite seu usuário e senha para entrar, ou registre-se abaixo.')
        try:
            if authenticator.register_user(
                fields={
                    'form_name': 'Registrar Novo Usuário',
                    'username': 'Usuário desejado',
                    'name': 'Seu Nome Completo',
                    'email': 'Seu Email',
                    'password': 'Senha',
                    'repeat_password': 'Repita a Senha',
                    'register': 'Registrar'
                },
                pre_authorization=False 
            ): 
                new_users_list = []
                if 'credentials' in config and 'usernames' in config['credentials']:
                    for uname, details in config['credentials']['usernames'].items():
                        details['username'] = uname
                        new_users_list.append(details)
                
                new_users_df = pd.DataFrame(new_users_list)
                if not new_users_df.empty:
                    final_users_df = new_users_df[['username', 'email', 'name', 'password']]
                    database.update_users(sheet, final_users_df)
                
                st.success('Usuário registrado com sucesso! Por favor, faça o login com suas novas credenciais.')

        except Exception as e:
            st.error(f"Ocorreu um erro ao tentar renderizar o formulário de registro:\n{e}")

    # --- 3. APLICATIVO PRINCIPAL (APÓS LOGIN BEM-SUCEDIDO) ---
    if authentication_status:
        st.sidebar.write(f'Bem-vindo(a) **{name}**!')
        authenticator.logout('Sair', 'sidebar')
        
        evento = database.get_evento_atual(sheet, username)

        if evento is None:
            st.header("✨ Bem-vindo(a)! Vamos configurar seu evento.")
            with st.form("form_evento"):
                titulo_evento = st.text_input("Primeiro, dê um nome para o seu evento:", "Chá de Bebê")
                eh_gemeos = st.radio("É uma gravidez de gêmeos?", ("Não", "Sim"), horizontal=True, index=0)
                nomes_bebes_list, sexos_bebes_list = [], []

                if eh_gemeos == "Não":
                    nome_bebe = st.text_input("Nome do bebê:")
                    sexo_bebe = st.selectbox("Sexo do bebê:", ["Menina", "Menino", "Prefiro não informar"])
                    if nome_bebe:
                        nomes_bebes_list.append(nome_bebe.strip())
                        sexos_bebes_list.append(sexo_bebe)
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        nome_bebe1 = st.text_input("Nome do primeiro bebê:")
                        sexo_bebe1 = st.selectbox("Sexo do primeiro bebê:", ["Menina", "Menino", "Prefiro não informar"], key="sexo1")
                    with col2:
                        nome_bebe2 = st.text_input("Nome do segundo bebê:")
                        sexo_bebe2 = st.selectbox("Sexo do segundo bebê:", ["Menina", "Menino", "Prefiro não informar"], key="sexo2")
                    if nome_bebe1: nomes_bebes_list.append(nome_bebe1.strip()); sexos_bebes_list.append(sexo_bebe1)
                    if nome_bebe2: nomes_bebes_list.append(nome_bebe2.strip()); sexos_bebes_list.append(sexo_bebe2)
                
                data_nao_definida = st.checkbox("Ainda não defini a data do chá")
                data_cha = st.date_input("Data do Chá:", disabled=data_nao_definida, min_value=datetime.today())

                if st.form_submit_button("Salvar e Começar a Planejar!"):
                    if not titulo_evento or not nomes_bebes_list:
                        st.error("Por favor, preencha pelo menos o título do evento e o nome de um bebê.")
                    else:
                        evento_data = {
                            "titulo_evento": titulo_evento,
                            "eh_gemeos": eh_gemeos,
                            "nomes_bebes": ",".join(nomes_bebes_list),
                            "sexos_bebes": ",".join(sexos_bebes_list),
                            "data_cha": data_cha.isoformat() if not data_nao_definida else ""
                        }
                        database.set_evento_atual(sheet, username, evento_data)
                        st.success("Evento salvo! Seu organizador está pronto.")
                        st.rerun()
                
                else: 
                    st.sidebar.title("🎀 Navegação")
                    paginas = ["🗓️ Painel Principal", "👥 Convidados", "✅ Checklist", "💸 Gastos", "🎁 Presentes", "💡 Sugestões", "🎲 Brincadeiras", "⚙️ Configurações"]
                    pagina = st.sidebar.radio("Ir para:", paginas)
                    
                    with st.sidebar.expander("⚙️ Configurações do Evento"):
                        if st.button("Limpar e Iniciar Novo Planejamento", type="primary", help="Isso apagará TODOS os dados do evento atual."):
                            database.reset_all_data_for_user(sheet, username)
                            st.rerun()

                    nomes_bebes = evento['nomes_bebes']
                    if evento.get('eh_gemeos') == "Sim" and len(nomes_bebes.split(',')) > 1:
                        nomes_bebes = " e ".join(nomes_bebes.split(','))
                    st.title(f"👶 Chá de Bebê de {nomes_bebes}")
                    st.divider()
                    
                    if pagina == "🗓️ Painel Principal":
                        st.header("Seu Painel de Controle")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Número de Convidados", len(database.get_convidados(sheet, username)))
                        with col2:
                            tarefas, status = database.get_checklist(sheet, username)
                            st.metric("Tarefas Pendentes", len(tarefas) - sum(status))
                        st.divider()
                        st.subheader("💰 Resumo do Orçamento")
                        orcamento = database.get_orcamento(sheet, username)
                        gastos_df = database.get_gastos(sheet, username)
                        total_gasto = gastos_df['valor'].sum() if not gastos_df.empty else 0.0
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Orçamento Total", f"R$ {orcamento:.2f}")
                        c2.metric("Total Gasto", f"R$ {total_gasto:.2f}")
                        saldo = orcamento - total_gasto
                        c3.metric("Saldo Restante", f"R$ {saldo:.2f}")
                        if orcamento > 0:
                            st.progress(total_gasto / orcamento if orcamento > 0 else 0)

                    elif pagina == "👥 Convidados":
                        st.header("👥 Lista de Convidados")
                        convidados = database.get_convidados(sheet, username)
                        novo_convidado = st.text_input("Adicionar novo convidado:", key="add_guest_input")
                        if st.button("Adicionar"):
                            if novo_convidado and novo_convidado not in convidados:
                                database.set_convidados(sheet, username, convidados + [novo_convidado])
                                st.session_state.add_guest_input = ""
                                st.success(f"'{novo_convidado}' adicionado à sua lista!")
                                st.rerun()
                            elif novo_convidado in convidados: st.warning("Este convidado já está na lista.")
                            else: st.error("Por favor, digite um nome.")
                        st.divider()
                        st.subheader("Sua Lista de Convidados:")
                        if convidados:
                            for convidado in convidados: st.markdown(f"- {convidado}")
                        else:
                            st.info("Você ainda não adicionou nenhum convidado.")
                    
                    elif pagina == "✅ Checklist":
                        st.header("✅ Checklist de Preparativos")
                        tarefas, status = database.get_checklist(sheet, username)
                        with st.expander("➕ Adicionar nova tarefa"):
                            nova_tarefa_texto = st.text_input("Digite o nome da nova tarefa:", key="add_task_input")
                            if st.button("Adicionar Tarefa"):
                                if nova_tarefa_texto and nova_tarefa_texto not in tarefas:
                                    tarefas.append(nova_tarefa_texto)
                                    status.append(0)
                                    database.set_checklist(sheet, username, tarefas, status)
                                    st.rerun()
                        st.divider()
                        for i, tarefa in enumerate(tarefas):
                            col1, col2 = st.columns([10, 1])
                            status_atual = bool(status[i])
                            if col1.checkbox(tarefa, value=status_atual, key=f"task_{i}") != status_atual:
                                status[i] = 1 if not status_atual else 0
                                database.set_checklist(sheet, username, tarefas, status)
                                st.rerun()
                            if col2.button("🗑️", key=f"del_task_{i}", help="Remover tarefa"):
                                tarefas.pop(i)
                                status.pop(i)
                                database.set_checklist(sheet, username, tarefas, status)
                                st.rerun()
                    
                    elif pagina == "💸 Gastos":
                        st.header("💸 Controle de Gastos")
                        orcamento_atual = database.get_orcamento(sheet, username)
                        novo_orcamento = st.number_input("Defina seu orçamento total:", min_value=0.0, value=orcamento_atual, format="%.2f")
                        if novo_orcamento != orcamento_atual:
                            database.set_orcamento(sheet, username, novo_orcamento)
                            st.success("Orçamento atualizado!")
                            st.rerun()
                        with st.expander("➕ Adicionar novo gasto"):
                            with st.form("form_gasto", clear_on_submit=True):
                                descricao = st.text_input("Descrição do gasto")
                                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                                forma_pagamento = st.selectbox("Forma de pagamento", ["PIX", "Cartão de crédito", "Dinheiro", "Outro"])
                                submitted = st.form_submit_button("Adicionar Gasto")
                                if submitted:
                                    if descricao and valor > 0:
                                        gastos_df = database.get_gastos(sheet, username)
                                        novo_gasto = pd.DataFrame([{'descricao': descricao, 'valor': valor, 'forma_pagamento': forma_pagamento}])
                                        df_atualizado = pd.concat([gastos_df, novo_gasto], ignore_index=True)
                                        database.set_gastos(sheet, username, df_atualizado)
                                        st.success("Gasto adicionado!")
                                    else:
                                        st.warning("Preencha a descrição e um valor maior que zero.")
                        st.divider()
                        st.subheader("📊 Lista de Gastos")
                        gastos_df = database.get_gastos(sheet, username)
                        if not gastos_df.empty:
                            st.dataframe(gastos_df, use_container_width=True)
                            total_gasto = gastos_df['valor'].sum()
                            st.markdown(f"### **💰 Total gasto:** R$ {total_gasto:.2f}")
                        else:
                            st.info("Nenhum gasto registrado ainda.")

                    elif pagina == "🎁 Presentes":
                        st.header("🎁 Presentes Recebidos")
                        with st.expander("➕ Registrar novo presente"):
                            with st.form("form_presente", clear_on_submit=True):
                                convidado = st.text_input("Nome do convidado que presenteou")
                                presente = st.text_input("Presente recebido")
                                submitted = st.form_submit_button("Registrar Presente")
                                if submitted:
                                    if convidado and presente:
                                        presentes_df = database.get_presentes(sheet, username)
                                        novo_presente = pd.DataFrame([{'convidado': convidado, 'presente': presente, 'agradecimento_enviado': 'Não'}])
                                        df_atualizado = pd.concat([presentes_df, novo_presente], ignore_index=True)
                                        database.set_presentes(sheet, username, df_atualizado)
                                        st.success("Presente registrado!")
                                    else:
                                        st.warning("Por favor, preencha todos os campos.")
                        st.divider()
                        st.subheader("📦 Lista de Presentes")
                        presentes_df = database.get_presentes(sheet, username)
                        if not presentes_df.empty:
                            edited_df = st.data_editor(presentes_df, num_rows="dynamic", use_container_width=True, hide_index=True)
                            if st.button("Salvar alterações nos presentes"):
                                database.set_presentes(sheet, username, edited_df)
                                st.success("Alterações salvas!")
                                st.rerun()
                        else:
                            st.info("Nenhum presente registrado ainda.")
                    
                    elif pagina == "💡 Sugestões":
                        st.header("💡 Sugestões de Presentes")
                        st.info("Crie uma lista de presentes que você gostaria de ganhar para compartilhar com seus convidados.")
                        with st.expander("➕ Adicionar nova sugestão"):
                            with st.form("form_sugestao", clear_on_submit=True):
                                item = st.text_input("Item sugerido (ex: Fralda G, Body RN)")
                                detalhes = st.text_area("Detalhes (opcional: tamanho, cor, marca, link da loja)")
                                submitted = st.form_submit_button("Adicionar Sugestão")
                                if submitted:
                                    if item:
                                        sugestoes_df = database.get_sugestoes(sheet, username)
                                        nova_sugestao = pd.DataFrame([{'item': item, 'detalhes': detalhes}])
                                        df_atualizado = pd.concat([sugestoes_df, novo_sugestao], ignore_index=True)
                                        database.set_sugestoes(sheet, username, df_atualizado)
                                        st.success("Sugestão adicionada!")
                                    else:
                                        st.warning("O nome do item é obrigatório.")
                        st.divider()
                        st.subheader("📋 Sua Lista de Sugestões")
                        sugestoes_df = database.get_sugestoes(sheet, username)
                        if not sugestoes_df.empty:
                            st.dataframe(sugestoes_df, use_container_width=True, hide_index=True)
                        else:
                            st.info("Nenhuma sugestão de presente adicionada ainda.")

                    elif pagina == "🎲 Brincadeiras":
                        st.header("🎲 Planejamento de Brincadeiras")
                        st.info("Liste aqui as brincadeiras e atividades planejadas para o seu evento.")
                        with st.expander("➕ Adicionar nova brincadeira"):
                            with st.form("form_brincadeira", clear_on_submit=True):
                                nome = st.text_input("Nome da brincadeira")
                                regras = st.text_area("Regras e materiais necessários")
                                submitted = st.form_submit_button("Adicionar Brincadeira")
                                if submitted:
                                    if nome:
                                        brincadeiras_df = database.get_brincadeiras(sheet, username)
                                        nova_brincadeira = pd.DataFrame([{'nome': nome, 'regras': regras}])
                                        df_atualizado = pd.concat([brincadeiras_df, novo_brincadeira], ignore_index=True)
                                        database.set_brincadeiras(sheet, username, df_atualizado)
                                        st.success("Brincadeira adicionada!")
                                    else:
                                        st.warning("O nome da brincadeira é obrigatório.")
                        st.divider()
                        st.subheader("🕹️ Suas Brincadeiras Planejadas")
                        brincadeiras_df = database.get_brincadeiras(sheet, username)
                        if not brincadeiras_df.empty:
                            for i, row in brincadeiras_df.iterrows():
                                with st.expander(f"**{row['nome']}**"):
                                    st.write(row['regras'])
                                    if st.button("Remover Brincadeira", key=f"del_brincadeira_{i}", type="secondary"):
                                        df_atualizado = brincadeiras_df.drop(i)
                                        database.set_brincadeiras(sheet, username, df_atualizado)
                                        st.rerun()
                        else:
                            st.info("Nenhuma brincadeira adicionada ainda.")

                    elif pagina == "⚙️ Configurações":
                        st.header("⚙️ Configurações da Conta")
                        st.subheader("⚠️ Área de Risco")
                        st.write("A ação abaixo irá apagar **todos os dados** que você inseriu neste evento: convidados, gastos, checklist, tudo. Isso é útil se você quiser começar a planejar um novo evento do zero.")

                        with st.expander("Quero começar um novo planejamento"):
                            st.warning("**Atenção:** Esta ação não pode ser desfeita.")
                            
                            confirmacao = st.checkbox("Eu entendo que todos os meus dados atuais serão permanentemente apagados.")
                            
                            if confirmacao:
                                if st.button("Apagar tudo e começar de novo", type="primary"):
                                    try:
                                        database.reset_all_data_for_user(sheet, username)
                                        st.success("Todos os dados foram apagados! Você será redirecionado para a tela de configuração inicial.")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Ocorreu um erro ao tentar apagar os dados: {e}")

except Exception as e:
    st.error(f"Ocorreu um erro na conexão ou na inicialização do aplicativo: `{e}`")
    st.info("Verifique se as credenciais do Google Sheets estão configuradas corretamente no Streamlit Secrets e se o nome da planilha está correto.")