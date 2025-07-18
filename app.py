import streamlit as st 
import pandas as pd
from datetime import datetime
import pytz
import os

# Configurações
EXCEL_PATH = "dados_controle.xlsx"
SHEET_NAME = "Controle"
FUSO_HORARIO = pytz.timezone("America/Sao_Paulo")

st.set_page_config(page_title="Controle Logístico", layout="centered")

# Função para criar arquivo vazio, se não existir
def criar_planilha():
    if not os.path.exists(EXCEL_PATH):
        colunas = [
            "Data", "Placa do caminhão", "Nome do conferente",
            "Entrada no pátio", "Encostou na doca", "Início carregamento",
            "Fim carregamento", "Faturado", "Amarração carga", "Saída CD"
        ]
        df_vazio = pd.DataFrame(columns=colunas)
        df_vazio.to_excel(EXCEL_PATH, sheet_name=SHEET_NAME, index=False)

criar_planilha()

if "pagina" not in st.session_state:
    st.session_state.pagina = "inicial"

# Tela inicial
if st.session_state.pagina == "inicial":
    st.title("O que deseja fazer?")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Baixar Arquivo"):
            with open(EXCEL_PATH, "rb") as f:
                st.download_button(
                    label="Clique para baixar",
                    data=f,
                    file_name="dados_controle.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    with col2:
        if st.button("📝 Lançar Novo Controle"):
            st.session_state.pagina = "lancar"
            st.experimental_rerun()

    with col3:
        if st.button("✏️ Editar Lançamentos Incompletos"):
            st.session_state.pagina = "editar"
            st.experimental_rerun()

# Tela de lançamento
elif st.session_state.pagina == "lancar":
    st.header("📝 Novo Lançamento de Controle")

    # Inicializar dicionário com valores dos campos (timestamps) no session_state para persistir
    campos = [
        "Entrada no pátio", "Encostou na doca", "Início carregamento",
        "Fim carregamento", "Faturado", "Amarração carga", "Saída CD"
    ]
    if "valores" not in st.session_state:
        st.session_state.valores = {campo: "" for campo in campos}

    with st.form(key="form_lancar"):
        data = st.date_input("Data", value=datetime.now(FUSO_HORARIO).date())
        placa = st.text_input("Placa do caminhão")
        conferente = st.text_input("Nome do conferente")

        # Para cada campo, mostra input + botão para preencher com timestamp
        for campo in campos:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.session_state.valores[campo] = st.text_input(f"{campo}", value=st.session_state.valores[campo], key=f"{campo}_input")
            with col2:
                if st.form_submit_button(f"Registrar agora - {campo}", help=f"Clicar para registrar horário atual em {campo}", on_click=None):
                    # Atenção: Não podemos chamar st.experimental_rerun() aqui dentro do form_submit_button
                    st.session_state.valores[campo] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                    # Força rerun para atualizar campo
                    st.experimental_rerun()

        if st.form_submit_button("Salvar Lançamento"):
            novo = pd.DataFrame([{
                "Data": data.strftime("%Y-%m-%d"),
                "Placa do caminhão": placa,
                "Nome do conferente": conferente,
                **st.session_state.valores
            }])

            df_existente = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
            df_final = pd.concat([df_existente, novo], ignore_index=True)

            with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                df_final.to_excel(writer, sheet_name=SHEET_NAME, index=False)

            st.success("✅ Lançamento salvo com sucesso!")
            st.session_state.pagina = "inicial"
            st.session_state.valores = {campo: "" for campo in campos}
            st.experimental_rerun()

# Tela de edição
elif st.session_state.pagina == "editar":
    st.subheader("✏️ Editar lançamentos onde 'Saída CD' ainda não foi preenchido")

    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")

        incompletos = df[df["Saída CD"].isna() | (df["Saída CD"] == "")]

        if not incompletos.empty:
            idx = st.selectbox("Selecione um registro para editar:", incompletos.index)
            registro = incompletos.loc[idx]

            st.markdown(f"**Data:** {registro['Data']} &nbsp;&nbsp;&nbsp; **Placa:** {registro['Placa do caminhão']}")
            st.markdown(f"**Conferente:** {registro['Nome do conferente']}")

            campos_editaveis = {}

            for coluna in df.columns:
                valor = registro[coluna]
                if pd.isna(valor) or valor == "":
                    key = f"{coluna}_edicao"
                    if key not in st.session_state:
                        st.session_state[key] = ""

                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.session_state[key] = st.text_input(f"{coluna}", value=st.session_state[key], key=key)
                    with col2:
                        if st.button(f"📍 Registrar agora: {coluna}", key=f"btn_{coluna}"):
                            st.session_state[key] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                            st.experimental_rerun()

                    campos_editaveis[coluna] = key
                else:
                    st.text_input(coluna, value=str(valor), disabled=True)

            if st.button("💾 Salvar preenchimento"):
                for coluna, state_key in campos_editaveis.items():
                    valor_novo = st.session_state[state_key].strip()
                    if valor_novo != "":
                        df.at[idx, coluna] = valor_novo

                with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                    df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

                st.success("✅ Registro atualizado com sucesso!")
                st.session_state.pagina = "inicial"

                for key in campos_editaveis.values():
                    st.session_state[key] = ""

                st.experimental_rerun()
        else:
            st.info("✅ Todos os lançamentos já foram finalizados com 'Saída CD'.")
    else:
        st.error("❌ Planilha não encontrada.")
