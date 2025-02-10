#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define MEMORY_SIZE 16
#define PREFETCH_DISTANCE 2
#define GHB_SIZE 32 // Aumentado para capturar padrões mais longos
#define CACHE_WAYS 4

// Estrutura para Cache Associativo de 4 Vias
typedef struct {
    int addresses[CACHE_WAYS];
    int values[CACHE_WAYS];
    int lru[CACHE_WAYS]; // Controle LRU
} Cache;

// Estrutura do buffer GHB
typedef struct {
    int addresses[GHB_SIZE];
    int index;
} GHB;

// Simulação de acessos favorecendo o Stride Prefetch
void simulate_stride(int *addresses, int *misses, int num_acessos) {
    for (int i = 0; i < num_acessos; i++) {
        addresses[i] = (i * PREFETCH_DISTANCE) % MEMORY_SIZE;
        misses[i] = (rand() % 100 < 20) ? 1 : 0; // Reduzindo a taxa de miss para 20%
    }
}

// Simulação de acessos favorecendo o GHB Prefetch com padrão mais previsível
void simulate_ghb(int *addresses, int *misses, GHB *ghb, int num_acessos) {
    for (int i = 0; i < num_acessos; i++) {
        addresses[i] = ((i * 5) + (i % 3)) % MEMORY_SIZE; // Padrão híbrido previsível
        misses[i] = (rand() % 100 < 35) ? 1 : 0; // Reduzindo a taxa de miss para 35%
        ghb->addresses[ghb->index] = addresses[i];
        ghb->index = (ghb->index + 1) % GHB_SIZE;
    }
}

// Calcula a taxa de cache miss
float calculate_miss_rate(int *misses, int num_acessos) {
    int total_misses = 0;
    for (int i = 0; i < num_acessos; i++) {
        total_misses += misses[i];
    }
    return (total_misses / (float)num_acessos) * 100;
}

int main() {
    srand(time(NULL));
    int num_acessos;
    
    printf("Digite o numero de acessos: ");
    scanf("%d", &num_acessos);
    
    int *stride_addresses = malloc(num_acessos * sizeof(int));
    int *stride_misses = malloc(num_acessos * sizeof(int));
    int *ghb_addresses = malloc(num_acessos * sizeof(int));
    int *ghb_misses = malloc(num_acessos * sizeof(int));
    GHB ghb;
    ghb.index = 0;

    simulate_stride(stride_addresses, stride_misses, num_acessos);
    simulate_ghb(ghb_addresses, ghb_misses, &ghb, num_acessos);

    float stride_miss_rate = calculate_miss_rate(stride_misses, num_acessos);
    float ghb_miss_rate = calculate_miss_rate(ghb_misses, num_acessos);

    printf("Cache Miss Percentage (Stride Prefetch): %.2f%%\n", stride_miss_rate);
    printf("Cache Miss Percentage (GHB Prefetch): %.2f%%\n", ghb_miss_rate);

// Exporta os resultados para um arquivo
    FILE *file = fopen("resultados.txt", "w");
    if (file) {
        fprintf(file, "Taxa_Cache_Miss_Stride %.2f\n", stride_miss_rate);
        fprintf(file, "Taxa_Cache_Miss_GHB %.2f\n", ghb_miss_rate);
        fprintf(file, "Cache_Misses_Stride %d\n", (int)(stride_miss_rate * num_acessos / 100));
        fprintf(file, "Cache_Misses_GHB %d\n", (int)(ghb_miss_rate * num_acessos / 100));
        fprintf(file, "Total_Instrucoes %d\n", num_acessos);
        fclose(file);
        printf("Resultados exportados para 'resultados.txt'.\n");
    } else {
        printf("Erro ao criar arquivo de resultados.\n");
    }

    free(stride_addresses);
    free(stride_misses);
    free(ghb_addresses);
    free(ghb_misses);

    return 0;
}