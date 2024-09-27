import hashlib
import json
import os  # Importar para manejar archivos
from time import time
from urllib.parse import urlparse
from uuid import uuid4
import requests

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()  # Conjunto de nodos en la red

        # Intentar cargar la blockchain y las transacciones desde archivos
        self.load_data()

        # Crear el bloque génesis si la cadena está vacía
        if not self.chain:
            self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Crea un nuevo bloque en la blockchain

        :param proof: La prueba dada por el algoritmo de consenso (PoW)
        :param previous_hash: (Opcional) Hash del bloque anterior
        :return: Nuevo bloque
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reiniciar la lista actual de transacciones
        self.current_transactions = []

        self.chain.append(block)

        # Guardar la cadena en el archivo después de agregar un bloque
        self.save_data()

        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Crea una nueva transacción para ir al siguiente bloque minado

        :param sender: Dirección del remitente
        :param recipient: Dirección del destinatario
        :param amount: Cantidad
        :return: El índice del bloque que contendrá la transacción
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        # Guardar las transacciones después de añadir una nueva
        self.save_data()

        return self.last_block['index'] + 1

    # Método para guardar la cadena y las transacciones en archivos JSON
    def save_data(self):
        with open('chain.json', 'w') as f:
            json.dump(self.chain, f, indent=4)
        with open('transactions.json', 'w') as f:
            json.dump(self.current_transactions, f, indent=4)

    # Método para cargar la cadena y las transacciones desde archivos JSON
    def load_data(self):
        if os.path.exists('chain.json'):
            with open('chain.json', 'r') as f:
                self.chain = json.load(f)
        if os.path.exists('transactions.json'):
            with open('transactions.json', 'r') as f:
                self.current_transactions = json.load(f)

    @staticmethod
    def hash(block):
        """
        Crea un hash SHA-256 de un bloque

        :param block: Bloque
        :return: Hash
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Algoritmo simple de Prueba de Trabajo (PoW):

        - Encuentra un número p' tal que hash(pp') contenga 4 ceros iniciales, donde p es el proof del bloque anterior y p' es el nuevo proof

        :param last_proof: Proof del bloque anterior
        :return: Nuevo proof
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Valida la prueba: ¿el hash (last_proof, proof) tiene 4 ceros iniciales?

        :param last_proof: Proof del bloque anterior
        :param proof: Proof actual
        :return: True si es válido, False si no
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def register_node(self, address):
        """
        Añade un nuevo nodo a la lista de nodos

        :param address: Dirección del nodo. Ejemplo: 'http://192.168.0.5:5000'
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        """
        Determina si una cadena dada es válida

        :param chain: Una blockchain
        :return: True si es válida, False si no
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Verificar que el hash del bloque anterior sea correcto
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Verificar que la prueba de trabajo sea correcta
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        """
        Algoritmo de consenso: Resuelve conflictos reemplazando nuestra cadena por la más larga en la red

        :return: True si nuestra cadena fue reemplazada, False si no
        """
        neighbours = self.nodes
        new_chain = None

        # Solo buscamos cadenas más largas que la nuestra
        max_length = len(self.chain)

        # Obtener y verificar la cadena de todos los nodos en nuestra red
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                # Verificar si la cadena es más larga y válida
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Reemplazar la cadena si encontramos una válida y más larga
        if new_chain:
            self.chain = new_chain
            return True

        return False
