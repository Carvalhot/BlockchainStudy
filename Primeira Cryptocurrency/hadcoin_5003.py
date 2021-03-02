import datetime # Para armazenar a data de criação dos blocos
import hashlib # Para utilizar as funções hash
import json # P/ transformar os blocos em json para depois transformalos em hash
from flask import Flask, jsonify, request # Fazer os requests no Postman e exibir os resultados e retornar os resultados em json
import requests
from uuid import uuid4
from urllib.parse import urlparse


# Parte 1, criar um blockchain

# Bloco Gênesis/Config do Bloco
class Blockchain:
    def __init__(self): 
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()
        
    # Criação do bloco com as respectivas informações
    def create_block(self, proof, previous_hash):#, block_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'transactions': self.transactions
                 }
        self.transactions = []
        self.chain.append(block)
        return block
    
    # Método para retornar o último bloco criado
    def get_previous_block(self):
        return self.chain[-1]
        
    # Criação da função PoW
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    # Função para encripitar um bloco
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    # Função para validar a cadeia de blocos
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            # Se a propriedade "previous_hash" do bloco atual for diferente do valor do hash do ultimo bloco (previous_block) a cadeia de blocos não é válida
            if block['previous_hash'] != self.hash(previous_block):
                return False
            # Se o valor do hash dos proof's não começar com uma sequencia de 4 zeros, o bloco é inválido
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
 
    # Função para adicionar transações
    def add_transaction(self, sender, receiver, amount):
        self.transactions.append({'sender': sender, 
                                   'receiver': receiver, 
                                   'amount': amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
     
     # Função para pegar o ip dos nós da rede   
    def add_nodes(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    
    # Função protocolo de consenso
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']                
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

# Segunda parte, mineirando o bloco
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

node_address = str(uuid4()).replace('-', '')


# Instanciando a classe blockchain
blockchain = Blockchain()

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    replace_chain()
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address,
                               receiver = 'Ciclano',
                               amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Parabéns você minerou um bloco!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transaction': block['transactions']}
    return jsonify(response), 200

@app.route('/get_chain', methods = ['GET'])    
def get_chain():
    response = {'chain': blockchain.chain, 
                'length': len(blockchain.chain)}
    return jsonify(response), 200


@app.route('/get_is_chain_valid', methods = ['GET'])
def get_is_chain_valid():
    is_valid = {'Valid': blockchain.is_chain_valid(blockchain.chain)}
    if is_valid:
        response = {'message': 'Blockchain é válido!'}
    else:
        response = {'message': 'Blockchain é inválido!'}
    return jsonify(response), 200

@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transactions_key = ['sender','receiver','amount']
    if not all(key in json for key in transactions_key):
        return 'Alguns elementos estão faltando', 400
    index = blockchain.add_transaction(json['sender'],
                                       json['receiver'],
                                       json['amount'])
    response = {'message': f'Esta transação será adicionada ao bloco {index}'}
    return jsonify(response),201

@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'Sem nós', 400
    for node in nodes:
        blockchain.add_nodes(node)
    response = {'message': 'Nós conectados!',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Função para substituir o blockchain menor
@app.route('/replace_chain', methods =  ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message:': 'Conflito de blocos. Cadeia substituída!',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'Sem conflito de blocos.',
                    'actual_chain': blockchain.chain}
    return jsonify(response),201



app.run(host = '0.0.0.0', port = 5003)