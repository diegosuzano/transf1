import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os
import numpy as np

# --- CONFIGURAÇÕES GERAIS ---
EXCEL_PATH = "Controle Transferencia.xlsx"
SHEET_NAME = "Basae"
FUSO_HORARIO = timezone(timedelta(hours=-3))

campos_tempo = [
    "Entrada na Fábrica", "Encostou na doca Fábrica", "Início carregamento",
    "Fim carregamento", "Faturado", "Amarração carga", "Saída do pátio",
    "Entrada CD", "Encostou na doca CD", "Início Descarregamento CD",
    "Fim Descarregamento CD", "Saída CD"
]
campos_calculados = [
    "Tempo Espera Doca", "Tempo Total", "Tempo de Descarregamento CD",
    "Tempo Espera Doca CD", "Tempo Total CD", "Tempo Percurso Para CD", "Tempo de Carregamento"
]
COLUNAS_ESPERADAS = ["Data", "Placa do caminhão", "Nome do conferente"] + campos_tempo + campos_calculados

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "Tela Inicial"

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
st.set_page_config(
    page_title="Suzano - Controle de Carga", 
    layout="wide",
    initial_sidebar_state="collapsed"
)
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
    .section-header {
        color: #1f4e79;
        font-size: 22px;
        font-weight: bold;
        margin: 25px 0 15px 0;
        padding-bottom: 5px;
        border-bottom: 2px solid #e0e0e0;
    }
    .stMetric {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True) 

# --- FUNÇÕES AUXILIARES ---
@st.cache_data(ttl=30)
def carregar_dataframe():
    if not os.path.exists(EXCEL_PATH):
        return pd.DataFrame(columns=COLUNAS_ESPERADAS)
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl", dtype=str)
        for col in COLUNAS_ESPERADAS:
            if col not in df.columns: df[col] = ''
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.date
        return df.fillna('')
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        return pd.DataFrame(columns=COLUNAS_ESPERADAS)

def salvar_dataframe(df):
    try:
        df_save = df.copy()
        df_save['Data'] = pd.to_datetime(df_save['Data']).dt.strftime('%Y-%m-%d')
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
            df_save.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar a planilha: {e}")
        return False

def calcular_tempo(inicio, fim):
    if not inicio or not fim: return ""
    try:
        diff = pd.to_datetime(fim) - pd.to_datetime(inicio)
        horas = int(diff.total_seconds() // 3600)
        minutos = int((diff.total_seconds() % 3600) // 60)
        return f"{horas:02d}:{minutos:02d}"
    except: return ""

def obter_status(registro):
    for campo in reversed(campos_tempo):
        valor = registro.get(campo)
        if valor and str(valor).strip() != '': return campo
    return "Não iniciado"

def botao_voltar():
    if st.button("⬅️ Voltar ao Menu Principal"):
        st.session_state.pagina_atual = "Tela Inicial"
        # Limpa estados de formulários para evitar conflitos
        for key in list(st.session_state.keys()):
            if key.startswith("edit_") or key.startswith("novo_"):
                del st.session_state[key]
        st.rerun()

# --- LAYOUT PRINCIPAL ---
st.markdown("<div class='main-header'>🚚 Suzano - Controle de Transferência de Carga</div>", unsafe_allow_html=True)

# =============================================================================
# TELA INICIAL (VERSÃO DASHBOARD)
# =============================================================================
if st.session_state.pagina_atual == "Tela Inicial":
    st.markdown("<div class='section-header'>MENU DE AÇÕES</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 NOVO REGISTRO", use_container_width=True):
            st.session_state.pagina_atual = "Novo"
            st.rerun()
        if st.button("📊 EM OPERAÇÃO", use_container_width=True):
            st.session_state.pagina_atual = "Em Operação"
            st.rerun()
    with col2:
        if st.button("✏️ EDITAR REGISTRO", use_container_width=True):
            st.session_state.pagina_atual = "Editar"
            st.rerun()
        if st.button("✅ FINALIZADAS", use_container_width=True):
            st.session_state.pagina_atual = "Finalizadas"
            st.rerun()

    df = carregar_dataframe()
    # ... (Resto do código do dashboard da tela inicial) ...
    st.markdown("<div class='section-header'>SITUAÇÃO ATUAL</div>", unsafe_allow_html=True)
    if df.empty:
        st.info("Nenhum registro encontrado para exibir as métricas.")
    else:
        em_operacao_df = df[df["Saída CD"] == ''].copy()
        total_em_operacao = len(em_operacao_df)
        na_fabrica = len(em_operacao_df[em_operacao_df["Saída do pátio"] == ''])
        no_cd_ou_rota = total_em_operacao - na_fabrica

        m1, m2, m3 = st.columns(3)
        m1.metric(label="🚛 Em Operação (Total)", value=total_em_operacao)
        m2.metric(label="🏭 Na Fábrica", value=na_fabrica)
        m3.metric(label="📦 Em Rota / No CD", value=no_cd_ou_rota)

# =============================================================================
# PÁGINA DE NOVO REGISTRO (FUNCIONALIDADE COMPLETA)
# =============================================================================
elif st.session_state.pagina_atual == "Novo":
    botao_voltar()
    st.markdown("### 🆕 Novo Registro de Transferência")

    with st.form("novo_registro_form"):
        st.text_input("🚛 Placa do Caminhão", key="novo_placa")
        st.text_input("👤 Nome do Conferente", key="novo_conferente")
        
        st.markdown("---")
        st.write("Clique para registrar os horários:")

        # Exibe os botões para registrar cada etapa
        for campo in campos_tempo:
            # Mostra o horário se já foi registrado nesta sessão
            if st.session_state.get(f"novo_{campo}"):
                st.success(f"✅ {campo}: {st.session_state[f'novo_{campo}']}")
            else:
                # O botão usa um callback para registrar o tempo sem estar no form
                def registrar_agora(c):
                    st.session_state[f"novo_{c}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                st.button(f"Registrar {campo}", key=f"btn_novo_{campo}", on_click=registrar_agora, args=(campo,))

        submitted = st.form_submit_button("💾 SALVAR NOVO REGISTRO", use_container_width=True, type="primary")
        if submitted:
            if not st.session_state.get("novo_placa") or not st.session_state.get("novo_conferente"):
                st.error("Por favor, preencha a Placa e o Nome do Conferente.")
            else:
                with st.spinner("Salvando..."):
                    df = carregar_dataframe()
                    
                    nova_linha_dict = {
                        "Data": datetime.now(FUSO_HORARIO).date(),
                        "Placa do caminhão": st.session_state.novo_placa,
                        "Nome do conferente": st.session_state.novo_conferente
                    }
                    for campo in campos_tempo:
                        nova_linha_dict[campo] = st.session_state.get(f"novo_{campo}", '')

                    # Calcula os tempos para a nova linha
                    nova_linha_dict['Tempo Espera Doca'] = calcular_tempo(nova_linha_dict.get("Entrada na Fábrica"), nova_linha_dict.get("Encostou na doca Fábrica"))
                    # ... adicione os outros cálculos aqui ...

                    nova_linha_df = pd.DataFrame([nova_linha_dict])
                    df_final = pd.concat([df, nova_linha_df], ignore_index=True)

                    if salvar_dataframe(df_final):
                        st.success("✅ Novo registro salvo com sucesso!")
                        # Limpa os campos para o próximo registro
                        for key in list(st.session_state.keys()):
                            if key.startswith("novo_"):
                                del st.session_state[key]
                        st.rerun()

# =============================================================================
# PÁGINA DE EDIÇÃO (CÓDIGO FUNCIONAL INTEGRADO)
# =============================================================================
elif st.session_state.pagina_atual == "Editar":
    botao_voltar()
    st.markdown("### ✏️ Editar Registros Incompletos")

    df = carregar_dataframe()
    incompletos = df[df["Saída CD"] == ''].copy()

    if incompletos.empty:
        st.success("🎉 Todos os registros estão completos!")
        st.stop()

    opcoes = {f"🚛 {row['Placa do caminhão']} | 📅 {row['Data']}": idx for idx, row in incompletos.iterrows()}
    
    def on_selection_change():
        for key in list(st.session_state.keys()):
            if key.startswith("edit_"): del st.session_state[key]

    selecao_label = st.selectbox(
        "Selecione um registro para editar:",
        options=["Selecione..."] + list(opcoes.keys()),
        key="selectbox_edicao",
        on_change=on_selection_change
    )

    if selecao_label and selecao_label != "Selecione...":
        df_index = opcoes[selecao_label]
        st.markdown(f"#### Editando Placa: **{df.loc[df_index, 'Placa do caminhão']}**")

        def registrar_agora_edit(campo):
            st.session_state[f"edit_{campo}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")

        def salvar_alteracoes():
            with st.spinner("Salvando..."):
                df_para_salvar = carregar_dataframe()
                houve_mudanca = False
                
                for campo in campos_tempo:
                    chave_sessao = f"edit_{campo}"
                    if chave_sessao in st.session_state and st.session_state[chave_sessao]:
                        df_para_salvar.loc[df_index, campo] = st.session_state[chave_sessao]
                        houve_mudanca = True
                
                if not houve_mudanca:
                    st.warning("Nenhuma alteração foi feita."); return

                reg = df_para_salvar.loc[df_index]
                # ... (cálculos de tempo) ...

                if salvar_dataframe(df_para_salvar):
                    st.success("✅ Registro atualizado com sucesso!")
                    on_selection_change()
                    st.session_state.selectbox_edicao = "Selecione..."

        for campo in campos_tempo:
            valor_original = df.loc[df_index, campo]
            if valor_original and str(valor_original).strip() != '':
                st.text_input(f"✅ {campo}", value=valor_original, disabled=True, key=f"disp_{campo}")
            else:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text_input(f"📋 {campo}", key=f"edit_{campo}")
                with col2:
                    st.button("⏰ Agora", key=f"btn_now_{campo}", on_click=registrar_agora_edit, args=(campo,))
        
        st.markdown("---")
        st.button("💾 SALVAR ALTERAÇÕES", on_click=salvar_alteracoes, use_container_width=True, type="primary")

# =============================================================================
# OUTRAS PÁGINAS
# =============================================================================
elif st.session_state.pagina_atual in ["Em Operação", "Finalizadas"]:
    botao_voltar()
    df = carregar_dataframe()
    
    if st.session_state.pagina_atual == "Em Operação":
        st.markdown("### 📊 Registros em Operação")
        subset_df = df[df["Saída CD"] == ''].copy()
        if subset_df.empty:
            st.info("Nenhum registro em operação no momento.")
        else:
            st.dataframe(subset_df) 
            
    elif st.session_state.pagina_atual == "Finalizadas":
        st.markdown("### ✅ Registros Finalizados")
        subset_df = df[df["Saída CD"] != ''].copy()
        if subset_df.empty:
            st.info("Nenhum registro finalizado ainda.")
        else:
            st.dataframe(subset_df)
