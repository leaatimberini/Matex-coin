import json
import hashlib
from uuid import uuid4

class Wallet:
    def __init__(self):
        self.address = self.create_wallet_address()

    def create_wallet_address(self):
        # Genera una dirección de billetera única usando UUID y SHA-256
        random_id = str(uuid4()).encode('utf-8')
        return hashlib.sha256(random_id).hexdigest()

    def to_dict(self):
        return {
            'address': self.address
        }

def save_wallet(wallet, filename='wallets.json'):
    try:
        with open(filename, 'r') as f:
            wallets = json.load(f)
    except FileNotFoundError:
        wallets = []

    wallets.append(wallet.to_dict())

    with open(filename, 'w') as f:
        json.dump(wallets, f, indent=4)

def load_wallets(filename='wallets.json'):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
