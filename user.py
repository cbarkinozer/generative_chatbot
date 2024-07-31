from memory import Memory

class User:
    def __init__(self, username):
        self.username = username
        self.llm = "llama3" #gemini-pro
        self.embedder = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.memory = Memory()