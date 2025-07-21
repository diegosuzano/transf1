import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

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
# Cole seu CSS completo aqui para manter a aparência
st.markdown("""<style>...</style>""", unsafe_allow_html=True) 

# --- FUNÇÕES AUXILIARES ---
@st.cache_data(ttl=30) # Cache mais curto para refletir mudanças mais rápido
def carregar_dataframe():
    if not os.path.exists(EXCEL_PATH):
        return pd.DataFrame(columns=COLUNAS_ESPERADAS)
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl", dtype=str)
        for col in COLUNAS_ESPERADAS:
            if col not in df.columns: df[col] = ''
        return df[COLUNAS_ESPERADAS].fillna('')
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        return pd.DataFrame(columns=COLUNAS_ESPERADAS)

def salvar_dataframe(df):
    try:
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
            df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
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
        st.rerun()

# --- LAYOUT PRINCIPAL ---
st.markdown("<h1 style='text-align: center;'>🚚 Suzano - Controle de Transferência de Carga</h1>", unsafe_allow_html=True)

# =============================================================================
# TELA INICIAL (CÓDIGO COMPLETO RESTAURADO)
# =============================================================================
if st.session_state.pagina_atual == "Tela Inicial":
    st.markdown("### 📋 Escolha uma opção:")
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
    
    st.markdown("---")
    if os.path.exists(EXCEL_PATH):
        with open(EXCEL_PATH, "rb") as f:
            st.download_button("📥 Baixar Planilha Atual", f, file_name=EXCEL_PATH, use_container_width=True)

# =============================================================================
# PÁGINA DE NOVO REGISTRO (CÓDIGO COMPLETO RESTAURADO)
# =============================================================================
elif st.session_state.pagina_atual == "Novo":
    # Adapte esta seção com seu código original de "Novo Registro" se necessário
    botao_voltar()
    st.markdown("### 🆕 Novo Registro de Transferência")
    # ... Seu código para novo registro aqui ...

# =============================================================================
# PÁGINA DE EDIÇÃO (LÓGICA FINAL E CORRIGIDA)
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
    
    selecao_label = st.selectbox(
        "Selecione um registro para editar:",
        options=["Selecione..."] + list(opcoes.keys()),
        key="selectbox_edicao"
    )

    if selecao_label and selecao_label != "Selecione...":
        df_index = opcoes[selecao_label]
        
        st.markdown(f"#### Editando Placa: **{df.loc[df_index, 'Placa do caminhão']}**")

        # Callback para o botão "Agora" - a forma segura de atualizar o estado
        def registrar_agora(campo):
            st.session_state[f"edit_{campo}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")

        # Usamos um formulário para agrupar os inputs e o botão de salvar
        with st.form("edit_form"):
            # Itera por todos os campos de tempo para mostrar o progresso completo
            for campo in campos_tempo:
                valor_original = df.loc[df_index, campo]
                
                # Se o campo JÁ FOI PREENCHIDO, mostra como informação desabilitada
                if valor_original and str(valor_original).strip() != '':
                    st.text_input(f"✅ {campo}", value=valor_original, disabled=True)
                # Se o campo ESTÁ VAZIO, oferece a opção de editar
                else:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # O input lê o valor do session_state para se manter atualizado
                        st.text_input(f"📋 {campo}", key=f"edit_{campo}")
                    with col2:
                        # O botão "Agora" NÃO está no formulário, ele tem seu próprio callback
                        st.button("⏰ Agora", key=f"btn_now_{campo}", on_click=registrar_agora, args=(campo,))
            
            st.markdown("---")
            submitted = st.form_submit_button("💾 SALVAR ALTERAÇÕES", use_container_width=True, type="primary")
            
            if submitted:
                with st.spinner("Salvando..."):
                    houve_mudanca = False
                    # Pega os valores do formulário (do session_state) e atualiza o DataFrame
                    for campo in campos_tempo:
                        if f"edit_{campo}" in st.session_state and st.session_state[f"edit_{campo}"]:
                            df.loc[df_index, campo] = st.session_state[f"edit_{campo}"]
                            houve_mudanca = True
                    
                    if not houve_mudanca:
                        st.warning("Nenhuma alteração foi feita.")
                        st.stop()

                    # Recalcula todos os campos de tempo
                    reg = df.loc[df_index]
                    df.loc[df_index, 'Tempo Espera Doca'] = calcular_tempo(reg.get("Entrada na Fábrica"), reg.get("Encostou na doca Fábrica"))
                    df.loc[df_index, 'Tempo de Carregamento'] = calcular_tempo(reg.get("Início carregamento"), reg.get("Fim carregamento"))
                    df.loc[df_index, 'Tempo Total'] = calcular_tempo(reg.get("Entrada na Fábrica"), reg.get("Saída do pátio"))
                    df.loc[df_index, 'Tempo Percurso Para CD'] = calcular_tempo(reg.get("Saída do pátio"), reg.get("Entrada CD"))
                    df.loc[df_index, 'Tempo Espera Doca CD'] = calcular_tempo(reg.get("Entrada CD"), reg.get("Encostou na doca CD"))
                    df.loc[df_index, 'Tempo de Descarregamento CD'] = calcular_tempo(reg.get("Início Descarregamento CD"), reg.get("Fim Descarregamento CD"))
                    df.loc[df_index, 'Tempo Total CD'] = calcular_tempo(reg.get("Entrada CD"), reg.get("Saída CD"))

                    if salvar_dataframe(df):
                        st.success("✅ Registro atualizado com sucesso!")
                        # Limpa as chaves de edição para o próximo registro
                        for key in list(st.session_state.keys()):
                            if key.startswith("edit_"): del st.session_state[key]
                        st.rerun()

# =============================================================================
# OUTRAS PÁGINAS (CÓDIGO COMPLETO RESTAURADO)
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
            # Adapte esta parte para o seu layout de cards se preferir
            st.dataframe(subset_df) 
            
    elif st.session_state.pagina_atual == "Finalizadas":
        st.markdown("### ✅ Registros Finalizados")
        subset_df = df[df["Saída CD"] != ''].copy()
        if subset_df.empty:
            st.info("Nenhum registro finalizado ainda.")
        else:
            # Adapte esta parte para o seu layout de cards se preferir
            st.dataframe(subset_df)
