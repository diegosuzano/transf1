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
st.set_page_config(page_title="Suzano - Controle de Carga", layout="wide")
st.markdown("""<style>...</style>""", unsafe_allow_html=True) # Seu CSS aqui

# --- FUNÇÕES AUXILIARES ---
@st.cache_data(ttl=60)
def carregar_dataframe():
    if not os.path.exists(EXCEL_PATH):
        return pd.DataFrame(columns=COLUNAS_ESPERADAS)
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        for col in COLUNAS_ESPERADAS:
            if col not in df.columns: df[col] = pd.NA
        return df[COLUNAS_ESPERADAS]
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
    if pd.isna(inicio) or pd.isna(fim) or inicio == "" or fim == "": return ""
    try:
        diff = pd.to_datetime(fim) - pd.to_datetime(inicio)
        horas = int(diff.total_seconds() // 3600)
        minutos = int((diff.total_seconds() % 3600) // 60)
        return f"{horas:02d}:{minutos:02d}"
    except: return ""

def obter_status(registro):
    for campo in reversed(campos_tempo):
        valor = registro.get(campo)
        if pd.notna(valor) and str(valor).strip() != '': return campo
    return "Não iniciado"

def botao_voltar():
    if st.button("⬅️ Voltar ao Menu Principal"):
        for key in list(st.session_state.keys()):
            if key.startswith("edit_") or key.startswith("selectbox_"): del st.session_state[key]
        st.session_state.pagina_atual = "Tela Inicial"
        st.rerun()

# --- LAYOUT PRINCIPAL ---
st.markdown("<h1 style='text-align: center;'>🚚 Suzano - Controle de Transferência de Carga</h1>", unsafe_allow_html=True)

# =============================================================================
# TELA INICIAL
# =============================================================================
if st.session_state.pagina_atual == "Tela Inicial":
    # ... Seu código da tela inicial aqui ...
    if st.button("✏️ EDITAR REGISTRO"):
        st.session_state.pagina_atual = "Editar"
        st.rerun()

# =============================================================================
# PÁGINA DE EDIÇÃO (LÓGICA FINAL E CORRIGIDA)
# =============================================================================
elif st.session_state.pagina_atual == "Editar":
    botao_voltar()
    st.markdown("### ✏️ Editar Registros Incompletos")

    df = carregar_dataframe()
    incompletos = df[pd.isna(df["Saída CD"]) | (df["Saída CD"] == "")].copy()

    if incompletos.empty:
        st.success("🎉 Todos os registros estão completos!")
        st.stop()

    incompletos['df_index'] = incompletos.index
    opcoes = {f"🚛 {row['Placa do caminhão']} | 📅 {row['Data']} | 📍 {obter_status(row)}": idx for idx, row in incompletos.iterrows()}
    
    def on_selection_change():
        for key in list(st.session_state.keys()):
            if key.startswith("edit_val_"): del st.session_state[key]

    selecao_label = st.selectbox(
        "Selecione um registro para editar:",
        options=["Selecione..."] + list(opcoes.keys()),
        key="selectbox_edicao",
        on_change=on_selection_change
    )

    if selecao_label and selecao_label != "Selecione...":
        df_index_selecionado = opcoes[selecao_label]
        registro_original = df.loc[df_index_selecionado].to_dict()
        
        st.markdown(f"#### Editando Placa: **{registro_original['Placa do caminhão']}**")

        # >>> INÍCIO DA CORREÇÃO <<<
        # Criamos um espaço reservado (placeholder) para os widgets de edição.
        # Isso nos permite processar a lógica do botão ANTES de desenhar os widgets.
        edit_placeholder = st.empty()
        
        # Verificamos se algum botão "Agora" foi pressionado.
        # A chave do botão clicado é armazenada pelo Streamlit no session_state.
        # Ex: st.session_state.btn_now_Início_carregamento será True se esse botão for clicado.
        campo_clicado = None
        for campo in campos_tempo:
            if st.session_state.get(f"btn_now_{campo.replace(' ', '_')}"):
                campo_clicado = campo
                break

        # Se um botão foi clicado, atualizamos o estado e recarregamos.
        if campo_clicado:
            st.session_state[f"edit_val_{campo_clicado}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
            # Limpamos o estado do botão para evitar um loop
            del st.session_state[f"btn_now_{campo_clicado.replace(' ', '_')}"]
            st.rerun()

        # Agora, dentro do placeholder, renderizamos os widgets.
        # Esta parte do código só é executada quando nenhum botão "Agora" foi clicado na passagem atual.
        with edit_placeholder.container():
            for campo in campos_tempo:
                valor_atual = st.session_state.get(f"edit_val_{campo}", registro_original.get(campo))
                
                if pd.isna(valor_atual) or str(valor_atual).strip() == '':
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text_input(f"📋 {campo}", key=f"edit_val_{campo}")
                    with col2:
                        # Usamos uma chave única para o botão, sem caracteres especiais
                        st.button("⏰ Agora", key=f"btn_now_{campo.replace(' ', '_')}")
            # >>> FIM DA CORREÇÃO <<<

            st.markdown("---")
            if st.button("💾 SALVAR ALTERAÇÕES", use_container_width=True, type="primary"):
                # A lógica de salvamento permanece a mesma, pois já estava correta.
                with st.spinner("Salvando..."):
                    houve_mudanca = False
                    for campo in campos_tempo:
                        chave_sessao = f"edit_val_{campo}"
                        if chave_sessao in st.session_state:
                            novo_valor = st.session_state[chave_sessao]
                            if novo_valor and pd.isna(df.at[df_index_selecionado, campo]):
                                df.at[df_index_selecionado, campo] = novo_valor
                                houve_mudanca = True
                    
                    if not houve_mudanca:
                        st.warning("Nenhuma alteração foi feita.")
                        st.stop()

                    # Recalcula os campos de tempo
                    registro_atualizado = df.loc[df_index_selecionado]
                    for calc_campo in campos_calculados:
                        # Adapte esta lógica para seus cálculos específicos
                        if calc_campo == "Tempo Espera Doca":
                            df.at[df_index_selecionado, calc_campo] = calcular_tempo(registro_atualizado.get("Entrada na Fábrica"), registro_atualizado.get("Encostou na doca Fábrica"))
                        # ... adicione os outros cálculos aqui ...

                    if salvar_dataframe(df):
                        st.success("✅ Registro atualizado com sucesso!")
                        on_selection_change()
                        st.session_state.selectbox_edicao = "Selecione..."
                        st.rerun()

# =============================================================================
# OUTRAS PÁGINAS
# =============================================================================
# Adicione aqui o código para as páginas "Novo", "Em Operação" e "Finalizadas"
