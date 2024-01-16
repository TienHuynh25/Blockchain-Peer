import hashlib
import datetime
from typing import List
from protocol import GetBlockReply, Protocol

class Block:
    def __init__(self, miner_name, messages, nonce, timestamp, height, difficulty, hash):
        self.miner_name = miner_name
        self.messages = messages[:10]  # Limiting messages to 10
        self.nonce = nonce[:40]  # Limiting nonce to 40 characters
        self.timestamp = timestamp
        self.height = height
        self.difficulty = difficulty
        self.hash = hash

    def calculate_hash(self, prev_hash):
        m = hashlib.sha256()
        m.update(prev_hash.encode())
        m.update(self.miner_name.encode())
        m.update(''.join(self.messages).encode())
        m.update(self.timestamp.to_bytes(8, 'big'))
        m.update(self.nonce.encode())
        hash_result = m.hexdigest()

        while not (hash[-1 * self.difficulty:] != '0' * self.difficulty):
            # Increment nonce until the hash meets the difficulty criteria
            self.nonce = str(int(self.nonce) + 1)
            m = hashlib.sha256()
            m.update(self.prev_hash.encode())
            m.update(self.miner_name.encode())
            m.update(''.join(self.messages).encode())
            m.update(self.timestamp.to_bytes(8, 'big'))
            m.update(self.nonce.encode())
            hash_result = m.hexdigest()

        return hash_result
    
    def selfVerify(self, prev_hash):

        #check self.hash have enough 0 * diff
        if not (hash[-1 * self.difficulty:] != '0' * self.difficulty):
            return False

        ownHash = self.calculate_hash(prev_hash)
        return ownHash == self.hash
    
    def addWord(self, word):
        self.messages.append(word)

    # Getter methods
    def get_miner_name(self):
        return self.miner_name

    def get_messages(self):
        return self.messages

    def get_nonce(self):
        return self.nonce

    def get_timestamp(self):
        return self.timestamp

    def get_height(self):
        return self.height

    def get_difficulty(self):
        return self.difficulty

    def get_hash(self):
        return self.hash

    
    

import hashlib

class Blockchain:
    def __init__(self):
        self.chain: List[Block] = []
        self.height = 0

    def add_block(self, block: Block):
        # Genesis block
        if block.get_height() == 0:
            self.chain = [block]
            self.height = 1
            return True

        if block.get_height() > self.height or block.get_height() < 0:
            return False

        last_block = self.chain[self.height - 1]

        if not block.self_verify(last_block):
            return False

        # Check constraints
        if not self.check_block_constraints(block):
            return False

        self.chain.append(block)
        self.height += 1
        return True

    def check_block_constraints(self, block: Block):
        # Check message length constraint
        if any(len(message) > 20 for message in block.get_messages()):
            return False

        # Check maximum messages per block constraint
        if len(block.get_messages()) > 10:
            return False

        # Check nonce length constraint
        if len(block.get_nonce()) > 40:
            return False

        # Check difficulty constraint
        if not self.check_difficulty(block.get_hash(), block.get_difficulty()):
            return False

        return True

    def check_difficulty(self, hash_value, difficulty):
        # Implement difficulty check logic (e.g., check if the hash starts with 'difficulty' number of leading zeros)
        # This is a simplified example; you may need to adjust it based on your hashing algorithm
        return hash[-1 * self.difficulty:] == '0' * difficulty
    
    def selfConsensus(self):
        return self.validate_chain(self.chain)


    def validate_chain(self, chain):
        # Validate the entire chain
        for i in range(1, len(chain)):
            if not chain[i].selfVerify(chain[i - 1]):
                return False
        return True
    
    def doConsensus(self, other_chains):
        # Compare chains and replace if a longer valid chain is found
        for other_chain in other_chains:
            if len(other_chain) > len(self.chain) and self.validate_chain(other_chain):
                self.chain = other_chain
                self.height = len(other_chain)
                return True

        return False

    def returnBlock(self, height):
        noneBlock = GetBlockReply(
                protocol=Protocol(protocol_type="GET_BLOCK_REPLY"),
                hash=None,
                height=None,
                messages=None,
                minedBy=None,
                nonce=None,
                timestamp=None
            )
        
        if (height > self.height or height < 0):
            return noneBlock
        
        print(f"height: {height}. self.height: {self.height}")

        requestBlock = self.chain[height]
        try:
            getBlock_reply = GetBlockReply(
                type=Protocol(protocol_type="GET_BLOCK_REPLY"),
                hash=requestBlock.get_hash(),
                height=requestBlock.get_height(),
                messages=requestBlock.get_messages(),
                minedBy=requestBlock.get_miner_name(),
                nonce=requestBlock.get_nonce(),
                timestamp=requestBlock.get_timestamp()
            )

            #safety checks
            if (getBlock_reply.protocol.protocol_type != "GET_BLOCK_REPLY" or
                    getBlock_reply.hash in ["None", "null"] or
                    not getBlock_reply.messages or
                    getBlock_reply.nonce in ["NONE", "null"] or
                    getBlock_reply.minedBy in ["None", "null"]):
                print("invalid GET_BLOCK_REPLY")
                return noneBlock
        except Exception as e:
            print(f"Error handling GET_BLOCK_REPLY: {e}")

        return getBlock_reply
    
    def addWord(self, word):
        if(self.height != 0):
            self.chain[self.height-1].addWord(word) 

    def get_height(self):
        return self.height
    
    def get_lastHash(self):
        if(self.height == 0):
            return ""
        return self.chain[self.height-1].get_hash()