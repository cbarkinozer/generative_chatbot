"""Assistant's memory features."""

from collections import deque

class Memory:
    def __init__(self):
        self.memory_deque = deque(maxlen=5)

    def save(self, question, answer) -> None:
        """Saves to a deque and keeps the element count less than 5."""
        concatenated_memory = ''.join(self.memory_deque)
        if len(self.memory_deque) >= 5 or (len(concatenated_memory) + len(question)) > 1000:
            self.memory_deque.popleft()      
        self.memory_deque.append(f"<Previous Question>: {question} <Previous Answer>: {answer}")
    
    def get_last_answer(self) -> str:
        """Calls the last speaking turn."""
        # Return the last answer given by the bot from the chat history.
        if self.memory_deque:
            last_entry = self.memory_deque[-1]
            # Extract the last answer from the stored format
            start = last_entry.find('<previous_answer>') + len('<previous_answer>')
            end = last_entry.find('</previous_answer>')
            return last_entry[start:end]
        return ""
    
    def get_memory(self) -> str:
        """Remembers the all previous turns."""
        concatenated_memory = "Chat history: <chat_history>" + ''.join(self.memory_deque) + "</chat_history>"
        return concatenated_memory
    
    def clear(self) -> None:
        """Cleans mind."""
        self.memory_deque.clear()