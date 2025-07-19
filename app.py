import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

# Configurações
EXCEL_PATH = "Controle Transferencia.xlsx"
SHEET_NAME = "Basae"
FUSO_HORARIO = timezone(timedelta(hours=-3))  # UTC-3

campos_tempo = [
    "Entrada na Fábrica", "Encostou na doca Fábrica", "Início carregamento",
    "Fim carregamento", "Faturado", "Amarração carga", "Saída do pátio",
    "Entrada CD", "Encostou na doca CD", "Início Descarregamento CD",
    "Fim Descarregamento CD", "Saída CD"
]

# Campos de cálculo que devem ser salvos
campos_calculados = [
    "Tempo Espera Doca", "Tempo Total", "Tempo de Descarregamento CD",
    "Tempo Espera Doca CD", "Tempo Total CD", "Tempo Percurso Para CD", "Tempo de Carregamento"
]

# Inicializa session_state para os campos de tempo
for campo in campos_tempo:
    if campo not in st.session_state:
        st.session_state[campo] = ""

# Inicializa página atual se não existir
if 'pagina_atual' not in st.session_state:
    st.session_state.pagina_atual = "Tela Inicial"

# Configuração da página
st.set_page_config(
    page_title="Suzano - Controle de Carga", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS customizado para melhorar a aparência
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
    
    .big-button {
        width: 100%;
        height: 80px;
        font-size: 18px;
        font-weight: bold;
        margin: 10px 0;
        border-radius: 10px;
        border: none;
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .btn-primary {
        background: linear-gradient(45deg, #2e8b57, #3cb371);
        color: white;
    }
    
    .btn-secondary {
        background: linear-gradient(45deg, #4682b4, #5f9ea0);
        color: white;
    }
    
    .btn-info {
        background: linear-gradient(45deg, #ff8c00, #ffa500);
        color: white;
    }
    
    .btn-warning {
        background: linear-gradient(45deg, #dc143c, #ff6347);
        color: white;
    }
    
    .back-button {
        background: linear-gradient(45deg, #696969, #808080);
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        border: none;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    .status-card {
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid;
    }
    
    .status-success {
        background-color: #d4edda;
        border-color: #28a745;
        color: #155724;
    }
    
    .status-warning {
        background-color: #fff3cd;
        border-color: #ffc107;
        color: #856404;
    }
    
    .status-info {
        background-color: #d1ecf1;
        border-color: #17a2b8;
        color: #0c5460;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
        margin: 10px 0;
    }
    
    .section-header {
        color: #1f4e79;
        font-size: 20px;
        font-weight: bold;
        margin: 20px 0 10px 0;
        padding-bottom: 5px;
        border-bottom: 2px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Função para calcular diferença de tempo
def calcular_tempo(inicio, fim):
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

# Função para encontrar o último campo preenchido (status)
def obter_status(registro):
    for campo in reversed(campos_tempo):
        if not pd.isna(registro[campo]) and registro[campo] != "":
            return campo
    return "Não iniciado"

# Função para botão de voltar
def botao_voltar():
    if st.button("⬅️ Voltar ao Menu Principal", key="btn_voltar", help="Clique para voltar à tela inicial"):
        st.session_state.pagina_atual = "Tela Inicial"
        st.rerun()

# Header principal
st.markdown("<div class=\"main-header\">🚚 Suzano - Controle de Transferência de Carga</div>", unsafe_allow_html=True)

# TELA INICIAL COM BOTÕES
if st.session_state.pagina_atual == "Tela Inicial":
    st.markdown("<div class=\"section-header\">📋 Escolha uma opção:</div>", unsafe_allow_html=True)
    
    # Layout em colunas para os botões principais
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🆕 NOVO REGISTRO", key="btn_novo", help="Registrar uma nova transferência de carga", use_container_width=True):
            st.session_state.pagina_atual = "Lançar Novo Controle"
            st.rerun()
        
        if st.button("📊 EM OPERAÇÃO", key="btn_operacao", help="Ver cargas em andamento", use_container_width=True):
            st.session_state.pagina_atual = "Em Operação"
            st.rerun()
    
    with col2:
        if st.button("✏️ EDITAR REGISTRO", key="btn_editar", help="Editar registros incompletos", use_container_width=True):
            st.session_state.pagina_atual = "Editar Lançamentos Incompletos"
            st.rerun()
        
        if st.button("✅ FINALIZADAS", key="btn_finalizadas", help="Ver cargas finalizadas", use_container_width=True):
            st.session_state.pagina_atual = "Finalizadas"
            st.rerun()
    
    # Seção de informações e download
    st.markdown("<div class=\"section-header\">📥 Download da Planilha</div>", unsafe_allow_html=True)
    
    if os.path.exists(EXCEL_PATH):
        with open(EXCEL_PATH, "rb") as f:
            st.download_button(
                label="📥 Baixar Planilha Atual",
                data=f,
                file_name=EXCEL_PATH,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.info("📋 Nenhuma planilha encontrada. Crie o primeiro registro para gerar a planilha.")
    
    # Estatísticas rápidas se houver dados
    if os.path.exists(EXCEL_PATH):
        try:
            df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
            
            st.markdown("<div class=\"section-header\">📈 Resumo Rápido</div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_registros = len(df)
                st.metric("📋 Total de Registros", total_registros)
            
            with col2:
                em_operacao = len(df[(pd.isna(df["Saída CD"])) | (df["Saída CD"] == "")])
                st.metric("🚛 Em Operação", em_operacao)
            
            with col3:
                finalizadas = len(df[~(pd.isna(df["Saída CD"])) & (df["Saída CD"] != "")])
                st.metric("✅ Finalizadas", finalizadas)
                
        except Exception as e:
            st.warning("⚠️ Erro ao carregar estatísticas da planilha.")

# LANÇAR NOVO CONTROLE
elif st.session_state.pagina_atual == "Lançar Novo Controle":
    botao_voltar()
    
    st.markdown("<div class=\"section-header\">🆕 Novo Registro de Transferência</div>", unsafe_allow_html=True)
    
    # Dados básicos em layout mais limpo
    col1, col2, col3 = st.columns(3)
    
    with col1:
        data = st.date_input("📅 Data", value=datetime.now(FUSO_HORARIO).date())
    with col2:
        placa = st.text_input("🚛 Placa do Caminhão", placeholder="Ex: ABC-1234")
    with col3:
        conferente = st.text_input("👤 Nome do Conferente", placeholder="Digite o nome")

    # Seção Fábrica
    st.markdown("<div class=\"section-header\">🏭 Registros da Fábrica</div>", unsafe_allow_html=True)
    
    for i, campo in enumerate(campos_tempo[:7]):
        col1, col2 = st.columns([3, 1])
        with col1:
            valor_atual = st.session_state[campo]
            if valor_atual:
                st.success(f"✅ {campo}: {valor_atual}")
            else:
                st.info(f"⏳ {campo}: Aguardando registro...")
        with col2:
            if st.button(f"📝 Registrar", key=f"btn_{campo}", help=f"Registrar {campo}"):
                st.session_state[campo] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"✅ {campo} registrado!")
                st.rerun()

    # Seção CD
    st.markdown("<div class=\"section-header\">📦 Registros do Centro de Distribuição</div>", unsafe_allow_html=True)
    
    for campo in campos_tempo[7:]:
        col1, col2 = st.columns([3, 1])
        with col1:
            valor_atual = st.session_state[campo]
            if valor_atual:
                st.success(f"✅ {campo}: {valor_atual}")
            else:
                st.info(f"⏳ {campo}: Aguardando registro...")
        with col2:
            if st.button(f"📝 Registrar", key=f"btn_{campo}", help=f"Registrar {campo}"):
                st.session_state[campo] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                st.success(f"✅ {campo} registrado!")
                st.rerun()

    # Botão de salvar destacado
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 SALVAR REGISTRO", key="btn_salvar", help="Salvar todos os dados registrados", use_container_width=True):
            if not placa or not conferente:
                st.error("❌ Por favor, preencha a placa do caminhão e o nome do conferente!")
            else:
                # Calcular os tempos antes de salvar
                tempo_espera_doca = calcular_tempo(st.session_state.get("Entrada na Fábrica"), st.session_state.get("Encostou na doca Fábrica"))
                tempo_total = calcular_tempo(st.session_state.get("Entrada na Fábrica"), st.session_state.get("Saída do pátio"))
                tempo_descarregamento_cd = calcular_tempo(st.session_state.get("Início Descarregamento CD"), st.session_state.get("Fim Descarregamento CD"))
                tempo_espera_doca_cd = calcular_tempo(st.session_state.get("Entrada CD"), st.session_state.get("Encostou na doca CD"))
                tempo_total_cd = calcular_tempo(st.session_state.get("Entrada CD"), st.session_state.get("Saída CD"))
                tempo_percurso_para_cd = calcular_tempo(st.session_state.get("Saída do pátio"), st.session_state.get("Entrada CD"))
                tempo_carregamento = calcular_tempo(st.session_state.get("Início carregamento"), st.session_state.get("Fim carregamento"))
                
                nova_linha = {
                    "Data": data.strftime("%Y-%m-%d"),
                    "Placa do caminhão": placa,
                    "Nome do conferente": conferente,
                    **{campo: st.session_state[campo] for campo in campos_tempo},
                    "Tempo Espera Doca": tempo_espera_doca,
                    "Tempo Total": tempo_total,
                    "Tempo de Descarregamento CD": tempo_descarregamento_cd,
                    "Tempo Espera Doca CD": tempo_espera_doca_cd,
                    "Tempo Total CD": tempo_total_cd,
                    "Tempo Percurso Para CD": tempo_percurso_para_cd,
                    "Tempo de Carregamento": tempo_carregamento
                }
                
                try:
                    if os.path.exists(EXCEL_PATH):
                        df_existente = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
                        # Definir a ordem esperada das colunas
                        colunas_esperadas = ["Data", "Placa do caminhão", "Nome do conferente"] + campos_tempo + campos_calculados
                        
                        # Adicionar colunas ausentes ao df_existente com valores vazios
                        for col in colunas_esperadas:
                            if col not in df_existente.columns:
                                df_existente[col] = ""
                        
                        # Reordenar as colunas do df_existente
                        df_existente = df_existente[colunas_esperadas]
                        
                        df_novo = pd.concat([df_existente, pd.DataFrame([nova_linha])], ignore_index=True)
                    else:
                        # Criar um DataFrame com todas as colunas esperadas, incluindo as calculadas
                        colunas_iniciais = ["Data", "Placa do caminhão", "Nome do conferente"] + campos_tempo + campos_calculados
                        df_novo = pd.DataFrame([nova_linha], columns=colunas_iniciais)

                    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                        df_novo.to_excel(writer, sheet_name=SHEET_NAME, index=False)

                    st.success("✅ Registro salvo com sucesso!")
                    
                    # Limpa campos depois de salvar
                    for campo in campos_tempo:
                        st.session_state[campo] = ""
                    
                    # Opção de voltar ou criar novo
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🏠 Voltar ao Menu", key="btn_voltar_pos_salvar"):
                            st.session_state.pagina_atual = "Tela Inicial"
                            st.rerun()
                    with col2:
                        if st.button("🆕 Novo Registro", key="btn_novo_pos_salvar"):
                            st.rerun()

                except Exception as e:
                    st.error(f"❌ Erro ao salvar: {str(e)}")

# EDITAR LANÇAMENTOS INCOMPLETOS
elif st.session_state.pagina_atual == "Editar Lançamentos Incompletos":
    botao_voltar()
    
    st.markdown("<div class=\"section-header\">✏️ Editar Registros Incompletos</div>", unsafe_allow_html=True)

    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        incompletos = df[(pd.isna(df["Saída CD"])) | (df["Saída CD"] == "")]

        if not incompletos.empty:
            # Seleção mais visual
            st.info(f"📋 Encontrados {len(incompletos)} registros incompletos")
            
            opcoes = []
            for idx in incompletos.index:
                placa = incompletos.loc[idx, 'Placa do caminhão']
                data = incompletos.loc[idx, 'Data']
                status = obter_status(incompletos.loc[idx])
                opcoes.append(f"🚛 {placa} | 📅 {data} | 📍 {status}")
            
            opcao_selecionada = st.selectbox("Selecione um registro para editar:", opcoes, key="select_edicao")
            
            if opcao_selecionada:
                # Extrair índice da opção selecionada
                placa_selecionada = opcao_selecionada.split(" | ")[0].replace("🚛 ", "")
                idx = incompletos[incompletos['Placa do caminhão'] == placa_selecionada].index[0]
                
                registro = incompletos.loc[idx]
                
                st.markdown(f'<div class="status-card status-info"><strong>Editando registro da placa: {registro["Placa do caminhão"]}</strong></div>', unsafe_allow_html=True)
                
                # Inicializa session_state para os campos editáveis se ainda não existirem
                for coluna in df.columns:
                    if f"temp_edit_{coluna}" not in st.session_state:
                        st.session_state[f"temp_edit_{coluna}"] = str(registro[coluna]) if not pd.isna(registro[coluna]) else ""

                # Campos editáveis organizados por seção
                campos_editaveis = []
                for coluna in df.columns:
                    valor = registro[coluna]
                    if pd.isna(valor) or valor == "":
                        campos_editaveis.append(coluna)

                if campos_editaveis:
                    st.markdown("<div class=\"section-header\">📝 Campos Disponíveis para Edição</div>", unsafe_allow_html=True)
                    
                    for coluna in campos_editaveis:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.text_input(f"📋 {coluna}", value=st.session_state[f"temp_edit_{coluna}"], key=f"temp_edit_{coluna}")
                        with col2:
                            if coluna in campos_tempo:
                                def update_time(col):
                                    st.session_state[f"temp_edit_{col}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                                st.button(f"⏰ Agora", key=f"btn_now_{coluna}", on_click=update_time, args=(coluna,))

                    st.markdown("---")
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button("💾 SALVAR ALTERAÇÕES", key="btn_salvar_edicao", use_container_width=True):
                            for coluna in df.columns:
                                if pd.isna(registro[coluna]) or registro[coluna] == "":
                                    novo_valor = st.session_state[f"temp_edit_{coluna}"]
                                    if novo_valor.strip() != "":
                                        df.at[idx, coluna] = novo_valor

                            with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                                df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

                            st.success("✅ Registro atualizado com sucesso!")
                            
                            # Limpa os campos editáveis do session_state
                            for coluna in df.columns:
                                if f"temp_edit_{coluna}" in st.session_state:
                                    del st.session_state[f"temp_edit_{coluna}"]
                            
                            st.rerun()
                else:
                    st.success("✅ Este registro já está completo!")
        else:
            st.success("🎉 Todos os registros estão completos!")
    else:
        st.error("❌ Planilha não encontrada.")

# EM OPERAÇÃO
elif st.session_state.pagina_atual == "Em Operação":
    botao_voltar()
    
    st.markdown("<div class=\"section-header\">🚛 Registros em Operação</div>", unsafe_allow_html=True)
    
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        em_operacao = df[(pd.isna(df["Saída CD"])) | (df["Saída CD"] == "")]
        
        if not em_operacao.empty:
            # Métricas em cards visuais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🚚 Veículos em Operação", len(em_operacao))
            with col2:
                na_fabrica = len(em_operacao[pd.isna(em_operacao["Entrada CD"]) | (em_operacao["Entrada CD"] == "")])
                st.metric("🏭 Na Fábrica", na_fabrica)
            with col3:
                no_cd = len(em_operacao) - na_fabrica
                st.metric("📦 No CD", no_cd)
            
            st.markdown("---")
            
            # Cards de veículos mais visuais
            for idx in em_operacao.index:
                registro = em_operacao.loc[idx]
                placa = registro.get('Placa do caminhão', 'N/A')
                status = obter_status(registro)
                conferente = registro.get('Nome do conferente', 'N/A')
                
                # Determinar cor e ícone do status
                if "Saída" in status:
                    status_color = "success"
                    status_icon = "🟢"
                elif "CD" in status:
                    status_color = "warning"
                    status_icon = "🟡"
                elif "Fábrica" in status or "carregamento" in status:
                    status_color = "info"
                    status_icon = "🔵"
                else:
                    status_color = "info"
                    status_icon = "⚪"
                
                with st.expander(f"{status_icon} **{placa}** - {status}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**👤 Conferente:** {conferente}")
                        st.write(f"**📅 Data:** {registro.get('Data', 'N/A')}")
                        st.write(f"**📍 Status Atual:** {status}")
                    
                    with col2:
                        # Tempos calculados
                        tempo_espera_doca = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Encostou na doca Fábrica"))
                        tempo_total = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Saída do pátio"))
                        tempo_percurso_para_cd = calcular_tempo(registro.get("Saída do pátio"), registro.get("Entrada CD"))
                        
                        if tempo_espera_doca:
                            st.metric("⏱️ Tempo Espera Doca", tempo_espera_doca)
                        if tempo_total:
                            st.metric("⏰ Tempo Total Fábrica", tempo_total)
                        if tempo_percurso_para_cd:
                            st.metric("🚛 Tempo Percurso CD", tempo_percurso_para_cd)
                    
                    # Timeline visual simplificada
                    st.write("**📊 Progresso:**")
                    eventos = [
                        ("Entrada", registro.get("Entrada na Fábrica")),
                        ("Doca", registro.get("Encostou na doca Fábrica")),
                        ("Carregamento", registro.get("Fim carregamento")),
                        ("Saída Fábrica", registro.get("Saída do pátio")),
                        ("Entrada CD", registro.get("Entrada CD")),
                        ("Saída CD", registro.get("Saída CD"))
                    ]
                    
                    progress_cols = st.columns(6)
                    for i, (evento, timestamp) in enumerate(eventos):
                        with progress_cols[i]:
                            if timestamp and not pd.isna(timestamp) and timestamp != "":
                                st.success(f"✅ {evento}")
                            else:
                                st.info(f"⏳ {evento}")
            
        else:
            st.info("📋 Nenhum registro em operação no momento.")
    else:
        st.error("❌ Planilha não encontrada.")

# FINALIZADAS
elif st.session_state.pagina_atual == "Finalizadas":
    botao_voltar()
    
    st.markdown("<div class=\"section-header\">✅ Registros Finalizados</div>", unsafe_allow_html=True)
    
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        finalizados = df[~(pd.isna(df["Saída CD"])) & (df["Saída CD"] != "")]
        
        if not finalizados.empty:
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Cargas Finalizadas", len(finalizados))
            with col2:
                st.metric("📊 Total de Registros", len(df))
            with col3:
                percentual = round((len(finalizados) / len(df)) * 100, 1) if len(df) > 0 else 0
                st.metric("📈 % Finalizadas", f"{percentual}%")
            
            st.markdown("---")
            
            # Lista de finalizados mais compacta
            for idx in finalizados.index:
                registro = finalizados.loc[idx]
                placa = registro.get("Placa do caminhão", "N/A")
                conferente = registro.get("Nome do conferente", "N/A")
                data_saida = registro.get("Saída CD", "N/A")
                
                with st.expander(f"✅ **{placa}** - Finalizada em {data_saida}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**👤 Conferente:** {conferente}")
                        st.write(f"**📅 Data:** {registro.get('Data', 'N/A')}")
                        st.write(f"**🏁 Finalizada:** {data_saida}")
                    
                    with col2:
                        # Tempos calculados
                        tempo_total = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Saída do pátio"))
                        tempo_percurso = calcular_tempo(registro.get("Saída do pátio"), registro.get("Entrada CD"))
                        tempo_total_cd = calcular_tempo(registro.get("Entrada CD"), registro.get("Saída CD"))
                        
                        if tempo_total:
                            st.metric("⏰ Tempo Total Fábrica", tempo_total)
                        if tempo_percurso:
                            st.metric("🚛 Tempo Percurso", tempo_percurso)
                        if tempo_total_cd:
                            st.metric("📦 Tempo Total CD", tempo_total_cd)
            
        else:
            st.info("📋 Nenhum registro finalizado no momento.")
    else:
        st.error("❌ Planilha não encontrada.")

