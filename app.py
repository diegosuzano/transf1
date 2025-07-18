import streamlit as st
import pandas as pd
from datetime import datetime
import os

ARQUIVO = "Controle Transferencia.xlsx"
CAMPOS = [
    "Data",
    "Placa",
    "Entrada no pátio",
    "Encostou na doca",
    "Início carregamento",
    "Fim carregamento",
    "Faturado",
    "Amarração carga",
    "Saída CD"
]

# Funções auxiliares
def carregar_dados():
    if os.path.exists(ARQUIVO):
        return pd.read_excel(ARQUIVO)
    else:
        return pd.DataFrame(columns=CAMPOS)

def salvar_dados(df):
    df.to_excel(ARQUIVO, index=False)

def registrar_lancamento():
    st.subheader("Lancar Novo Controle")
    with st.form("form_lancamento"):
        placa = st.text_input("Placa")
        if placa:
            campos = {campo: "" for campo in CAMPOS[2:]}
            campos["Data"] = datetime.now().strftime("%d/%m/%Y")
            campos["Placa"] = placa.upper()
            for campo in campos:
                if campo not in ["Data", "Placa"]:
                    if st.form_submit_button(f"Registrar agora - {campo}"):
                        df = carregar_dados()
                        novo = campos.copy()
                        novo[campo] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
                        salvar_dados(df)
                        st.success(f"Registrado: {campo}")
                        st.experimental_rerun()


def editar_lancamentos():
    st.subheader("Editar Lançamentos Incompletos")
    df = carregar_dados()
    df_incompleto = df[df["Saída CD"].isna() | (df["Saída CD"] == "")]

    if df_incompleto.empty:
        st.info("Nenhum registro incompleto encontrado.")
        return

    placas = df_incompleto["Placa"].unique()
    placa_sel = st.selectbox("Selecione a Placa", placas)
    registros = df_incompleto[df_incompleto["Placa"] == placa_sel].copy()

    for idx, row in registros.iterrows():
        st.markdown(f"### Registro {idx+1}")
        for campo in CAMPOS[2:]:
            valor_atual = row[campo]
            if pd.isna(valor_atual) or valor_atual == "":
                if st.button(f"Registrar agora - {campo} (linha {idx})"):
                    df.at[idx, campo] = datetime.now().strftime("%d/%m/%Y %H:%M")
                    salvar_dados(df)
                    st.success(f"Campo {campo} atualizado para a placa {placa_sel}")
                    st.experimental_rerun()


def em_operacao():
    st.subheader("Em Operação")
    df = carregar_dados()
    em_proc = df[df["Saída CD"].isna() | (df["Saída CD"] == "")].copy()

    if em_proc.empty:
        st.info("Nenhum veículo em operação.")
        return

    def ultimo_campo_preenchido(row):
        for campo in reversed(CAMPOS[2:]):
            if pd.notna(row[campo]) and row[campo] != "":
                return campo
        return "Início"

    def calcular_tempo(inicio, fim):
        if pd.notna(inicio) and pd.notna(fim):
            try:
                t1 = pd.to_datetime(inicio, dayfirst=True)
                t2 = pd.to_datetime(fim, dayfirst=True)
                return str(t2 - t1)
            except:
                return "-"
        return "-"

    agora = datetime.now()
    em_proc["Status"] = em_proc.apply(ultimo_campo_preenchido, axis=1)
    em_proc["Tempo Carregamento"] = em_proc.apply(lambda r: calcular_tempo(r["Início carregamento"], r["Fim carregamento"]), axis=1)
    em_proc["Tempo Total"] = em_proc.apply(lambda r: calcular_tempo(r["Entrada no pátio"], agora), axis=1)
    em_proc["Tempo Percurso para CD"] = em_proc.apply(lambda r: calcular_tempo(r["Fim carregamento"], r["Faturado"]), axis=1)
    em_proc["Tempo Descarregamento CD"] = em_proc.apply(lambda r: calcular_tempo(r["Amarração carga"], r["Saída CD"]), axis=1)
    em_proc["Tempo Total CD"] = em_proc.apply(lambda r: calcular_tempo(r["Faturado"], r["Saída CD"]), axis=1)

    st.dataframe(em_proc[["Placa", "Status", "Tempo Carregamento", "Tempo Total", "Tempo Percurso para CD", "Tempo Descarregamento CD", "Tempo Total CD"]])

# Interface principal
st.title("Controle de Transferências")

opcao = st.selectbox("Escolha a opção:", [
    "Lancar Novo Controle",
    "Editar Lançamentos Incompletos",
    "Em Operação"
])

if opcao == "Lancar Novo Controle":
    registrar_lancamento()
elif opcao == "Editar Lançamentos Incompletos":
    editar_lancamentos()
elif opcao == "Em Operação":
    em_operacao()
