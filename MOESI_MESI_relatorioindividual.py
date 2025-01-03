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
    class CPU:
        def __init__(self, protocol_type="MESI"):
            self.protocol = Protocol(protocol_type)
            self.memory = sharedMemory()
            self.bus = Bus(self.memory, self.protocol)
            self.processors = []
            self.instructions = []
            self.miss_rates = []  # Lista para armazenar a taxa de miss após cada instrução

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
                self.track_miss_rate()

        def track_miss_rate(self):
            # Calcula e armazena a taxa de miss após cada instrução
            metrics = self.bus.metrics
            miss_rate = metrics.cache_misses / metrics.total_instructions if metrics.total_instructions > 0 else 0
            self.miss_rates.append(miss_rate)

        def plot_miss_rate(self):
            # Plota a evolução da taxa de miss ao longo das instruções
            plt.figure(figsize=(10, 6))
            plt.plot(self.miss_rates, label="Taxa de Cache Miss", color="blue", marker="o")
            plt.xlabel("Instrução")
            plt.ylabel("Taxa de Cache Miss")
            plt.title(f"Evolução da Taxa de Cache Miss ({self.protocol.type} Protocol)")
            plt.grid(True)
            plt.legend()
            plt.show()

        def printStatus(self):
            # (Método inalterado, exceto pela inclusão da chamada para `track_miss_rate`.)

            print(f"\nRodando o Protocolo {self.protocol.type}")
            print(f"Memória Principal: {self.bus.memory.data}")
            if self.bus.instruction_processor != NULL:
                op_type = self.bus.instruction_type
                proc = self.bus.instruction_processor
                addr = self.bus.instruction_address
                val = self.bus.instruction_value

                if op_type == "reads":
                    print(f"Instrução: Processador_{proc} lê do endereço: {addr}")
                else:
                    print(f"Instrução: Processador_{proc} escreve o valor: {val} no endereço: {addr}")

            for proc in range(len(self.bus.processors)):
                print(f"\nProcessador {proc}:")
                print(f"Estado da Cache: {self.bus.processors[proc].cache.state}")
                print(f"Endereço da Cache: {self.bus.processors[proc].cache.address or 'vazio'}")
                print(f"Valor na Cache: {self.bus.processors[proc].cache.value or 'vazio'}")

            metrics = self.bus.metrics
            metrics.idle_cycles = metrics.total_cycles - metrics.compute_cycles
            miss_rate = metrics.cache_misses / metrics.total_instructions if metrics.total_instructions > 0 else 0

            print("\nMétricas de performace")
            print("=" * 30)
            print(f"Ciclos Totais: {metrics.total_cycles}")
            print(f"Ciclos Computados(o número simulado): {metrics.compute_cycles}")
            print(f"Ciclos em Idle : {metrics.idle_cycles}")
            print(f"Instruções de Leitura: {metrics.load_instructions}")
            print(f"Instruções de Escrita: {metrics.store_instructions}")
            print(f"Taxa de Cache Miss : {miss_rate:.2%}")
            print("\n" + "*" * 50)

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

    if __name__ == "__main__":
        protocol = input("Entre o tipo de protocolo (MESI/MOESI): ").upper()
        if protocol not in ["MESI", "MOESI"]:
            print("Protocolo Inválido. Padrão é o MESI.")
            protocol = "MESI"
        cpu = CPU(protocol)
        n = int(input("Número de instruções para simular: "))
        cpu.generate_instructions(n)
        cpu.run_simulation()
        cpu.print_final_metrics()
        cpu.plot_miss_rate()