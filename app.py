import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Caminho do arquivo Excel existente
EXCEL_PATH = "Controle Transferencia.xlsx"
SHEET_NAME = "Basae"

st.set_page_config(page_title="Registro Transferência", layout="centered")
st.title("🚚 Registro de Transferência de Carga")

# Função para registrar timestamp atual
def registrar_tempo(label):
    if st.button(f"Registrar {label}"):
        st.session_state[label] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Inicializar variáveis de sessão
campos_tempo = [
    "Entrada na Fábrica", "Encostou na doca Fábrica", "Início carregamento", "Fim carregamento",
    "Faturado", "Amarração carga", "Saída do pátio", "Entrada CD", "Encostou na doca CD",
    "Início Descarregamento CD", "Fim Descarregamento CD", "Saída CD"
]

for campo in campos_tempo:
    if campo not in st.session_state:
        st.session_state[campo] = ""

# Campos manuais
st.subheader("Dados do Veículo")
data = st.date_input("Data", value=datetime.today())
placa = st.text_input("Placa do caminhão")
conferente = st.text_input("Nome do conferente")

# Campos com botoes
st.subheader("Fábrica")
for campo in campos_tempo[:7]:
    registrar_tempo(campo)
    st.text_input(campo, value=st.session_state[campo], disabled=True)

st.subheader("Centro de Distribuição (CD)")
for campo in campos_tempo[7:]:
    registrar_tempo(campo)
    st.text_input(campo, value=st.session_state[campo], disabled=True)

# Calcular tempos automáticos
def calc_tempo(fim, inicio):
    try:
        t1 = datetime.strptime(st.session_state[fim], "%Y-%m-%d %H:%M:%S")
        t0 = datetime.strptime(st.session_state[inicio], "%Y-%m-%d %H:%M:%S")
        return str(t1 - t0)
    except:
        return ""

# Campos calculados
tempo_carreg = calc_tempo("Fim carregamento", "Início carregamento")
tempo_espera = calc_tempo("Encostou na doca Fábrica", "Entrada na Fábrica")
tempo_total = calc_tempo("Saída do pátio", "Entrada na Fábrica")
tempo_descarga = calc_tempo("Fim Descarregamento CD", "Início Descarregamento CD")
tempo_espera_cd = calc_tempo("Encostou na doca CD", "Entrada CD")
tempo_total_cd = calc_tempo("Saída CD", "Entrada CD")
tempo_percurso = calc_tempo("Entrada CD", "Saída do pátio")

# Botão para salvar
if st.button("✅ Salvar Registro"):
    nova_linha = {
        "Data": data,
        "Placa do caminhão": placa,
        "Nome do conferente": conferente,
        **{campo: st.session_state[campo] for campo in campos_tempo},
        "Tempo de Carregamento": tempo_carreg,
        "Tempo Espera Doca": tempo_espera,
        "Tempo Total": tempo_total,
        "Tempo de Descarregamento CD": tempo_descarga,
        "Tempo Espera Doca CD": tempo_espera_cd,
        "Tempo Total CD": tempo_total_cd,
        "Tempo Percurso Para CD": tempo_percurso,
    }

    if os.path.exists(EXCEL_PATH):
        df_existente = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
        df_novo = pd.concat([df_existente, pd.DataFrame([nova_linha])], ignore_index=True)
    else:
        df_novo = pd.DataFrame([nova_linha])

    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
        df_novo.to_excel(writer, sheet_name=SHEET_NAME, index=False)

    st.success("Registro salvo com sucesso!")

    # Resetar campos
    for campo in campos_tempo:
        st.session_state[campo] = ""