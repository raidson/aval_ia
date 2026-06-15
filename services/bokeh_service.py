"""
Módulo: services/bokeh_service.py
Serviço para geração de gráficos interativos com a biblioteca Bokeh.
"""

from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter
from bokeh.transform import factor_cmap
from bokeh.palettes import Spectral6, Category10
import pandas as pd
import numpy as np

class BokehService:
    """Encapsula a lógica de criação de gráficos Bokeh para o SIMPA."""

    @staticmethod
    def _get_theme_params():
        """Define parâmetros de tema base para os gráficos."""
        return {
            "background_fill_color": "#ffffff",
            "border_fill_color": "#ffffff",
            "outline_line_color": "#e0e0e0",
            "outline_line_alpha": 0.5,
        }

    @staticmethod
    def gerar_dispersao_nota_frequencia(pontos: list, turma_nome: str):
        """
        Gera um gráfico de dispersão (scatter plot) comparando Média Final vs. Frequência.

        Args:
            pontos (list): Uma lista de dicionários, cada um contendo 'media', 'frequencia' e 'nome'.
            turma_nome (str): Nome da turma para o título do gráfico.

        Returns:
            tuple: (script, div) componentes do gráfico Bokeh.
        """
        if not pontos:
            return None, None

        df = pd.DataFrame(pontos)
        
        # Linha de Regressão Linear Simples
        if len(df) > 1:
            par = np.polyfit(df['frequencia'], df['media'], 1)
            df['regressao'] = df['frequencia'] * par[0] + par[1]

        source = ColumnDataSource(df)

        p = figure(
            height=350,
            sizing_mode="stretch_width",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            title=f"Correlação: Média vs. Frequência ({turma_nome})",
            x_axis_label="Frequência Média (%)",
            y_axis_label="Média Final",
        )
        for k, v in BokehService._get_theme_params().items():
            setattr(p, k, v)

        # Ferramenta de Hover
        hover = HoverTool(
            tooltips=[
                ("Aluno", "@nome"),
                ("Média", "@media{0.00}"),
                ("Frequência", "@frequencia{0.0}%"),
            ]
        )
        p.add_tools(hover)

        # Adiciona os glifos (círculos)
        p.circle(
            x="frequencia",
            y="media",
            source=source,
            size=10,
            color="#6366f1",
            alpha=0.7,
            legend_label="Alunos",
        )

        if len(df) > 1:
            p.line(x='frequencia', y='regressao', source=source, color='tomato', line_width=2, legend_label='Tendência (Regressão)')

        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        p.xaxis.formatter = NumeralTickFormatter(format="0,0'%'")

        s, d = components(p)
        s = s.replace("<script", '<script crossorigin="anonymous"')
        return s, d

    @staticmethod
    def gerar_histograma_desempenho(medias: list, turma_nome: str):
        """
        Gera um histograma da distribuição de médias finais.

        Args:
            medias (list): Lista de médias finais dos alunos.
            turma_nome (str): Nome da turma para o título do gráfico.

        Returns:
            tuple: (script, div) componentes do gráfico Bokeh.
        """
        if not medias:
            return None, None

        hist, edges = np.histogram(medias, bins=[0, 2, 4, 6, 8, 10])
        
        df = pd.DataFrame({
            'contagem': hist,
            'esquerda': edges[:-1],
            'direita': edges[1:]
        })
        df['faixa'] = [f"{l}-{r}" for l, r in zip(df['esquerda'], df['direita'])]
        source = ColumnDataSource(df)

        p = figure(
            x_range=df['faixa'],
            height=350,
            sizing_mode="stretch_width",
            title=f"Distribuição de Desempenho ({turma_nome})",
            x_axis_label="Faixa de Média",
            y_axis_label="Nº de Alunos",
            tools="hover,save",
            tooltips=[("Faixa", "@faixa"), ("Alunos", "@contagem")],
        )
        for k, v in BokehService._get_theme_params().items():
            setattr(p, k, v)

        p.vbar(
            x='faixa',
            top='contagem',
            width=0.8,
            source=source,
            color="#34d399",
            alpha=0.8
        )

        p.xgrid.grid_line_color = None
        p.y_range.start = 0

        s, d = components(p)
        s = s.replace("<script", '<script crossorigin="anonymous"')
        return s, d

    @staticmethod
    def gerar_boxplot_disciplinas(disciplinas_data: list, turma_nome: str):
        """
        Gera um boxplot comparando o desempenho entre as disciplinas.

        Args:
            disciplinas_data (list): Lista de dicionários, cada um com 'disciplina' e 'medias'.
            turma_nome (str): Nome da turma para o título do gráfico.

        Returns:
            tuple: (script, div) componentes do gráfico Bokeh.
        """
        if not disciplinas_data:
            return None, None

        cats = [d['disciplina'] for d in disciplinas_data]
        
        # Estrutura de dados para o boxplot
        df_data = {'disciplina': [], 'media': []}
        for d in disciplinas_data:
            for m in d['medias']:
                df_data['disciplina'].append(d['disciplina'])
                df_data['media'].append(m)
        
        df = pd.DataFrame(df_data)
        
        p = figure(
            x_range=cats,
            height=350,
            sizing_mode="stretch_width",
            title=f"Variabilidade de Notas por Disciplina ({turma_nome})",
            tools="pan,wheel_zoom,box_zoom,reset,save",
            y_axis_label="Média Final"
        )
        for k, v in BokehService._get_theme_params().items():
            setattr(p, k, v)

        # Boxplot
        q1 = df.groupby('disciplina')['media'].quantile(q=0.25)
        q2 = df.groupby('disciplina')['media'].quantile(q=0.5)
        q3 = df.groupby('disciplina')['media'].quantile(q=0.75)
        iqr = q3 - q1
        upper = q3 + 1.5 * iqr
        lower = q1 - 1.5 * iqr

        source = ColumnDataSource(data=dict(
            base=cats, q1=q1, q2=q2, q3=q3, upper=upper, lower=lower
        ))

        p.vbar(x='base', width=0.7, bottom='q2', top='q3', source=source, fill_color=Spectral6[0], line_color="black")
        p.vbar(x='base', width=0.7, bottom='q1', top='q2', source=source, fill_color=Spectral6[1], line_color="black")
        p.rect(x='base', y='lower', width=0.2, height=0.01, source=source, line_color="black")
        p.rect(x='base', y='upper', width=0.2, height=0.01, source=source, line_color="black")
        
        p.xgrid.grid_line_color = None
        p.xaxis.major_label_orientation = np.pi / 4

        s, d = components(p)
        s = s.replace("<script", '<script crossorigin="anonymous"')
        return s, d
