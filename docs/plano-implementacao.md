# Plano de implementação do TPF

Plano fechado em 2026-11-20 para o trabalho final de Análise e Projeto de Algoritmos (desafio SBPO 2025). O texto está em português, e todo o código, os nomes de arquivos, os comentários, as docstrings e as chaves dos JSON ficam em inglês.

## Decisões

- O enunciado da disciplina é a regra final. O README, a descrição do problema e o regulamento do desafio só valem para o que o enunciado não define. Por isso Python e HiGHS são permitidos (seção 2 do enunciado), mesmo com o regulamento exigindo Java e CPLEX ou OR-Tools.
- Solver HiGHS via `highspy`, com o método de Dinkelbach para tratar o objetivo em forma de fração.
- Algoritmo genético com vetor de bits sobre os corredores e penalidade para ondas abaixo de LB. Em 2026-11-21 essa versão substituiu a primeira, que usava bits sobre os pedidos e reparo, porque a primeira visitava quase todos os corredores e chegava a menos de 7% do melhor valor oficial.
- As 30 instâncias da fase final (conjuntos B e X), com 600 s por instância e por método nas rodadas atuais.
- O professor confirmou que a avaliação da disciplina não usa o limite de tempo do desafio. O grupo mantém `time_limit_seconds` como parâmetro, porque sem limite o algoritmo exato pode não terminar em tempo útil nas instâncias grandes. Como a nota compara a qualidade das soluções com a dos outros grupos, o grupo pode escolher um limite maior para a rodada final.
- Cada execução gera um par `.txt` e `.json`. Na avaliação, o grupo escolhe qual algoritmo submeter.
- A comparação final usa `best_objectives.csv` do repositório oficial.
- O enunciado não diz quais instâncias a turma avalia. Usar B e X é uma suposição do grupo.

## Arquivos

```
TPF/
├── configs/
│   ├── run.json                  uma instância, um método e os parâmetros dele
│   └── batch.json                listas de instâncias, métodos e parâmetros
├── data/
│   ├── b_instance_0001.txt ...   as 30 instâncias, com prefixo b_ ou x_
│   └── best_objectives.csv       cópia do arquivo oficial
├── results/
│   ├── b_instance_0001_exact.txt
│   ├── b_instance_0001_exact.json
│   ├── b_instance_0001_genetic_<parameters>.txt
│   └── b_instance_0001_genetic_<parameters>.json
├── src/order_selection/
│   ├── __init__.py               vazio, marca o pacote
│   ├── __main__.py               só chama cli
│   ├── cli.py                    recebe o caminho do JSON e chama o lote
│   ├── batch_runner.py           itertools.product das listas, uma execução por combinação
│   ├── instance.py               lê a instância, escreve a solução, calcula o objetivo
│   ├── exact_algorithm.py        Dinkelbach com HiGHS
│   ├── genetic_algorithm.py      cromossomo, decodificador, evolução
│   └── checker.py                checker.py oficial copiado sem mudanças
├── tests/
│   ├── test_instance.py          testes de exemplo e de propriedade
│   └── test_genetic_algorithm.py testes do decodificador e da evolução
└── pyproject.toml
```

O prefixo `b_` ou `x_` é necessário porque os dois conjuntos repetem nomes como `instance_0001`.

Cada `.txt` segue o formato oficial lido pelo `checker.py`. Cada `.json` guarda os dados da instância (pedidos, itens, corredores, LB e UB), o método, os parâmetros, o commit que rodou, o objetivo, os corredores visitados, o melhor valor oficial e a porcentagem dele. O algoritmo genético acrescenta as gerações e o segundo em que achou a melhor solução. O algoritmo exato acrescenta os limites inferior e superior, o status e o tempo. O formato completo está na issue #14.

## Dependências externas

- `highspy`: solver gratuito de Programação Linear Inteira que resolve o algoritmo exato.
- `pytest`: roda os testes. Fica no grupo de desenvolvimento.
- `hypothesis`: gera entradas aleatórias para os testes de propriedade. Fica no grupo de desenvolvimento.
- `numpy`: faz as operações sobre vetores do algoritmo genético. O `checker.py` oficial já depende dela.

JSON, `itertools` e `time` vêm da biblioteca padrão.

## Algoritmos

**Algoritmo exato.** O Dinkelbach maximiza "unidades − λ·corredores" com as restrições (2), (3) e (4) da descrição oficial e depois atualiza λ para unidades/corredores da solução encontrada. Ele para quando o máximo chega a zero. Se os 600 s acabarem, o limite inferior é o λ atual e o limite superior é λ + F̄, onde F̄ é o limite superior que o HiGHS devolve para a última rodada. Essa conta vale porque o número de corredores de qualquer solução é pelo menos 1.

**Algoritmo genético.** O indivíduo é um vetor de bits sobre os corredores, e o bit 1 quer dizer que a onda visita o corredor. Um decodificador transforma os corredores em pedidos. Ele soma o estoque dos corredores visitados, fica com os pedidos que cabem nesse estoque, divide o estoque disputado pela ordem de prioridade dos pedidos (do maior para o menor) e para de acrescentar pedidos ao chegar a UB. A onda respeita o estoque e UB por construção. Se ficar abaixo de LB, a aptidão é menos o que falta para LB. Caso contrário, é unidades/corredores. O resto é torneio, cruzamento uniforme, mutação por troca de bit e parada por número de gerações, com o limite de tempo como trava. Os parâmetros (tamanho da população, tamanho do torneio, taxa de mutação, número máximo de gerações, semente e tempo limite) vêm do JSON de configuração.

## Passos e critério de pronto

Todo passo só termina com `ruff check .`, `complexipy .`, `vulture .` e `pytest` passando.

1. **Configurar o projeto.** Pronto quando `pyproject.toml` declarar o pacote em `src/` e as dependências, excluir `checker.py` do Ruff, do complexipy e do Vulture, e `uv sync` rodar sem erro.
2. **Baixar os dados.** Pronto quando `data/` tiver as 30 instâncias e `best_objectives.csv`, e o `checker.py` aceitar uma solução escrita à mão para o exemplo oficial.
3. **Escrever `instance.py`.** Pronto quando o exemplo oficial (pedidos 0, 1, 2 e 4 com os corredores 1 e 3) der objetivo 5 e um teste de propriedade mostrar que escrever e depois ler uma solução devolve a mesma solução.
4. **Escrever `genetic_algorithm.py`.** Pronto quando um teste de propriedade mostrar que toda onda decodificada com aptidão positiva é viável e o `checker.py` aprovar a saída de `b_instance_0001`.
5. **Escrever `exact_algorithm.py`.** Pronto quando o exemplo oficial terminar com ótimo provado igual a 5 e o `checker.py` aprovar a saída de `b_instance_0001`, com os limites gravados no JSON.
6. **Escrever `cli.py` e `batch_runner.py`.** Pronto quando `uv run python -m order_selection configs/batch.json` gerar um par `.txt` e `.json` para cada combinação de um lote pequeno.
7. **Rodar as 30 instâncias com os dois métodos** (perto de 10 horas). Pronto quando o `checker.py` aprovar as 60 soluções e cada JSON trouxer a porcentagem do valor oficial.

## Divisão de tarefas

A base (passos 1 a 3) já estará pronta quando a divisão começar.

1. **Slides.** A apresentação inteira (issue #7), com a tabela de resultados recebida do integrante 5.
2. **Algoritmo exato.** `exact_algorithm.py` (passo 5, issue #12).
3. **Algoritmo genético.** `genetic_algorithm.py` (passo 4, issue #13).
4. **Lotes.** `batch_runner.py` e os JSON de `configs/` (parte do passo 6, issue #14).
5. **CLI e resultados.** `cli.py` (parte do passo 6), as 60 rodadas e a tabela contra os valores oficiais (passo 7, issue #15).

Duas issues extras ainda sem responsável completam a divisão. A #17 gera os gráficos dos slides em `charts.py`, e a #18 cria uma interface web em React para mostrar os resultados e rodar o algoritmo genético com parâmetros escolhidos na tela.

## Riscos

- Em 2026-11-21 o algoritmo genético rodou as 30 instâncias por 600 s cada, com semente 1, e chegou em média a 98,3% do melhor valor oficial. A pior foi `x_instance_0004`, com 93,0%. Os pares `.txt` e `.json` estão em `results/`.
- Sem limite de tempo na avaliação, outros grupos podem rodar por mais tempo e chegar a soluções melhores. Uma rodada final mais longa do algoritmo genético diminui esse risco.
- Uma instância nova apresentada na hora não cabe em 600 s dentro dos 5 minutos de apresentação.
