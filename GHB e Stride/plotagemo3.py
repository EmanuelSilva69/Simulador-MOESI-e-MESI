from bokeh.plotting import figure, show, output_file
from bokeh.models import ColumnDataSource, FactorRange
from bokeh.layouts import row
import os

print("Diretório atual:", os.getcwd())
print("Arquivo encontrado?", os.path.exists("resultados.txt"))
# Verifica se o arquivo de resultados existe
if not os.path.exists("resultados.txt"):
    print("Erro: O arquivo 'resultados.txt' não foi encontrado. Execute o código em C primeiro.")
    exit()

# Inicializar variáveis
stride_miss_rate = 0
ghb_miss_rate = 0
stride_miss_count = 0
ghb_miss_count = 0
num_instr = 0

# Ler os dados do arquivo `resultados.txt`
with open("resultados.txt", "r") as file:

    for line in file:
        parts = line.split()
        if parts[0] == "Taxa_Cache_Miss_Stride":
            stride_miss_rate = float(parts[1])
        elif parts[0] == "Taxa_Cache_Miss_GHB":
            ghb_miss_rate = float(parts[1])
        elif parts[0] == "Cache_Misses_Stride":
            stride_miss_count = int(parts[1])
        elif parts[0] == "Cache_Misses_GHB":
            ghb_miss_count = int(parts[1])
        elif parts[0] == "Total_Instrucoes":
            num_instr = int(parts[1])

# Criar fontes de dados para gráficos interativos
protocolos = ["Stride", "GHB"]
cores = ["blue", "red"]

source_rate = ColumnDataSource(data=dict(
    protocolos=protocolos,
    valores=[stride_miss_rate, ghb_miss_rate],
    cores=cores
))

# Criar os dados para comparação de Cache Miss vs Total de Instruções
data_cache_miss = [("Stride", "Cache Miss"), ("Stride", "Total Instr"),
                   ("GHB", "Cache Miss"), ("GHB", "Total Instr")]

valores_cache_miss = [stride_miss_count, num_instr, ghb_miss_count, num_instr]

cores_duplas = ["blue", "green", "red", "green"]

source_count = ColumnDataSource(data=dict(
    categorias=data_cache_miss,
    valores=valores_cache_miss,
    cores=cores_duplas
))

# Criar o gráfico para a Taxa de Cache Miss (%)
p1 = figure(x_range=protocolos, height=500, width=600, title="Taxa de Cache Miss (%)",
            tools="pan,box_zoom,reset,save,hover", tooltips=[("Taxa", "@valores%")])

p1.vbar(x='protocolos', top='valores', width=0.6, source=source_rate, color='cores')

p1.xgrid.grid_line_color = None
p1.y_range.start = 0
p1.yaxis.axis_label = "Taxa de Cache Miss (%)"
p1.xaxis.axis_label = "Métodos de Prefetch"

# Criar o gráfico para o Número de Cache Miss comparado ao Total de Instruções
p2 = figure(x_range=FactorRange(*data_cache_miss), height=500, width=600,
            title="Cache Miss vs Total de Instruções",
            tools="pan,box_zoom,reset,save,hover", tooltips=[("Valor", "@valores")])

p2.vbar(x='categorias', top='valores', width=0.6, source=source_count, color='cores')

p2.xgrid.grid_line_color = None
p2.y_range.start = 0
p2.yaxis.axis_label = "Quantidade"
p2.xaxis.axis_label = "Métodos e Métricas"

# **📌 Criar o HTML para Visualização Offline**
output_file("cache_miss_comparacao.html")
show(row(p1, p2))  # Abre o navegador automaticamente com os gráficos
