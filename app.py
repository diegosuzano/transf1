import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import base64
import requests

EXCEL_PATH = "Controle Transferencia.xlsx"
SHEET_NAME = "Base"

st.set_page_config(page_title="Registro Transferência", layout="centered")
st.title("🚚 Registro de Transferência de Carga")

# Fuso horário de Brasília
fuso_brasilia = timezone(timedelta(hours=-3))

def registrar_tempo(label):
    if st.button(f"Registrar {label}"):
        agora = datetime.now(fuso_brasilia)
        st.session_state[label] = agora.strftime("%Y-%m-%d %H:%M:%S")

campos_tempo = [
    "Entrada na Fábrica", "Encostou na doca Fábrica", "Início carregamento",
    "Fim carregamento", "Faturado", "Amarração carga", "Saída do pátio",
    "Entrada CD", "Encostou na doca CD", "Início Descarregamento CD",
    "Fim Descarregamento CD", "Saída CD"
]

for campo in campos_tempo:
    if campo not in st.session_state:
        st.session_state[campo] = ""

opcao = st.radio("Escolha uma opção:", ["Lançar Controle", "Editar Lançamentos", "Baixar Arquivo"])

def calc_tempo(fim, inicio):
    try:
        t1 = datetime.strptime(st.session_state[fim], "%Y-%m-%d %H:%M:%S")
        t0 = datetime.strptime(st.session_state[inicio], "%Y-%m-%d %H:%M:%S")
        return str(t1 - t0)
    except:
        return ""

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

if opcao == "Lançar Controle":
    st.subheader("Dados do Veículo")
    data = st.date_input("Data", value=datetime.now(fuso_brasilia).date())
    placa = st.text_input("Placa do caminhão")
    conferente = st.text_input("Nome do conferente")

    st.subheader("Fábrica")
    for campo in campos_tempo[:7]:
        registrar_tempo(campo)
        st.text_input(campo, value=st.session_state[campo], disabled=True)

    st.subheader("Centro de Distribuição (CD)")
    for campo in campos_tempo[7:]:
        registrar_tempo(campo)
        st.text_input(campo, value=st.session_state[campo], disabled=True)

    tempo_carreg = calc_tempo("Fim carregamento", "Início carregamento")
    tempo_espera = calc_tempo("Encostou na doca Fábrica", "Entrada na Fábrica")
    tempo_total = calc_tempo("Saída do pátio", "Entrada na Fábrica")
    tempo_descarga = calc_tempo("Fim Descarregamento CD", "Início Descarregamento CD")
    tempo_espera_cd = calc_tempo("Encostou na doca CD", "Entrada CD")
    tempo_total_cd = calc_tempo("Saída CD", "Entrada CD")
    tempo_percurso = calc_tempo("Entrada CD", "Saída do pátio")

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
                link_download = f"https://github.com/{repo}/raw/main/{caminho_repo}"
                st.markdown(f'📥 Baixar planilha atualizada', unsafe_allow_html=True)
            else:
                st.error("❌ Falha ao enviar a planilha para o GitHub.")

        except Exception as e:
            st.error("❌ Erro ao salvar a planilha localmente.")
            st.text(str(e))

elif opcao == "Editar Lançamentos":
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        incompletos = df[df.isnull().any(axis=1)]
        if not incompletos.empty:
            st.subheader("Registros Incompletos")
            editados = st.data_editor(incompletos, num_rows="dynamic", use_container_width=True)
            if st.button("Salvar Edições"):
                df.update(editados)
                df.to_excel(EXCEL_PATH, sheet_name=SHEET_NAME, index=False, engine="openpyxl")
                st.success("Alterações salvas com sucesso!")
        else:
            st.info("Nenhum registro incompleto encontrado.")
    else:
        st.warning("Arquivo de dados não encontrado.")

elif opcao == "Baixar Arquivo":
    repo = "diegosuzano/transf1"
    caminho_repo = "Controle Transferencia.xlsx"
    link_download = f"https://github.com/{repo}/raw/main/{caminho_repo}"
    st.markdown(f'[📥 Clique aqui para baixar a planilha]({nsafe_allow_html=True)
