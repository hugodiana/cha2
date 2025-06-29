Peço desculpas pela persistência do erro. Se a mesma mensagem continua aparecendo mesmo após a alteração, a causa mais provável é que a mudança não foi salva corretamente no arquivo ou o Streamlit ainda está executando uma versão antiga do código que estava em cache.

A forma mais garantida de resolvermos isso de uma vez por todas é substituir o conteúdo completo do seu arquivo `app_cha_de_bebe_web.py`. Assim, não há risco de a linha incorreta ter permanecido.

Por favor, siga estes passos:

1.  Abra seu arquivo `app_cha_de_bebe_web.py`.
2.  **Apague absolutamente todo o conteúdo dele.**
3.  **Copie e cole o código completo abaixo** no arquivo agora vazio.

Este código é idêntico ao que te enviei da última vez, mas com a garantia de que a correção na função `register_user` está presente e é a única versão no arquivo.

### ✅ **Arquivo Completo e Corrigido: `app_cha_de_bebe_web.py`**

```python
import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime
import database 

st.set_page_config(page_title="Organizador de Chá de Bebê", layout="wide")

try:
    sheet = database.connect_to_sheet()
    users_df = database.fetch_all_users(sheet)

    if not users_df.empty:
        users_dict = users_df.set_index('username').to_dict('index')
    else:
        users_dict = {}

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

    name, authentication_status, username = authenticator.login(fields={'Form name': 'Acessar Organizador', 'Username': 'Usuário', 'Password': 'Senha', 'Login': 'Entrar'})

    if authentication_status == False: 
        st.error('Usuário ou senha incorreto.')
    
    if authentication_status == None:
        st.warning('Por favor, digite seu usuário e senha.')
        try:
            # <<< CORREÇÃO APLICADA AQUI >>>
            # A chamada a 'register_user' foi atualizada para usar o parâmetro 'fields'
            if authenticator.register_user(fields={'Form name': 'Registrar novo usuário', 
                                                   'Username': 'Usuário', 
                                                   'Name':'Nome', 
                                                   'Password':'Senha'}, 
                                           pre_authorization=False):
                
                st.success('Usuário registrado com sucesso! Por favor, faça o login com suas novas credenciais.')
                
        except Exception as e:
            st.error(e)

    if authentication_status:
        # --- NOVO BLOCO: VERIFICAÇÃO DO SETUP INICIAL ---
        evento_info = database.get_evento_atual(sheet, username)
        setup_completo = evento_info.get('setup_completo', False) if evento_info else False

        # Se o setup não foi concluído, exibe a tela de configuração
        if not setup_completo:
            st.title("✨ Bem-vindo(a) ao seu Organizador!")
            st.header("Vamos começar com alguns detalhes importantes.")

            with st.form("form_setup"):
                st.write("### Sobre o Bebê (ou Bebês!)")
                e_gemeos = st.radio("É uma gravidez de gêmeos?", ("Não", "Sim"), horizontal=True)

                if e_gemeos == "Não":
                    nome_bebe_1 = st.text_input("Nome do bebê")
                    sexo_bebe_1 = st.selectbox("Sexo do bebê", ["Não quero informar", "Menina", "Menino", "Surpresa!"])
                    nome_bebe_2 = ""
                    sexo_bebe_2 = ""
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        nome_bebe_1 = st.text_input("Nome do Bebê 1")
                        sexo_bebe_1 = st.selectbox("Sexo do Bebê 1", ["Não quero informar", "Menina", "Menino", "Surpresa!"], key="sexo1")
                    with col2:
                        nome_bebe_2 = st.text_input("Nome do Bebê 2")
                        sexo_bebe_2 = st.selectbox("Sexo do Bebê 2", ["Não quero informar", "Menina", "Menino", "Surpresa!"], key="sexo2")
                
                st.write("---")
                st.write("### Sobre o Evento")
                data_cha = st.date_input("Qual a data prevista para o Chá de Bebê?", value=None)

                submitted = st.form_submit_button("Salvar e começar a organizar!")

                if submitted:
                    if not nome_bebe_1:
                        st.error("Por favor, preencha o nome do bebê.")
                    else:
                        evento_data = {
                            'setup_completo': "Sim",
                            'e_gemeos': e_gemeos,
                            'nome_bebe_1': nome_bebe_1,
                            'sexo_bebe_1': sexo_bebe_1,
                            'nome_bebe_2': nome_bebe_2,
                            'sexo_bebe_2': sexo_bebe_2,
                            'data_cha': data_cha.isoformat() if data_cha else ""
                        }
                        database.set_evento_atual(sheet, username, evento_data)
                        st.success("Tudo pronto! Seu painel já está configurado.")
                        st.balloons()
                        st.rerun()
        
        # Se o setup já foi feito, mostra o aplicativo normalmente
        else:
            # --- BARRA LATERAL ---
            st.sidebar.write(f'Bem-vindo(a) **{name}**!')
            authenticator.logout('Sair', 'sidebar')

            st.sidebar.title("🎀 Navegação")
            paginas = ["🗓️ Painel Principal", "👥 Convidados", "✅ Checklist", "💸 Gastos", "🎁 Presentes", "💡 Sugestões", "🎲 Brincadeiras", "⚙️ Configurações"]
            pagina = st.sidebar.radio("Ir para:", paginas)

            # --- PÁGINAS DO APP ---
            nomes_bebes = evento_info.get('nome_bebe_1', '')
            if evento_info.get('e_gemeos') == "Sim" and evento_info.get('nome_bebe_2'):
                nomes_bebes += f" e {evento_info.get('nome_bebe_2', '')}"
            st.title(f"👶 Chá de Bebê de {nomes_bebes}")
            st.divider()

            if pagina == "🗓️ Painel Principal":
                # ... (código da página do painel principal) ...
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

            # ... (código das outras páginas como Convidados, Checklist, etc.)
            elif pagina == "👥 Convidados":
                st.header("👥 Lista de Convidados")
                convidados = database.get_convidados(sheet, username)
                novo_convidado = st.text_input("Adicionar novo convidado:")
                if st.button("Adicionar"):
                    if novo_convidado and novo_convidado not in convidados:
                        database.set_convidados(sheet, username, convidados + [novo_convidado])
                        st.success(f"'{novo_convidado}' adicionado à sua lista!")
                        st.rerun()
                    elif novo_convidado in convidados: st.warning("Este convidado já está na lista.")
                    else: st.error("Por favor, digite um nome.")
                st.divider()
                st.subheader("Sua Lista de Convidados:")
                if convidados:
                    for i, convidado in enumerate(convidados):
                        st.markdown(f"- {convidado}")
                else:
                    st.info("Você ainda não adicionou nenhum convidado.")
            # (O restante do código das outras páginas continua aqui, sem alterações)
            
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
                    # Usando st.data_editor para uma edição mais interativa
                    edited_df = st.data_editor(presentes_df, num_rows="dynamic", use_container_width=True, hide_index=True)
                    if st.button("Salvar alterações nos presentes"):
                        database.set_presentes(sheet, username, edited_df)
                        st.success("Alterações salvas!")
                        st.rerun()
                else:
                    st.info("Nenhum presente registrado ainda.")
            
            elif pagina == "💡 Sugestões":
                st.header("💡 Sugestões de Presentes")
                # (código da página de sugestões)
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
                                df_atualizado = pd.concat([sugestoes_df, nova_sugestao], ignore_index=True)
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
                # (código da página de brincadeiras)
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
                                df_atualizado = pd.concat([brincadeiras_df, nova_brincadeira], ignore_index=True)
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

```

Depois de substituir e salvar o arquivo, por favor, pare seu servidor Streamlit (com `Ctrl+C` no terminal) e inicie-o novamente (`streamlit run app_cha_de_bebe_web.py`). Isso garante que ele lerá a nova versão do arquivo do zero.

Se possível, faça também uma atualização forçada no seu navegador (normalmente `Ctrl+F5` ou `Cmd+Shift+R`) para limpar o cache do navegador.