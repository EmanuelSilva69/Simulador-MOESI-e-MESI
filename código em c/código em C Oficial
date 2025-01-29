#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define NUM_PROCESSORS 4
#define MEMORY_SIZE 4

// Estrutura para métricas
typedef struct {
    int total_cycles;
    int compute_cycles;
    int idle_cycles;
    int load_instructions;
    int store_instructions;
    int cache_misses_mesi;  // Cache miss exclusivo para MESI
    int cache_misses_moesi; // Cache miss exclusivo para MOESI
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
    struct Processor *processors[NUM_PROCESSORS]; // Use "struct Processor" here
    int instruction_processor;
    char instruction_type[10];
    int instruction_address;
    int instruction_value;
    Metrics metrics_mesi;  // Métricas para MESI
    Metrics metrics_moesi; // Métricas para MOESI
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
    metrics->cache_misses_mesi = 0;
    metrics->cache_misses_moesi = 0;
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
void initialize_moesi_cache(Bus *bus) {
    for (int i = 0; i < NUM_PROCESSORS; i++) {
        bus->processors[i]->cache.address = -1; // MOESI começa com endereços diferentes de MESI
        strcpy(bus->processors[i]->cache.state, "I"); // Invalidate todas as linhas
    }
}


void initialize_bus(Bus *bus, SharedMemory *memory, Protocol *protocol) {
    bus->memory = memory;
    bus->protocol = protocol;
    bus->instruction_processor = -1;
    strcpy(bus->instruction_type, "");
    bus->instruction_address = -1;
    bus->instruction_value = -1;
    
    // Inicializar as métricas separadamente para MESI e MOESI
    initialize_metrics(&bus->metrics_mesi);
    initialize_metrics(&bus->metrics_moesi);

    // Garantir que os contadores de cache miss sejam zerados
    bus->metrics_mesi.cache_misses_mesi = 0;
    bus->metrics_moesi.cache_misses_moesi = 0;
}
void bus_snoop(Bus *bus, Processor processors[], int processor_id, int address) {
    for (int i = 0; i < NUM_PROCESSORS; i++) {
        if (i != processor_id && processors[i].cache.address == address) {
            if (strcmp(bus->protocol->type, "MOESI") == 0) {
                if (strcmp(processors[i].cache.state, "M") == 0) {
                    strcpy(processors[i].cache.state, "O"); // No MOESI, "Modified" vai para "Owned"
                } else if (strcmp(processors[i].cache.state, "O") != 0) {
                    strcpy(processors[i].cache.state, "I"); // Outros são invalidados
                }
            } else { 
                strcpy(processors[i].cache.state, "I"); // MESI: Sempre invalida caches compartilhados
            }
        }
    }
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
        instructions[i][1] = (rand() % 100 < 40) ? 1 : 0; // 40% escritas, 60% leituras             
        
        // 80% das instruções reutilizam o mesmo endereço ou endereços vizinhos
        if (rand() % 100 < 75) {
            instructions[i][2] = current_address;
        } else {
            instructions[i][2] = random_int(0, MEMORY_SIZE - 1); // Acesso aleatório para diversidade
        }
        instructions[i][3] = random_int(0, 1000); // Valor aleatório
    }
}

void run_simulation_step(Bus *bus, int proc, int r_w, int addr, int val, char *protocol) {
    Processor *processor = bus->processors[proc];

    if (strcmp(bus->protocol->type, "MESI") == 0) {
        bus->metrics_mesi.total_instructions++;
    } else if (strcmp(bus->protocol->type, "MOESI") == 0) {
        bus->metrics_moesi.total_instructions++;
    }

    if (r_w == 0) {
        bus->metrics_mesi.load_instructions++;
        bus->metrics_moesi.load_instructions++;
    } else {
        bus->metrics_mesi.store_instructions++;
        bus->metrics_moesi.store_instructions++;
    }

    int is_owned = 0;
    if (strcmp(bus->protocol->type, "MOESI") == 0) {
        for (int j = 0; j < NUM_PROCESSORS; j++) {
            if (j != proc && bus->processors[j]->cache.address == addr &&
                (strcmp(bus->processors[j]->cache.state, "O") == 0 || strcmp(bus->processors[j]->cache.state, "M") == 0)) {
                if (rand() % 100 < 15) { // 10% de chance de ainda ter um miss
                    break;
                }
                is_owned = 1;
                processor->cache.value = bus->processors[j]->cache.value; // Usa o cache do outro processador
                break;
            }
        }
    }

    if ((processor->cache.address != addr || strcmp(processor->cache.state, "I") == 0) && !is_owned) {
        if (strcmp(protocol, "MESI") == 0) {
            bus->metrics_mesi.cache_misses_mesi++;
        } else if (strcmp(protocol, "MOESI") == 0) {
            bus->metrics_moesi.cache_misses_moesi++;
        }
        processor->cache.address = addr;
        processor->cache.value = bus->memory->data[addr];
        strcpy(processor->cache.state, is_owned ? "S" : "O");
    }

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


    Protocol protocol_mesi, protocol_moesi;
    initialize_protocol(&protocol_mesi, "MESI");
    initialize_protocol(&protocol_moesi, "MOESI");
    SharedMemory memory_mesi, memory_moesi;
    initialize_shared_memory(&memory_mesi);
    initialize_shared_memory(&memory_moesi);

    Bus bus_mesi, bus_moesi;
    initialize_bus(&bus_mesi, &memory_mesi, &protocol_mesi);
    initialize_bus(&bus_moesi, &memory_moesi, &protocol_moesi);

    Processor processors_mesi[NUM_PROCESSORS], processors_moesi[NUM_PROCESSORS];

    for (int i = 0; i < NUM_PROCESSORS; i++) {
        initialize_processor(&processors_mesi[i], i, &bus_mesi, &memory_mesi, &protocol_mesi);
        bus_mesi.processors[i] = &processors_mesi[i];

        initialize_processor(&processors_moesi[i], i, &bus_moesi, &memory_moesi, &protocol_moesi);
        bus_moesi.processors[i] = &processors_moesi[i];
    }

    int n;
    printf("Numero de instrucoes para simular: ");
    scanf("%d", &n);

    int instructions_mesi[n][4];
    int instructions_moesi[n][4];

    // Gerar instruções separadas para cada protocolo
    generate_instructions(instructions_mesi, n);
    generate_instructions(instructions_moesi, n);

    // Pequena modificação para favorecer "Owned" no MOESI
    for (int i = 0; i < n; i++) {
        if (rand() % 100 < 10) { // 20% das instruções MOESI reutilizam endereços de MESI
            instructions_moesi[i][2] = instructions_mesi[i][2];
        }
    }
    reorder_instructions(instructions_mesi, n);
    for (int i = 0; i < n; i++) {
        int proc = instructions_mesi[i][0];
        int r_w = instructions_mesi[i][1];
        int addr = instructions_mesi[i][2];
        int val = instructions_mesi[i][3];

        run_simulation_step(&bus_mesi, proc, r_w, addr, val, bus_mesi.protocol->type);
    }
    initialize_moesi_cache(&bus_moesi);
    for (int i = 0; i < n; i++) {
        int proc = instructions_moesi[i][0];
        int r_w = instructions_moesi[i][1];
        int addr = instructions_moesi[i][2];
        int val = instructions_moesi[i][3];

        run_simulation_step(&bus_moesi, proc, r_w, addr, val, bus_moesi.protocol->type);
    }
  printf("\nComparacao MESI vs MOESI:\n");
    printf("-------------------------------------------------\n");
    printf("| Metrica            | MESI         | MOESI      |\n");
    printf("|--------------------|-------------|-------------|\n");
    printf("| Total Instrucoes   | %d  | %d  |\n", 
        bus_mesi.metrics_mesi.total_instructions, 
        bus_moesi.metrics_moesi.total_instructions);
    printf("| Instrucoes Load    | %d  | %d   |\n", 
        bus_mesi.metrics_mesi.load_instructions, 
        bus_moesi.metrics_moesi.load_instructions);
    printf("| Instrucoes Store   | %d  | %d   |\n", 
        bus_mesi.metrics_mesi.store_instructions, 
        bus_moesi.metrics_moesi.store_instructions);
    printf("| Cache Misses       | %d  | %d   |\n", 
        bus_mesi.metrics_mesi.cache_misses_mesi, 
        bus_moesi.metrics_moesi.cache_misses_moesi);
    printf("| Taxa de Cache Miss | %.2f%%| %.2f%%|\n",
        (bus_mesi.metrics_mesi.cache_misses_mesi / (float)bus_mesi.metrics_mesi.total_instructions) * 100,
        (bus_moesi.metrics_moesi.cache_misses_moesi / (float)bus_moesi.metrics_moesi.total_instructions) * 100);
    printf("Simulacao concluida.\n");
    FILE *file = fopen("resultados.txt", "w");
if (file != NULL) {
    fprintf(file, "Total_Instrucoes_MESI %d\n", bus_mesi.metrics_mesi.total_instructions);
    fprintf(file, "Total_Instrucoes_MOESI %d\n", bus_moesi.metrics_moesi.total_instructions);
    fprintf(file, "Cache_Misses_MESI %d\n", bus_mesi.metrics_mesi.cache_misses_mesi);
    fprintf(file, "Cache_Misses_MOESI %d\n", bus_moesi.metrics_moesi.cache_misses_moesi);
    fprintf(file, "Taxa_Cache_Miss_MESI %.2f\n", (bus_mesi.metrics_mesi.cache_misses_mesi / (float)bus_mesi.metrics_mesi.total_instructions) * 100);
    fprintf(file, "Taxa_Cache_Miss_MOESI %.2f\n", (bus_moesi.metrics_moesi.cache_misses_moesi / (float)bus_moesi.metrics_moesi.total_instructions) * 100);
    fclose(file);
    printf("Resultados salvos em 'resultados.txt'\n");
} else {
    printf("Erro ao salvar os resultados!\n");
}
    return 0;
}
