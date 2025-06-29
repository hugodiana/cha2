import tkinter as tk
from tkinter import messagebox
from checklist import tarefas, concluir_tarefa, carregar_tarefas, salvar_tarefas, concluidas
from convidados import adicionar_convidado, convidados
from presentes import adicionar_presente, presentes

# Atualiza a lista de tarefas
def atualizar_checklist():
    checklist_listbox.delete(0, tk.END)
    for i, tarefa in enumerate(tarefas):
        status = "✅" if concluidas[i] else "❌"
        checklist_listbox.insert(tk.END, f"{i+1}. {tarefa} - {status}")

# Marca a tarefa selecionada como concluída
def marcar_tarefa():
    selecao = checklist_listbox.curselection()
    if selecao:
        indice = selecao[0]
        concluir_tarefa(indice)
        atualizar_checklist()

# Adiciona um novo convidado
def adicionar_convidado_gui():
    nome = entrada_convidado.get()
    if nome:
        adicionar_convidado(nome)
        entrada_convidado.delete(0, tk.END)
        atualizar_convidados()

# Atualiza a lista de convidados
def atualizar_convidados():
    convidados_listbox.delete(0, tk.END)
    for nome in convidados:
        convidados_listbox.insert(tk.END, nome)

# Adiciona um novo presente
def adicionar_presente_gui():
    nome = entrada_nome_presente.get()
    presente = entrada_presente.get()
    if nome and presente:
        adicionar_presente(nome, presente)
        entrada_nome_presente.delete(0, tk.END)
        entrada_presente.delete(0, tk.END)
        atualizar_presentes()

# Atualiza a lista de presentes
def atualizar_presentes():
    presentes_listbox.delete(0, tk.END)
    for p in presentes:
        presentes_listbox.insert(tk.END, f"{p['convidado']} - {p['presente']}")

# Janela principal
janela = tk.Tk()
janela.title("Organizador do Chá de Bebê")
janela.geometry("800x600")

# Frame do Checklist
frame_checklist = tk.LabelFrame(janela, text="Checklist")
frame_checklist.pack(fill="both", expand="yes", padx=10, pady=5)

checklist_listbox = tk.Listbox(frame_checklist, width=80)
checklist_listbox.pack(padx=5, pady=5)

botao_concluir = tk.Button(frame_checklist, text="Marcar como concluída", command=marcar_tarefa)
botao_concluir.pack(pady=5)

# Frame de Convidados
frame_convidados = tk.LabelFrame(janela, text="Convidados")
frame_convidados.pack(fill="both", expand="yes", padx=10, pady=5)

entrada_convidado = tk.Entry(frame_convidados, width=40)
entrada_convidado.pack(side="left", padx=5)
botao_add_convidado = tk.Button(frame_convidados, text="Adicionar", command=adicionar_convidado_gui)
botao_add_convidado.pack(side="left", padx=5)

convidados_listbox = tk.Listbox(frame_convidados, width=50)
convidados_listbox.pack(padx=5, pady=5)

# Frame de Presentes
frame_presentes = tk.LabelFrame(janela, text="Presentes Recebidos")
frame_presentes.pack(fill="both", expand="yes", padx=10, pady=5)

entrada_nome_presente = tk.Entry(frame_presentes, width=25)
entrada_nome_presente.insert(0, "Nome do convidado")
entrada_nome_presente.pack(side="left", padx=5)

entrada_presente = tk.Entry(frame_presentes, width=40)
entrada_presente.insert(0, "Presente dado")
entrada_presente.pack(side="left", padx=5)

botao_add_presente = tk.Button(frame_presentes, text="Adicionar Presente", command=adicionar_presente_gui)
botao_add_presente.pack(side="left", padx=5)

presentes_listbox = tk.Listbox(frame_presentes, width=80)
presentes_listbox.pack(padx=5, pady=5)

# Atualiza as listas ao iniciar
atualizar_checklist()
atualizar_convidados()
atualizar_presentes()

# Roda o aplicativo
janela.mainloop()
