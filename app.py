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

# Inicializa session_state para os campos de tempo e calculados
for campo in campos_tempo:
    if campo not in st.session_state:
        st.session_state[campo] = ""

st.set_page_config(page_title="Registro Transferência", layout="centered")
st.title("🚚 Registro de Transferência de Carga - Suzano Papel e Celulose")

pagina = st.selectbox("📌 Escolha uma opção", ["Tela Inicial", "Lançar Novo Controle", "Editar Lançamentos Incompletos", "Em Operação", "Finalizadas"])

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


if pagina == "Tela Inicial":
    st.subheader("Bem-vindo ao Sistema de Controle de Transferência")
    st.write("Use o menu acima para navegar entre as opções disponíveis:")
    st.write("- **Lançar Novo Controle**: Para registrar um novo controle de transferência")
    st.write("- **Editar Lançamentos Incompletos**: Para editar registros que ainda não foram finalizados")
    st.write("- **Em Operação**: Para visualizar os registros que estão em processo")
    
    # Opção de download da planilha mantida na tela inicial
    if os.path.exists(EXCEL_PATH):
        with open(EXCEL_PATH, "rb") as f:
            st.download_button(
                label="📥 Baixar Planilha Atual",
                data=f,
                file_name=EXCEL_PATH,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Nenhuma planilha encontrada ainda. Crie o primeiro registro para gerar a planilha.")

elif pagina == "Lançar Novo Controle":
    st.subheader("Dados do Veículo")
    data = st.date_input("Data", value=datetime.now(FUSO_HORARIO).date())
    placa = st.text_input("Placa do caminhão")
    conferente = st.text_input("Nome do conferente")

    st.subheader("Fábrica")
    for campo in campos_tempo[:7]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(campo, value=st.session_state[campo], disabled=True, key=f"txt_{campo}")
        with col2:
            if st.button(f"Registrar {campo}", key=f"btn_{campo}"):
                st.session_state[campo] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                # NÃO CHAMAR st.experimental_rerun() aqui!

    st.subheader("Centro de Distribuição (CD)")
    for campo in campos_tempo[7:]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(campo, value=st.session_state[campo], disabled=True, key=f"txt_{campo}")
        with col2:
            if st.button(f"Registrar {campo}", key=f"btn_{campo}"):
                st.session_state[campo] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                # NÃO CHAMAR st.experimental_rerun() aqui!

    if st.button("✅ Salvar Registro"):
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
            for campo in campos_tempo + campos_calculados:
                st.session_state[campo] = ""


        except Exception as e:
            st.error("Erro ao salvar planilha localmente:")
            st.text(str(e))

elif pagina == "Editar Lançamentos Incompletos":
    st.subheader("✏️ Edição de Registros Incompletos")

    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        # Filtrar apenas registros onde \'Saída CD\' está vazia
        incompletos = df[(pd.isna(df["Saída CD"])) | (df["Saída CD"] == "")]

        if not incompletos.empty:
            # Criar opções do selectbox mostrando a placa
            opcoes = []
            for idx in incompletos.index:
                placa = incompletos.loc[idx, 'Placa do caminhão']
                data = incompletos.loc[idx, 'Data']
                opcoes.append(f"Índice {idx} - Placa: {placa} - Data: {data}")
            
            opcao_selecionada = st.selectbox("Selecione um registro para editar:", opcoes)
            idx = int(opcao_selecionada.split(" - ")[0].replace("Índice ", ""))
            
            registro = incompletos.loc[idx]
            
            st.write(f"**Editando registro da placa: {registro['Placa do caminhão']}**")
            
            # Inicializa session_state para os campos editáveis se ainda não existirem
            for coluna in df.columns:
                if f"edit_{coluna}" not in st.session_state:
                    st.session_state[f"edit_{coluna}"] = str(registro[coluna]) if not pd.isna(registro[coluna]) else ""

            for coluna in df.columns:
                valor = registro[coluna]
                if pd.isna(valor) or valor == "":
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # Usar o valor do session_state para o text_input
                        st.text_input(f"{coluna}", value=st.session_state[f"edit_{coluna}"], key=f"edit_{coluna}")
                    with col2:
                        if coluna in campos_tempo:
                            # Callback para o botão \'Agora\'
                            def update_time(col):
                                st.session_state[f"edit_{col}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                            st.button(f"⏰ Agora", key=f"btn_now_{coluna}", on_click=update_time, args=(coluna,))
                else:
                    st.text_input(f"{coluna}", value=str(valor), disabled=True, key=f"readonly_{coluna}")

            if st.button("💾 Salvar preenchimento"):
                for coluna in df.columns:
                    if pd.isna(registro[coluna]) or registro[coluna] == "": # Apenas atualiza campos que estavam vazios
                        novo_valor = st.session_state[f"edit_{coluna}"]
                        if novo_valor.strip() != "":
                            df.at[idx, coluna] = novo_valor

                with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                    df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

                st.success("✅ Registro atualizado com sucesso!")
                # Limpa os campos editáveis do session_state para a próxima edição
                for coluna in df.columns:
                    if f"edit_{coluna}" in st.session_state:
                        del st.session_state[f"edit_{coluna}"]


        else:
            st.info("✅ Todos os registros estão completos!")
    else:
        st.error("❌ Planilha não encontrada.")

elif pagina == "Em Operação":
    st.subheader("🚛 Registros em Operação")
    
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        # Filtrar registros onde \'Saída CD\' está vazia (em operação)
        em_operacao = df[(pd.isna(df["Saída CD"])) | (df["Saída CD"] == "")]
        
        if not em_operacao.empty:
            # Métricas gerais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🚚 Veículos em Operação", len(em_operacao))
            with col2:
                na_fabrica = len(em_operacao[pd.isna(em_operacao["Entrada CD"]) | (em_operacao["Entrada CD"] == "")])
                st.metric("🏭 Na Fábrica", na_fabrica)
            with col3:
                no_cd = len(em_operacao) - na_fabrica
                st.metric("📦 No CD", no_cd)
            
            st.divider()
            
            # Exibir cada veículo em um card expandível
            for idx in em_operacao.index:
                registro = em_operacao.loc[idx]
                placa = registro.get('Placa do caminhão', 'N/A')
                status = obter_status(registro)
                conferente = registro.get('Nome do conferente', 'N/A')
                
                # Determinar cor do status
                if "Saída" in status:
                    status_color = "🟢"
                elif "CD" in status:
                    status_color = "🟡"
                elif "Fábrica" in status or "carregamento" in status:
                    status_color = "🔵"
                else:
                    status_color = "⚪"
                
                with st.expander(f"{status_color} **{placa}** - {status}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**📋 Conferente:** {conferente}")
                        st.write(f"**📅 Data:** {registro.get('Data', 'N/A')}")
                        st.write(f"**🔄 Status Atual:** {status}")
                    
                    with col2:
                        # Calcular e exibir tempos
                        tempo_espera_doca = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Encostou na doca Fábrica"))
                        tempo_total = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Saída do pátio"))
                        tempo_descarregamento_cd = calcular_tempo(registro.get("Início Descarregamento CD"), registro.get("Fim Descarregamento CD"))
                        tempo_espera_doca_cd = calcular_tempo(registro.get("Entrada CD"), registro.get("Encostou na doca CD"))
                        tempo_total_cd = calcular_tempo(registro.get("Entrada CD"), registro.get("Saída CD"))
                        tempo_percurso_para_cd = calcular_tempo(registro.get("Saída do pátio"), registro.get("Entrada CD"))
                        tempo_carregamento = calcular_tempo(registro.get("Início carregamento"), registro.get("Fim carregamento"))
                        
                        if tempo_espera_doca:                            st.metric("⏱️ Tempo Espera Doca", tempo_espera_doca)
                        if tempo_total:
                            st.metric("⏰ Tempo Total Fábrica", tempo_total)
                        if tempo_percurso_para_cd:
                            st.metric("🚛 Tempo Percurso CD", tempo_percurso_para_cd)
                    
                    # Timeline visual dos eventos
                    st.write("**📊 Timeline dos Eventos:**")
                    timeline_cols = st.columns(6)
                    
                    eventos = [
                        ("Entrada Fábrica", registro.get("Entrada na Fábrica")),
                        ("Doca Fábrica", registro.get("Encostou na doca Fábrica")),
                        ("Carregamento", registro.get("Fim carregamento")),
                        ("Saída Fábrica", registro.get("Saída do pátio")),
                        ("Entrada CD", registro.get("Entrada CD")),
                        ("Saída CD", registro.get("Saída CD"))
                    ]
                    
                    for i, (evento, timestamp) in enumerate(eventos):
                        with timeline_cols[i]:
                            if timestamp and not pd.isna(timestamp) and timestamp != "":
                                st.success(f"✅ {evento}")
                                st.caption(timestamp.split()[1] if " " in str(timestamp) else str(timestamp))
                            else:
                                st.info(f"⏳ {evento}")
                                st.caption("Pendente")
            
            st.divider()
            
            # Tabela resumo
            st.subheader("📊 Resumo Geral")
            dados_operacao = []
            for idx in em_operacao.index:
                registro = em_operacao.loc[idx]
                
                # Calcular tempos
                tempo_espera_doca = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Encostou na doca Fábrica"))
                tempo_total = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Saída do pátio"))
                tempo_descarregamento_cd = calcular_tempo(registro.get("Início Descarregamento CD"), registro.get("Fim Descarregamento CD"))
                tempo_espera_doca_cd = calcular_tempo(registro.get("Entrada CD"), registro.get("Encostou na doca CD"))
                tempo_total_cd = calcular_tempo(registro.get("Entrada CD"), registro.get("Saída CD"))
                tempo_percurso_para_cd = calcular_tempo(registro.get("Saída do pátio"), registro.get("Entrada CD"))
                tempo_carregamento = calcular_tempo(registro.get("Início carregamento"), registro.get("Fim carregamento"))
                
                dados_operacao.append({
                    'Placa': registro.get('Placa do caminhão', ''),
                    'Status': obter_status(registro),
                    'Tempo Espera Doca': tempo_espera_doca,
                    'Tempo Total': tempo_total,
                    'Tempo de Descarregamento CD': tempo_descarregamento_cd,
                    'Tempo Espera Doca CD': tempo_espera_doca_cd,
                    'Tempo Total CD': tempo_total_cd,
                    'Tempo Percurso Para CD': tempo_percurso_para_cd,
                    'Tempo de Carregamento': tempo_carregamento
                })
            
            # Exibir tabela
            df_operacao = pd.DataFrame(dados_operacao)
            st.dataframe(df_operacao, use_container_width=True)
            
        else:
            st.info("📋 Nenhum registro em operação no momento.")
    else:
        st.error("❌ Planilha não encontrada.")



elif pagina == "Finalizadas":
    st.subheader("✅ Registros Finalizados")
    
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        # Filtrar registros onde \'Saída CD\' está preenchida (finalizados)
        finalizados = df[~(pd.isna(df["Saída CD"])) & (df["Saída CD"] != "")]
        
        if not finalizados.empty:
            # Métricas gerais
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Cargas Finalizadas", len(finalizados))
            with col2:
                # Exemplo: tempo médio de carregamento (se houver dados)
                # Para isso, precisaríamos converter os tempos para um formato numérico
                st.info("Métricas adicionais podem ser implementadas aqui.")
            with col3:
                st.info("Ex: Tempo médio de descarregamento.")
            
            st.divider()
            
            # Exibir cada veículo em um card expandível
            for idx in finalizados.index:
                registro = finalizados.loc[idx]
                placa = registro.get("Placa do caminhão", "N/A")
                status = obter_status(registro) # Deve ser 'Saída CD' para finalizados
                conferente = registro.get("Nome do conferente", "N/A")
                
                with st.expander(f"✅ **{placa}** - {status}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**📋 Conferente:** {conferente}")
                        st.write(f"**📅 Data:** {registro.get("Data", "N/A")}")
                        st.write(f"**🔄 Status Atual:** {status}")
                    
                    with col2:
                        # Calcular e exibir tempos
                        tempo_espera_doca = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Encostou na doca Fábrica"))
                        tempo_total = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Saída do pátio"))
                        tempo_descarregamento_cd = calcular_tempo(registro.get("Início Descarregamento CD"), registro.get("Fim Descarregamento CD"))
                        tempo_espera_doca_cd = calcular_tempo(registro.get("Entrada CD"), registro.get("Encostou na doca CD"))
                        tempo_total_cd = calcular_tempo(registro.get("Entrada CD"), registro.get("Saída CD"))
                        tempo_percurso_para_cd = calcular_tempo(registro.get("Saída do pátio"), registro.get("Entrada CD"))
                        tempo_carregamento = calcular_tempo(registro.get("Início carregamento"), registro.get("Fim carregamento"))
                        
                        if tempo_espera_doca:
                            st.metric("⏱️ Tempo Espera Doca", tempo_espera_doca)
                        if tempo_total:
                            st.metric("⏰ Tempo Total Fábrica", tempo_total)
                        if tempo_percurso_para_cd:
                            st.metric("🚛 Tempo Percurso CD", tempo_percurso_para_cd)
                        if tempo_descarregamento_cd:
                            st.metric("⏳ Tempo Desc. CD", tempo_descarregamento_cd)
                        if tempo_total_cd:
                            st.metric("⏱️ Tempo Total CD", tempo_total_cd)
                        if tempo_carregamento:
                            st.metric("⏰ Tempo Carregamento", tempo_carregamento)
                    
                    # Timeline visual dos eventos
                    st.write("**📊 Timeline dos Eventos:**")
                    timeline_cols = st.columns(6)
                    
                    eventos = [
                        ("Entrada Fábrica", registro.get("Entrada na Fábrica")),
                        ("Doca Fábrica", registro.get("Encostou na doca Fábrica")),
                        ("Carregamento", registro.get("Fim carregamento")),
                        ("Saída Fábrica", registro.get("Saída do pátio")),
                        ("Entrada CD", registro.get("Entrada CD")),
                        ("Saída CD", registro.get("Saída CD"))
                    ]
                    
                    for i, (evento, timestamp) in enumerate(eventos):
                        with timeline_cols[i]:
                            if timestamp and not pd.isna(timestamp) and timestamp != "":
                                st.success(f"✅ {evento}")
                                st.caption(timestamp.split()[1] if " " in str(timestamp) else str(timestamp))
                            else:
                                st.info(f"⏳ {evento}")
                                st.caption("Pendente")
            
            st.divider()
            
            # Tabela resumo
            st.subheader("📊 Resumo Geral de Cargas Finalizadas")
            dados_finalizados = []
            for idx in finalizados.index:
                registro = finalizados.loc[idx]
                
                # Calcular tempos
                tempo_espera_doca = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Encostou na doca Fábrica"))
                tempo_total = calcular_tempo(registro.get("Entrada na Fábrica"), registro.get("Saída do pátio"))
                tempo_descarregamento_cd = calcular_tempo(registro.get("Início Descarregamento CD"), registro.get("Fim Descarregamento CD"))
                tempo_espera_doca_cd = calcular_tempo(registro.get("Entrada CD"), registro.get("Encostou na doca CD"))
                tempo_total_cd = calcular_tempo(registro.get("Entrada CD"), registro.get("Saída CD"))
                tempo_percurso_para_cd = calcular_tempo(registro.get("Saída do pátio"), registro.get("Entrada CD"))
                tempo_carregamento = calcular_tempo(registro.get("Início carregamento"), registro.get("Fim carregamento"))
                
                dados_finalizados.append({
                    "Placa": registro.get("Placa do caminhão", ""),
                    "Conferente": registro.get("Nome do conferente", ""),
                    "Data Saída CD": registro.get("Saída CD", ""),
                    "Tempo Espera Doca": tempo_espera_doca,
                    "Tempo Total Fábrica": tempo_total,
                    "Tempo Percurso CD": tempo_percurso_para_cd,
                    "Tempo Desc. CD": tempo_descarregamento_cd,
                    "Tempo Total CD": tempo_total_cd,
                    "Tempo Carregamento": tempo_carregamento
                })
            
            # Exibir tabela
            df_finalizados = pd.DataFrame(dados_finalizados)
            st.dataframe(df_finalizados, use_container_width=True)
            
        else:
            st.info("📋 Nenhum registro finalizado no momento.")
    else:
        st.error("❌ Planilha não encontrada.")

