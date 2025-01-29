from bokeh.plotting import figure, show, output_file, curdoc
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.layouts import row
import pandas as pd

# Inicializar variáveis
mesi_miss_rate = 0
moesi_miss_rate = 0
mesi_miss_count = 0
moesi_miss_count = 0
total_instr_mesi = 0
total_instr_moesi = 0

# Ler os dados do arquivo `resultados.txt`
try:
    with open("resultados.txt", "r") as file:
        for line in file:
            parts = line.split()
            if parts[0] == "Taxa_Cache_Miss_MESI":
                mesi_miss_rate = float(parts[1])
            elif parts[0] == "Taxa_Cache_Miss_MOESI":
                moesi_miss_rate = float(parts[1])
            elif parts[0] == "Cache_Misses_MESI":
                mesi_miss_count = int(parts[1])
            elif parts[0] == "Cache_Misses_MOESI":
                moesi_miss_count = int(parts[1])
            elif parts[0] == "Total_Instrucoes_MESI":
                total_instr_mesi = int(parts[1])
            elif parts[0] == "Total_Instrucoes_MOESI":
                total_instr_moesi = int(parts[1])
except FileNotFoundError:
    print("Erro: O arquivo 'resultados.txt' não foi encontrado.")
    exit()

# Criar fontes de dados para gráficos interativos
protocolos = ["MESI", "MOESI"]
cores = ["blue", "red"]

source_rate = ColumnDataSource(data=dict(
    protocolos=protocolos,
    valores=[mesi_miss_rate, moesi_miss_rate],
    cores=cores
))

# Criar os dados para comparação de Cache Miss vs Total de Instruções
data_cache_miss = [("MESI", "Cache Miss"), ("MESI", "Total Instr"),
                   ("MOESI", "Cache Miss"), ("MOESI", "Total Instr")]

valores_cache_miss = [mesi_miss_count, total_instr_mesi,
                      moesi_miss_count, total_instr_moesi]

cores_duplas = ["blue", "green", "red", "green"]

source_count = ColumnDataSource(data=dict(
    categorias=data_cache_miss,
    valores=valores_cache_miss,
    cores=cores_duplas
))

# Criar o gráfico para a Taxa de Cache Miss (%)
p1 = figure(x_range=protocolos, height=900, width=900, title="Taxa de Cache Miss (%)",
            tools="pan,box_zoom,reset,save,hover", tooltips=[("Taxa", "@valores%")])

p1.vbar(x='protocolos', top='valores', width=0.6, source=source_rate, color='cores')

p1.xgrid.grid_line_color = None
p1.y_range.start = 0
p1.yaxis.axis_label = "Taxa de Cache Miss (%)"
p1.xaxis.axis_label = "Protocolos"

# Criar o gráfico para o Número de Cache Miss comparado ao Total de Instruções
p2 = figure(x_range=FactorRange(*data_cache_miss), height=900, width=900,
            title="Cache Miss vs Total de Instruções",
            tools="pan,box_zoom,reset,save,hover", tooltips=[("Valor", "@valores")])

p2.vbar(x='categorias', top='valores', width=0.6, source=source_count, color='cores')

p2.xgrid.grid_line_color = None
p2.y_range.start = 0
p2.yaxis.axis_label = "Quantidade"
p2.xaxis.axis_label = "Protocolos e Métricas"

# **📌 Criar o HTML para Visualização Offline**
output_file("cache_comparacao_ampliado.html")
show(row(p1, p2))  # Abre o navegador automaticamente com o HTML

# **📌 Criar o Servidor Interativo**
curdoc().add_root(row(p1, p2))
curdoc().title = "Comparação de Cache MESI vs MOESI"
