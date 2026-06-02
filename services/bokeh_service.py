from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import ColumnDataSource, HoverTool
import pandas as pd
import numpy as np

class BokehService:
    @staticmethod
    def gerar_histograma_desempenho(notas: list) -> tuple:
        """Gera histograma de distribuição de notas (script, div)."""
        if not notas:
            return "", "<div>Sem dados suficientes para Histograma.</div>"

        hist, edges = np.histogram(notas, bins=10, range=[0, 10])
        p = figure(title="Distribuição de Notas Institucionais", tools="", background_fill_color="#fafafa")
        p.quad(top=hist, bottom=0, left=edges[:-1], right=edges[1:],
               fill_color="navy", line_color="white", alpha=0.5)

        p.y_range.start = 0
        p.xaxis.axis_label = 'Nota Final'
        p.yaxis.axis_label = 'Qtd Alunos'
        p.grid.grid_line_color="white"

        return components(p)

    @staticmethod
    def gerar_dispersao_nota_frequencia(dados: list) -> tuple:
        """Gera gráfico de dispersão: Nota x Frequência (script, div).
        dados = [{'nota': 8.5, 'freq': 85.0, 'aluno': 'Nome'}, ...]
        """
        if not dados:
            return "", "<div>Sem dados suficientes para Dispersão.</div>"

        df = pd.DataFrame(dados)
        source = ColumnDataSource(df)

        p = figure(title="Correlação: Assiduidade vs Sucesso", x_axis_label='Frequência (%)', y_axis_label='Nota Final', tools="pan,wheel_zoom,box_zoom,reset")

        p.scatter(x='freq', y='nota', size=8, source=source, fill_color="orange", alpha=0.6)

        hover = HoverTool()
        hover.tooltips = [
            ("Nota", "@nota"),
            ("Frequência", "@freq%")
        ]
        p.add_tools(hover)

        return components(p)

    @staticmethod
    def gerar_boxplot_variabilidade(dados_por_turma: dict) -> tuple:
        """Gera boxplots para comparar turmas (script, div).
        dados_por_turma = {'Matemática': [7, 8, 5, 9, 10], 'Física': [5, 6, 4, 7, 3]}
        """
        if not dados_por_turma:
            return "", "<div>Sem dados suficientes para Boxplot.</div>"

        turmas = list(dados_por_turma.keys())
        p = figure(x_range=turmas, title="Variabilidade de Desempenho por Turma", tools="", background_fill_color="#eaefef")

        # Manually calculating quartiles for plotting since BoxPlot is high-level Holoviews or requires explicit whisker mapping in Bokeh figure
        q1s, q2s, q3s, iqrs, uppers, lowers = [], [], [], [], [], []

        for t in turmas:
            notas = pd.Series(dados_por_turma[t])
            if notas.empty:
                q1s.append(0); q2s.append(0); q3s.append(0); uppers.append(0); lowers.append(0)
                continue
            q1 = notas.quantile(0.25)
            q2 = notas.quantile(0.50)
            q3 = notas.quantile(0.75)
            iqr = q3 - q1
            upper = min(q3 + 1.5*iqr, notas.max())
            lower = max(q1 - 1.5*iqr, notas.min())

            q1s.append(q1); q2s.append(q2); q3s.append(q3); uppers.append(upper); lowers.append(lower)

        # Stems
        p.segment(turmas, lowers, turmas, q1s, line_color="black")
        p.segment(turmas, uppers, turmas, q3s, line_color="black")

        # Boxes
        p.vbar(turmas, 0.7, q2s, q3s, fill_color="#E08E79", line_color="black")
        p.vbar(turmas, 0.7, q1s, q2s, fill_color="#3B8686", line_color="black")

        # Whiskers
        p.rect(turmas, lowers, 0.2, 0.01, line_color="black")
        p.rect(turmas, uppers, 0.2, 0.01, line_color="black")

        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = "white"
        p.grid.grid_line_width = 2
        p.xaxis.major_label_text_font_size="12pt"

        return components(p)
