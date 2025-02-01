import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
import plotly.express as px
import requests 
import base64
from streamlit_calendar import calendar



# Configuração de estilo
st.set_page_config(page_title="Gestão de Processos", layout="wide")
st.markdown(
    """
    <style>
    .main-container {
        background-color: #f9f9f9;
        padding: 20px;
    }
    .sidebar {
        background-color: #0E2C4E;
        color: white;
    }
    .process-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
        color: #333333;
    }
    .process-card h4 {
        color: #0E2C4E;
        margin: 0;
    }
    .metric-box {
        background-color: #CF8C28;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-box h3 {
        margin: 0;
        color: #ffffff;
        font-size: 24px;
        font-weight: bold;
    }
    .metric-box p {
        margin: 0;
        font-size: 20px;
        color: #ffffff;
    }
    .stButton button {
        background-color: #0E2C4E;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stButton button:hover {
        background-color: #CF8C28;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Conectar ao banco de dados
conn = sqlite3.connect('gestao_processos.db')
cursor = conn.cursor()

# Criar tabela de processos
cursor.execute('''
CREATE TABLE IF NOT EXISTS processos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_processo TEXT NOT NULL,
    data TEXT NOT NULL,
    prazo_final TEXT NOT NULL,
    descricao TEXT NOT NULL,
    responsavel TEXT NOT NULL,
    status TEXT NOT NULL,
    prioridade TEXT NOT NULL
)
''')

# Criar tabela de tarefas
cursor.execute('''
CREATE TABLE IF NOT EXISTS tarefas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_processo INTEGER NOT NULL,
    descricao TEXT NOT NULL,
    data TEXT NOT NULL,
    concluida INTEGER DEFAULT 0
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS financeiro (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_processo INTEGER NOT NULL,
    tipo TEXT NOT NULL,  -- Honorário, Pagamento, Despesa
    valor REAL NOT NULL,
    data TEXT NOT NULL,
    descricao TEXT
)
''')

CREATE TABLE IF NOT EXISTS documentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_processo INTEGER NOT NULL,
    nome_arquivo TEXT NOT NULL,
    caminho_arquivo TEXT NOT NULL,
    data_upload TEXT NOT NULL
)
''')

conn.commit()

def get_base64(file_path):
    with open(file_path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode()
    return encoded

background_image = get_base64("fundo.png")

st.markdown(
    f"""
    <style>
        .stApp {{
            background: url("data:image/png;base64,{background_image}");
            background-size: cover;
            background-position: center;
        }}
    </style>
    """,
    unsafe_allow_html=True
)
# Funções do sistema
def adicionar_processo(numero_processo, data, prazo_final, descricao, responsavel, status, prioridade):
    cursor.execute('''
    INSERT INTO processos (numero_processo, data, prazo_final, descricao, responsavel, status, prioridade)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (numero_processo, data, prazo_final, descricao, responsavel, status, prioridade))
    conn.commit()

def excluir_processo(id_processo):
    cursor.execute('DELETE FROM processos WHERE id = ?', (id_processo,))
    conn.commit()

def buscar_processos(numero_processo=None, status=None, responsavel=None, prioridade=None):
    query = 'SELECT * FROM processos WHERE 1=1'
    params = []
    if numero_processo:
        query += ' AND numero_processo = ?'
        params.append(numero_processo)
    if status:
        query += ' AND status = ?'
        params.append(status)
    if responsavel:
        query += ' AND responsavel = ?'
        params.append(responsavel)
    if prioridade:
        query += ' AND prioridade = ?'
        params.append(prioridade)
    cursor.execute(query, tuple(params))
    return cursor.fetchall()

def atualizar_processo(id_processo, novo_status):
    cursor.execute('UPDATE processos SET status = ? WHERE id = ?', (novo_status, id_processo))
    conn.commit()

def contar_processos_por_status():
    cursor.execute('SELECT status, COUNT(*) FROM processos GROUP BY status')
    return {status: count for status, count in cursor.fetchall()}


TOKEN = "7675741218:AAHTrrWDS05aiSq2qY3vcrAhsLNLRaz9dhI"
CHAT_ID = "-1002371255186"

def enviar_mensagem(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Verifica se a requisição foi bem-sucedida
        print("Mensagem enviada com sucesso:", response.json())  # Log para depuração
    except requests.exceptions.RequestException as e:
        print("Erro ao enviar mensagem:", e)  # Log para depuração

def excluir_tarefa(id_tarefa):
    cursor.execute('DELETE FROM tarefas WHERE id = ?', (id_tarefa,))
    conn.commit()

# Função para verificar prazos
def verificar_prazos():
    # Busca todos os processos
    cursor.execute('SELECT id, prazo_final, numero_processo, status FROM processos')
    processos = cursor.fetchall()
    print(f"Total de processos encontrados: {len(processos)}")  # Log para depuração

    hoje = datetime.now()
    mensagens_enviadas = 0  # Contador de mensagens enviadas

    for processo in processos:
        prazo_final = datetime.strptime(processo[1], "%Y-%m-%d")
        dias_restantes = (prazo_final - hoje).days
        print(f"Processo {processo[2]} (Status: {processo[3]}): {dias_restantes} dias restantes")  # Log para depuração

        # Verifica se o prazo está entre 0 e 7 dias
        if 0 <= dias_restantes <= 7:
            mensagem = f"""
🚨 Alerta de Prazo 🚨

📋 Processo: #{processo[2]}  
📌 Status: {processo[3]}  
📅 Prazo Final: {prazo_final.strftime('%Y-%m-%d')}  
⏳ Dias Restantes: {'**HOJE**' if dias_restantes == 0 else f'{dias_restantes} dia(s)'}

⚠️ **Atenção:** Este processo está próximo do prazo final. Tome as providências necessárias.
"""
            print(f"Mensagem a ser enviada: {mensagem}")  # Log para depuração
            try:
                enviar_mensagem(mensagem)
                st.sidebar.success(f"Mensagem enviada para o processo nº {processo[2]}")
                mensagens_enviadas += 1  # Incrementa o contador
            except Exception as e:
                print(f"Erro ao enviar mensagem: {e}")  # Log para depuração
                st.sidebar.error(f"Erro ao enviar mensagem para o processo nº {processo[2]}")

    # Confirmação final
    if mensagens_enviadas > 0:
        st.sidebar.success(f"Total de mensagens enviadas: {mensagens_enviadas}")
    else:
        st.sidebar.warning("Nenhum processo próximo do prazo foi encontrado.")
def gerar_relatorio_pdf(processos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for processo in processos:
        pdf.cell(200, 10, txt=f"Processo nº {processo[1]} - Responsável: {processo[5]} - Descrição: {processo[4]} - PRAZO FINAL: {processo[3]}", ln=True)
    pdf.output("relatorio.pdf")
    st.success("Relatório gerado com sucesso!")

def excluir_registro_financeiro(id_registro):
    cursor.execute('DELETE FROM financeiro WHERE id = ?', (id_registro,))
    conn.commit()

def adicionar_tarefa(id_processo, descricao, data):
    cursor.execute('''
    INSERT INTO tarefas (id_processo, descricao, data)
    VALUES (?, ?, ?)
    ''', (id_processo, descricao, data))
    conn.commit()
    # Enviar mensagem via Telegram
    mensagem = f"""
✅ Nova Tarefa Criada ✅

📋 Processo ID: #{id_processo}  
📝 Descrição: {descricao}  
📅 Data: {data}

⚠️ **Atenção:** Não se esqueça de realizar essa tarefa dentro do prazo!
"""
    enviar_mensagem(mensagem)

def listar_tarefas(id_processo):
    cursor.execute('SELECT * FROM tarefas WHERE id_processo = ?', (id_processo,))
    return cursor.fetchall()

def adicionar_registro_financeiro(id_processo, tipo, valor, data, descricao):
    cursor.execute('''
    INSERT INTO financeiro (id_processo, tipo, valor, data, descricao)
    VALUES (?, ?, ?, ?, ?)
    ''', (id_processo, tipo, valor, data, descricao))
    conn.commit()
    # Enviar mensagem via Telegram
    mensagem = f"""
💰 Novo Registro Financeiro 💰

📋 Processo ID: {id_processo}  
📌 Tipo: {tipo}  
💵 Valor: R$ {valor:.2f}  
📅 Data: {data}  
📝 Descrição: {descricao}

⚠️ **Atenção:** Registro financeiro adicionado com sucesso. Verifique as métricas atualizadas.
"""
    enviar_mensagem(mensagem)

def listar_registros_financeiros(id_processo=None):
    query = 'SELECT * FROM financeiro'
    params = []
    if id_processo:
        query += ' WHERE id_processo = ?'
        params.append(id_processo)
    cursor.execute(query, tuple(params))
    return cursor.fetchall()

def calcular_total_financeiro():
    cursor.execute('SELECT tipo, SUM(valor) FROM financeiro GROUP BY tipo')
    return {tipo: total for tipo, total in cursor.fetchall()}

# Função para adicionar documento
def adicionar_documento(id_processo, nome_arquivo, caminho_arquivo):
    data_upload = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
    INSERT INTO documentos (id_processo, nome_arquivo, caminho_arquivo, data_upload)
    VALUES (?, ?, ?, ?)
    ''', (id_processo, nome_arquivo, caminho_arquivo, data_upload))
    conn.commit()

# Função para listar documentos de um processo
def listar_documentos(id_processo):
    cursor.execute('SELECT * FROM documentos WHERE id_processo = ?', (id_processo,))
    return cursor.fetchall()

# Função para excluir documento
def excluir_documento(id_documento):
    cursor.execute('DELETE FROM documentos WHERE id = ?', (id_documento,))
    conn.commit()
    
def buscar_eventos():
    cursor.execute('''
    SELECT id, numero_processo, prazo_final, descricao, status
    FROM processos
    WHERE prazo_final IS NOT NULL
''')  # <-- Fechamento correto
    processos = cursor.fetchall()
    eventos = []
    for processo in processos:
        eventos.append({
            "title": f"Prazo: {processo[1]} - {processo[3]}",
            "start": processo[2],
            "end": processo[2],
            "resourceId": processo[0],
            "color": "#FF6B6B" if processo[4] == "Aguardando" else "#4ECDC4"
        })
    return eventos
# Interface do Streamlit
st.sidebar.title("Gestão de Processos 📂")
st.sidebar.text("Sistema de Gerenciamento")

opcao = st.sidebar.radio("Páginas", ["Início", "Cadastrar Processos", "Tarefas", "Relatórios", "Controle Financeiro"])

if opcao == "Início":
    st.image("logo.png", width=300)
    st.subheader("Consulta e Atualização de Processos")


    # Filtros
    st.write("### Filtrar Processos")
    filtro_status = st.selectbox("Filtrar por Situação", ["",
                                        "Aguardando Audiência",
                                        "Aguardando Citação",
                                        "Aguardando Diligência",
                                        "Aguardando Manifestação das Partes",
                                        "Aguardando Pagamento",
                                        "Aguardando Perícia",
                                        "Aguardando Provas",
                                        "Aguardando Recurso",
                                        "Aguardando Resposta do Réu",
                                        "Aguardando Sentença",
                                        "Arquivado",
                                        "Audiência Realizada – Aguardando Decisão",
                                        "Baixado",
                                        "Decisão Transitada em Julgado",
                                        "Desistência",
                                        "Distribuído",
                                        "Em Andamento",
                                        "Em Cumprimento de Acordo",
                                        "Em Fase Recursal",
                                        "Em Execução de Sentença",
                                        "Extinto sem Resolução do Mérito",
                                        "Finalizado",
                                        "Homologado Acordo",
                                        "Improcedente",
                                        "Parcialmente Procedente",
                                        "Procedente",
                                        "Sentença Proferida",
                                        "Suspenso"])
    filtro_responsavel = st.text_input("Buscar por Responsável")
    filtro_prioridade = st.selectbox("Filtrar por Prioridade", ["", "Alta", "Média", "Baixa"])

    resultados = buscar_processos(
        status=filtro_status if filtro_status else None,
        responsavel=filtro_responsavel if filtro_responsavel else None,
        prioridade=filtro_prioridade if filtro_prioridade else None
    )

    # Exibir processos
    st.write("### Processos Encontrados")
    for processo in resultados:
        with st.expander(f"Processo nº {processo[1]} - Responsável: {processo[5]}"):
            st.write(f"**Data:** {processo[2]}")
            st.write(f"**Prazo Final:** {processo[3]}")
            st.write(f"**Descrição:** {processo[4]}")
            st.write(f"**Status Atual:** {processo[6]}")
            st.write(f"**Prioridade:** {processo[7]}")

            novo_status = st.selectbox("Atualizar Status", [                                        
                                        "Aguardando Audiência",
                                        "Aguardando Citação",
                                        "Aguardando Diligência",
                                        "Aguardando Manifestação das Partes",
                                        "Aguardando Pagamento",
                                        "Aguardando Perícia",
                                        "Aguardando Provas",
                                        "Aguardando Recurso",
                                        "Aguardando Resposta do Réu",
                                        "Aguardando Sentença",
                                        "Arquivado",
                                        "Audiência Realizada – Aguardando Decisão",
                                        "Baixado",
                                        "Decisão Transitada em Julgado",
                                        "Desistência",
                                        "Distribuído",
                                        "Em Andamento",
                                        "Em Cumprimento de Acordo",
                                        "Em Fase Recursal",
                                        "Em Execução de Sentença",
                                        "Extinto sem Resolução do Mérito",
                                        "Finalizado",
                                        "Homologado Acordo",
                                        "Improcedente",
                                        "Parcialmente Procedente",
                                        "Procedente",
                                        "Sentença Proferida",
                                        "Suspenso"], key=f"status_{processo[0]}")
            if st.button("Atualizar", key=f"atualizar_{processo[0]}"):
                atualizar_processo(processo[0], novo_status)
                st.success("Status atualizado com sucesso!")


            if st.button("Excluir", key=f"excluir_{processo[0]}"):
                excluir_processo(processo[0])
                st.success("Processo excluído com sucesso!")


    # Verificar prazos
    if st.sidebar.button("Verificar Prazos"):
        verificar_prazos()
        st.sidebar.success("Verificação de prazos concluída!")

elif opcao == "Cadastrar Processos":
    st.title("Cadastrar Novo Processo")

    # Opção para escolher entre adicionar manualmente ou buscar automaticamente
    modo_cadastro = st.radio("Escolha o modo de cadastro:", ("Manual"))

    if modo_cadastro == "Manual":
        with st.form("form_cadastro_manual"):
            numero_processo = st.text_input("Nº do Processo")
            data = st.text_input("Data (ex: 2022-10-11)")
            prazo_final = st.text_input("Prazo Final (ex: 2023-09-03)")
            descricao = st.text_input("Descrição")
            responsavel = st.text_input("Responsável")
            status = st.selectbox("Situação", [
                                "Aguardando Audiência",
                                "Aguardando Citação",
                                "Aguardando Diligência",
                                "Aguardando Manifestação das Partes",
                                "Aguardando Pagamento",
                                "Aguardando Perícia",
                                "Aguardando Provas",
                                "Aguardando Recurso",
                                "Aguardando Resposta do Réu",
                                "Aguardando Sentença",
                                "Arquivado",
                                "Audiência Realizada – Aguardando Decisão",
                                "Baixado",
                                "Decisão Transitada em Julgado",
                                "Desistência",
                                "Distribuído",
                                "Em Andamento",
                                "Em Cumprimento de Acordo",
                                "Em Fase Recursal",
                                "Em Execução de Sentença",
                                "Extinto sem Resolução do Mérito",
                                "Finalizado",
                                "Homologado Acordo",
                                "Improcedente",
                                "Parcialmente Procedente",
                                "Procedente",
                                "Sentença Proferida",
                                "Suspenso"
                            ])
            prioridade = st.selectbox("Prioridade", ["Alta", "Média", "Baixa"])
            enviar = st.form_submit_button("Cadastrar Processo")

            if enviar:
                adicionar_processo(numero_processo, data, prazo_final, descricao, responsavel, status, prioridade)
                st.success("Processo cadastrado com sucesso!")
    
                # Mensagem formatada para o Telegram
                mensagem = f"""
🧑‍⚖️ Processo Novo Criado! 🧑‍⚖️

📋 Processo: {numero_processo}  
📌 Situação: {status}  
🤵🏻 Responsável(s): {responsavel}
📅 Prazo Final: {prazo_final}  
🚩 Prioridade: {prioridade}  
"""
                print(f"Mensagem a ser enviada: {mensagem}")  # Log para depuração
                try:
                    enviar_mensagem(mensagem)
                    st.sidebar.success(f"Mensagem enviada para o processo nº {numero_processo}")
                except Exception as e:
                    print(f"Erro ao enviar mensagem: {e}")  # Log para depuração
                    st.sidebar.error(f"Erro ao enviar mensagem para o processo nº {numero_processo}")


elif opcao == "Tarefas":
    st.title("Gestão de Tarefas")
    id_processo = st.number_input("ID do Processo", min_value=1)
    descricao = st.text_input("Descrição da Tarefa")
    data_tarefa = st.text_input("Data da Tarefa (ex: 2023-09-03)")
    if st.button("Adicionar Tarefa"):
        adicionar_tarefa(id_processo, descricao, data_tarefa)
        st.success("Tarefa adicionada com sucesso!")

    st.write("### Tarefas do Processo")
    tarefas = listar_tarefas(id_processo)
    for tarefa in tarefas:
        st.write(f"**ID:** {tarefa[0]} | **Descrição:** {tarefa[2]} | **Data:** {tarefa[3]} | **Concluída:** {'Sim' if tarefa[4] else 'Não'}")

    # Adicionar funcionalidade de exclusão de tarefas
    st.write("### Excluir Tarefa")
    id_tarefa_excluir = st.number_input("ID da Tarefa para Excluir", min_value=1, key="excluir_tarefa")
    if st.button("Excluir Tarefa", key="excluir_tarefa_botao"):
        excluir_tarefa(id_tarefa_excluir)
        st.success("Tarefa excluída com sucesso!")
        st.button("Recarregar Página")  


elif opcao == "Relatórios":
    st.title("Relatórios")
    if st.button("Gerar Relatório PDF"):
        processos = buscar_processos()
        gerar_relatorio_pdf(processos)
        st.success("Relatório gerado com sucesso!")

elif opcao == "Controle Financeiro":
    st.title("Controle Financeiro 💰")
    st.markdown("---")

    # Adicionar Registro Financeiro
    with st.expander("Adicionar Registro Financeiro"):
        id_processo = st.number_input("ID do Processo", min_value=1, key="financeiro_id_processo")
        tipo = st.selectbox("Tipo", ["Honorário", "Pagamento", "Despesa"], key="financeiro_tipo")
        valor = st.number_input("Valor", min_value=0.0, key="financeiro_valor")
        data = st.text_input("Data (ex: 2023-09-03)", key="financeiro_data")
        descricao = st.text_input("Descrição", key="financeiro_descricao")
        if st.button("Adicionar Registro", key="financeiro_adicionar"):
            adicionar_registro_financeiro(id_processo, tipo, valor, data, descricao)
            st.success("Registro financeiro adicionado com sucesso!")

    # Exibir Registros Financeiros
    st.write("### Registros Financeiros")
    registros = listar_registros_financeiros()
    if registros:
        df_financeiro = pd.DataFrame(registros, columns=["ID", "ID Processo", "Tipo", "Valor", "Data", "Descrição"])
        st.dataframe(df_financeiro)

        # Adicionar botão de exclusão para cada registro
        st.write("### Excluir Registro Financeiro")
        id_registro_excluir = st.number_input("ID do Registro para Excluir", min_value=1, key="excluir_registro")
        if st.button("Excluir Registro", key="excluir_registro_botao"):
            excluir_registro_financeiro(id_registro_excluir)
            st.success("Registro financeiro excluído com sucesso!")
            st.button("Recarregar Página")  # Adiciona um botão para recarregar manualmente
    else:
        st.info("Nenhum registro financeiro encontrado.")

    # Métricas Financeiras
    st.markdown("---")
    st.write("### Métricas Financeiras")
    totais = calcular_total_financeiro()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Honorários", f"R$ {totais.get('Honorário', 0):.2f}")
    col2.metric("Total Pagamentos", f"R$ {totais.get('Pagamento', 0):.2f}")
    col3.metric("Total Despesas", f"R$ {totais.get('Despesa', 0):.2f}")

    # Gráficos
    st.markdown("---")
    st.write("### Gráficos Financeiros")
    if registros:
        df_financeiro = pd.DataFrame(registros, columns=["ID", "ID Processo", "Tipo", "Valor", "Data", "Descrição"])
        
        # Gráfico de Pizza (Distribuição por Tipo)
        st.write("#### Distribuição por Tipo")
        fig_pie = px.pie(df_financeiro, names="Tipo", values="Valor", title="Distribuição de Valores por Tipo")
        st.plotly_chart(fig_pie)

        # Gráfico de Barras (Valores por Processo)
        st.write("#### Valores por Processo")
        df_processo = df_financeiro.groupby("ID Processo")["Valor"].sum().reset_index()
        fig_bar = px.bar(df_processo, x="ID Processo", y="Valor", title="Valores por Processo")
        st.plotly_chart(fig_bar)
    else:
        st.info("Nenhum dado disponível para exibir gráficos.")

elif opcao == "Gestão de Documentos":
    st.title("Gestão de Documentos 📂")
    id_processo = st.number_input("ID do Processo", min_value=1, key="documentos_id_processo")

    # Upload de Documentos
    st.write("### Adicionar Documento")
    uploaded_file = st.file_uploader("Escolha um arquivo", type=["pdf", "docx", "xlsx", "txt"])
    if uploaded_file is not None:
        nome_arquivo = uploaded_file.name
        caminho_arquivo = f"documentos/{id_processo}_{nome_arquivo}"
        with open(caminho_arquivo, "wb") as f:
            f.write(uploaded_file.getbuffer())
        adicionar_documento(id_processo, nome_arquivo, caminho_arquivo)
        st.success("Documento adicionado com sucesso!")

    # Listar Documentos
    st.write("### Documentos do Processo")
    documentos = listar_documentos(id_processo)
    if documentos:
        for doc in documentos:
            st.write(f"**ID:** {doc[0]} | **Nome:** {doc[2]} | **Data de Upload:** {doc[4]}")
            with open(doc[3], "rb") as f:
                st.download_button(
                    label="Baixar Documento",
                    data=f,
                    file_name=doc[2],
                    mime="application/octet-stream"
                )
            if st.button(f"Excluir Documento {doc[0]}", key=f"excluir_doc_{doc[0]}"):
                excluir_documento(doc[0])
                st.success("Documento excluído com sucesso!")
                st.experimental_rerun()  # Recarregar a página
    else:
        st.info("Nenhum documento encontrado para este processo.")

elif opcao == "Calendário de Prazos e Audiências":
    st.title("Calendário de Prazos e Audiências 📅")
    eventos = buscar_eventos()

    # Configuração do calendário
    calendar_options = {
        "editable": "true",
        "selectable": "true",
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "resourceTimelineDay,resourceTimelineWeek,resourceTimelineMonth",
        },
        "initialView": "resourceTimelineMonth",
        "resourceGroupField": "resourceId",
    }

    # Exibir calendário
    calendar_result = calendar(
        events=eventos,
        options=calendar_options,
        key="calendario"
    )

    # Exibir detalhes do evento selecionado
    if calendar_result.get("eventClick"):
        evento = calendar_result["eventClick"]["event"]
        st.write(f"### Detalhes do Evento")
        st.write(f"**Processo:** {evento['title']}")
        st.write(f"**Data:** {evento['start']}")
        st.write(f"**Status:** {'Aguardando' if evento['color'] == '#FF6B6B' else 'Concluído'}")
