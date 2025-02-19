import mysql.connector
from mysql.connector import Error
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


def connect_to_mariadb():
    # Configuração da página para layout amplo
    st.set_page_config(layout="wide")
    st.markdown(
        """
        <style>
        .main > div {
            max-width: 100%;
            padding-left: 5%;
            padding-right: 5%;
        }
        .stButton > button {
            width: 100%;
        }
        .stTextInput > div > div > input {
            width: 100%;
        }
        .stSelectbox > div > div > div {
            width: 100%;
        }
        .stSlider > div > div > div {
            width: 100%;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    connection = None
    try:
        connection = mysql.connector.connect(
            host='sgddolp.com',
            database='dolpenge_views',
            user='dolpenge_dolpviews',
            password='EuL7(s%MA4)fUZ,l0U'
        )

        if connection.is_connected():
            st.success("Conexão bem-sucedida!")

            cursor = connection.cursor()
            cursor.execute("SET SQL_BIG_SELECTS=1")

            # 🔹 Query da view de turnos
            query_turnos = """
            SELECT 
                unidade, idtb_turnos, num_operacional, prefixo, 
                dt_inicio, dt_fim, tipo, motora, nom_fant
            FROM 
                view_power_bi_turnos
            """

            cursor.execute(query_turnos)
            resultados_turnos = cursor.fetchall()

            # 🔹 Query da view de monitoria (avulsa_mon)
            query_avulsa = """
            SELECT 
                unidade, equipe_real, dt_monitoria, situacao, 
                gravou_atividade, monitor, supervisor
            FROM 
                view_power_bi_avulsa_mon
            """

            cursor.execute(query_avulsa)
            resultados_avulsa = cursor.fetchall()

            # Criando os DataFrames
            colunas_turnos = [
                'unidade', 'idtb_turnos', 'num_operacional', 'prefixo',
                'dt_inicio', 'dt_fim', 'tipo', 'motora', 'nom_fant'
            ]
            df_turnos = pd.DataFrame(resultados_turnos, columns=colunas_turnos)

            colunas_avulsa = [
                'unidade', 'equipe_real', 'dt_monitoria', 'situacao',
                'gravou_atividade', 'monitor', 'supervisor'
            ]
            df_avulsa = pd.DataFrame(resultados_avulsa, columns=colunas_avulsa)

            # Convertendo colunas de data
            df_turnos['dt_inicio'] = pd.to_datetime(df_turnos['dt_inicio'], errors='coerce')
            df_turnos['dt_fim'] = pd.to_datetime(df_turnos['dt_fim'], errors='coerce')
            df_avulsa['dt_monitoria'] = pd.to_datetime(df_avulsa['dt_monitoria'], errors='coerce')

            # Extraindo os últimos caracteres da coluna 'equipe_real'
            df_avulsa['equipe_real'] = df_avulsa['equipe_real'].astype(str).str[:6]

            # Garantindo que a coluna 'equipe_real' seja tratada como string
            df_avulsa['equipe_real'] = df_avulsa['equipe_real'].astype(str)

            # Removendo espaços em branco e caracteres invisíveis
            df_avulsa['equipe_real'] = df_avulsa['equipe_real'].str.strip()

            # Adicionando uma nova coluna para classificar os contratos
            df_avulsa['tipo_contrato'] = df_avulsa['equipe_real'].apply(
                lambda x: 'Âncora' if len(x) > 7 else 'Satélite'
            )

            # Adicionando a classificação de prefixo
            df_turnos['tipo_prefixo'] = df_turnos['prefixo'].apply(
                lambda x: 'Âncora' if len(str(x)) > 1 else 'Satélite'
            )

            # Criando uma coluna de relacionamento em ambos os DataFrames
            df_turnos['relacionamento'] = df_turnos['num_operacional'].astype(str)
            df_avulsa['relacionamento'] = df_avulsa['equipe_real'].astype(str)

            return df_turnos, df_avulsa

    except Error as e:
        st.error(f"Erro ao conectar ao banco: {e}")
        return None, None

    finally:
        if connection and connection.is_connected():
            connection.close()
            st.info("Conexão encerrada.")


# Chamando a função
df_turnos, df_avulsa = connect_to_mariadb()

if df_turnos is not None and df_avulsa is not None:
    # Filtros na barra lateral (Sidebar)
    st.logo('https://www.dolpengenharia.com.br/wp-content/uploads/2021/01/logotipo-definitivo-250614.png',
            link='https://www.dolpengenharia.com.br/')

    # Filtro de Ano
    anos = df_turnos['dt_inicio'].dt.year.unique()
    anos_avulsa = df_avulsa['dt_monitoria'].dt.year.unique()
    anos_combined = sorted(set(anos) | set(anos_avulsa))

    ano_selecionado = st.sidebar.selectbox("Selecione o Ano:", anos_combined)

    # Filtro de Meses com dados disponíveis
    meses_com_dados_turnos = df_turnos[df_turnos['dt_inicio'].dt.year == ano_selecionado]['dt_inicio'].dt.month.unique()
    meses_com_dados_avulsa = df_avulsa[df_avulsa['dt_monitoria'].dt.year == ano_selecionado][
        'dt_monitoria'].dt.month.unique()

    # Unindo os meses de ambos os DataFrames e mantendo apenas os meses com dados
    meses_com_dados = sorted(set(meses_com_dados_turnos) | set(meses_com_dados_avulsa))

    meses_selecionados = st.sidebar.multiselect("Selecione os Meses:", meses_com_dados, default=meses_com_dados)

    # Filtro de Empresa
    empresas = df_turnos['nom_fant'].unique()
    empresa_selecionada = st.sidebar.selectbox("Selecione a Empresa:", empresas)

    # Filtro Dinâmico de Unidade (dependente da Empresa)
    unidades_filtradas = df_turnos[df_turnos['nom_fant'] == empresa_selecionada]['unidade'].unique()

    unidades_selecionadas = st.sidebar.multiselect(
        "Selecione as Unidades:",
        unidades_filtradas,
        default=unidades_filtradas
    )

    # Filtro de Tipo de Prefixo com a opção "Todas"
    tipos_prefixo = ['Todas'] + list(df_turnos['tipo_prefixo'].unique())
    tipo_prefixo_selecionado = st.sidebar.selectbox("Selecione o Tipo de Prefixo:", tipos_prefixo)

    # Filtro de Equipe
    equipe_desejada = st.sidebar.text_input("Digite o número da equipe:")

    # Filtro de Supervisor
    supervisores = ['Todos'] + list(df_avulsa['supervisor'].unique())
    supervisor_selecionado = st.sidebar.selectbox("Selecione o Supervisor:", supervisores)

    # Filtro de Monitor
    monitores = ['Todos'] + list(df_avulsa['monitor'].unique())
    monitor_selecionado = st.sidebar.selectbox("Selecione o Monitor:", monitores)

    # Filtrando os dados com base nos filtros da barra lateral
    df_turnos_filtrado = df_turnos[(
                                           df_turnos['dt_inicio'].dt.year == ano_selecionado) &
                                   (df_turnos['dt_inicio'].dt.month.isin(meses_selecionados)) &
                                   (df_turnos['unidade'].isin(unidades_selecionadas)) &
                                   (df_turnos['nom_fant'] == empresa_selecionada)
                                   ]

    # Aplicando o filtro de tipo_prefixo, se não for "Todas"
    if tipo_prefixo_selecionado != "Todas":
        df_turnos_filtrado = df_turnos_filtrado[df_turnos_filtrado['tipo_prefixo'] == tipo_prefixo_selecionado]

    # Aplicando o filtro de equipe, se fornecido
    if equipe_desejada:
        df_turnos_filtrado = df_turnos_filtrado[df_turnos_filtrado['num_operacional'] == equipe_desejada]

    # Filtrando a base de monitoria com base no relacionamento com a base de turnos
    equipes_filtradas = df_turnos_filtrado['num_operacional'].unique()
    df_avulsa_filtrado = df_avulsa[(
                                           df_avulsa['dt_monitoria'].dt.year == ano_selecionado) &
                                   (df_avulsa['dt_monitoria'].dt.month.isin(meses_selecionados)) &
                                   (df_avulsa['unidade'].isin(unidades_selecionadas)) &
                                   (df_avulsa['equipe_real'].isin(equipes_filtradas))
                                   ]

    # Aplicando o filtro de supervisor, se não for "Todos"
    if supervisor_selecionado != "Todos":
        df_avulsa_filtrado = df_avulsa_filtrado[df_avulsa_filtrado['supervisor'] == supervisor_selecionado]

    # Aplicando o filtro de monitor, se não for "Todos"
    if monitor_selecionado != "Todos":
        df_avulsa_filtrado = df_avulsa_filtrado[df_avulsa_filtrado['monitor'] == monitor_selecionado]



    ########################################### MEDIDAS DOS GRAFICOS ##############################################################
    # Dividindo as equipes com base em 'gravou_atividade'
    gravou_atividade_sim = df_avulsa_filtrado[df_avulsa_filtrado['gravou_atividade'] == 'SIM']
    gravou_atividade_nao = df_avulsa_filtrado[df_avulsa_filtrado['gravou_atividade'] == 'NÃO']

    # Removendo duplicação de equipes
    gravou_atividade_sim_distinct = gravou_atividade_sim.drop_duplicates(subset='equipe_real')
    gravou_atividade_nao_distinct = gravou_atividade_nao.drop_duplicates(subset='equipe_real')

    # Contagem das equipes
    total_gravou_sim = len(gravou_atividade_sim_distinct)
    total_gravou_nao = len(gravou_atividade_nao_distinct)

    # Contando todas as equipes para garantir que o valor de "equipes totais" esteja correto
    total_gravou_sim_total = len(gravou_atividade_sim)
    total_gravou_nao_total = len(gravou_atividade_nao)

    # Concatenando os dois DataFrames e removendo duplicatas
    todas_equipes_distintas = pd.concat([gravou_atividade_sim_distinct, gravou_atividade_nao_distinct])
    todas_equipes_distintas = todas_equipes_distintas.drop_duplicates(subset='equipe_real')

    # Contagem total de equipes distintas
    total_equipes_distintas = len(todas_equipes_distintas)

    # Calculando o total de equipes
    total_equipes = total_gravou_sim_total + total_gravou_nao_total

    # Calculando as porcentagens
    porcentagem_gravou_sim = (total_gravou_sim_total / total_equipes) * 100 if total_equipes > 0 else 0
    porcentagem_gravou_nao = (total_gravou_nao_total / total_equipes) * 100 if total_equipes > 0 else 0

    # Calculando as equipes distintas de num_operacional com base nos filtros de data
    total_equipes_distintas_turnos = df_turnos_filtrado['num_operacional'].nunique()

    # Calculando os turnos distintos de 'idtb_turnos' com base nos filtros de data
    total_turnos_distintos = df_turnos_filtrado['idtb_turnos'].nunique()

    # Calculando a porcentagem de equipes que abriram turnos em relação às equipes vistas
    porcentagem_abertura_turnos_equipes = (
            (total_equipes_distintas / total_equipes_distintas_turnos) * 100) if total_equipes_distintas_turnos else 0

    # Calculando a porcentagem de turnos analisados em relação aos turnos abertos
    porcentagem_abertura_turnos = (
            (total_equipes / total_turnos_distintos) * 100) if total_turnos_distintos else 0


    ################################################################################################################

    ######################################## CARTÕES INFORMATIVOS  ############################################


    st.markdown(
        """
        <div style="text-align: center;">
            <h3>📊 <strong>INDICADORES DE ANALISES DE MONITORAMENTO DAS FILMAGENS</strong></h3>
        </div>
        """,
        unsafe_allow_html=True
    )


        # SEPARADOR
    st.markdown("<hr>", unsafe_allow_html=True)

    ###########################################   graficos de rosca informativos principais ##############################################################

    import plotly.graph_objects as go
    import streamlit as st

    # Criando três colunas no Streamlit
    col1, col2, col3 = st.columns(3)

    import plotly.graph_objects as go
    import streamlit as st

    # Gráfico para a coluna 1: % EQUIPES QUE FILMARAM A ATIVIDADE
    fig1 = go.Figure(data=[go.Pie(
        labels=['Gravou Atividade', 'Não Gravou Atividade'],
        values=[total_gravou_sim_total, total_gravou_nao_total],
        hole=0.6,
        marker=dict(colors=['#27AE60', '#E74C3C']),
        textinfo='value',
        textfont=dict(size=18, color="white")  # Ajuste do tamanho e cor do texto
    )])

    fig1.update_layout(
        title='% EQUIPES QUE FILMARAM A ATIVIDADE',
        title_x=0.5,
        annotations=[dict(
            text=f"{porcentagem_gravou_sim:.2f}%",
            x=0.5, y=0.5, font_size=24, showarrow=False, font_color="white"
        )],
        template="plotly_dark",
    )

    import plotly.graph_objects as go
    import streamlit as st

    # Gráfico para a coluna 1: % EQUIPES QUE FILMARAM A ATIVIDADE
    fig1 = go.Figure(data=[go.Pie(
        labels=['Gravou Atividade', 'Não Gravou Atividade'],
        values=[total_gravou_sim_total, total_gravou_nao_total],
        hole=0.6,
        marker=dict(colors=['#27AE60', '#E74C3C']),
        textinfo='value',
        textfont=dict(size=18, color="white")  # Ajuste do tamanho e cor do texto
    )])

    fig1.update_layout(
        title='% EQUIPES QUE FILMARAM A ATIVIDADE',
        title_x=0.5,
        annotations=[dict(
            text=f"{porcentagem_gravou_sim:.2f}%",
            x=0.5, y=0.5, font_size=24, showarrow=False, font_color="white"
        )],
        template="plotly_dark",
    )

    with col1:
        st.plotly_chart(fig1)

        # Gráfico 1: % EQUIPES QUE ABRIAM TURNOS POR EQUIPES ANALISADAS
        fig1 = go.Figure(data=[go.Pie(
            labels=['Equipes que Abriram Turnos', 'Equipes Monitoradas'],
            values=[total_equipes_distintas_turnos, total_equipes_distintas],
            hole=0.6,
            marker=dict(colors=['#27AE60', '#E74C3C']),
            textinfo='value',
            textfont=dict(size=18, color="white")  # Ajuste do tamanho e cor do texto
        )])

        fig1.update_layout(
            title='% EQUIPES QUE ABRIAM TURNOS POR EQUIPES ANALISADAS',
            title_x=0.5,
            annotations=[dict(
                text=f"{porcentagem_abertura_turnos_equipes:.2f}%",
                x=0.5, y=0.5, font_size=24, showarrow=False, font_color="white"
            )],
            template="plotly_dark",
        )

        with col2:
            st.plotly_chart(fig1)

        # Gráfico 2: % TURNOS ANALISADOS POR TURNOS ABERTOS
        fig2 = go.Figure(data=[go.Pie(
            labels=['Turnos Abertos', 'Turnos Analisados'],
            values=[total_turnos_distintos, total_equipes],
            hole=0.6,
            marker=dict(colors=['#27AE60', '#E74C3C']),
            textinfo='value',
            textfont=dict(size=18, color="white")  # Ajuste do tamanho e cor do texto
        )])

        fig2.update_layout(
            title='% TURNOS ANALISADOS POR TURNOS ABERTOS',
            title_x=0.5,
            annotations=[dict(
                text=f"{porcentagem_abertura_turnos:.2f}%",
                x=0.5, y=0.5, font_size=24, showarrow=False, font_color="white"
            )],
            template="plotly_dark",
        )

        with col3:
            st.plotly_chart(fig2)

    ######################################## GRAFICO DE EVOLUÇÃO MENSAL ############################################
        # SEPARADOR
    st.markdown("<hr>", unsafe_allow_html=True)
    import plotly.graph_objects as go
    import streamlit as st

    st.markdown(
        """
        <div style="text-align: center;">
            <h3>📊 <strong>GRAFICO DE EVOLUÇÃO MENSAL </strong></h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Garantindo que a coluna 'mes' seja criada e dados nulos sejam tratados
    gravou_atividade_sim['mes'] = gravou_atividade_sim['dt_monitoria'].dt.month
    gravou_atividade_nao['mes'] = gravou_atividade_nao['dt_monitoria'].dt.month
    gravou_atividade_sim = gravou_atividade_sim.dropna(subset=['mes'])
    gravou_atividade_nao = gravou_atividade_nao.dropna(subset=['mes'])

    # Agrupando e contando os meses
    gravou_atividade_sim_monthly = gravou_atividade_sim.groupby('mes').size()
    gravou_atividade_nao_monthly = gravou_atividade_nao.groupby('mes').size()

    # Garantindo que todos os meses estejam presentes (meses ausentes terão valor 0)
    gravou_atividade_sim_monthly = gravou_atividade_sim_monthly.reindex(meses_selecionados, fill_value=0)
    gravou_atividade_nao_monthly = gravou_atividade_nao_monthly.reindex(meses_selecionados, fill_value=0)

    # Calculando as porcentagens
    total_equipes_mensal = gravou_atividade_sim_monthly + gravou_atividade_nao_monthly
    porcentagem_sim_mensal = (gravou_atividade_sim_monthly / total_equipes_mensal) * 100
    porcentagem_nao_mensal = (gravou_atividade_nao_monthly / total_equipes_mensal) * 100

    # Layout com duas colunas
    col1, col2 = st.columns(2)

    with col1:
        # Criando o gráfico de barras com plotly
        fig = go.Figure()

        # Adicionando barras para 'Gravaram Atividade'
        fig.add_trace(go.Bar(
            x=meses_selecionados,
            y=gravou_atividade_sim_monthly,
            name='Gravaram Atividade',
            marker_color='#27AE60',
            text=[f'{int(val)}\n({perc:.1f}%)' for val, perc in
                  zip(gravou_atividade_sim_monthly, porcentagem_sim_mensal)],
            textposition='outside',
            hoverinfo='x+y+text'
        ))

        # Adicionando barras para 'Não Gravaram Atividade'
        fig.add_trace(go.Bar(
            x=meses_selecionados,
            y=gravou_atividade_nao_monthly,
            name='Não Gravaram Atividade',
            marker_color='#E74C3C',
            text=[f'{int(val)}\n({perc:.1f}%)' for val, perc in
                  zip(gravou_atividade_nao_monthly, porcentagem_nao_mensal)],
            textposition='outside',
            hoverinfo='x+y+text'
        ))

        # Atualizando o layout do gráfico
        fig.update_layout(
            title='Evolução Mensal das Equipes que Gravaram vs Não Gravaram Atividade',
            title_x=0.5,
            xaxis_title='',  # Removendo o título do eixo X
            yaxis_title='',  # Removendo o título do eixo Y,
            xaxis=dict(tickmode='array', tickvals=meses_selecionados,
                       ticktext=[f'Mês {i}' for i in meses_selecionados]),
            barmode='group',
            legend_title='Status da Atividade',
            legend=dict(font=dict(size=12), bordercolor='black', borderwidth=2),
            template='plotly_dark',  # Usando tema dark, você pode mudar para 'plotly' ou outro tema
            margin=dict(t=100, b=100, l=50, r=50)
        )

        # Exibindo o gráfico no Streamlit
        st.plotly_chart(fig)

    with col2:
        # SEPARADOR
        st.markdown("<hr>", unsafe_allow_html=True)

        with st.expander("Ver Detalhes das Equipes que Não Gravaram"):
            st.write(gravou_atividade_nao_distinct[['unidade', 'equipe_real', 'dt_monitoria']])

        with st.expander("Ver Detalhes das Equipes que Gravaram"):
            st.write(gravou_atividade_sim_distinct[['unidade', 'equipe_real', 'dt_monitoria', 'monitor', 'supervisor']])

        # SEPARADOR
        st.markdown("<hr>", unsafe_allow_html=True)

        # Aumentando a resolução do gráfico (dpi)
        plt.rcParams['figure.dpi'] = 300  # Resolução ainda mais alta

        # SEPARADOR
    st.markdown("<hr>", unsafe_allow_html=True)

    ################################################################################################################

    ########################################  DE EVOLUÇÃO MENSAL ############################################


    ##############################################################################################################################
################################################# GRAFICOS DE EVOLUÇÃO DAS EQUIPES ##############################################
    # Organizando os gráficos em duas colunas
    col1, col2, col3 = st.columns(3)

    col1, col2, col3 = st.columns([1, 1, 1])  # Distribuindo as três colunas com a mesma largura

    import plotly.graph_objects as go
    import streamlit as st

    with col1:
        st.markdown("<h2 style='text-align: center; font-size: 26px; color: #e7e7ec;'>Porcentagem por Equipes</h2>",
                    unsafe_allow_html=True)

        # Calculando as porcentagens por equipe
        equipes_porcentagem = df_avulsa_filtrado.groupby(['equipe_real', 'gravou_atividade']).size().unstack(
            fill_value=0)
        equipes_porcentagem['Total'] = equipes_porcentagem.sum(axis=1)
        equipes_porcentagem['SIM %'] = (equipes_porcentagem.get('SIM', 0) / equipes_porcentagem['Total']) * 100
        equipes_porcentagem['NÃO %'] = (equipes_porcentagem.get('NÃO', 0) / equipes_porcentagem['Total']) * 100
        equipes_porcentagem = equipes_porcentagem.sort_values(by='SIM %', ascending=False)

        # Plotando gráfico de porcentagens
        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=equipes_porcentagem.index,
            x=equipes_porcentagem['SIM %'],
            orientation='h',
            name='Gravaram Atividade',
            marker_color='#27AE60',
            text=[f'{val:.1f}%' for val in equipes_porcentagem['SIM %']],
            textposition='inside',
            hoverinfo='x+y+text'
        ))

        fig.add_trace(go.Bar(
            y=equipes_porcentagem.index,
            x=equipes_porcentagem['NÃO %'],
            orientation='h',
            name='Não Gravaram Atividade',
            marker_color='#E74C3C',
            text=[f'{val:.1f}%' for val in equipes_porcentagem['NÃO %']],
            textposition='inside',
            hoverinfo='x+y+text'
        ))

        fig.update_layout(
            title='Porcentagem de Atividades Gravadas por Equipe',
            title_x=0.5,

            xaxis_title='',  # Removendo o título do eixo X
            yaxis_title='',  # Removendo o título do eixo Y,
            barmode='stack',
            template='plotly_dark',
            margin=dict(t=100, b=100, l=50, r=50),
            legend_title='Status da Atividade',
            legend=dict(font=dict(size=12), bordercolor='black', borderwidth=2)
        )

        # Exibindo o gráfico
        st.plotly_chart(fig)

    with col2:
        st.markdown(
            "<h2 style='text-align: center; font-size: 26px; color: #e7e7ec;'>Quantidade de Registros por Equipe</h2>",
            unsafe_allow_html=True)

        # Calculando a quantidade de registros por equipe
        equipes_quantidade = df_avulsa_filtrado.groupby(['equipe_real', 'gravou_atividade']).size().unstack(
            fill_value=0)
        equipes_quantidade = equipes_quantidade.rename(columns={'SIM': 'Gravaram', 'NÃO': 'Não Gravaram'})
        equipes_quantidade['Total'] = equipes_quantidade.sum(axis=1)
        equipes_quantidade = equipes_quantidade.sort_values(by='Total', ascending=False)

        # Plotando gráfico de quantidade de registros
        fig2 = go.Figure()

        fig2.add_trace(go.Bar(
            y=equipes_quantidade.index,
            x=equipes_quantidade['Gravaram'],
            orientation='h',
            name='Gravaram Atividade',
            marker_color='#27AE60',
            text=[f'{val}' for val in equipes_quantidade['Gravaram']],
            textposition='inside',
            hoverinfo='x+y+text'
        ))

        fig2.add_trace(go.Bar(
            y=equipes_quantidade.index,
            x=equipes_quantidade['Não Gravaram'],
            orientation='h',
            name='Não Gravaram Atividade',
            marker_color='#E74C3C',
            text=[f'{val}' for val in equipes_quantidade['Não Gravaram']],
            textposition='inside',
            hoverinfo='x+y+text'
        ))

        fig2.update_layout(
            title='Porcentagem de Atividades Gravadas por Equipe',
            title_x=0.5,  # Centraliza o título horizontalmente
            xaxis_title='',  # Removendo o título do eixo X
            yaxis_title='',  # Removendo o título do eixo Y
            barmode='stack',
            template='plotly_dark',
            margin=dict(t=100, b=100, l=50, r=50),  # Ajuste a margem superior (t) se necessário
            legend_title='Status da Atividade',
            legend=dict(font=dict(size=12), bordercolor='black', borderwidth=2)
        )

        # Exibindo o gráfico
        st.plotly_chart(fig2)

    with col3:
        st.markdown("<h3 style='text-align: center;'>Porcentagem de Gravação por Equipe</h3>", unsafe_allow_html=True)

        # Cálculos para a tabela
        gravou_atividade_sim['semana'] = gravou_atividade_sim['dt_monitoria'].dt.isocalendar().week
        gravou_atividade_nao['semana'] = gravou_atividade_nao['dt_monitoria'].dt.isocalendar().week

        gravou_atividade_sim = gravou_atividade_sim.dropna(subset=['semana'])
        gravou_atividade_nao = gravou_atividade_nao.dropna(subset=['semana'])

        gravou_atividade_sim_weekly = gravou_atividade_sim.groupby(['semana', 'equipe_real']).size().unstack(
            fill_value=0)
        gravou_atividade_nao_weekly = gravou_atividade_nao.groupby(['semana', 'equipe_real']).size().unstack(
            fill_value=0)

        total_equipes_weekly = gravou_atividade_sim_weekly.add(gravou_atividade_nao_weekly, fill_value=0)
        equipes_porcentagem = (gravou_atividade_sim_weekly / total_equipes_weekly) * 100
        equipes_porcentagem = equipes_porcentagem.fillna(0)

        # Formatando a tabela para mostrar as porcentagens com "%"
        equipes_porcentagem_formatada = equipes_porcentagem.applymap(lambda x: f"{int(x)}%")
        tabela_porcentagem = equipes_porcentagem_formatada.T

        # A primeira linha para a tabela precisa ser o nome das colunas (semana)
        semanas = tabela_porcentagem.columns.tolist()
        equipes = tabela_porcentagem.index.tolist()


        # Função para aplicar a cor de fundo dependendo da porcentagem
        def estilo_tabela(val):
            if isinstance(val, str) and "%" in val:
                # Convertendo porcentagem para número para calcular a cor
                percentage = int(val.replace('%', ''))
                # Definindo o gradiente de verde (100%) para vermelho (0%)
                red = 255 - int(percentage * 2.55)
                green = int(percentage * 2.55)
                color = f'rgb({red}, {green}, 0)'
                return f'background-color: {color}; color: black'
            return 'background-color: white; color: black'


        tabela_porcentagem_style = tabela_porcentagem.style.applymap(estilo_tabela).set_table_styles(
            [{'selector': 'thead th',
              'props': [('background-color', '#f5f5f5'), ('font-weight', 'bold'), ('font-size', '16px')]},
             {'selector': 'tbody td', 'props': [('padding', '15px'), ('text-align', 'center'), ('font-size', '14px')]},
             {'selector': 'table',
              'props': [('width', '100%'), ('border-collapse', 'collapse'), ('margin-left', 'auto'),
                        ('margin-right', 'auto')]}]
        )

        # Exibindo a tabela com o estilo gráfico no Streamlit
        st.dataframe(tabela_porcentagem_style, use_container_width=True)

     ###############################################################detalhe equipes#################################################

    # Criando a tabela pivotada e formatada no estilo solicitado
    # Adicionando uma coluna de semana ao DataFrame
    gravou_atividade_sim['semana'] = gravou_atividade_sim['dt_monitoria'].dt.isocalendar().week
    gravou_atividade_nao['semana'] = gravou_atividade_nao['dt_monitoria'].dt.isocalendar().week

    # Removendo qualquer linha onde a semana seja nula ou inválida
    gravou_atividade_sim = gravou_atividade_sim.dropna(subset=['semana'])
    gravou_atividade_nao = gravou_atividade_nao.dropna(subset=['semana'])

    # Agrupando por semana e equipe
    gravou_atividade_weekly = (
        pd.concat([
            gravou_atividade_sim.assign(Tipo='Sim'),
            gravou_atividade_nao.assign(Tipo='Não')
        ])
        .groupby(['semana', 'equipe_real', 'Tipo']).size()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Calculando a porcentagem de gravação por equipe por semana
    gravou_atividade_weekly['filmagens'] = (
            gravou_atividade_weekly['Sim'] / (gravou_atividade_weekly['Sim'] + gravou_atividade_weekly['Não']) * 100
    ).fillna(0)

    # Transformando para o formato solicitado
    tabela_long = gravou_atividade_weekly.melt(id_vars=['semana', 'equipe_real'], var_name='Tipo', value_name='Valor')

    # Criando uma tabela pivotada para exibição
    tabela_pivot = tabela_long.pivot(index=['equipe_real', 'Tipo'], columns='semana', values='Valor').fillna(0)

    # Organizando a coluna 'Tipo' na ordem: 'Sim', 'Não', '%Sim'
    tipo_order = ['Sim', 'Não', 'filmagens']
    tabela_pivot = tabela_pivot.reindex(tipo_order, level='Tipo')

    # SEPARADOR
    st.markdown("<hr>", unsafe_allow_html=True)

    # Dividindo em três colunas para exibição no Streamlit
    col1, col2, col3 = st.columns(3)

    # Listando equipes para distribuir nas colunas
    equipes = list(tabela_pivot.index.get_level_values('equipe_real').unique())

    # Atribuindo equipes às colunas
    for idx, equipe in enumerate(equipes):
        if idx % 3 == 0:
            coluna_atual = col1
        elif idx % 3 == 1:
            coluna_atual = col2
        else:
            coluna_atual = col3

        with coluna_atual:
            with st.expander(f"📌 {equipe} - Detalhes das Atividades Semanais"):
                # Filtrando os dados da equipe específica
                equipe_data = tabela_pivot.loc[equipe]

                # Criando a tabela para cada equipe com semanas como colunas
                st.markdown(f"### Atividades Semanais da Equipe {equipe}", unsafe_allow_html=True)

                # Criando um DataFrame para a exibição mais bonita
                atividades = pd.DataFrame({
                    'Semana': [f"Semana {semana}" for semana in equipe_data.columns],
                    'Sim': [int(equipe_data.loc['Sim', semana]) for semana in equipe_data.columns],
                    # Convertendo para inteiro
                    'Não': [int(equipe_data.loc['Não', semana]) for semana in equipe_data.columns],
                    # Convertendo para inteiro
                    'Filmagens (%)': [f"{equipe_data.loc['filmagens', semana]:.2f}%" for semana in equipe_data.columns]
                })

                # Calculando o total de "Sim", "Não" e a média da porcentagem de filmagens
                total_sim = atividades['Sim'].sum()
                total_nao = atividades['Não'].sum()
                media_filmagens = atividades['Filmagens (%)'].apply(lambda x: float(x.replace('%', ''))).mean()

                # Adicionando a última linha com os totais e a média de filmagens
                atividades.loc['Total', :] = ['Total', total_sim, total_nao, f"{media_filmagens:.2f}%"]

                # Estilo aprimorado da tabela
                st.table(atividades.style.set_table_styles(
                    [{'selector': 'thead th', 'props': [('background-color', '#0a142d'),
                                                        ('font-weight', 'bold'),
                                                        ('color', '#e7e7ec'),
                                                        ('text-align', 'center'),
                                                        ('padding', '10px')]},  # Cabeçalhos
                     {'selector': 'tbody td', 'props': [('padding', '10px'),
                                                        ('color', '#e7e7ec'),
                                                        ('text-align', 'center')]},  # Cores e alinhamento do corpo
                     {'selector': 'tr:nth-child(even)', 'props': [('background-color', '#163e58')]},  # Linhas pares
                     {'selector': 'tr:nth-child(odd)', 'props': [('background-color', '#0a142d')]},  # Linhas ímpares
                     {'selector': 'tr:nth-child(last)', 'props': [('font-weight', 'bold'),
                                                                  ('background-color', '#163e58')]}
                     # Estilo da linha de total
                     ],
                    axis=1  # Aplica o estilo nas colunas
                ).background_gradient(cmap='coolwarm', axis=None))  # Gradiente de fundo

                st.markdown("---")

                # SEPARADOR
    st.markdown("<hr>", unsafe_allow_html=True)







































