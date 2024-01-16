import json
from typing import List
from uuid import uuid4


class Protocol:
    def __init__(self, protocol_type: str):
        self.protocol_type = protocol_type
    
    def to_dict(self):
        return self.protocol_type


class Flood:
    def __init__(self, host: str, port: int, name: str, protocol: Protocol):
        self.host = host
        self.port = port
        self.name = name
        self.protocol = protocol
        
    def to_dict(self):
        return {
            'host': self.host,
            'port': self.port,
            'name': self.name,
            'type': self.protocol.to_dict(),
        }


class FloodRequest:
    def __init__(self, id: str, flood: Flood):
        self.id = id
        self.flood = flood
    
    def to_dict(self):
        result = {'id': self.id}
        result.update(self.flood.to_dict())
        return result


class FloodReply:
    def __init__(self, flood: Flood):
        self.flood = flood
    
    def to_dict(self):
        return self.flood.to_dict()


def new_flood_reply(host: str, port: str, name: str) -> FloodReply:
    return FloodReply(flood=Flood(host=host, port=int(port), name=name, protocol=Protocol(protocol_type="GOSSIP_REPLY")))


def new_flood_request(host: str, port: str, name: str) -> FloodRequest:
    return FloodRequest(id=str(uuid4()), flood=Flood(host=host, port=int(port), name=name, protocol=Protocol(protocol_type="GOSSIP")))


class StatsRequest:
    protocol: Protocol
    def __init__(self, protocol) -> None:
        self.protocol = protocol
    
    def to_dict(self):
        return {'type': self.protocol.to_dict()}


class StatsReply:
    def __init__(self, protocol: Protocol, height: int, hash: str):
        self.protocol = protocol
        self.height = height
        self.hash = hash
    
    def to_dict(self):
        return {'type': self.protocol.to_dict(), 'height': self.height, 'hash': self.hash}


class GetBlockRequest:
    def __init__(self, protocol: Protocol, height: int):
        self.protocol = protocol
        self.height = height
    
    def to_dict(self):
        return {'type': self.protocol.to_dict(), 'height': self.height}


class GetBlockReply:
    def __init__(self, protocol: Protocol, height: int, minedBy: str, nonce: str, messages: List[str], hash: str, timestamp: str):
        self.protocol = protocol
        self.height = height
        self.minedBy = minedBy
        self.nonce = nonce
        self.messages = messages
        self.hash = hash
        self.timestamp = timestamp
    
    def to_dict(self):
        return {
            'type': self.protocol.to_dict(),
            'height': self.height,
            'minedBy': self.minedBy,
            'nonce': self.nonce,
            'messages': self.messages,
            'hash': self.hash,
            'timestamp': self.timestamp
        }


class ConsensusRequest:
    def __init__(self, protocol: Protocol):
        self.protocol = protocol
    
    def to_dict(self):
        return {'type': self.protocol.to_dict()}


class AnnounceMessage:
    def __init__(self, protocol: Protocol, height: int, minedBy: str, nonce: str, messages: List[str], hash: str):
        self.protocol = protocol
        self.height = height
        self.minedBy = minedBy
        self.nonce = nonce
        self.messages = messages
        self.hash = hash
    
    def to_dict(self):
        return {
            'type': self.protocol.to_dict(),
            'height': self.height,
            'minedBy': self.minedBy,
            'nonce': self.nonce,
            'messages': self.messages,
            'hash': self.hash,
        }


class NewWordRequest:
    def __init__(self, protocol: Protocol, word: str):
        self.protocol = protocol
        self.word = word
    
    def to_dict(self):
        return {'type': self.protocol.to_dict(), 'word': self.word}
