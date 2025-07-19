import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

# Configurações
EXCEL_PATH = "Controle Transferencia.xlsx"
SHEET_NAME = "Basae"
FUSO_HORARIO = timezone(timedelta(hours=-3))  # UTC-3

campos_tempo = [
    "Entrada na Fábrica", "Encostou na doca Fábrica", "Início carregamento",
    "Fim carregamento", "Faturado", "Amarração carga", "Saída do pátio",
    "Entrada CD", "Encostou na doca CD", "Início Descarregamento CD",
    "Fim Descarregamento CD", "Saída CD"
]

# Campos de cálculo que devem ser salvos
campos_calculados = [
    "Tempo Espera Doca", "Tempo Total", "Tempo de Descarregamento CD",
    "Tempo Espera Doca CD", "Tempo Total CD", "Tempo Percurso Para CD", "Tempo de Carregamento"
]

# Inicializa session_state para os campos de tempo
for campo in campos_tempo:
    if campo not in st.session_state:
        st.session_state[campo] = ""

# Inicializa página atual se não existir
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "Tela Inicial"

# Configuração da página
st.set_page_config(
    page_title="Suzano - Controle de Carga", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado para melhorar a aparência
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f4e79;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 30px;
        padding: 20px;
        background: linear-gradient(90deg, #e8f4f8 0%, #f0f8ff 100%);
        border-radius: 10px;
        border-left: 5px solid #1f4e79;
    }
    
    .big-button {
        width: 100%;
        height: 80px;
        font-size: 18px;
        font-weight: bold;
        margin: 10px 0;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .btn-primary {
        background: linear-gradient(45deg, #2e8b57, #3cb371);
        color: white;
    }
    
    .btn-secondary {
        background: linear-gradient(45deg, #4682b4, #5f9ea0);
        color: white;
    }
    
    .btn-info {
        background: linear-gradient(45deg, #ff8c00, #ffa500);
        color: white;
    }
    
    .btn-warning {
        background: linear-gradient(45deg, #dc143c, #ff6347);
        color: white;
    }
    
    .back-button {
        background: linear-gradient(45deg, #696969, #808080);
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    .status-card {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid;
    }
    
    .status-success {
        background-color: #d4edda;
        border-color: #28a745;
        color: #155724;
    }
    
    .status-warning {
        background-color: #fff3cd;
        border-color: #ffc107;
        color: #856404;
    }
    
    .status-info {
        background-color: #d1ecf1;
        border-color: #17a2b8;
        color: #0c5460;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 10px 0;
    }
    
    .section-header {
        color: #1f4e79;
        font-size: 20px;
        font-weight: bold;
        margin: 20px 0 10px 0;
        padding-bottom: 5px;
        border-bottom: 2px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Função para calcular diferença de tempo
def calcular_tempo(inicio, fim):
    if pd.isna(inicio) or pd.isna(fim) or inicio == "" or fim == "":
        return ""
    try:
        inicio_dt = pd.to_datetime(inicio)
        fim_dt = pd.to_datetime(fim)
        diff = fim_dt - inicio_dt
        horas = int(diff.total_seconds() // 3600)
        minutos = int((diff.total_seconds() % 3600) // 60)
        return f"{horas:02d}:{minutos:02d}"
    except:
        return ""

# Função para encontrar o último campo preenchido (status)
def obter_status(registro):
    for campo in reversed(campos_tempo):
        if not pd.isna(registro[campo]) and registro[campo] != "":
            return campo
    return "Não iniciado"

# Função para botão de voltar
def botao_voltar():
    if st.button("⬅️ Voltar ao Menu Principal", key="btn_voltar", help="Clique para voltar à tela inicial"):
        st.session_state.pagina_atual = "Tela Inicial"
        st.rerun()

# Header principal
st.markdown('<div class="main-header">🚚 Suzano - Controle de Transferência de Carga</div>', unsafe_allow_html=True)

# TELA INICIAL COM BOTÕES
if st.session_state.pagina_atual == "Tela Inicial":
    st.markdown('<div class="section-header">📋 Escolha uma opção:</div>', unsafe_allow_html=True)
    
    # Layout em colunas para os botões principais
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🆕 NOVO REGISTRO", key="btn_novo", help="Registrar uma nova transferência de carga", use_container_width=True):
            st.session_state.pagina_atual = "Lançar Novo Controle"
            st.rerun()
        
        if st.button("📊 EM OPERAÇÃO", key="btn_operacao", help="Ver cargas em andamento", use_container_width=True):
            st.session_state.pagina_atual = "Em Operação"
            st.rerun()
    
    with col2:
        if st.button("✏️ EDITAR REGISTRO", key="btn_editar", help="Editar registros incompletos", use_container_width=True):
            st.session_state.pagina_atual = "Editar Lançamentos Incom
