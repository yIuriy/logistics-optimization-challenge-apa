# Resumo da rodada final

Resultados gerados automaticamente a partir dos 60 arquivos `.json` em `results/` (30 instâncias dos conjuntos B e X × algoritmo exato e algoritmo genético), todos validados pelo `checker.py` oficial (`60/60` viáveis).

## Ambiente de execução

- **Processador:** AMD Ryzen 5 4500 6-Core Processor (6 núcleos físicos / 12 threads)
- **Memória:** 15,8 GB de RAM (referência do regulamento: 8 vCPUs e 16 GB de RAM)
- **Sistema operacional:** Microsoft Windows 11 Home (10.0.26300)
- **Commit do código:** `e957035`
- **Limite de tempo:** 600 s por instância e por método
- **Parâmetros do algoritmo genético:** população 50, torneio 3, taxa de mutação 0,002, semente 1, `max_generations` 1000000000
- **Execução na mesma máquina:** algoritmo exato rodou sequencialmente (1 processo por vez); algoritmo genético rodou em 5 processos paralelos (1 por núcleo físico)

## Tabela comparativa

Em cada linha, o valor em **negrito** marca o método com maior objetivo (ambos em negrito em caso de empate).

| instância | melhor oficial | algoritmo exato | limite superior do algoritmo exato | algoritmo genético | % do melhor (algoritmo genético) |
| --- | ---: | ---: | ---: | ---: | ---: |
| b_instance_0001 | 631.50 | 440.89 | 3812.28 | **629.50** | 99.68% |
| b_instance_0002 | 180.64 | 154.77 | 3031.73 | **180.45** | 99.90% |
| b_instance_0003 | 149.60 | 134.38 | 1989.50 | **141.27** | 94.43% |
| b_instance_0004 | 155.94 | 140.10 | 2559.60 | **155.67** | 99.82% |
| b_instance_0005 | 368.00 | 259.64 | 2707.46 | **368.00** | 100.00% |
| b_instance_0006 | 84.03 | 80.84 | 2770.47 | **83.32** | 99.16% |
| b_instance_0007 | 108.00 | **108.00** | 108.00 | **108.00** | 100.00% |
| b_instance_0008 | 227.10 | 127.50 | 5502.92 | **225.00** | 99.08% |
| b_instance_0009 | 82.50 | 53.42 | 2778.56 | **82.50** | 100.00% |
| b_instance_0010 | 444.00 | 115.57 | 8300.91 | **443.00** | 99.77% |
| b_instance_0011 | 898.80 | 123.71 | 19101.00 | **885.10** | 98.48% |
| b_instance_0012 | 567.64 | 177.89 | 11957.75 | **557.45** | 98.21% |
| b_instance_0013 | 757.00 | 107.68 | 19417.00 | **743.56** | 98.22% |
| b_instance_0014 | 885.17 | 112.69 | 18556.22 | **881.00** | 99.53% |
| b_instance_0015 | 166.14 | 90.09 | 6016.78 | **162.07** | 97.55% |
| x_instance_0001 | 70.85 | 68.00 | 1976.12 | **69.62** | 98.26% |
| x_instance_0002 | 217.67 | **217.67** | 217.67 | **217.67** | 100.00% |
| x_instance_0003 | 667.67 | 494.75 | 3817.52 | **666.00** | 99.75% |
| x_instance_0004 | 202.75 | 178.71 | 3777.10 | **188.50** | 92.97% |
| x_instance_0005 | 628.67 | 392.23 | 5099.00 | **628.67** | 100.00% |
| x_instance_0006 | 191.86 | 175.24 | 2742.34 | **187.13** | 97.54% |
| x_instance_0007 | 115.15 | 70.74 | 4527.98 | **112.64** | 97.82% |
| x_instance_0008 | 438.22 | 115.60 | 10520.00 | **414.50** | 94.59% |
| x_instance_0009 | 819.88 | 106.63 | 17674.86 | **805.75** | 98.28% |
| x_instance_0010 | 964.62 | 172.12 | 14433.00 | **914.22** | 94.77% |
| x_instance_0011 | 1060.00 | 105.12 | 20588.24 | **1045.50** | 98.63% |
| x_instance_0012 | 1339.67 | 132.18 | 28890.00 | **1334.00** | 99.58% |
| x_instance_0013 | 1060.71 | 121.57 | 28203.00 | **1043.57** | 98.38% |
| x_instance_0014 | 1633.67 | 183.19 | 22918.00 | **1617.00** | 98.98% |
| x_instance_0015 | 263.91 | 227.48 | 4254.05 | **261.36** | 99.04% |

## Médias da porcentagem do melhor valor oficial

| conjunto | algoritmo genético | algoritmo exato |
| --- | ---: | ---: |
| Conjunto B (15 instâncias) | 98.92% | 58.34% |
| Conjunto X (15 instâncias) | 97.91% | 50.62% |
| **Geral (30 instâncias)** | **98.41%** | **54.48%** |

## Observações

- **Maior objetivo por instância:** algoritmo genético venceu em 28 instâncias, empatou no ótimo com o algoritmo exato em 2 (`b_instance_0007`, `x_instance_0002`) e o algoritmo exato venceu em 0.
- **Ótimos provados pelo algoritmo exato em 600 s:** 2 de 30 (`b_instance_0007`, `x_instance_0002`).
