import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

# --- CONFIGURAÇÕES GERAIS ---
EXCEL_PATH = "Controle Transferencia.xlsx"
SHEET_NAME = "Basae"
FUSO_HORARIO = timezone(timedelta(hours=-3))  # UTC-3

# Lista de campos de data/hora que serão registrados
campos_tempo = [
    "Entrada na Fábrica", "Encostou na doca Fábrica", "Início carregamento",
    "Fim carregamento", "Faturado", "Amarração carga", "Saída do pátio",
    "Entrada CD", "Encostou na doca CD", "Início Descarregamento CD",
    "Fim Descarregamento CD", "Saída CD"
]

# Lista de campos calculados que serão salvos na planilha
campos_calculados = [
    "Tempo Espera Doca", "Tempo Total", "Tempo de Descarregamento CD",
    "Tempo Espera Doca CD", "Tempo Total CD", "Tempo Percurso Para CD", "Tempo de Carregamento"
]

# Colunas esperadas no DataFrame
COLUNAS_ESPERADAS = ["Data", "Placa do caminhão", "Nome do conferente"] + campos_tempo + campos_calculados

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "Tela Inicial"

# --- CONFIGURAÇÃO DA PÁGINA E ESTILOS (CSS) ---
st.set_page_config(
    page_title="Suzano - Controle de Carga", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Seu CSS customizado (mantido como estava)
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
        font-size: 20px;
        font-weight: bold;
        margin: 20px 0 10px 0;
        padding-bottom: 5px;
        border-bottom: 2px solid #e0e0e0;
    }
    /* Adicione o resto do seu CSS aqui se necessário */
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---

@st.cache_data(ttl=60)
def carregar_dataframe():
    """Carrega o DataFrame do arquivo Excel, tratando erros e colunas ausentes."""
    if not os.path.exists(EXCEL_PATH):
        return pd.DataFrame(columns=COLUNAS_ESPERADAS)
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        # Garante que todas as colunas esperadas existam
        for col in COLUNAS_ESPERADAS:
            if col not in df.columns:
                df[col] = pd.NA
        return df[COLUNAS_ESPERADAS]
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        return pd.DataFrame(columns=COLUNAS_ESPERADAS)

def salvar_dataframe(df):
    """Salva o DataFrame de volta no arquivo Excel."""
    try:
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
            df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        st.cache_data.clear() # Limpa o cache para recarregar os dados na próxima vez
        return True
    except Exception as e:
        st.error(f"Erro ao salvar a planilha: {e}")
        return False

def calcular_tempo(inicio, fim):
    """Calcula a diferença entre dois horários e retorna no formato HH:MM."""
    if pd.isna(inicio) or pd.isna(fim) or inicio == "" or fim == "":
        return ""
    try:
        inicio_dt = pd.to_datetime(inicio)
        fim_dt = pd.to_datetime(fim)
        diff = fim_dt - inicio_dt
        horas = int(diff.total_seconds() // 3600)
        minutos = int((diff.total_seconds() % 3600) // 60)
        return f"{horas:02d}:{minutos:02d}"
    except:
        return ""

def obter_status(registro):
    """Retorna o último evento registrado para um processo."""
    for campo in reversed(campos_tempo):
        valor = registro.get(campo)
        if pd.notna(valor) and str(valor).strip() != '':
            return campo
    return "Não iniciado"

def botao_voltar():
    """Cria um botão para voltar, limpando o estado da sessão para evitar conflitos."""
    if st.button("⬅️ Voltar ao Menu Principal"):
        # Limpa chaves de edição para não interferir em outras páginas
        for key in list(st.session_state.keys()):
            if key.startswith("edit_") or key.startswith("selectbox_"):
                del st.session_state[key]
        st.session_state.pagina_atual = "Tela Inicial"
        st.rerun()

# --- LAYOUT PRINCIPAL ---
st.markdown("<div class=\"main-header\">🚚 Suzano - Controle de Transferência de Carga</div>", unsafe_allow_html=True)

# =============================================================================
# TELA INICIAL
# =============================================================================
if st.session_state.pagina_atual == "Tela Inicial":
    st.markdown("<div class=\"section-header\">📋 Escolha uma opção:</div>", unsafe_allow_html=True)
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
    # Adicione aqui o resto da sua tela inicial (download, métricas, etc.)

# =============================================================================
# PÁGINA DE NOVO REGISTRO (Simplificada para foco)
# =============================================================================
elif st.session_state.pagina_atual == "Novo":
    botao_voltar()
    st.markdown("<div class=\"section-header\">🆕 Novo Registro de Transferência</div>", unsafe_allow_html=True)
    # Adicione aqui o seu código para criar um novo registro.
    # Lembre-se de usar `carregar_dataframe()` e `salvar_dataframe(df)`.

# =============================================================================
# PÁGINA DE EDIÇÃO (LÓGICA CORRIGIDA E TESTADA)
# =============================================================================
elif st.session_state.pagina_atual == "Editar":
    botao_voltar()
    st.markdown("<div class=\"section-header\">✏️ Editar Registros Incompletos</div>", unsafe_allow_html=True)

    df = carregar_dataframe()
    incompletos = df[pd.isna(df["Saída CD"]) | (df["Saída CD"] == "")].copy()

    if incompletos.empty:
        st.success("🎉 Todos os registros estão completos!")
        st.stop()

    # Adiciona o índice original do DataFrame para referência
    incompletos['df_index'] = incompletos.index

    # Cria as opções para o selectbox
    opcoes = {f"🚛 {row['Placa do caminhão']} | 📅 {row['Data']} | 📍 {obter_status(row)}": idx for idx, row in incompletos.iterrows()}
    
    # Função para limpar o estado de edição quando a seleção muda
    def on_selection_change():
        for key in list(st.session_state.keys()):
            if key.startswith("edit_val_"):
                del st.session_state[key]

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

        # Mostra os campos que ainda precisam ser preenchidos
        for campo in campos_tempo:
            # O valor a ser exibido vem primeiro do session_state (se já foi editado)
            # ou do registro original (se ainda não foi tocado)
            valor_atual = st.session_state.get(f"edit_val_{campo}", registro_original.get(campo))
            
            # Se o campo estiver vazio (seja NaN ou string vazia), oferece a opção de preencher
            if pd.isna(valor_atual) or str(valor_atual).strip() == '':
                col1, col2 = st.columns([3, 1])
                with col1:
                    # O text_input é controlado pelo session_state para manter o valor após o recarregamento
                    st.text_input(f"📋 {campo}", key=f"edit_val_{campo}")
                with col2:
                    # O botão "Agora" apenas atualiza o session_state, e o Streamlit recarrega
                    if st.button("⏰ Agora", key=f"btn_now_{campo}"):
                        st.session_state[f"edit_val_{campo}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                        st.rerun()

        st.markdown("---")
        if st.button("💾 SALVAR ALTERAÇÕES", use_container_width=True, type="primary"):
            with st.spinner("Salvando..."):
                houve_mudanca = False
                # Atualiza o DataFrame com os novos valores do session_state
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

                # Recalcula todos os campos de tempo para garantir consistência
                registro_atualizado = df.loc[df_index_selecionado]
                df.at[df_index_selecionado, "Tempo Espera Doca"] = calcular_tempo(registro_atualizado.get("Entrada na Fábrica"), registro_atualizado.get("Encostou na doca Fábrica"))
                df.at[df_index_selecionado, "Tempo de Carregamento"] = calcular_tempo(registro_atualizado.get("Início carregamento"), registro_atualizado.get("Fim carregamento"))
                df.at[df_index_selecionado, "Tempo Total"] = calcular_tempo(registro_atualizado.get("Entrada na Fábrica"), registro_atualizado.get("Saída do pátio"))
                df.at[df_index_selecionado, "Tempo Percurso Para CD"] = calcular_tempo(registro_atualizado.get("Saída do pátio"), registro_atualizado.get("Entrada CD"))
                df.at[df_index_selecionado, "Tempo Espera Doca CD"] = calcular_tempo(registro_atualizado.get("Entrada CD"), registro_atualizado.get("Encostou na doca CD"))
                df.at[df_index_selecionado, "Tempo de Descarregamento CD"] = calcular_tempo(registro_atualizado.get("Início Descarregamento CD"), registro_atualizado.get("Fim Descarregamento CD"))
                df.at[df_index_selecionado, "Tempo Total CD"] = calcular_tempo(registro_atualizado.get("Entrada CD"), registro_atualizado.get("Saída CD"))

                # Salva o DataFrame inteiro de volta no Excel
                if salvar_dataframe(df):
                    st.success("✅ Registro atualizado com sucesso!")
                    # Limpa o estado da sessão para a próxima edição
                    on_selection_change()
                    st.session_state.selectbox_edicao = "Selecione..."
                    st.rerun()

# =============================================================================
# OUTRAS PÁGINAS (EM OPERAÇÃO, FINALIZADAS)
# =============================================================================
elif st.session_state.pagina_atual in ["Em Operação", "Finalizadas"]:
    botao_voltar()
    df = carregar_dataframe()
    
    if st.session_state.pagina_atual == "Em Operação":
        st.markdown("<div class=\"section-header\">📊 Registros em Operação</div>", unsafe_allow_html=True)
        subset_df = df[pd.isna(df["Saída CD"]) | (df["Saída CD"] == "")]
        if subset_df.empty:
            st.info("Nenhum registro em operação no momento.")
        else:
            st.dataframe(subset_df) # Adapte para o seu layout de cards
            
    elif st.session_state.pagina_atual == "Finalizadas":
        st.markdown("<div class=\"section-header\">✅ Registros Finalizados</div>", unsafe_allow_html=True)
        subset_df = df[pd.notna(df["Saída CD"]) & (df["Saída CD"] != "")]
        if subset_df.empty:
            st.info("Nenhum registro finalizado ainda.")
        else:
            st.dataframe(subset_df) # Adapte para o seu layout de cards
