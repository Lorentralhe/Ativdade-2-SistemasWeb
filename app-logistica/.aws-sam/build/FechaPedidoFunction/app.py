import json
import boto3
import uuid
import os

# Inicializa os clientes da AWS
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

# Obtém nomes das variáveis de ambiente definidas no template.yaml
PEDIDOS_TABLE_NAME = os.environ['PEDIDOS_TABLE_NAME']
ALOCACAO_QUEUE_URL = os.environ['ALOCACAO_QUEUE_URL']

def lambda_handler(event, context):
    """
    Recebe um pedido via API Gateway, salva no DynamoDB
    e envia para a fila SQS para processamento.
    """
    try:
        # Pega os dados do corpo da requisição da API
        # Ex: {"produtoId": "prod-123", "clienteLoc": {"x": 10, "y": 25}}
        body = json.loads(event.get('body', '{}'))

        produto_id = body.get('produtoId')
        cliente_loc = body.get('clienteLoc') # Geolocalização do cliente

        if not produto_id or not cliente_loc:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'produtoId e clienteLoc são obrigatórios'})
            }

        # 1. Gera um ID único para o pedido
        pedido_id = str(uuid.uuid4())

        # 2. Salva o pedido inicial no DynamoDB (Tabela: Pedidos Realizados)
        table = dynamodb.Table(PEDIDOS_TABLE_NAME)
        table.put_item(
            Item={
                'pedidoId': pedido_id,
                'produtoId': produto_id,
                'clienteLoc': cliente_loc,
                'status': 'PENDENTE_ALOCACAO'
            }
        )

        # 3. Prepara a mensagem para a fila SQS (Fila: Alocação)
        message_body = {
            'pedidoId': pedido_id,
            'produtoId': produto_id,
            'clienteLoc': cliente_loc
        }

        # 4. Envia a mensagem para o SQS
        sqs.send_message(
            QueueUrl=ALOCACAO_QUEUE_URL,
            MessageBody=json.dumps(message_body)
        )

        # 5. Retorna sucesso para o usuário
        return {
            'statusCode': 201, # 201 Created
            'body': json.dumps({
                'message': 'Pedido recebido com sucesso!',
                'pedidoId': pedido_id
            })
        }

    except Exception as e:
        print(f"Erro: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Erro interno no servidor'})
        }