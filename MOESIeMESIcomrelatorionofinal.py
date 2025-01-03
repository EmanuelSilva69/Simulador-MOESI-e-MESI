from random import randint
import matplotlib.pyplot as plt
NULL = None


class Metrics:
    def __init__(self):
        # Contadores de ciclos e instruções
        self.total_cycles = 0  # Total de ciclos de execução
        self.compute_cycles = 0  # Ciclos gastos em computação
        self.idle_cycles = 0  # Ciclos ociosos
        self.load_instructions = 0  # Total de instruções de leitura
        self.store_instructions = 0  # Total de instruções de escrita
        self.cache_misses = 0  # Número de cache misses
        self.total_instructions = 0  # Total de instruções executadas

        # Custos em ciclos para diferentes operações
        self.memory_access_cycles = 100  # Acesso à memória principal
        self.cache_access_cycles = 1  # Acesso à cache
        self.bus_cycles = 2  # Operações no bus
        self.compute_cost = 1  # Custo de computação

# Protocolo de coerência de cache (MESI ou MOESI)
class Protocol:
    def __init__(self, protocol_type="MESI"):
        self.type = protocol_type
        # Estados válidos para cada protocolo
        # MESI: Modified, Exclusive, Shared, Invalid
        # MOESI: Modified, Owned, Exclusive, Shared, Invalid
        self.valid_states = ["M", "E", "S", "I"] if protocol_type == "MESI" else ["M", "O", "E", "S", "I"]


class sharedMemory:
    def __init__(self):
        # Status de cada bloco (limpo/sujo)
        self.data = [randint(0, 1000) for x in range(4)]
        # Status de cada bloco (limpo/sujo)
        self.status = ["clean" for x in range(4)]


class Bus:
    def __init__(self, memory, protocol):
        self.memory = memory
        self.protocol = protocol
        self.processors = [] # Lista de processadores
        # Informações da instrução atual
        self.instruction_processor = NULL
        self.instruction_type = NULL
        self.instruction_address = NULL
        self.instruction_value = NULL
        self.metrics = Metrics()

    def instruction(self, processor, r_w, address, value):
        self.instruction_processor = processor
        self.instruction_type = "reads" if r_w == 0 else "writes"
        self.instruction_address = address
        self.instruction_value = value

        self.metrics.total_instructions += 1
        # Executa instrução de leitura (r_w=0) ou escrita (r_w=1)
        if r_w:
            self.metrics.store_instructions += 1
            self.processors[processor].writeValue(address, value)
        else:
            self.metrics.load_instructions += 1
            self.processors[processor].readValue(address)

    def bus_snoop(self, processor_no, address):
        self.metrics.total_cycles += self.metrics.bus_cycles
        invalidate_others = False
        for proc in range(len(self.processors)):
            if proc != processor_no and self.processors[proc].cache.address == address:
                if self.protocol.type == "MOESI" and self.processors[proc].cache.state == "M":
                    self.processors[proc].cache.state = "O"
                else:
                    self.processors[proc].cache.state = "I"
                invalidate_others = True
        return invalidate_others

    def read_bus_snoop(self, processor_number, address):
        self.metrics.total_cycles += self.metrics.bus_cycles
        shared_copy_exists = False
        for proc in range(len(self.processors)):
            if proc != processor_number and self.processors[proc].cache.address == address:
                if self.processors[proc].cache.state != "I":
                    if self.protocol.type == "MOESI" and self.processors[proc].cache.state == "M":
                        self.processors[proc].cache.state = "O"
                    else:
                        self.processors[proc].cache.state = "S"

                    if self.memory.status[self.processors[proc].cache.address] == "dirty":
                        self.metrics.total_cycles += self.metrics.memory_access_cycles
                        self.memory.data[self.processors[proc].cache.address] = self.processors[proc].cache.value
                        self.memory.status[self.processors[proc].cache.address] = "clean"
                    shared_copy_exists = True
        return shared_copy_exists


class Processor:
    def __init__(self, processor_number, bus, memory, protocol):
        self.cache = Cache(protocol)
        self.processor_number = processor_number
        self.bus = bus
        self.memory = memory
        self.protocol = protocol
        self.bus.processors.append(self)

    def writeValue(self, address, value):
        self.bus.metrics.compute_cycles += self.bus.metrics.compute_cost

        # Conta miss apenas se endereço não está na cache e estado é Invalid
        if (self.cache.address != address) and (self.cache.state == "I"):
            self.bus.metrics.cache_misses += 1
            self.bus.metrics.total_cycles += self.bus.metrics.memory_access_cycles
        else:
            self.bus.metrics.total_cycles += self.bus.metrics.cache_access_cycles

        if self.cache.address == NULL:
            if self.bus.bus_snoop(self.processor_number, address):
                self.cache.state = "E"
            else:
                self.cache.state = "M"
            self.cache.address = address
            self.cache.value = value
            self.memory.status[address] = "dirty"

        elif self.cache.address == address:
            if self.cache.state in ["S", "E", "O"]:
                self.cache.state = "M"
                self.cache.value = value
                self.memory.status[address] = "dirty"
                self.bus.bus_snoop(self.processor_number, address)
            elif self.cache.state == "M":
                self.cache.value = value

        else:
            if self.cache.state in ["M", "O"]:
                self.memory.data[self.cache.address] = self.cache.value
                self.memory.status[self.cache.address] = "clean"

            if self.bus.bus_snoop(self.processor_number, address):
                self.cache.state = "E"
            else:
                self.cache.state = "M"
            self.cache.value = value
            self.cache.address = address
            self.memory.status[address] = "dirty"

    def readValue(self, address):
        self.bus.metrics.compute_cycles += self.bus.metrics.compute_cost

        # Similar à escrita, conta miss nas mesmas condições
        if (self.cache.address != address) and (self.cache.state == "I"):
            self.bus.metrics.cache_misses += 1
            self.bus.metrics.total_cycles += self.bus.metrics.memory_access_cycles
            if self.bus.read_bus_snoop(self.processor_number, address):
                self.cache.state = "S"
            else:
                self.cache.state = "E"
            self.cache.address = address
            self.cache.value = self.memory.data[address]
        else:
            self.bus.metrics.total_cycles += self.bus.metrics.cache_access_cycles

        if self.protocol.type == "MOESI" and self.cache.state == "O":
            return self.cache.value

        return self.cache.value


class Cache:
    def __init__(self, protocol):
        self.protocol = protocol
        self.state = "I"
        self.value = NULL
        self.address = NULL


class CPU:
    def __init__(self, protocol_type="MESI"):
        self.protocol = Protocol(protocol_type)
        self.memory = sharedMemory()
        self.bus = Bus(self.memory, self.protocol)
        self.processors = []
        self.instructions = []

        for processor_number in range(4):
            self.processors.append(Processor(processor_number, self.bus, self.memory, self.protocol))

    def generate_instructions(self, n):
        self.instructions = [
            (randint(0, 3), randint(0, 1), randint(0, 3), randint(0, 1000))
            for _ in range(n)
        ]

    def run_simulation(self):
        for proc, r_w, addr, val in self.instructions:
            self.bus.instruction(proc, r_w, addr, val)

    def get_metrics(self):
        metrics = self.bus.metrics
        metrics.idle_cycles = metrics.total_cycles - metrics.compute_cycles
        miss_rate = metrics.cache_misses / metrics.total_instructions if metrics.total_instructions > 0 else 0
        return {
            "total_cycles": metrics.total_cycles,
            "compute_cycles": metrics.compute_cycles,
            "idle_cycles": metrics.idle_cycles,
            "load_instructions": metrics.load_instructions,
            "store_instructions": metrics.store_instructions,
            "miss_rate": miss_rate
        }

    '''
    def print_final_metrics(self):
        metrics = self.bus.metrics
        metrics.idle_cycles = metrics.total_cycles - metrics.compute_cycles
        miss_rate = metrics.cache_misses / metrics.total_instructions if metrics.total_instructions > 0 else 0

        print("\nMétricas Finais de performace")
        print("=" * 30)
        print(f"Ciclos Totais: {metrics.total_cycles}")
        print(f"Ciclos Computados(o número simulado): {metrics.compute_cycles}")
        print(f"Ciclos em Idle : {metrics.idle_cycles}")
        print(f"Instruções de Leitura: {metrics.load_instructions}")
        print(f"Instruções de Escrita: {metrics.store_instructions}")
        print(f"Taxa de Cache Miss : {miss_rate:.2%}")
'''
    def print_final_metrics(self):
        metrics = self.get_metrics()
        print("\nMétricas Finais de performance")
        print("=" * 30)
        print(f"Ciclos Totais: {metrics['total_cycles']}")
        print(f"Ciclos Computados: {metrics['compute_cycles']}")
        print(f"Ciclos em Idle: {metrics['idle_cycles']}")
        print(f"Instruções de Leitura: {metrics['load_instructions']}")
        print(f"Instruções de Escrita: {metrics['store_instructions']}")
        print(f"Taxa de Cache Miss: {metrics['miss_rate']:.2%}")
        return metrics  # Retorna as métricas


def plot_comparison(mesi_metrics, moesi_metrics):
   """
    labels = ['Ciclos Totais', 'Ciclos Computados', 'Ciclos em Idle', 'Instruções de Leitura', 'Instruções de Escrita',
              'Taxa de Cache Miss']

    mesi_values = [mesi_metrics['total_cycles'], mesi_metrics['compute_cycles'], mesi_metrics['idle_cycles'],
                   mesi_metrics['load_instructions'], mesi_metrics['store_instructions'], mesi_metrics['miss_rate']]
    moesi_values = [moesi_metrics['total_cycles'], moesi_metrics['compute_cycles'], moesi_metrics['idle_cycles'],
                    moesi_metrics['load_instructions'], moesi_metrics['store_instructions'], moesi_metrics['miss_rate']]

    x = range(len(labels))
#Esse é o código pro negócio completo!! Os gráficos de todos os parametros
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x, mesi_values, width=0.4, label='MESI', align='center')
    ax.bar(x, moesi_values, width=0.4, label='MOESI', align='edge')

    ax.set_ylabel('Valores de Métricas')
    ax.set_title('Comparação entre MESI e MOESI')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha="right")
    ax.legend()

    plt.tight_layout()
    plt.show()
"""
   labels = ['MESI', 'MOESI']
   miss_rates = [mesi_metrics['miss_rate'], moesi_metrics['miss_rate']]

   x = range(len(labels))

   fig, ax = plt.subplots(figsize=(6, 6))
   ax.bar(x, miss_rates, width=0.4, color=['blue', 'orange'], label='Taxa de Cache Miss')

   ax.set_ylabel('Taxa de Cache Miss')
   ax.set_title('Comparação da Taxa de Cache Miss entre MESI e MOESI')
   ax.set_xticks(x)
   ax.set_xticklabels(labels)
   ax.legend()

   plt.tight_layout()
   plt.show()
if __name__ == "__main__":
    var = int(input("Digite 1 para testar individualmente e 2 para comparar ambos:"))
    if var == 1:
        protocol = input("Entre o tipo de protocolo (MESI/MOESI): ").upper()
        if protocol not in ["MESI", "MOESI"]:
            print("Protocolo Inválido. Padrão é o MESI.")
            protocol = "MESI"

        n = int(input("Número de instruções para simular: "))

        cpu = CPU(protocol)
        cpu.generate_instructions(n)
        cpu.run_simulation()
        cpu.print_final_metrics()
    elif var == 2:
        # Simulando com MESI
        n = int(input("Número de instruções para simular: "))
        print("Simulando com o protocolo MESI...")
        cpu_mesi = CPU(protocol_type="MESI")
        cpu_mesi.generate_instructions(n)
        cpu_mesi.run_simulation()
        mesi_metrics = cpu_mesi.print_final_metrics()

        # Simulando com MOESI
        print("\nSimulando com o protocolo MOESI...")
        cpu_moesi = CPU(protocol_type="MOESI")
        cpu_moesi.generate_instructions(n)
        cpu_moesi.run_simulation()
        moesi_metrics = cpu_moesi.print_final_metrics()

        # Gerando gráfico de comparação
        plot_comparison(mesi_metrics, moesi_metrics)
    else:
        print("Retorne uma variável existente")