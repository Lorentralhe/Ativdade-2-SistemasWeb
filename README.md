# API de Logística Serverless na AWS

![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg?logo=python\&logoColor=white)
![AWS SAM](https://img.shields.io/badge/AWS-SAM-orange.svg?logo=amazon-aws\&logoColor=white)
![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg?logo=amazon-aws\&logoColor=white)
![Amazon SQS](https://img.shields.io/badge/Amazon-SQS-red.svg?logo=amazon-aws\&logoColor=white)
![Amazon DynamoDB](https://img.shields.io/badge/Amazon-DynamoDB-blue.svg?logo=amazon-aws\&logoColor=white)
![Licença](https://img.shields.io/badge/Licença-MIT-green.svg)

## 🎯 Objetivo do Projeto

Este projeto implementa uma API serverless de alta disponibilidade para um sistema de logística. O objetivo é receber pedidos e, de forma assíncrona, processar a geolocalização do cliente para alocar o centro de distribuição (galpão) mais próximo, otimizando assim o tempo de entrega e garantindo que o sistema seja escalável e resiliente.

A aplicação é construída inteiramente com serviços gerenciados da AWS, seguindo os padrões de arquitetura serverless e Infraestrutura como Código (IaC) usando o **AWS Serverless Application Model (SAM)**.

---

## 🏛️ Arquitetura

O fluxo da aplicação é totalmente desacoplado para garantir resiliência e escalabilidade:

1. Um usuário envia um pedido `POST` para o **Amazon API Gateway**.
2. O API Gateway invoca a função Lambda **`FechaPedidoFunction`**.
3. Esta Lambda valida os dados recebidos, gera um `pedidoId` único e salva o pedido com status `PENDENTE_ALOCACAO` na tabela **DynamoDB (`PedidosRealizadosTable`)**.
4. A Lambda envia uma mensagem com os dados do pedido para uma fila **Amazon SQS (`AlocacaoQueue`)**.
5. A fila SQS invoca de forma assíncrona a função Lambda **`CalculaDistanciaFunction`**.
6. A segunda Lambda lê a localização de todos os galpões cadastrados na tabela **DynamoDB (`CadastraGalpoesLocTable`)**, calcula a distância euclidiana e atualiza o item com o `galpaoId` e status `ALOCADO`.

![Diagrama da Arquitetura](docs/arquitetura.jpg)

---

## 💻 Tecnologias Utilizadas

* **IaC:** AWS SAM
* **Serverless:** AWS Lambda
* **API:** Amazon API Gateway
* **Banco de Dados:** Amazon DynamoDB
* **Mensageria:** Amazon SQS
* **Linguagem:** Python 3.11
* **Logs e Monitoramento:** Amazon CloudWatch

---

## 🗂️ Estrutura do Projeto

```
.
├── .gitignore
├── README.md
├── calcula_distancia/
│   ├── app.py
│   └── requirements.txt
├── fecha_pedido/
│   ├── app.py
│   └── requirements.txt
└── template.yaml
```

---

## 🔧 Configuração e Variáveis de Ambiente

Variáveis definidas no `template.yaml` via `!Ref` e `!GetAtt`.

```yaml
globals:
  Function:
    Environment:
      Variables:
        PEDIDOS_TABLE_NAME: !Ref PedidosRealizadosTable
        GALPOES_TABLE_NAME: !Ref CadastraGalpoesLocTable
        ALOCACAO_QUEUE_URL: !Ref AlocacaoQueue
```

---

## 🚀 Guia de Deploy

### Pré-requisitos

* Conta AWS
* AWS CLI configurado
* AWS SAM CLI
* Python 3.11
* Docker

### Passos

```bash
git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
cd SEU-REPOSITORIO
sam build
sam deploy --guided
```

Configurações recomendadas:

* Stack Name: `app-logistica`
* Region: `us-east-1`
* Allow IAM: Yes

---

## 🧪 Testando a Aplicação

### 1. Inserir galpões

**Galpão Vitória:**

```json
{
  "galpaoId": "g-vitoria",
  "localizacao": { "x": 10, "y": 15 },
  "nome": "Galpão de Vitória"
}
```

**Galpão Serra:**

```json
{
  "galpaoId": "g-serra",
  "localizacao": { "x": 80, "y": 90 },
  "nome": "Galpão da Serra"
}
```

### 2. Criar `payload.json`

```json
{
  "produtoId": "prod-456",
  "clienteLoc": { "x": 12, "y": 18 }
}
```

### 3. Enviar requisição

```bash
curl -X POST "https://SUA-URL.execute-api.REGION.amazonaws.com/Prod/pedido" \
-H "Content-Type: application/json" \
-d "@payload.json"
```

### Resposta esperada

```json
{"message": "Pedido recebido com sucesso!", "pedidoId": "..."}
```

---

## 🌟 Melhorias Futuras

* Autenticação (Cognito/API Keys)
* Geolocalização otimizada (Geohash/Amazon Location Service)
* Validação de entrada via API Gateway
* Pipeline CI/CD
* DLQ para SQS

---

## 🧹 Limpeza dos Recursos

```bash
sam delete --stack-name app-logistica
```

---

## 📄 Licença

Projeto licenciado sob MIT.
