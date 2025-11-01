import json
import boto3
import math
import os
from decimal import Decimal # Necessário para o DynamoDB

# Inicializa os clientes da AWS
dynamodb = boto3.resource('dynamodb')

# Obtém nomes das variáveis de ambiente
PEDIDOS_TABLE_NAME = os.environ['PEDIDOS_TABLE_NAME']
GALPOES_TABLE_NAME = os.environ['GALPOES_TABLE_NAME']
# PRODUTO_TABLE_NAME = os.environ['PRODUTO_ORIGEM_LOC_TABLE_NAME'] # Descomente se for usar

def calculate_distance(point_a, point_b):
    """
    Calcula a distância Euclidiana (conforme imagem)
    point_a/b devem ser dicionários como {'x': 10, 'y': 20}
    """
    x1, y1 = point_a['x'], point_a['y']
    x2, y2 = point_b['x'], point_b['y']
    
    # Converte para float para cálculo, caso venham como Decimal do DynamoDB
    distancia = math.sqrt((float(x2) - float(x1))**2 + (float(y2) - float(y1))**2)
    return distancia

def lambda_handler(event, context):
    """
    Recebe uma mensagem do SQS, encontra o galpão mais próximo
    e atualiza o pedido no DynamoDB.
    """
    pedidos_table = dynamodb.Table(PEDIDOS_TABLE_NAME)
    galpoes_table = dynamodb.Table(GALPOES_TABLE_NAME)

    # Processa cada mensagem recebida do SQS
    for record in event['Records']:
        try:
            message = json.loads(record['body'])
            
            pedido_id = message['pedidoId']
            cliente_loc = message['clienteLoc'] # Ex: {'x': 10, 'y': 25}

            print(f"Processando Pedido: {pedido_id} para Cliente em: {cliente_loc}")

            # 1. Lê a tabela de galpões
            # Nota: .scan() lê a tabela inteira. Para produção, use uma
            # arquitetura de geolocalização (ex: Geo Library for DynamoDB)
            response = galpoes_table.scan()
            galpoes = response.get('Items', [])

            if not galpoes:
                print("Nenhum galpão cadastrado.")
                continue # Pula para a próxima mensagem

            # 2. Encontra o galpão mais próximo
            closest_galpao = None
            min_distance = float('inf')

            for galpao in galpoes:
                # Assume que o galpão tem um atributo 'localizacao'
                # Ex: {'galpaoId': 'g1', 'nome': 'Galpao Vitoria', 'localizacao': {'x': 5, 'y': 8}}
                galpao_loc = galpao['localizacao']
                
                distancia = calculate_distance(cliente_loc, galpao_loc)
                
                print(f"Distância para {galpao['galpaoId']}: {distancia}")

                if distancia < min_distance:
                    min_distance = distancia
                    closest_galpao = galpao

            # 3. Atualiza o pedido no DynamoDB com o galpão alocado
            if closest_galpao:
                print(f"Galpão mais próximo: {closest_galpao['galpaoId']} a {min_distance} unidades.")
                
                # Converte floats para Decimal para salvar no DynamoDB
                min_distance_decimal = Decimal(str(min_distance))

                pedidos_table.update_item(
                    Key={'pedidoId': pedido_id},
                    UpdateExpression="set #status = :s, galpaoAlocadoId = :g, distancia = :d",
                    ExpressionAttributeNames={
                        '#status': 'status' # 'status' é uma palavra reservada
                    },
                    ExpressionAttributeValues={
                        ':s': 'ALOCADO',
                        ':g': closest_galpao['galpaoId'],
                        ':d': min_distance_decimal
                    }
                )
            else:
                print("Não foi possível encontrar um galpão.")

        except Exception as e:
            print(f"Erro ao processar mensagem: {e}")
            # Considerar mover a mensagem para uma Dead-Letter Queue (DLQ)
            # Aqui, apenas logamos o erro e continuamos
            
    return {'status': 'sucesso'}