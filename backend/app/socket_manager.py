from fastapi import WebSocket
from typing import List, Dict

class ConnectionManager:
    def __init__(self):
        # This dictionary will store a list of active connections for each room_id
        # Example: {"room_1": [socket_userA, socket_userB], "room_2": [socket_userC]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        # 1. Accept the incoming connection
        await websocket.accept()
        
        # 2. If the room doesn't exist in our dictionary yet, create an empty list for it
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
            
        # 3. Add this specific user's connection to that room's list
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        # Remove the user from the room's list when they leave
        if room_id in self.active_connections:
            # We use .remove() to take out this specific socket
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
            
            # (Optional) If the room is empty, we could delete the key to save memory
            # if len(self.active_connections[room_id]) == 0:
            #     del self.active_connections[room_id]

    async def broadcast(self, message: str, room_id: str):
        # Send a message to everyone in the specific room
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    # Sometimes a connection might look open but is actually dead.
                    # We print the error but don't crash the loop.
                    print(f"Error sending message: {e}")

# Create a single instance of the manager to use throughout the app
manager = ConnectionManager()