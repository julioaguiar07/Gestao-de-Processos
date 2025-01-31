import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
import plotly.express as px
import requests 
import base64


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
    response = requests.post(url, json=payload)
    print(response.json())  # Para depuração

def verificar_prazos():
    cursor.execute('SELECT id, prazo_final, numero_processo FROM processos WHERE status = "Em andamento"')
    processos = cursor.fetchall()

    hoje = datetime.now()
    for processo in processos:
        prazo_final = datetime.strptime(processo[1], "%Y-%m-%d")
        dias_restantes = (prazo_final - hoje).days

        if 0 < dias_restantes <= 7:  
            mensagem = f"Queria te avisar que o processo nº {processo[2]} está próximo do prazo final ({prazo_final.strftime('%Y-%m-%d')}). Faltam {dias_restantes} dias."
            enviar_mensagem(mensagem)
            st.sidebar.success(f"Mensagem enviada para o processo nº {processo[2]}")
def gerar_relatorio_pdf(processos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for processo in processos:
        pdf.cell(200, 10, txt=f"Processo nº {processo[1]} - Responsável: {processo[5]} - Descrição: {processo[4]} - PRAZO FINAL: {processo[3]}", ln=True)
    pdf.output("relatorio.pdf")
    st.success("Relatório gerado com sucesso!")

def adicionar_tarefa(id_processo, descricao, data):
    cursor.execute('''
    INSERT INTO tarefas (id_processo, descricao, data)
    VALUES (?, ?, ?)
    ''', (id_processo, descricao, data))
    conn.commit()

def listar_tarefas(id_processo):
    cursor.execute('SELECT * FROM tarefas WHERE id_processo = ?', (id_processo,))
    return cursor.fetchall()

def adicionar_registro_financeiro(id_processo, tipo, valor, data, descricao):
    cursor.execute('''
    INSERT INTO financeiro (id_processo, tipo, valor, data, descricao)
    VALUES (?, ?, ?, ?, ?)
    ''', (id_processo, tipo, valor, data, descricao))
    conn.commit()

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

# Função para buscar processo na Brasil API
def buscar_processo_brasil_api(numero_processo):
    # Remove pontos e hífens para verificar se o restante são dígitos
    numero_limpo = numero_processo.replace(".", "").replace("-", "")
    
    # Verifica se o número do processo está no formato CNJ
    if not numero_processo or not numero_limpo.isdigit() or len(numero_limpo) != 20:
        st.error("Número do processo inválido. O número deve estar no formato CNJ (exemplo: 5001682-88.2020.8.13.0672).")
        return None

    url = f"https://brasilapi.com.br/api/cnj/v1/{numero_processo}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Levanta uma exceção para códigos de erro HTTP
        return response.json()  # Retorna os dados do processo
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            st.error("Processo não encontrado. Verifique o número do processo e tente novamente.")
        else:
            st.error(f"Erro ao consultar o processo: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"Erro de conexão: {e}")
    return None

# Interface do Streamlit
st.sidebar.title("Gestão de Processos 📂")
st.sidebar.text("Sistema de Gerenciamento")

opcao = st.sidebar.radio("Páginas", ["Início", "Cadastrar Processos", "Tarefas", "Relatórios", "Controle Financeiro"])

if opcao == "Início":
    st.image("logo.png", width=300)
    st.subheader("Consulta e Atualização de Processos")
    
    # Campo para buscar processo na Brasil API
    st.write("### Consultar Processo na Brasil API")
    numero_processo = st.text_input("Digite o número do processo (formato CNJ):")

    if st.button("Buscar Processo"):
        if numero_processo:
            dados_processo = buscar_processo_brasil_api(numero_processo)
            if dados_processo:
                st.write("### Dados do Processo")
                st.json(dados_processo)  # Exibe os dados em formato JSON
        else:
            st.error("Por favor, insira um número de processo válido.")

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
                st.experimental_rerun()

            if st.button("Excluir", key=f"excluir_{processo[0]}"):
                excluir_processo(processo[0])
                st.success("Processo excluído com sucesso!")
                st.experimental_rerun()

    # Verificar prazos
    if st.sidebar.button("Verificar Prazos"):
        verificar_prazos()
        st.sidebar.success("Verificação de prazos concluída!")

elif opcao == "Cadastrar Processos":
    st.title("Cadastrar Novo Processo")

    # Opção para escolher entre adicionar manualmente ou buscar automaticamente
    modo_cadastro = st.radio("Escolha o modo de cadastro:", ("Manual", "Automático (Brasil API)"))

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
                enviar_mensagem(f"Um novo processo de número {numero_processo} foi criado! O responsável por ele é: {responsavel}, sua situação: {status}, e sua descrição é: {descricao}. Prazo final: {prazo_final}.")

    elif modo_cadastro == "Automático (Brasil API)":
        with st.form("form_cadastro_automatico"):
            numero_processo = st.text_input("Nº do Processo (formato CNJ, ex: 0710802-55.2018.8.02.0001)")
            buscar = st.form_submit_button("Buscar Processo")

            if buscar:
                if not numero_processo:
                    st.error("Por favor, insira um número de processo válido.")
                else:
                    dados_processo = buscar_processo_brasil_api(numero_processo)
                    if dados_processo:
                        st.write("### Dados do Processo Encontrado")
                        st.write(f"**Número do Processo:** {dados_processo.get('numero')}")
                        st.write(f"**Classe:** {dados_processo.get('classe')}")
                        st.write(f"**Assunto:** {dados_processo.get('assunto')}")
                        st.write(f"**Órgão Julgador:** {dados_processo.get('orgao_julgador')}")
                        st.write(f"**Status:** {dados_processo.get('status')}")

                        # Preencher automaticamente o formulário de cadastro
                        data = datetime.now().strftime("%Y-%m-%d")
                        prazo_final = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")  # Prazo de 30 dias
                        descricao = f"Processo {dados_processo.get('numero')} - {dados_processo.get('assunto')}"
                        responsavel = "Responsável Padrão"  # Defina um responsável padrão ou permita a edição
                        status = "Em andamento"
                        prioridade = "Média"

                        if st.form_submit_button("Cadastrar com Dados da API"):
                            adicionar_processo(numero_processo, data, prazo_final, descricao, responsavel, status, prioridade)
                            st.success("Processo cadastrado com sucesso!")

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
        st.write(f"**Descrição:** {tarefa[2]} | **Data:** {tarefa[3]} | **Concluída:** {'Sim' if tarefa[4] else 'Não'}")

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
