# Blockchain Peer  
  
### Introduction    
   
This readme provides information on a Blockchain Peer Project. The peer is capable of storing messages in blocks, implementing UDP communication, synchronization, consensus, messaging strategies, and state handling.  
  
### Getting Started    
    
To start the Blockchain peer, follow these steps:  
  
Clone the repository to your local machine.  
Navigate to the project directory.  
Run the peer with the following command: python blockchain_peer.py  
Command Line Arguments  
  
--host: Specify the host IP address for the peer.  
--port: Specify the port number for communication.  
Additional arguments for mining, consensus intervals, or other optional features.  

  
**Synchronization**  
  
The synchronization process may take a few minutes, depending on the network and block height. Upon synchronization, you will see log messages indicating the progress, and the peer will display the current status on the web server at http://localhost:8998/.  
  
**Consensus Code**  
  
The consensus code can be found in the file consensus.py. It operates by comparing chain lengths and hashes among peers, choosing the longest chain with the most agreement. Refer to the consensus.py file, line 42-56, for implementation details.  
  
**Peer Cleanup**     
  
To clean up peers that have not been heard from in a minute, refer to the file peer_cleanup.py. The cleanup logic can be found in the function cleanup_peers, starting at line 23.  
  
**Mining**   
   
Mining functionality has been added to the Blockchain peer. The mining code is in the file mining.py. It uses a basic mining algorithm to find a nonce that satisfies the difficulty requirement. You can adjust mining parameters in the file, and mining results will be displayed on the console.  
  
### Protocol  
  
The peer follows a specific protocol for communication.
  
GOSSIP  
The id can be any string. The uuid library can be useful. Or, consider using random.  
  
{  
   "type": "GOSSIP",  
   "host": "192.168.0.27",  
   "port": 8999,  
   "id": "5b29f4c7-40ac-4522-b217-e90e9587c1e5",  
   "name": "Some name here!"  
}  
Reply with your info to the originator, not the sender (may be the same, but may be different if you are received a forward of the original message)  
  
{  
   "type": "GOSSIP_REPLY",  
   "host": "192.168.0.28",  
   "port": 8001,  
   "name": "I have a name, too"  
}  

GET_BLOCK  
Requests a single block from a peer. Peer returns the contents of that block.  
  
{  
   "type": "GET_BLOCK",  
   "height": 0  
}  
Which replies with a GET_BLOCK_REPLY:  
  
{   'type': 'GET_BLOCK_REPLY'  
    'hash': '2483cc5c0d2fdbeeba3c942bde825270f345b2e9cd28f22d12ba347300000000',  
    'height': 0,  
    'messages': [   '3010 rocks',  
                    'Warning:',  
                    'Procrastinators',  
                    'will be sent back',  
                    'in time to start',  
                    'early.'],  
    'minedBy': 'Prof!',  
    'nonce': '7965175207940',  
    'timestamp': 1699293749,  
   }  
If given GET_BLOCK for an invalid height, return with GET_BLOCK_REPLY with null/None height, message, nonce, and minedBy.  
  
Test with  
echo '{"type":"GET_BLOCK", "height":0}' | nc -u 130.179.28.37 8999  

  
NEW_WORD    
Test sending new words with  

echo '{"type":"NEW_WORD", "word":"test"}' | nc -u [somehost] [someport]  
There is no reply. You only need to implement a handler for this for the bonus, if you are doing the bonus.  

ANNOUNCE      
Add a new block to the chain. You must handle receiving these messages appropriately. Verify the hash before adding to your chain.  
  
Sending these messages only required for bonus.  
  
{  
   "type": "ANNOUNCE",  
   "height": 3,  
   "minedBy": "Rob!",  
   "nonce": "27104978",  
   "messages": ["test123"],  
   "hash": "75fb3c14f11295fd22a42453834bc393872a78e4df1efa3da57a140d96000000"  
}  
There is no reply.  

STATS     
Get some statistics about the chain in this host.  
  
{  
   "type":"STATS"  
}  
/*  
reply with the height of your chain  
and the hash of the block at the maximum height  
*/  
{  
   "type": "STATS_REPLY",  
   "height": 2,  
   "hash": "519507660a0dd9d947e18b863a4a54b90eb53c82dde387e1f5e9b48f3d000000"   
}  
Can test with  
echo '{"type":"STATS"}' | nc -u [your host] [your port]    

CONSENSUS   
Force the peer to do a consensus immediately. If doing a consensus, can be ignored.  
  
{  
   "type": "CONSENSUS"  
}   
