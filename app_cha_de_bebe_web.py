import streamlit as st
import streamlit_authenticator as stauth
import pandas as pd
from datetime import datetime
import database

st.set_page_config(page_title="Organizador de Chá de Bebê", layout="wide")

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

        # Contador dias restantes se houver data
        if evento and evento.get('data_cha'):
            try:
                data_evento = datetime.fromisoformat(evento['data_cha']).date()
                hoje = datetime.today().date()
                dias_restantes = (data_evento - hoje).days
                if dias_restantes >= 0:
                    st.success(f"⏳ Faltam {dias_restantes} dia(s) para o grande dia!")
                else:
                    st.warning("📅 A data do chá já passou.")
            except:
                pass

        # Tela inicial para cadastro do chá (se não tiver nome do bebê)
        if not evento or not evento.get('nome_bebe'):
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
                "🗓️ Painel Principal", "👥 Convidados", "✅ Checklist", "💸 Gastos",
                "🎁 Presentes", "💡 Sugestões", "🎲 Brincadeiras", "⚙️ Configurações"
            ]
            pagina = st.sidebar.radio("Ir para:", paginas)

            if pagina == "🗓️ Painel Principal":
                st.header("Seu Painel de Controle")
                col1, col2 = st.columns(2)
                convidados = database.get_convidados(sheet, username)
                tarefas, status = database.get_checklist(sheet, username)

                col1.metric("Número de Convidados", len(convidados))
                col2.metric("Tarefas Pendentes", len(tarefas) - sum(status))

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
                    st.progress(total_gasto / orcamento)

            elif pagina == "👥 Convidados":
                st.header("👥 Lista de Convidados")
                convidados = database.get_convidados(sheet, username)
                novo_convidado = st.text_input("Adicionar novo convidado:", key="add_guest_input")
                if st.button("Adicionar"):
                    if novo_convidado and novo_convidado not in convidados:
                        convidados.append(novo_convidado)
                        database.set_convidados(sheet, username, convidados)
                        st.success(f"'{novo_convidado}' adicionado à lista!")
                        st.experimental_rerun()
                    elif novo_convidado in convidados:
                        st.warning("Este convidado já está na lista.")
                    else:
                        st.error("Digite um nome válido.")
                st.divider()
                if convidados:
                    for c in convidados:
                        st.markdown(f"- {c}")
                else:
                    st.info("Nenhum convidado adicionado.")

            elif pagina == "✅ Checklist":
                st.header("✅ Checklist de Preparativos")
                tarefas, status = database.get_checklist(sheet, username)
                with st.expander("➕ Adicionar nova tarefa"):
                    nova_tarefa = st.text_input("Nova tarefa:", key="add_task_input")
                    if st.button("Adicionar tarefa"):
                        if nova_tarefa and nova_tarefa not in tarefas:
                            tarefas.append(nova_tarefa)
                            status.append(0)
                            database.set_checklist(sheet, username, tarefas, status)
                            st.experimental_rerun()
                        else:
                            st.warning("Tarefa inválida ou já existe.")
                st.divider()
                for i, tarefa in enumerate(tarefas):
                    col1, col2 = st.columns([10,1])
                    atual = bool(status[i])
                    check = col1.checkbox(tarefa, value=atual, key=f"task_{i}")
                    if check != atual:
                        status[i] = 1 if check else 0
                        database.set_checklist(sheet, username, tarefas, status)
                        st.experimental_rerun()
                    if col2.button("🗑️", key=f"del_task_{i}"):
                        tarefas.pop(i)
                        status.pop(i)
                        database.set_checklist(sheet, username, tarefas, status)
                        st.experimental_rerun()

            elif pagina == "💸 Gastos":
                st.header("💸 Controle de Gastos")
                orcamento = database.get_orcamento(sheet, username)
                novo_orcamento = st.number_input("Orçamento total (R$):", min_value=0.0, value=orcamento, format="%.2f")
                if novo_orcamento != orcamento:
                    database.set_orcamento(sheet, username, novo_orcamento)
                    st.success("Orçamento atualizado!")
                    st.experimental_rerun()
                with st.expander("➕ Adicionar novo gasto"):
                    with st.form("form_gasto", clear_on_submit=True):
                        desc = st.text_input("Descrição")
                        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                        pagamento = st.selectbox("Forma de pagamento", ["PIX", "Cartão", "Dinheiro", "Outro"])
                        if st.form_submit_button("Adicionar gasto"):
                            if desc and valor > 0:
                                gastos_df = database.get_gastos(sheet, username)
                                novo_gasto = pd.DataFrame([{'descricao': desc, 'valor': valor, 'forma_pagamento': pagamento}])
                                df_atualizado = pd.concat([gastos_df, novo_gasto], ignore_index=True)
                                database.set_gastos(sheet, username, df_atualizado)
                                st.success("Gasto adicionado!")
                                st.experimental_rerun()
                            else:
                                st.warning("Preencha descrição e valor válido.")
                st.divider()
                st.subheader("Lista de Gastos")
                gastos_df = database.get_gastos(sheet, username)
                if not gastos_df.empty:
                    st.dataframe(gastos_df, use_container_width=True)
                    total = gastos_df['valor'].sum()
                    st.markdown(f"### Total gasto: R$ {total:.2f}")
                else:
                    st.info("Nenhum gasto registrado.")

            elif pagina == "🎁 Presentes":
                st.header("🎁 Presentes Recebidos")
                with st.expander("➕ Registrar presente"):
                    with st.form("form_presente", clear_on_submit=True):
                        convidado = st.text_input("Nome do convidado")
                        presente = st.text_input("Presente")
                        if st.form_submit_button("Registrar"):
                            if convidado and presente:
                                presentes_df = database.get_presentes(sheet, username)
                                novo_presente = pd.DataFrame([{'convidado': convidado, 'presente': presente, 'agradecimento_enviado': 'Não'}])
                                df_atualizado = pd.concat([presentes_df, novo_presente], ignore_index=True)
                                database.set_presentes(sheet, username, df_atualizado)
                                st.success("Presente registrado!")
                                st.experimental_rerun()
                            else:
                                st.warning("Preencha todos os campos.")
                st.divider()
                presentes_df = database.get_presentes(sheet, username)
                if not presentes_df.empty:
                    edited = st.data_editor(presentes_df, num_rows="dynamic", use_container_width=True, hide_index=True)
                    if st.button("Salvar alterações"):
                        database.set_presentes(sheet, username, edited)
                        st.success("Alterações salvas!")
                        st.experimental_rerun()
                else:
                    st.info("Nenhum presente registrado.")

            elif pagina == "💡 Sugestões":
                st.header("💡 Sugestões de Presentes")
                with st.expander("➕ Adicionar sugestão"):
                    with st.form("form_sugestao", clear_on_submit=True):
                        item = st.text_input("Item")
                        detalhes = st.text_area("Detalhes (opcional)")
                        if st.form_submit_button("Adicionar"):
                            if item:
                                sugestoes_df = database.get_sugestoes(sheet, username)
                                nova_sugestao = pd.DataFrame([{'item': item, 'detalhes': detalhes}])
                                df_atualizado = pd.concat([sugestoes_df, nova_sugestao], ignore_index=True)
                                database.set_sugestoes(sheet, username, df_atualizado)
                                st.success("Sugestão adicionada!")
                                st.experimental_rerun()
                            else:
                                st.warning("Preencha o nome do item.")
                st.divider()
                sugestoes_df = database.get_sugestoes(sheet, username)
                if not sugestoes_df.empty:
                    st.dataframe(sugestoes_df, use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhuma sugestão adicionada.")

            elif pagina == "🎲 Brincadeiras":
                st.header("🎲 Planejamento de Brincadeiras")
                with st.expander("➕ Adicionar brincadeira"):
                    with st.form("form_brincadeira", clear_on_submit=True):
                        nome = st.text_input("Nome")
                        regras = st.text_area("Regras e materiais")
                        if st.form_submit_button("Adicionar"):
                            if nome:
                                brincadeiras_df = database.get_brincadeiras(sheet, username)
                                nova = pd.DataFrame([{'nome': nome, 'regras': regras}])
                                df_atualizado = pd.concat([brincadeiras_df, nova], ignore_index=True)
                                database.set_brincadeiras(sheet, username, df_atualizado)
                                st.success("Brincadeira adicionada!")
                                st.experimental_rerun()
                            else:
                                st.warning("Preencha o nome da brincadeira.")
                st.divider()
                brincadeiras_df = database.get_brincadeiras(sheet, username)
                if not brincadeiras_df.empty:
                    for i, row in brincadeiras_df.iterrows():
                        with st.expander(f"**{row['nome']}**"):
                            st.write(row['regras'])
                            if st.button("Remover", key=f"del_brincadeira_{i}"):
                                df_atualizado = brincadeiras_df.drop(i)
                                database.set_brincadeiras(sheet, username, df_atualizado)
                                st.experimental_rerun()
                else:
                    st.info("Nenhuma brincadeira adicionada.")

            elif pagina == "⚙️ Configurações":
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
