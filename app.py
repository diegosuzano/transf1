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

# --- INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
# Garante que a página inicial seja a padrão
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "Tela Inicial"

# Inicializa os campos de tempo para a tela de novo registro
for campo in campos_tempo:
    if campo not in st.session_state:
        st.session_state[campo] = ""

# --- CONFIGURAÇÃO DA PÁGINA E ESTILOS (CSS) ---
st.set_page_config(
    page_title="Suzano - Controle de Carga", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* ... (Seu CSS customizado permanece o mesmo) ... */
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
    .status-card {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid;
    }
    .status-info {
        background-color: #d1ecf1;
        border-color: #17a2b8;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNÇÕES AUXILIARES ---

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
    except Exception:
        return ""

def obter_status(registro):
    """Retorna o último evento registrado para um processo."""
    for campo in reversed(campos_tempo):
        if not pd.isna(registro[campo]) and registro[campo] != "":
            return campo
    return "Não iniciado"

def botao_voltar():
    """Cria um botão padrão para retornar ao menu principal."""
    if st.button("⬅️ Voltar ao Menu Principal", key="btn_voltar"):
        st.session_state.pagina_atual = "Tela Inicial"
        # Limpa o estado de edição ao voltar para o menu
        for key in list(st.session_state.keys()):
            if key.startswith("temp_edit_"):
                del st.session_state[key]
        st.rerun()

# >>> INÍCIO DA CORREÇÃO <<<
def carregar_dados_para_edicao():
    """
    Função chamada quando o selectbox de edição muda.
    Ela limpa o estado antigo e carrega os dados do novo registro selecionado.
    """
    opcao_selecionada = st.session_state.get("select_edicao")
    if not opcao_selecionada or opcao_selecionada == "Selecione um registro...":
        # Limpa os campos se nenhuma seleção válida for feita
        df_cols = ["Data", "Placa do caminhão", "Nome do conferente"] + campos_tempo + campos_calculados
        for coluna in df_cols:
            st.session_state[f"temp_edit_{coluna}"] = ""
        return
        
    placa_selecionada = opcao_selecionada.split(" | ")[0].replace("🚛 ", "")
    
    # Recarrega o dataframe para garantir dados atualizados
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
    incompletos = df[(pd.isna(df["Saída CD"])) | (df["Saída CD"] == "")]
    
    registro_para_editar = incompletos[incompletos['Placa do caminhão'] == placa_selecionada]
    
    if not registro_para_editar.empty:
        registro = registro_para_editar.iloc[0]
        # Atualiza o session_state com os dados do registro selecionado
        for coluna in df.columns:
            valor = registro[coluna]
            st.session_state[f"temp_edit_{coluna}"] = str(valor) if not pd.isna(valor) else ""
# >>> FIM DA CORREÇÃO <<<

# --- LAYOUT PRINCIPAL ---
st.markdown("<div class=\"main-header\">🚚 Suzano - Controle de Transferência de Carga</div>", unsafe_allow_html=True)

# --- NAVEGAÇÃO ENTRE PÁGINAS ---

# TELA INICIAL
if st.session_state.pagina_atual == "Tela Inicial":
    st.markdown("<div class=\"section-header\">📋 Escolha uma opção:</div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 NOVO REGISTRO", use_container_width=True):
            st.session_state.pagina_atual = "Lançar Novo Controle"
            st.rerun()
        if st.button("📊 EM OPERAÇÃO", use_container_width=True):
            st.session_state.pagina_atual = "Em Operação"
            st.rerun()
    with col2:
        if st.button("✏️ EDITAR REGISTRO", use_container_width=True):
            st.session_state.pagina_atual = "Editar Lançamentos Incompletos"
            st.rerun()
        if st.button("✅ FINALIZADAS", use_container_width=True):
            st.session_state.pagina_atual = "Finalizadas"
            st.rerun()
    # ... (Resto da sua tela inicial, que já estava boa)

# LANÇAR NOVO CONTROLE
elif st.session_state.pagina_atual == "Lançar Novo Controle":
    botao_voltar()
    st.markdown("<div class=\"section-header\">🆕 Novo Registro de Transferência</div>", unsafe_allow_html=True)
    # ... (Seu código para novo registro, que já estava bom)
    # ... (Para manter o foco, omiti o código que não foi alterado)
    # ... (Copie e cole a sua seção "Lançar Novo Controle" aqui)

# EDITAR LANÇAMENTOS INCOMPLETOS (SEÇÃO MODIFICADA)
elif st.session_state.pagina_atual == "Editar Lançamentos Incompletos":
    botao_voltar()
    st.markdown("<div class=\"section-header\">✏️ Editar Registros Incompletos</div>", unsafe_allow_html=True)

    if not os.path.exists(EXCEL_PATH):
        st.error("❌ Planilha não encontrada. Crie um registro primeiro.")
    else:
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        # Garante que a coluna 'Saída CD' exista para evitar erros
        if "Saída CD" not in df.columns:
            df["Saída CD"] = ""
            
        incompletos = df[(pd.isna(df["Saída CD"])) | (df["Saída CD"] == "")]

        if incompletos.empty:
            st.success("🎉 Todos os registros estão completos!")
        else:
            st.info(f"📋 Encontrados {len(incompletos)} registros incompletos.")
            
            opcoes = ["Selecione um registro..."]
            for idx, row in incompletos.iterrows():
                placa = row.get('Placa do caminhão', 'N/A')
                data = row.get('Data', 'N/A')
                status = obter_status(row)
                opcoes.append(f"🚛 {placa} | 📅 {data} | 📍 {status}")
            
            # Selectbox agora usa a função 'on_change' para carregar os dados corretos
            st.selectbox(
                "Selecione um registro para editar:", 
                opcoes, 
                key="select_edicao",
                on_change=carregar_dados_para_edicao
            )
            
            # Verifica se uma opção válida foi selecionada
            if st.session_state.get("select_edicao") and st.session_state.select_edicao != "Selecione um registro...":
                
                placa_selecionada = st.session_state.select_edicao.split(" | ")[0].replace("🚛 ", "")
                idx = incompletos[incompletos['Placa do caminhão'] == placa_selecionada].index[0]
                
                st.markdown(f'<div class="status-card status-info"><strong>Editando registro da placa: {placa_selecionada}</strong></div>', unsafe_allow_html=True)
                
                # Identifica os campos que ainda precisam ser preenchidos
                campos_a_preencher = [col for col in campos_tempo if st.session_state.get(f"temp_edit_{col}", "") == ""]

                if not campos_a_preencher:
                    st.success("✅ Este registro já está completo! Salve para finalizar.")
                
                st.markdown("<div class=\"section-header\">📝 Preencha os campos pendentes</div>", unsafe_allow_html=True)
                
                # Mostra apenas os campos que estão vazios e precisam de edição
                for coluna in campos_a_preencher:
                    if coluna in campos_tempo: # Garante que só campos de tempo tenham o botão "Agora"
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            # O valor é lido diretamente do session_state, que foi preenchido pela função de callback
                            st.text_input(f"📋 {coluna}", key=f"temp_edit_{coluna}")
                        with col2:
                            # Função para atualizar o horário com um clique
                            def update_time(col):
                                st.session_state[f"temp_edit_{col}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                            st.button("⏰ Agora", key=f"btn_now_{coluna}", on_click=update_time, args=(coluna,))

                st.markdown("---")
                if st.button("💾 SALVAR ALTERAÇÕES", key="btn_salvar_edicao", use_container_width=True):
                    # Atualiza o DataFrame com os novos valores do session_state
                    for coluna in campos_a_preencher:
                        novo_valor = st.session_state.get(f"temp_edit_{coluna}", "").strip()
                        if novo_valor:
                            df.at[idx, coluna] = novo_valor
                    
                    # Recalcula todos os tempos para garantir consistência
                    registro_atualizado = df.loc[idx]
                    df.at[idx, "Tempo Espera Doca"] = calcular_tempo(registro_atualizado.get("Entrada na Fábrica"), registro_atualizado.get("Encostou na doca Fábrica"))
                    df.at[idx, "Tempo de Carregamento"] = calcular_tempo(registro_atualizado.get("Início carregamento"), registro_atualizado.get("Fim carregamento"))
                    df.at[idx, "Tempo Total"] = calcular_tempo(registro_atualizado.get("Entrada na Fábrica"), registro_atualizado.get("Saída do pátio"))
                    df.at[idx, "Tempo Percurso Para CD"] = calcular_tempo(registro_atualizado.get("Saída do pátio"), registro_atualizado.get("Entrada CD"))
                    df.at[idx, "Tempo Espera Doca CD"] = calcular_tempo(registro_atualizado.get("Entrada CD"), registro_atualizado.get("Encostou na doca CD"))
                    df.at[idx, "Tempo de Descarregamento CD"] = calcular_tempo(registro_atualizado.get("Início Descarregamento CD"), registro_atualizado.get("Fim Descarregamento CD"))
                    df.at[idx, "Tempo Total CD"] = calcular_tempo(registro_atualizado.get("Entrada CD"), registro_atualizado.get("Saída CD"))

                    try:
                        # Salva o DataFrame inteiro de volta no Excel
                        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                            df.to_excel(writer, sheet_name=SHEET_NAME, index=False)
                        
                        st.success("✅ Registro atualizado com sucesso!")
                        
                        # Limpa os campos de edição do session_state para a próxima edição
                        for key in list(st.session_state.keys()):
                            if key.startswith("temp_edit_"):
                                del st.session_state[key]
                        
                        st.rerun()

                    except Exception as e:
                        st.error(f"❌ Erro ao salvar a planilha: {e}")

# EM OPERAÇÃO
elif st.session_state.pagina_atual == "Em Operação":
    botao_voltar()
    st.markdown("<div class=\"section-header\">🚛 Registros em Operação</div>", unsafe_allow_html=True)
    # ... (Seu código para "Em Operação", que já estava bom)
    # ... (Copie e cole a sua seção "Em Operação" aqui)

# FINALIZADAS
elif st.session_state.pagina_atual == "Finalizadas":
    botao_voltar()
    st.markdown("<div class=\"section-header\">✅ Registros Finalizados</div>", unsafe_allow_html=True)
    # ... (Seu código para "Finalizadas", que já estava bom)
    # ... (Copie e cole a sua seção "Finalizadas" aqui)

