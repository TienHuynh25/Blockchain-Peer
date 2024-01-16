import queue
import socket
import json
import threading
import time
from uuid import uuid4
from protocol import *
from typing import List
from threading import Lock
from Block import *

class PeerContact:
    def __init__(self, host, port, name, last_ping):
        self.host = host
        self.port = port
        self.name = name
        self.last_ping = last_ping
    
    def to_dict(self):
        return {
            'host': self.host,
            'port': self.port,
            'name': self.name,
            'last_ping': self.last_ping
        }

    def __eq__(self, other):
        if isinstance(other, PeerContact):
            return self.host == other.host and self.port == other.port
        return False
    
    def getHost(self):
        return self.host
    def getPort(self):
        return self.port
    

class BlockchainPeer:
    GOSSIP_REPEAT_LIMIT = 3
    DIFFICULTY=8

    def __init__(self, host, port, peer_id, name, known_host, known_port):
        self.host = host
        self.port = port
        self.peer_id = peer_id
        self.name = name
        self.known_host = known_host
        self.known_port = known_port
        self.peers: List[PeerContact] = []
        self.blockchain = Blockchain()
        self.keepalive_interval = 30  # seconds
        self.last_flood_time = time.time()
        self.mutex = threading.Lock()  # Mutex to protect shared data
        self.received_message_ids = []  # List to store received message IDs
        self.receive_queue = queue.Queue()
        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.keepalive_thread = threading.Thread(target=self.keep_alive, daemon=True)
        #self.stats_thread = threading.Thread(target=self.send_stats_periodically, daemon=True)



    ##### UDP
    def start_udp_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            server_socket.bind((self.host, self.port))
            print(f"UDP Server started on {self.host}:{self.port}")
        except Exception as e:
            print(f"Error binding the server socket: {e}")
            return
        
        # Set the timeout for the server socket
        server_socket.settimeout(120)  # timeout
        self.receive_thread.start()

        while True:
            try:
                data, addr = server_socket.recvfrom(1024)
                message = json.loads(data.decode('utf-8'))
                # Extract host and port from addr
                sender_host, sender_port = addr
                print(f"Received message: {message}")

                # Put the received message into the queue
                self.receive_queue.put((message, sender_host, sender_port))

            except socket.timeout:
                print("Socket timeout. No data received within the timeout period.")
            except Exception as e:
                print(f"Error while handling incoming data: {e}")

    def receive_messages(self):
        while True:
            try:
                message, sender_host, sender_port = self.receive_queue.get()
                    # Process the received message
                print(f"Received message: {message}")
                if 'type' in message:
                    if message['type'] == 'GOSSIP':
                        self.handle_flood(message)
                    elif message['type'] == 'GOSSIP_REPLY':
                        self.handle_flood_reply(message)
                    elif message['type'] == 'STATS':
                        self.handle_stats_reply(sender_host, sender_port)
                    elif message['type'] == 'STATS_REPLY':
                        self.handle_stats(message, sender_host, sender_port)
                    elif message['type'] == 'GET_BLOCK':
                        self.handle_get_block_reply(message.get('height'), sender_host, sender_port)
                    elif message['type'] == 'GET_BLOCK_REPLY':
                        self.handle_get_block(message, sender_host, sender_port)
                    elif message['type'] == 'NEW_WORD':
                        self.handle_add(message.get('word'))
                    elif message['type'] == 'CONSENSUS':
                        self.handle_consensus()

            except Exception as e:
                print(f"Error while processing received message:{message}")

    def send_udp_message(self, message, host, port):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            client_socket.sendto(json.dumps(message, default=lambda o: o.to_dict()).encode(), (host, port))
            print(f"Sent message to {host}:{port}")
        except Exception as e:
            print(f"Error while sending UDP message: {e}")
    
    #####FLOOD
    def flood(self):
        # Send a FLOOD message to the well-known host
        flood_request = new_flood_request(self.host, self.port, self.name)
        print(f"Send a FLOOD message to the well-known host")
        self.send_udp_message(flood_request, self.known_host, self.known_port)

        # Repeat the message to 3 tracked peers
        for peer in self.peers[:min(self.GOSSIP_REPEAT_LIMIT, len(self.peers))]:
            self.send_udp_message(flood_request, peer.getHost(), peer.getPort())
    
    def handle_flood(self, message):
            message_id = message['id']
            print(f"Received FLOOD from {message['id']} at {message['host']}:{message['port']}")
            # Check if this is a new flood message
            # Check if this message ID is already received
            if message_id not in self.received_message_ids:
                #print(f"\nForward FLOOD from {message['id']} at {message['host']}:{message['port']}")
                self.received_message_ids.append(message_id)
                # Reply to the originator
                flood_reply = new_flood_reply(self.host, self.port, self.name)
                self.send_udp_message(flood_reply, message['host'], message['port'])
            ## Add peer to peer list
            new_peer = PeerContact(message['host'],message['port'],message['name'], time.time())
            if not any(new_peer == peer for peer in self.peers):
                print(f"Adding new peer {new_peer.getHost()}:{new_peer.getPort()}")
                self.peers.append(new_peer)
            # Repeat the message to 3 tracked peers
            flood_request = new_flood_request(message['host'],message['port'], message['name'])
            for peer in self.peers[:min(self.GOSSIP_REPEAT_LIMIT, len(self.peers))]:
                self.send_udp_message(flood_request, peer.getHost(), peer.getPort())

    def handle_flood_reply(self, message):
            message_id = message['id']
            print(f"Received FLOOD_REPLY from {message['id']} at {message['host']}:{message['port']}")
            # Check if this is a new flood message
            # Check if this message ID is already received
            if message_id not in self.received_message_ids:
                print("\nNew Message")
                self.received_message_ids.append(message_id)
                # Reply to the originator
                flood_reply = new_flood_reply(self.host, self.port, self.name)
                self.send_udp_message(flood_reply, message['host'], message['port'])
            ## Add peer to peer list
            new_peer = PeerContact(message['host'],message['port'],message['name'], time.time())
            if not any(new_peer == peer for peer in self.peers):
                print(f"Adding new peer {new_peer.getHost()}:{new_peer.getPort()}")
                self.peers.append(new_peer)

    def keep_alive(self):
        while True:
            with self.mutex:
                self.flood()
                self.last_flood_time = time.time()
            time.sleep(self.keepalive_interval)


    #### STAT 
    def send_stats_request(self, sender_host, sender_port):
        stats_request = StatsRequest(protocol=Protocol(protocol_type="STATS"))
        print(f"Send STATS to {sender_host}:{sender_port}")
        try:
            self.send_udp_message(stats_request, sender_host, sender_port)
        except socket.timeout:
                print(f"Socket timeout in send_stats_request")
        except Exception as e:
                print(f"Error: {e}")

    def handle_stats(self, message, sender_host, sender_port):
        try:
            print(f"Received STATS_REPLY from {sender_host}:{sender_port}, height:{message['height']}, hash:{message['hash']}")
            if(self.blockchain.get_height() == message['height'] and self.blockchain.get_lastHash != message['hash']):
                self.send_consensus_request(host, port)
            if(self.blockchain.get_height() < message['height']):
                self.send_get_block_requests(sender_host, sender_port, message['height'])
        except Exception as e:
            print(f"Error in handle_stats: {e}")
    
    def handle_stats_reply(self, sender_host, sender_port):
            print(f"Received STATS from {sender_host}:{sender_port}")
            stat_reply = StatsReply(protocol=Protocol(protocol_type="STATS_REPLY"), height=str(self.blockchain.get_height()), hash=str(self.blockchain.get_lastHash()))
            try:
                self.send_udp_message(stat_reply, sender_host, sender_port)
            except socket.timeout:
                print(f"Socket timeout in handle_stats_reply")
                pass
            except Exception as e:
                print(f"Error: {e}")

    #GET_BLOCK
    def send_get_block_request(self, height: int, sender_host, sender_port):
        getBlock_request = GetBlockRequest(protocol=Protocol(protocol_type="GET_BLOCK"), height=height)
        try:
            self.send_udp_message(getBlock_request, sender_host, sender_port)
        except socket.timeout:
            print(f"Socket timeout in send_getBlock_request")
            pass
        except Exception as e:
            print(f"Error: {e}")
    
    def send_get_block_requests(self, sender_host, sender_port, target_height):
        for height in range(target_height + 1):
            # Send GET_BLOCK request
            self.send_get_block_request(target_height, sender_host, sender_port)

    def handle_get_block_reply(self, height,sender_host, sender_port):
            print(f"Handling GET_BLOCK request from {sender_host}:{sender_port}")
            getBlockReply = self.blockchain.returnBlock(height)
            try:
                self.send_udp_message(getBlockReply, sender_host, sender_port)
            except socket.timeout:
                print(f"Socket timeout in handle_stats_reply")
                pass
            except Exception as e:
                print(f"Error: {e}")
        
    def handle_get_block(self, message, sender_host, sender_port):
        try:
            print(f"Received GET_BLOCK_REPLY for height {message['height']}: {message}")
            block = Block(miner_name=message['minedBy'],messages=message['messages'], 
                                  nonce= message['nonce'], timestamp=message['timestamp'], height=message['height'], difficulty=self.DIFFICULTY, hash=message['hash'])

            successful = self.blockchain.add_block(block)
            if not (successful):
                self.send_get_block_request(message['height'], sender_host, sender_port)
        except Exception as e:
            print(f"Error in handle_get_block: {e}")
        
    #Consensus
    def send_consensus_request(self):
        # Send consensus request to known peers
        for peer in self.peers:
            threading.Thread(target=self.send_consensus_request_thread, args=(peer,)).start()
    
    def send_consensus_request_(self, host, port):
        threading.Thread(target=self.send_consensus_request_thread, args=(host, port,)).start()

    def send_consensus_request_thread(self, peer):
        consensus_request = ConsensusRequest(protocol=Protocol(protocol_type="CONSENSUS_REQUEST"))
        try:
            self.send_udp_message(consensus_request, peer.getHost(), peer.getPort())
        except socket.timeout:
            print("Socket timeout in send_consensus_request_thread")
        except Exception as e:
            print(f"Error: {e}")
    
    def send_consensus_request_thread_(self, host, port):
        consensus_request = ConsensusRequest(protocol=Protocol(protocol_type="CONSENSUS_REQUEST"))
        try:
            self.send_udp_message(consensus_request, host, port)
        except socket.timeout:
            print("Socket timeout in send_consensus_request_thread")
        except Exception as e:
            print(f"Error: {e}") 
    
    def handle_consensus(self):
            print("Doing consensus")
            self.blockchain.selfConsensus()
    
    #ADD
    def handle_add(self, word):
        self.blockchain.addWord(word)

    def send_stats_periodically(self):
        while True:
            for peer in self.peers:
                print(f"peer to send stats request: {peer.getHost()}:{peer.getPort()}")
                self.send_stats_request(peer.getHost(), peer.getPort())
        time.sleep(30)


if __name__ == "__main__":
    host = socket.gethostbyname(socket.gethostname())
    port = 8000
    peer_id = str(uuid4())
    name = "Tien Huynh"
    known_host = "130.179.28.37"
    known_port = 8999

    blockchain_peer = BlockchainPeer(host, port, peer_id, name, known_host, known_port)
    blockchain_peer.keepalive_thread.start()

    # Start the UDP server in a separate thread
    send_stats_thread = threading.Thread(target=blockchain_peer.send_stats_periodically)
    send_stats_thread.start()

    # Start the UDP server in a separate thread
    server_thread = threading.Thread(target=blockchain_peer.start_udp_server)
    server_thread.start()

    # Main thread waits for all threads to finish
    blockchain_peer.keepalive_thread.join()
    # blockchain_peer.stats_thread.join()
    server_thread.join()
    #blockchain_peer.stats_thread.start()
