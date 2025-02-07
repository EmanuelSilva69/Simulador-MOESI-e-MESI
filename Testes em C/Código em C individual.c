#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define NULL 0
#define NUM_PROCESSORS 4
#define MEMORY_SIZE 4

// Estrutura para métricas
typedef struct {
    int total_cycles;
    int compute_cycles;
    int idle_cycles;
    int load_instructions;
    int store_instructions;
    int cache_misses;
    int total_instructions;
    int memory_access_cycles;
    int cache_access_cycles;
    int bus_cycles;
    int compute_cost;
} Metrics;

// Estrutura para o protocolo
typedef struct {
    char type[6]; // MESI ou MOESI
    char valid_states[5][2];
} Protocol;

// Estrutura para memória compartilhada
typedef struct {
    int data[MEMORY_SIZE];
    char status[MEMORY_SIZE][10];
} SharedMemory;

// Estrutura para Cache
typedef struct {
    char state[2];
    int value;
    int address;
} Cache;

// Declaração de Processador (forward declaration para uso na estrutura do barramento)
struct Processor;

// Estrutura para barramento
typedef struct {
    SharedMemory *memory;
    Protocol *protocol;
    struct Processor *processors[NUM_PROCESSORS];
    int instruction_processor;
    char instruction_type[10];
    int instruction_address;
    int instruction_value;
    Metrics metrics;
} Bus;

// Estrutura para processador
typedef struct Processor {
    Cache cache;
    int processor_number;
    Bus *bus;
    SharedMemory *memory;
    Protocol *protocol;
} Processor;

// Funções auxiliares
int random_int(int min, int max) {
    return min + rand() % (max - min + 1);
}

// Inicialização das métricas
void initialize_metrics(Metrics *metrics) {
    metrics->total_cycles = 0;
    metrics->compute_cycles = 0;
    metrics->idle_cycles = 0;
    metrics->load_instructions = 0;
    metrics->store_instructions = 0;
    metrics->cache_misses = 0;
    metrics->total_instructions = 0;
    metrics->memory_access_cycles = 100;
    metrics->cache_access_cycles = 1;
    metrics->bus_cycles = 2;
    metrics->compute_cost = 1;
}

// Inicialização do protocolo
void initialize_protocol(Protocol *protocol, const char *type) {
    strcpy(protocol->type, type);
    if (strcmp(type, "MESI") == 0) {
        strcpy(protocol->valid_states[0], "M");
        strcpy(protocol->valid_states[1], "E");
        strcpy(protocol->valid_states[2], "S");
        strcpy(protocol->valid_states[3], "I");
    } else { // MOESI
        strcpy(protocol->valid_states[0], "M");
        strcpy(protocol->valid_states[1], "O");
        strcpy(protocol->valid_states[2], "E");
        strcpy(protocol->valid_states[3], "S");
        strcpy(protocol->valid_states[4], "I");
    }
}

// Inicialização da memória compartilhada
void initialize_shared_memory(SharedMemory *memory) {
    for (int i = 0; i < MEMORY_SIZE; i++) {
        memory->data[i] = random_int(0, 1000);
        strcpy(memory->status[i], "clean");
    }
}

// Inicialização do cache
void initialize_cache(Cache *cache) {
    strcpy(cache->state, "I");
    cache->value = 0;
    cache->address = -1;
}

// Inicialização do processador
void initialize_processor(Processor *processor, int processor_number, Bus *bus, SharedMemory *memory, Protocol *protocol) {
    initialize_cache(&processor->cache);
    processor->processor_number = processor_number;
    processor->bus = bus;
    processor->memory = memory;
    processor->protocol = protocol;
    bus->processors[processor_number] = processor;
}

// Inicialização do barramento
void initialize_bus(Bus *bus, SharedMemory *memory, Protocol *protocol) {
    bus->memory = memory;
    bus->protocol = protocol;
    bus->instruction_processor = -1;
    strcpy(bus->instruction_type, "");
    bus->instruction_address = -1;
    bus->instruction_value = -1;
    initialize_metrics(&bus->metrics);
}

// Geração de instruções aleatórias
//void generate_instructions(int instructions[][4], int n) {
   // for (int i = 0; i < n; i++) {
     //   instructions[i][0] = random_int(0, NUM_PROCESSORS - 1); // Processador
     //   instructions[i][1] = random_int(0, 1);                 // Leitura (0) ou escrita (1)
     //   instructions[i][2] = random_int(0, MEMORY_SIZE - 1);   // Endereço
     //   instructions[i][3] = random_int(0, 1000);              // Valor
  //  }
//}
// Geração de instruções localizadas
void generate_instructions(int instructions[][4], int n) {
    int current_address = random_int(0, MEMORY_SIZE - 1); // Endereço inicial aleatório
    for (int i = 0; i < n; i++) {
        instructions[i][0] = random_int(0, NUM_PROCESSORS - 1); // Escolha do processador
        instructions[i][1] = random_int(0, 1);                 // Leitura (0) ou escrita (1)
        
        // 80% das instruções reutilizam o mesmo endereço ou endereços vizinhos
        if (rand() % 100 < 80) {
            instructions[i][2] = current_address;
        } else {
            instructions[i][2] = random_int(0, MEMORY_SIZE - 1); // Acesso aleatório para diversidade
        }
        instructions[i][3] = random_int(0, 1000); // Valor aleatório
    }
}
// Simulação do barramento
void run_simulation(Bus *bus, int instructions[][4], int n) {
    int cache_hits = 0; // Contador de cache hits
    for (int i = 0; i < n; i++) {
        int proc = instructions[i][0];
        int r_w = instructions[i][1];
        int addr = instructions[i][2];
        int val = instructions[i][3];

        bus->instruction_processor = proc;
        strcpy(bus->instruction_type, r_w == 0 ? "reads" : "writes");
        bus->instruction_address = addr;
        bus->instruction_value = val;

        Processor *processor = bus->processors[proc];

        // Atualizar métricas de instruções
        bus->metrics.total_instructions++;
        if (r_w == 0) {
            bus->metrics.load_instructions++;
        } else {
            bus->metrics.store_instructions++;
        }

        // Verificar Cache Miss
        if (processor->cache.address != addr || strcmp(processor->cache.state, "I") == 0) {
            // Cache miss
            bus->metrics.cache_misses++;
            printf("Cache miss no Processador %d para endereco %d\n", proc, addr);

            // Carregar valor da memória para o cache
            processor->cache.address = addr;
            processor->cache.value = bus->memory->data[addr];

            // Definir estado do cache com base no protocolo
            if (strcmp(bus->protocol->type, "MOESI") == 0) {
                // Prefira "Shared" se outro processador já detém "Owned"
                int is_owned = 0;
                for (int j = 0; j < NUM_PROCESSORS; j++) {
                    if (j != proc && bus->processors[j]->cache.address == addr &&
                        strcmp(bus->processors[j]->cache.state, "O") == 0) {
                        is_owned = 1;
                        break;
                    }
                }
                if (is_owned) {
                    strcpy(processor->cache.state, "S"); // Definir como "Shared"
                } else {
                    strcpy(processor->cache.state, "O"); // Definir como "Owned"
                }
            } else {
                strcpy(processor->cache.state, "S"); // MESI: Definir como "Shared"
            }
        } else {
            // Cache hit
            cache_hits++;
            printf("Cache hit no Processador %d para endereco %d\n", proc, addr);
        }

        // Operação de leitura ou escrita
        if (r_w == 0) {
            // Leitura
            printf("Processador %d le valor %d do endereco %d\n", proc, processor->cache.value, addr);
        } else {
            // Escrita
            processor->cache.value = val;
            bus->memory->data[addr] = val; // Atualizar a memória principal

            // Atualizar estado durante escrita
            if (strcmp(bus->protocol->type, "MOESI") == 0 && strcmp(processor->cache.state, "S") == 0) {
                // Promover "Shared" para "Owned" no MOESI
                strcpy(processor->cache.state, "O");
            } else if (strcmp(processor->cache.state, "S") == 0) {
                // MESI: Promover "Shared" para "Modified"
                strcpy(processor->cache.state, "M");
            } else {
                strcpy(processor->cache.state, "M"); // Estado "Modified" padrão para escritas
            }

            printf("Processador %d escreve valor %d no endereco %d\n", proc, val, addr);
        }
    }

    // Exibir taxa de cache hits/misses
    printf("\nTaxa de Cache Hits: %.2f%%\n", (cache_hits / (float)bus->metrics.total_instructions) * 100);
    printf("Taxa de Cache Misses: %.2f%%\n", (bus->metrics.cache_misses / (float)bus->metrics.total_instructions) * 100);
}

void print_metrics(Bus *bus) {
    printf("\nMetricas de desempenho:\n");
    printf("========================\n");
    printf("Total de ciclos: %d\n", bus->metrics.total_cycles);
    printf("Ciclos de computacao: %d\n", bus->metrics.compute_cycles);
    printf("Ciclos ociosos: %d\n", bus->metrics.idle_cycles);
    printf("Instrucoes de leitura: %d\n", bus->metrics.load_instructions);
    printf("Instrucoes de escrita: %d\n", bus->metrics.store_instructions);
    printf("Total de instrucoes: %d\n", bus->metrics.total_instructions);
    printf("Cache misses: %d\n", bus->metrics.cache_misses);
    printf("Taxa de cache miss: %.2f%%\n",
           (bus->metrics.cache_misses / (float)bus->metrics.total_instructions) * 100);
}
// Reordenação de instruções para maximizar hits no cache
void reorder_instructions(int instructions[][4], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = i + 1; j < n; j++) {
            if (instructions[i][2] == instructions[j][2]) {
                // Troca de instruções para agrupar acessos ao mesmo endereço
                int temp[4];
                memcpy(temp, instructions[i], sizeof(temp));
                memcpy(instructions[i], instructions[j], sizeof(temp));
                memcpy(instructions[j], temp, sizeof(temp));
            }
        }
    }
}

// Função principal
int main() {
    srand(time(NULL));

    char protocol_type[6];
    printf("Entre o tipo de protocolo (MESI/MOESI): ");
    scanf("%s", protocol_type);

    if (strcmp(protocol_type, "MESI") != 0 && strcmp(protocol_type, "MOESI") != 0) {
        printf("Protocolo invalido. Padrao é MESI.\n");
        strcpy(protocol_type, "MESI");
    }

    Protocol protocol;
    initialize_protocol(&protocol, protocol_type);

    SharedMemory memory;
    initialize_shared_memory(&memory);

    Bus bus;
    initialize_bus(&bus, &memory, &protocol);

    Processor processors[NUM_PROCESSORS];
    for (int i = 0; i < NUM_PROCESSORS; i++) {
        initialize_processor(&processors[i], i, &bus, &memory, &protocol);
    }

    int n;
    printf("Numero de instrucoes para simular: ");
    scanf("%d", &n);

    int instructions[n][4];
    generate_instructions(instructions, n);
    reorder_instructions(instructions, n);
    run_simulation(&bus, instructions, n);
    print_metrics(&bus);
    printf("Simulacao concluida.\n");
    return 0;
}
