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
# TELA INICIAL
# =============================================================================
if st.session_state.pagina_atual == "Tela Inicial":
    st.markdown("<div class='section-header'>MENU DE AÇÕES</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 NOVO REGISTRO", use_container_width=True):
            st.session_state.pagina_atual = "Novo"
            # Limpa qualquer estado antigo de um novo registro
            for key in list(st.session_state.keys()):
                if key.startswith("novo_"):
                    del st.session_state[key]
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
    # ... (código do dashboard da tela inicial) ...

# =============================================================================
# PÁGINA DE NOVO REGISTRO (LÓGICA CORRIGIDA)
# =============================================================================
elif st.session_state.pagina_atual == "Novo":
    botao_voltar()
    st.markdown("### 🆕 Novo Registro de Transferência")

    # Etapa 1: Coletar informações básicas
    if 'novo_registro_iniciado' not in st.session_state:
        with st.form("info_basicas_form"):
            st.text_input("🚛 Placa do Caminhão", key="novo_placa")
            st.text_input("👤 Nome do Conferente", key="novo_conferente")
            submitted = st.form_submit_button("▶️ Iniciar Registro")
            if submitted:
                if not st.session_state.novo_placa or not st.session_state.novo_conferente:
                    st.error("Placa e Conferente são obrigatórios.")
                else:
                    st.session_state.novo_registro_iniciado = True
                    st.rerun()
    
    # Etapa 2: Registrar os tempos
    else:
        st.info(f"Registrando para a Placa: **{st.session_state.novo_placa}** | Conferente: **{st.session_state.novo_conferente}**")
        st.markdown("---")
        
        # Callback para os botões de registro de tempo
        def registrar_agora(campo):
            st.session_state[f"novo_{campo}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")

        # Renderiza os botões e os tempos já registrados
        for campo in campos_tempo:
            if st.session_state.get(f"novo_{campo}"):
                st.success(f"✅ {campo}: {st.session_state[f'novo_{campo}']}")
            else:
                st.button(f"Registrar {campo}", key=f"btn_novo_{campo}", on_click=registrar_agora, args=(campo,))
        
        st.markdown("---")
        
        # Callback para o botão de salvar
        def salvar_novo_registro():
            with st.spinner("Salvando..."):
                df = carregar_dataframe()
                
                nova_linha_dict = {
                    "Data": datetime.now(FUSO_HORARIO).date(),
                    "Placa do caminhão": st.session_state.novo_placa,
                    "Nome do conferente": st.session_state.novo_conferente
                }
                for campo in campos_tempo:
                    nova_linha_dict[campo] = st.session_state.get(f"novo_{campo}", '')

                # Adicione aqui os cálculos de tempo para a nova linha
                # ...

                nova_linha_df = pd.DataFrame([nova_linha_dict])
                df_final = pd.concat([df, nova_linha_df], ignore_index=True)

                if salvar_dataframe(df_final):
                    st.success("✅ Novo registro salvo com sucesso!")
                    # Limpa tudo para o próximo
                    for key in list(st.session_state.keys()):
                        if key.startswith("novo_"):
                            del st.session_state[key]
                # O rerun já acontece por causa do callback

        st.button("💾 SALVAR REGISTRO COMPLETO", on_click=salvar_novo_registro, use_container_width=True, type="primary")


# =============================================================================
# PÁGINA DE EDIÇÃO
# =============================================================================
elif st.session_state.pagina_atual == "Editar":
    botao_voltar()
    st.markdown("### ✏️ Editar Registros Incompletos")
    # ... (código da página de edição que já está funcional) ...
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
            # ... (código de salvar alterações) ...
            pass

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
        st.dataframe(subset_df) 
            
    elif st.session_state.pagina_atual == "Finalizadas":
        st.markdown("### ✅ Registros Finalizados")
        subset_df = df[df["Saída CD"] != ''].copy()
        st.dataframe(subset_df)
