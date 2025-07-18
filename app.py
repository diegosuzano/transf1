import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import base64
import requests

# CONFIG
EXCEL_PATH = "Controle Transferencia.xlsx"
SHEET_NAME = "Basae"
FUSO_HORARIO = timezone(timedelta(hours=-3))  # UTC-3

# CAMPOS PADRÃO
campos_tempo = [
    "Entrada na Fábrica", "Encostou na doca Fábrica", "Início carregamento",
    "Fim carregamento", "Faturado", "Amarração carga", "Saída do pátio",
    "Entrada CD", "Encostou na doca CD", "Início Descarregamento CD",
    "Fim Descarregamento CD", "Saída CD"
]

# Inicializa valores no session_state
for campo in campos_tempo:
    if campo not in st.session_state:
        st.session_state[campo] = ""

# Configura página
st.set_page_config(page_title="Registro Transferência", layout="centered")
st.title("🚚 Registro de Transferência de Carga")

# Menu simples
pagina = st.selectbox("📌 Escolha uma opção", ["Tela Inicial", "Lançar Novo Controle", "Editar Lançamentos Incompletos"])

if pagina == "Tela Inicial":
    st.subheader("O que deseja fazer?")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Baixar Arquivo"):
            if os.path.exists(EXCEL_PATH):
                with open(EXCEL_PATH, "rb") as f:
                    st.download_button(
                        label="Clique aqui para baixar a planilha",
                        data=f,
                        file_name=EXCEL_PATH,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error("Arquivo local não encontrado.")

    with col2:
        if st.button("📝 Lançar Novo Controle"):
            st.session_state.pagina = "lancar"
            st.experimental_rerun()

    with col3:
        if st.button("✏️ Editar Lançamentos Incompletos"):
            st.session_state.pagina = "editar"
            st.experimental_rerun()

elif pagina == "Lançar Novo Controle":
    st.subheader("Dados do Veículo")
    data = st.date_input("Data", value=datetime.now(FUSO_HORARIO).date())
    placa = st.text_input("Placa do caminhão")
    conferente = st.text_input("Nome do conferente")

    def registrar_tempo(label):
        if st.button(f"Registrar {label}"):
            st.session_state[label] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
            st.experimental_rerun()

    st.subheader("Fábrica")
    for campo in campos_tempo[:7]:
        registrar_tempo(campo)
        st.text_input(campo, value=st.session_state[campo], disabled=True)

    st.subheader("Centro de Distribuição (CD)")
    for campo in campos_tempo[7:]:
        registrar_tempo(campo)
        st.text_input(campo, value=st.session_state[campo], disabled=True)

    if st.button("✅ Salvar Registro"):
        nova_linha = {
            "Data": data.strftime("%Y-%m-%d"),
            "Placa do caminhão": placa,
            "Nome do conferente": conferente,
            **{campo: st.session_state[campo] for campo in campos_tempo},
        }
        try:
            if os.path.exists(EXCEL_PATH):
                df_existente = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
                df_novo = pd.concat([df_existente, pd.DataFrame([nova_linha])], ignore_index=True)
            else:
                df_novo = pd.DataFrame([nova_linha])

            with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                df_novo.to_excel(writer, sheet_name=SHEET_NAME, index=False)

            st.success("✅ Registro salvo com sucesso!")

            # Limpar session_state dos campos após salvar
            for campo in campos_tempo:
                st.session_state[campo] = ""

        except Exception as e:
            st.error("Erro ao salvar planilha localmente:")
            st.text(str(e))

elif pagina == "Editar Lançamentos Incompletos":
    st.subheader("✏️ Edição de Registros Incompletos")

    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        # Filtra registros com algum campo vazio ou NaN
        incompletos = df[df.isnull().any(axis=1) | (df == "").any(axis=1)]

        if not incompletos.empty:
            idx = st.selectbox("Selecione um registro para editar:", incompletos.index)
            registro = incompletos.loc[idx]
            campos_editaveis = {}

            for coluna in df.columns:
                valor = registro[coluna]
                if pd.isna(valor) or valor == "":
                    novo_valor = st.text_input(f"{coluna}", value="")
                    campos_editaveis[coluna] = novo_valor
                else:
                    st.text_input(f"{coluna}", value=str(valor), disabled=True)

            if st.button("💾 Salvar preenchimento"):
                for coluna, novo_valor in campos_editaveis.items():
                    if novo_valor.strip() != "":
                        df.at[idx, coluna] = novo_valor

                with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                    df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

                st.success("✅ Registro atualizado com sucesso!")
        else:
            st.info("✅ Todos os registros estão completos!")
    else:
        st.error("❌ Planilha não encontrada.")
