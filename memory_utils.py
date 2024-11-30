from typing import Dict, Optional,List
from langchain.memory import ConversationBufferMemory
import json
from doc_process_utils import os



class UserChatMemoryManager:
    def __init__(self, user_id: str, memory_dir: str = "user_memories"):
        """
        Initialize a memory manager for a specific user
        
        Args:
            user_id (str): Unique identifier for the user
            memory_dir (str, optional): Directory to store memory files
        """
        self.user_id = user_id
        self.memory_dir = memory_dir
        self.memories: Dict[str, ConversationBufferMemory] = {}
        
        # Ensure memory directory exists
        os.makedirs(self.memory_dir, exist_ok=True)
    
    def _get_memory_file_path(self, chatbot_id: str) -> str:
        """
        Generate a file path for a specific chatbot's memory
        
        Args:
            chatbot_id (str): Unique identifier for the chatbot
        
        Returns:
            str: Full path to the memory file
        """
        return os.path.join(self.memory_dir, f"{self.user_id}_{chatbot_id}_memory.json")
    
    def get_or_create_memory(self, chatbot_id: str) -> ConversationBufferMemory:
        """
        Retrieve or create a memory for a specific chatbot
        
        Args:
            chatbot_id (str): Unique identifier for the chatbot
        
        Returns:
            ConversationBufferMemory: Memory object for the chatbot
        """
        # Check if memory is already loaded
        if chatbot_id in self.memories:
            return self.memories[chatbot_id]
        
        # Create a new memory object
        memory = ConversationBufferMemory(
                        memory_key="chat_history",  # Set a specific memory key
                        return_messages=True    # Return full message objects
                    )
        
        # Try to load existing memory from file
        memory_file = self._get_memory_file_path(chatbot_id)
        if os.path.exists(memory_file):
            try:
                with open(memory_file, 'r') as f:
                    memory_data = json.load(f)
                    memory.chat_memory.messages = memory_data.get('messages', [])
            except Exception as e:
                print(f"Error loading memory for chatbot {chatbot_id}: {e}")
        
        # Store in memory dictionary
        self.memories[chatbot_id] = memory
        return memory
    
    def save_memory(self, chatbot_id: str):
        """
        Save memory for a specific chatbot to a file
        
        Args:
            chatbot_id (str): Unique identifier for the chatbot
        """
        if chatbot_id not in self.memories:
            return
        
        memory = self.memories[chatbot_id]
        memory_file = self._get_memory_file_path(chatbot_id)
        
        try:
            with open(memory_file, 'w') as f:
                json.dump({
                    'messages': memory.chat_memory.messages
                }, f, default=lambda x: str(x))
        except Exception as e:
            print(f"Error saving memory for chatbot {chatbot_id}: {e}")
    
    def save_all_memories(self):
        """
        Save memories for all loaded chatbots
        """
        for chatbot_id in self.memories:
            self.save_memory(chatbot_id)
    
    def clear_memory(self, chatbot_id: str):
        """
        Clear memory for a specific chatbot
        
        Args:
            chatbot_id (str): Unique identifier for the chatbot
        """
        if chatbot_id in self.memories:
            del self.memories[chatbot_id]
        
        # Remove memory file
        memory_file = self._get_memory_file_path(chatbot_id)
        if os.path.exists(memory_file):
            os.remove(memory_file)
    
    def clear_all_memories(self):
        """
        Clear all memories for the user
        """
        # Remove all memory files
        for filename in os.listdir(self.memory_dir):
            if filename.startswith(f"{self.user_id}_"):
                os.remove(os.path.join(self.memory_dir, filename))
        
        # Clear memory dictionary
        self.memories.clear()

# Example usage in a FastAPI endpoint
class ChatbotMemoryManager:
    def __init__(self):
        self.user_memory_managers: Dict[str, UserChatMemoryManager] = {}
    
    def get_user_memory_manager(self, user_id: str) -> UserChatMemoryManager:
        """
        Get or create a memory manager for a specific user
        
        Args:
            user_id (str): Unique identifier for the user
        
        Returns:
            UserChatMemoryManager: Memory manager for the user
        """
        if user_id not in self.user_memory_managers:
            self.user_memory_managers[user_id] = UserChatMemoryManager(user_id)
        return self.user_memory_managers[user_id]
    
    def get_chatbot_memory(self, user_id: str, chatbot_id: str):
        """
        Get memory for a specific chatbot
        
        Args:
            user_id (str): Unique identifier for the user
            chatbot_id (str): Unique identifier for the chatbot
        
        Returns:
            ConversationBufferMemory: Memory for the specific chatbot
        """
        user_memory_manager = self.get_user_memory_manager(user_id)
        return user_memory_manager.get_or_create_memory(chatbot_id)
