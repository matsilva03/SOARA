# Modelagem Matemática: Problema de Alocação de Salas com Múltiplos Objetivos

## 1. Conjuntos

- $D = \{1, \dots, n\}$: conjunto de disciplinas
- $S = \{1, \dots, s\}$: conjunto de salas regulares
- $L = \{1, \dots, l\}$: conjunto de laboratórios
- $R = S \cup L$: conjunto de todas as salas disponíveis
- $H = \{1, \dots, h\}$: conjunto de períodos de tempo (slots)

## 2. Parâmetros

### 2.1 Parâmetros Binários

- $t[d,h] = \begin{cases} 1, & \text{se a disciplina } d \text{ ocorre no período } h \\ 0, & \text{caso contrário} \end{cases}$

- $f[r,a] = \begin{cases} 1, & \text{se a sala } r \text{ está localizada no andar } a \\ 0, & \text{caso contrário} \end{cases}$

- $p[d,a] = \begin{cases} 1, & \text{se a disciplina } d \text{ tem preferência pelo andar } a \\ 0, & \text{caso contrário} \end{cases}$

- $\text{req}[d]$: indicador de requisito de laboratório para a disciplina $d$:
   - 0: requer sala regular
   - 1: requer laboratório

### 2.2 Pesos

- $w_1$: peso da penalização por alocação fora do andar preferencial
- $w_2$: peso da penalização por uso inadequado de laboratório
- $w_3$: peso da penalização por distância entre andares

## 3. Variáveis de Decisão

### 3.1 Variáveis Binárias

- $x[d,r] = \begin{cases} 1, & \text{se a disciplina } d \text{ é atribuída à sala } r \\ 0, & \text{caso contrário} \end{cases}$

### 3.2 Variáveis Inteiras

- $y[d] \geq 0$: distância em número de andares entre a sala atribuída e o andar preferencial para a disciplina $d$

## 4. Função Objetivo

Minimizar

$$
Z = w_1 \sum_{d \in D} \sum_{r \in R} \sum_{a \in A} \left[ x[d,r] \times p[d,a] \times (1 - f[r,a]) \right] + w_2 \sum_{d \in D} \sum_{r \in L} \left[ x[d,r] \times (1 - \text{req}[d]) \right] + w_3 \sum_{d \in D} y[d]
$$

onde:
- Primeiro termo: penaliza alocações fora do andar preferencial
- Segundo termo: penaliza uso desnecessário de laboratórios
- Terceiro termo: penaliza distância entre andares

## 5. Restrições

### 5.1 Atribuição Única

$$
\sum_{r \in R} x[d,r] = 1, \quad \forall d \in D
$$

Cada disciplina deve ser atribuída a exatamente uma sala.

### 5.2 Não Sobreposição de Horários

$$
\sum_{d \in D} x[d,r] \times t[d,h] \leq 1, \quad \forall r \in R, \forall h \in H
$$

Uma sala não pode ter mais de uma disciplina no mesmo horário.

### 5.3 Requisitos de Tipo de Sala

Para disciplinas que requerem laboratório ($\text{req}[d] = 1$):

$$
\sum_{r \in L} x[d,r] = 1, \quad \forall d \in D \text{ onde } \text{req}[d] = 1
$$

Para disciplinas que requerem sala regular ($\text{req}[d] = 0$):

$$
\sum_{r \in S} x[d,r] = 1, \quad \forall d \in D \text{ onde } \text{req}[d] = 0
$$

### 5.4 Cálculo de Distância entre Andares

$$
y[d] \geq \sum_{r \in R} \sum_{a_1 \in A} \sum_{a_2 \in A} \left[ x[d,r] \times p[d,a_1] \times f[r,a_2] \times |a_1 - a_2| \right], \quad \forall d \in D
$$

Calcula a distância em andares entre a alocação real e a preferencial.

## 6. Condições de Integralidade e Não-Negatividade

- $x[d,r] \in \{0,1\}, \quad \forall d \in D, \forall r \in R$
- $y[d] \geq 0$ e inteiro, $\forall d \in D$
