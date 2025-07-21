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
        df_save['Data'] = pd.to_datetime(df_save['Data'], errors='coerce').dt.strftime('%Y-%m-%d')
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
        for key in list(st.session_state.keys()):
            if key.startswith("edit_") or key.startswith("novo_"):
                del st.session_state[key]
        st.rerun()

# --- LAYOUT PRINCIPAL ---
st.markdown("<div class='main-header'>🚚 Suzano - Controle de Transferência de Carga</div>", unsafe_allow_html=True)

# =============================================================================
# TELA INICIAL (DASHBOARD RESTAURADO)
# =============================================================================
if st.session_state.pagina_atual == "Tela Inicial":
    st.markdown("<div class='section-header'>MENU DE AÇÕES</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 NOVO REGISTRO", use_container_width=True):
            st.session_state.pagina_atual = "Novo"
            for key in list(st.session_state.keys()):
                if key.startswith("novo_"): del st.session_state[key]
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

        with st.expander("Ver Detalhes dos Veículos em Operação"):
            if em_operacao_df.empty:
                st.write("Nenhum veículo em operação no momento.")
            else:
                for _, row in em_operacao_df.iterrows():
                    status = obter_status(row)
                    st.info(f"**Placa:** {row['Placa do caminhão']} | **Status Atual:** {status}")

    st.markdown("<div class='section-header'>📈 INDICADORES DE PERFORMANCE (HOJE)</div>", unsafe_allow_html=True)
    if df.empty:
        st.info("Nenhum registro hoje para calcular as médias.")
    else:
        hoje = datetime.now(FUSO_HORARIO).date()
        df_hoje = df[df['Data'] == hoje].copy()

        if df_hoje.empty:
            st.info("Nenhum registro encontrado com a data de hoje.")
        else:
            def hhmm_para_minutos(tempo_str):
                if not tempo_str or ':' not in str(tempo_str): return np.nan
                try:
                    h, m = map(int, str(tempo_str).split(':'))
                    return h * 60 + m
                except: return np.nan
            
            def calcular_media_tempo(series):
                minutos = series.apply(hhmm_para_minutos).mean()
                if pd.isna(minutos): return "N/D"
                horas_media = int(minutos // 60)
                minutos_media = int(minutos % 60)
                return f"{horas_media:02d}:{minutos_media:02d}"

            col_fabrica, col_cd = st.columns(2)
            with col_fabrica:
                st.subheader("Métricas da Fábrica")
                st.metric(label="Tempo Médio Esperando Doca", value=calcular_media_tempo(df_hoje['Tempo Espera Doca']))
                st.metric(label="Tempo Médio de Carregamento", value=calcular_media_tempo(df_hoje['Tempo de Carregamento']))
                st.metric(label="Tempo Médio Total na Fábrica", value=calcular_media_tempo(df_hoje['Tempo Total']))
            with col_cd:
                st.subheader("Métricas do CD")
                st.metric(label="Tempo Médio de Percurso", value=calcular_media_tempo(df_hoje['Tempo Percurso Para CD']))
                st.metric(label="Tempo Médio Esperando Doca (CD)", value=calcular_media_tempo(df_hoje['Tempo Espera Doca CD']))
                st.metric(label="Tempo Médio de Descarregamento", value=calcular_media_tempo(df_hoje['Tempo de Descarregamento CD']))
                st.metric(label="Tempo Médio Total no CD", value=calcular_media_tempo(df_hoje['Tempo Total CD']))

    st.markdown("---")
    if os.path.exists(EXCEL_PATH):
        with open(EXCEL_PATH, "rb") as f:
            st.download_button("📥 Baixar Planilha Completa", f, file_name=EXCEL_PATH, use_container_width=True)

# =============================================================================
# PÁGINA DE NOVO REGISTRO
# =============================================================================
elif st.session_state.pagina_atual == "Novo":
    botao_voltar()
    st.markdown("### 🆕 Novo Registro de Transferência")

    def registrar_agora(campo):
        st.session_state[f"novo_{campo}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")

    def salvar_novo_registro():
        if not st.session_state.get("novo_placa") or not st.session_state.get("novo_conferente"):
            st.session_state.notification = ("error", "Placa e Conferente são obrigatórios para salvar.")
            return

        with st.spinner("Salvando..."):
            df = carregar_dataframe()
            nova_linha_dict = { "Data": datetime.now(FUSO_HORARIO).date() }
            for key, value in st.session_state.items():
                if key.startswith("novo_"):
                    nova_linha_dict[key.replace("novo_", "")] = value
            
            # Recalcula todos os tempos
            for calc_campo in campos_calculados:
                # Adapte esta lógica para seus cálculos específicos
                if calc_campo == "Tempo Espera Doca":
                    nova_linha_dict[calc_campo] = calcular_tempo(nova_linha_dict.get("Entrada na Fábrica"), nova_linha_dict.get("Encostou na doca Fábrica"))
                # ... adicione os outros cálculos aqui ...

            nova_linha_df = pd.DataFrame([nova_linha_dict])
            df_final = pd.concat([df, nova_linha_df], ignore_index=True)

            if salvar_dataframe(df_final):
                st.session_state.notification = ("success", "Novo registro salvo com sucesso!")
                for key in list(st.session_state.keys()):
                    if key.startswith("novo_"): del st.session_state[key]
            else:
                st.session_state.notification = ("error", "Falha ao salvar o registro.")

    st.text_input("🚛 Placa do Caminhão", key="novo_placa")
    st.text_input("👤 Nome do Conferente", key="novo_conferente")
    st.markdown("---")

    for campo in campos_tempo:
        if st.session_state.get(f"novo_{campo}"):
            st.success(f"✅ {campo}: {st.session_state[f'novo_{campo}']}")
        else:
            st.button(f"Registrar {campo}", key=f"btn_novo_{campo}", on_click=registrar_agora, args=(campo,))
    
    st.markdown("---")
    
    # Placeholder para notificações
    notification_placeholder = st.empty()
    if st.session_state.get("notification"):
        msg_type, msg_text = st.session_state.notification
        if msg_type == "success":
            notification_placeholder.success(msg_text)
        else:
            notification_placeholder.error(msg_text)
        del st.session_state.notification

    st.button("💾 SALVAR NOVO REGISTRO", on_click=salvar_novo_registro, use_container_width=True, type="primary")

# =============================================================================
# PÁGINA DE EDIÇÃO (FUNCIONALIDADE DE SALVAR RESTAURADA)
# =============================================================================
elif st.session_state.pagina_atual == "Editar":
    botao_voltar()
    st.markdown("### ✏️ Editar Registros Incompletos")

    df = carregar_dataframe()
    incompletos = df[df["Saída CD"] == ''].copy()

    if incompletos.empty:
        st.success("🎉 Todos os registros estão completos!"); st.stop()

    opcoes = {f"🚛 {row['Placa do caminhão']} | 📅 {row['Data']}": idx for idx, row in incompletos.iterrows()}
    
    def on_selection_change():
        for key in list(st.session_state.keys()):
            if key.startswith("edit_") or key == "notification":
                del st.session_state[key]

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
                    st.session_state.notification = ("warning", "Nenhuma alteração foi feita.")
                    return

                reg = df_para_salvar.loc[df_index]
                # Recalcula todos os tempos
                df_para_salvar.loc[df_index, 'Tempo Espera Doca'] = calcular_tempo(reg.get("Entrada na Fábrica"), reg.get("Encostou na doca Fábrica"))
                df_para_salvar.loc[df_index, 'Tempo de Carregamento'] = calcular_tempo(reg.get("Início carregamento"), reg.get("Fim carregamento"))
                df_para_salvar.loc[df_index, 'Tempo Total'] = calcular_tempo(reg.get("Entrada na Fábrica"), reg.get("Saída do pátio"))
                df_para_salvar.loc[df_index, 'Tempo Percurso Para CD'] = calcular_tempo(reg.get("Saída do pátio"), reg.get("Entrada CD"))
                df_para_salvar.loc[df_index, 'Tempo Espera Doca CD'] = calcular_tempo(reg.get("Entrada CD"), reg.get("Encostou na doca CD"))
                df_para_salvar.loc[df_index, 'Tempo de Descarregamento CD'] = calcular_tempo(reg.get("Início Descarregamento CD"), reg.get("Fim Descarregamento CD"))
                df_para_salvar.loc[df_index, 'Tempo Total CD'] = calcular_tempo(reg.get("Entrada CD"), reg.get("Saída CD"))

                if salvar_dataframe(df_para_salvar):
                    st.session_state.notification = ("success", "Registro atualizado com sucesso!")
                    on_selection_change()
                else:
                    st.session_state.notification = ("error", "Falha ao salvar as alterações.")

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
        
        notification_placeholder_edit = st.empty()
        if st.session_state.get("notification"):
            msg_type, msg_text = st.session_state.notification
            if msg_type == "success": notification_placeholder_edit.success(msg_text)
            elif msg_type == "warning": notification_placeholder_edit.warning(msg_text)
            else: notification_placeholder_edit.error(msg_text)
            del st.session_state.notification

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
        st.dataframe(subset_df) 
            
    elif st.session_state.pagina_atual == "Finalizadas":
        st.markdown("### ✅ Registros Finalizados")
        subset_df = df[df["Saída CD"] != ''].copy()
        st.dataframe(subset_df)
