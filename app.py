import sys
from flask import Flask, jsonify, request
from uuid import uuid4
from blockchain import Blockchain

# El resto de tu código sigue igual...


# Instanciar la aplicación de Flask
app = Flask(__name__)

# Generar una dirección única para este nodo
node_identifier = str(uuid4()).replace('-', '')

# Instanciar la blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    # Ejecutar el algoritmo de consenso para obtener la siguiente prueba
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Recompensar al minero otorgándole una nueva transacción
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Crear el nuevo bloque
    block = blockchain.new_block(proof)

    response = {
        'message': "Nuevo Bloque Minado",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    # Verificar que los campos requeridos estén en los datos POST
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Faltan valores', 400

    # Crear una nueva transacción
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'La transacción se añadirá al bloque {index}'}
    return jsonify(response), 201

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Por favor, suministra una lista válida de nodos", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'Nuevos nodos han sido añadidos',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'La cadena fue reemplazada',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Nuestra cadena es autoritativa',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

# Ejecutar el servidor
if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '-p':
        port = int(sys.argv[2])
    else:
        port = 5000  # Puerto por defecto

    app.run(host='0.0.0.0', port=port)
