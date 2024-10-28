# Modelagem Matemática: Problema de Alocação de Salas com Múltiplos Objetivos

## 1. Descrição do Problema
O problema consiste em alocar um conjunto de disciplinas a salas de aula e laboratórios, considerando restrições de horário, capacidade, preferências de localização e requisitos específicos de infraestrutura, minimizando diversos tipos de penalidades.

## 2. Conjuntos
- $D = \{1, \dots, n\}$: conjunto de disciplinas
- $S = \{1, \dots, s\}$: conjunto de salas regulares
- $L = \{1, \dots, l\}$: conjunto de laboratórios
- $R = S \cup L$: conjunto de todas as salas disponíveis
- $H = \{1, \dots, h\}$: conjunto de períodos de tempo (slots)
- $A = \{1, \dots, a\}$: conjunto de andares do edifício

## 3. Parâmetros

### 3.1 Parâmetros Binários
- $t[d,h]$: matriz de horários das disciplinas
  - 1: se a disciplina $d$ ocorre no período $h$
  - 0: caso contrário
- $m[r,a]$: matriz de localização das salas
  - 1: se a sala $r$ está localizada no andar $a$
  - 0: caso contrário
- $req[d]$: requisito de infraestrutura da disciplina $d$
  - 1: requer laboratório
  - 0: requer sala regular
- $p[d,a]$: preferência de andar para disciplina $d$
  - 1: se há preferência pelo andar $a$
  - 0: caso contrário

### 3.2 Parâmetros Numéricos
- $c[d]$: número de alunos matriculados na disciplina $d$
- $cap[r]$: capacidade da sala $r$
- $\alpha$: limite máximo permitido de ocupação (em percentual da capacidade)
- $w_1$: peso da penalidade por alocação fora do andar preferencial
- $w_2$: peso da penalidade por uso inadequado de laboratório
- $w_3$: peso da penalidade por uso inadequado de sala regular
- $w_4$: peso da penalidade por distância entre andares
- $w_5$: peso da penalidade por violação de capacidade

## 4. Variáveis de Decisão

### 4.1 Variáveis Binárias
- $x[d,r]$: variável de alocação
  - 1: se a disciplina $d$ é atribuída à sala $r$
  - 0: caso contrário
- $v_l[d]$: variável de violação de requisito de laboratório
  - 1: se uma disciplina que requer laboratório é alocada em sala regular
  - 0: caso contrário
- $v_s[d]$: variável de violação de requisito de sala regular
  - 1: se uma disciplina que requer sala regular é alocada em laboratório
  - 0: caso contrário

### 4.2 Variáveis Inteiras
- $y[d]$: distância (em número de andares) entre a sala atribuída e o andar preferencial para a disciplina $d$
- $z[d,r]$: violação de capacidade quando a disciplina $d$ é atribuída à sala $r$

## 5. Função Objetivo
Minimizar
$$ 
Z = w_1 \sum_{d \in D} \sum_{r \in R} \sum_{a \in A} x[d,r] \times p[d,a] \times (1 - m[r,a]) + w_2 \sum_{d \in D} v_l[d] + w_3 \sum_{d \in D} v_s[d] + w_4 \sum_{d \in D} y[d] + w_5 \sum_{d \in D} \sum_{r \in R} z[d,r]
$$

## 6. Restrições

### 6.1 Atribuição Única
Cada disciplina deve ser atribuída a exatamente uma sala:
$$ \sum_{r \in R} x[d,r] = 1, \quad \forall d \in D $$

### 6.2 Não Sobreposição de Horários
Uma sala não pode ter mais de uma disciplina no mesmo horário:
$$ \sum_{d \in D} x[d,r] \times t[d,h] \leq 1, \quad \forall r \in R, \forall h \in H $$

### 6.3 Requisitos de Infraestrutura
Identificação de violações de requisitos de laboratório:
$$ v_l[d] = req[d] \times (1 - \sum_{r \in L} x[d,r]), \quad \forall d \in D $$

Identificação de violações de requisitos de sala regular:
$$ v_s[d] = (1 - req[d]) \times \sum_{r \in L} x[d,r], \quad \forall d \in D $$

### 6.4 Cálculo de Distância
Para cada disciplina, a distância em relação ao andar preferencial:
$$ y[d] \geq \sum_{r \in R} \sum_{a_1 \in A} \sum_{a_2 \in A} x[d,r] \times p[d,a_1] \times m[r,a_2] \times |a_1 - a_2|, \quad \forall d \in D $$

### 6.5 Restrições de Capacidade
Cálculo da violação de capacidade:
$$ z[d,r] \geq x[d,r] \times (c[d] - cap[r]), \quad \forall d \in D, \forall r \in R $$

Limite de violação de capacidade:
$$ c[d] \leq cap[r] \times \alpha + M \times (1 - x[d,r]), \quad \forall d \in D, \forall r \in R $$
onde $M$ é um número suficientemente grande.

## 7. Condições de Integralidade e Não-Negatividade
- $x[d,r] \in \{0,1\}, \quad \forall d \in D, \forall r \in R$
- $v_l[d] \in \{0,1\}, \quad \forall d \in D$
- $v_s[d] \in \{0,1\}, \quad \forall d \in D$
- $y[d] \geq 0$ e inteiro, $\forall d \in D$
- $z[d,r] \geq 0$ e inteiro, $\forall d \in D, \forall r \in R$
