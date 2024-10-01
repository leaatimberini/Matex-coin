import sys
from flask import Flask, jsonify, request
from uuid import uuid4
from blockchain import Blockchain
from functools import wraps
import jwt
import datetime
from wallet import Wallet, save_wallet, load_wallets

SECRET_KEY = 'Pb]XQkjdfP77Rf;LNiw^'  # Asegúrate de cambiarla por algo más seguro

# Instanciar la aplicación de Flask
app = Flask(__name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')  # Obtener el token de los parámetros de la URL
        if not token:
            return jsonify({'message': 'Token es necesario!'}), 403
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'El token ha expirado!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido!'}), 401
        return f(*args, **kwargs)
    return decorated

# Generar una dirección única para este nodo
node_identifier = str(uuid4()).replace('-', '')

# Instanciar la blockchain
blockchain = Blockchain()
@app.route('/login', methods=['POST'])
def login():
    auth = request.get_json()
    if auth and auth['username'] == 'admin' and auth['password'] == 'password':  # Cambia a algo más seguro
        token = jwt.encode({'user': auth['username'], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, SECRET_KEY, algorithm="HS256")
        return jsonify({'token': token})
    return jsonify({'message': 'No autorizado'}), 401

@app.route('/mine', methods=['GET'])
@token_required
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
@token_required
def new_transaction():
    try:
        values = request.get_json()
        if not values:
            return 'Error: No se proporcionaron datos JSON', 400

        required = ['sender', 'recipient', 'amount']
        if not all(k in values for k in required):
            return 'Faltan valores en la transacción', 400

        # Verificar si el remitente tiene saldo suficiente
        if not blockchain.is_valid_transaction(values['sender'], values['amount']):
            return jsonify({'message': 'Saldo insuficiente para realizar la transacción'}), 400

        # Crear la nueva transacción
        index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

        # Difundir la transacción a otros nodos
        blockchain.broadcast_transaction(values)

        response = {'message': f'La transacción se añadirá al bloque {index}'}
        return jsonify(response), 201
    except Exception as e:
        print(f"Error procesando la transacción: {e}")
        return 'Error interno del servidor', 500


@app.route('/transactions/pending', methods=['GET'])
def get_pending_transactions():
    response = {
        'pending_transactions': blockchain.current_transactions,
        'total': len(blockchain.current_transactions)
    }
    return jsonify(response), 200

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
        return "Error: Favor de suministrar una lista válida de nodos", 400

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
            'message': 'Nuestra cadena es la autorizada',
            'chain': blockchain.chain
        }

    return jsonify(response), 200

# Endpoint para obtener el saldo de una dirección específica.
@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    """
    Endpoint para obtener el saldo de una dirección específica.

    :param address: Dirección a verificar
    :return: Saldo de la dirección
    """
    balance = blockchain.get_balance(address)
    response = {
        'address': address,
        'balance': balance,
    }
    return jsonify(response), 200

@app.route('/broadcast_block', methods=['POST'])
def broadcast_block():
    values = request.get_json()
    
    # Verificar que se recibieron datos
    if not values:
        return 'Error: No se proporcionaron datos JSON', 400
    
    # Intentar recibir el bloque
    block_added = blockchain.receive_block(values)
    
    if block_added:
        response = {'message': 'Bloque recibido y añadido correctamente'}
        return jsonify(response), 201
    else:
        response = {'message': 'El bloque no se pudo añadir. Cadena en proceso de consenso.'}
        return jsonify(response), 400
    
# Endpoint para crear una nueva billetera
@app.route('/wallet/new', methods=['GET'])
def new_wallet():
    wallet = Wallet()
    save_wallet(wallet)
    response = {
        'message': 'Nueva billetera creada',
        'address': wallet.address
    }
    return jsonify(response), 201

# Endpoint para obtener todas las billeteras
@app.route('/wallets', methods=['GET'])
def get_wallets():
    wallets = load_wallets()
    return jsonify({'wallets': wallets, 'total': len(wallets)}), 200

# Ejecutar el servidor
if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '-p':
        port = int(sys.argv[2])
    else:
        port = 5000  # Puerto por defecto

    app.run(host='0.0.0.0', port=port)
