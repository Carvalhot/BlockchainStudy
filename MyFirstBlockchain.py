import datetime # Para armazenar a data de criação dos blocos
import hashlib # Para utilizar as funções hash
import json # P/ transformar os blocos em json para depois transformalos em hash
from flask import Flask, jsonify # Fazer os requests no Postman e exibir os resultados e retornar os resultados em json

# Parte 1, criar um blockchain

# Bloco Gênesis
class Blockchain:
    def __init__(self): 
        self.chain = []
        self.create_block(proof = 1, previous_hash = '0')#, block_hash = 'null' )
        
    # Criação do bloco com as respectivas informações
    def create_block(self, proof, previous_hash):#, block_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash
                 #'block_hash': block_hash
                 }
        
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
 
# Segunda parte, mineirando o bloco
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
# Instanciando a classe blockchain
blockchain = Blockchain()

@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    # Aqui esta o problema
    # Preciso encripitar o block para ter o seu hash, 
    # Porém este hash deve ser inserido devolta neste block
    block = blockchain.create_block(proof, previous_hash)
    #block_hash = blockchain.hash(block)
    #block['block_hash'] = block_hash
    response = {'message': 'Parabéns você minerou um bloco!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash']
                #'block_hash': block['block_hash']
                }
  
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
        response = {'message':"Blockchain é válido!"}
    else:
        response = {'message': "Blockchain é inválido!"}
    return jsonify(response), 200

app.run(host = '0.0.0.0', port = 5000)