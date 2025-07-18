import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
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

# INICIALIZA ESTADO
for campo in campos_tempo:
    if campo not in st.session_state:
        st.session_state[campo] = ""

# TÍTULO E MENU
st.set_page_config(page_title="Registro Transferência", layout="centered")
st.title("🚚 Registro de Transferência de Carga")

pagina = st.selectbox("📌 Escolha uma opção", ["Tela Inicial", "Lançar Novo Controle", "Editar Lançamentos Incompletos"])

# TELA INICIAL
if pagina == "Tela Inicial":
    st.subheader("O que deseja fazer?")
    st.markdown("### ")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📥 Baixar Arquivo"):
            repo = "diegosuzano/transf1"
            caminho_repo = "Controle Transferencia.xlsx"
            link_download = f"https://github.com/{repo}/raw/main/{caminho_repo}"
            st.markdown(
                f'<a href="{link_download}" target="_blank" download style="font-size:18px;">📂 Clique aqui para baixar</a>',
                unsafe_allow_html=True
            )

    with col2:
        st.button("📝 Lançar Novo Controle")

    with col3:
        st.button("✏️ Editar Lançamentos Incompletos")

# LANÇAMENTO NOVO
elif pagina == "Lançar Novo Controle":
    st.subheader("Dados do Veículo")
    data = st.date_input("Data", value=datetime.now(FUSO_HORARIO).date())
    placa = st.text_input("Placa do caminhão")
    conferente = st.text_input("Nome do conferente")

    def registrar_tempo(label):
        if st.button(f"Registrar {label}"):
            st.session_state[label] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")

    st.subheader("Fábrica")
    for campo in campos_tempo[:7]:
        registrar_tempo(campo)
        st.text_input(campo, value=st.session_state[campo], disabled=True)

    st.subheader("Centro de Distribuição (CD)")
    for campo in campos_tempo[7:]:
        registrar_tempo(campo)
        st.text_input(campo, value=st.session_state[campo], disabled=True)

    def calc_tempo(fim, inicio):
        try:
            t1 = datetime.strptime(st.session_state[fim], "%Y-%m-%d %H:%M:%S")
            t0 = datetime.strptime(st.session_state[inicio], "%Y-%m-%d %H:%M:%S")
            return str(t1 - t0)
        except:
            return ""

    tempo_carreg = calc_tempo("Fim carregamento", "Início carregamento")
    tempo_espera = calc_tempo("Encostou na doca Fábrica", "Entrada na Fábrica")
    tempo_total = calc_tempo("Saída do pátio", "Entrada na Fábrica")
    tempo_descarga = calc_tempo("Fim Descarregamento CD", "Início Descarregamento CD")
    tempo_espera_cd = calc_tempo("Encostou na doca CD", "Entrada CD")
    tempo_total_cd = calc_tempo("Saída CD", "Entrada CD")
    tempo_percurso = calc_tempo("Entrada CD", "Saída do pátio")

    def enviar_para_github(caminho_arquivo, repo, caminho_repo, token):
        try:
            with open(caminho_arquivo, "rb") as f:
                conteudo = f.read()
            conteudo_b64 = base64.b64encode(conteudo).decode("utf-8")

            url = f"https://api.github.com/repos/{repo}/contents/{caminho_repo}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            }

            response = requests.get(url, headers=headers)
            sha = response.json()["sha"] if response.status_code == 200 else None

            payload = {
                "message": "Atualização automática da planilha",
                "content": conteudo_b64,
                "branch": "main"
            }
            if sha:
                payload["sha"] = sha

            r = requests.put(url, headers=headers, json=payload)

            if r.status_code not in [200, 201]:
                st.error(f"Erro ao enviar: {r.status_code}")
                try:
                    st.json(r.json())
                except Exception as e:
                    st.text(f"Erro ao interpretar resposta: {e}")
            return r.status_code in [200, 201]

        except Exception as e:
            st.error("Erro inesperado ao tentar enviar para o GitHub.")
            st.text(str(e))
            return False

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

        try:
            if os.path.exists(EXCEL_PATH):
                df_existente = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
                df_novo = pd.concat([df_existente, pd.DataFrame([nova_linha])], ignore_index=True)
            else:
                df_novo = pd.DataFrame([nova_linha])

            with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                df_novo.to_excel(writer, sheet_name=SHEET_NAME, index=False)

            st.success("✅ Registro salvo com sucesso!")

            for campo in campos_tempo:
                st.session_state[campo] = ""

            repo = "diegosuzano/transf1"
            caminho_repo = "Controle Transferencia.xlsx"
            token = st.secrets["github_token"]

            if enviar_para_github(EXCEL_PATH, repo, caminho_repo, token):
                st.success("📤 Planilha enviada para o GitHub com sucesso!")
            else:
                st.error("❌ Falha ao enviar a planilha para o GitHub.")

        except Exception as e:
            st.error("❌ Erro ao salvar a planilha localmente.")
            st.text(str(e))

# EDIÇÃO DE INCOMPLETOS
elif pagina == "Editar Lançamentos Incompletos":
    st.subheader("✏️ Edição de Registros Incompletos")

    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
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
