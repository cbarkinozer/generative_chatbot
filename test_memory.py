import unittest
from memory import Memory

class TestMemory(unittest.TestCase):

    def setUp(self):
        """Set up a Memory instance for testing."""
        self.memory = Memory()

    def test_save_single_entry(self):
        """Test that a single question-answer pair is saved correctly."""
        self.memory.save("What is your name?", "I am an assistant.")
        expected_entry = "<Previous Question>: What is your name? <Previous Answer>: I am an assistant."
        self.assertEqual(list(self.memory.memory_deque), [expected_entry])

    def test_save_multiple_entries_within_limit(self):
        """Test saving multiple entries within the 5-entry limit."""
        for i in range(3):
            question = f"Question {i}"
            answer = f"Answer {i}"
            self.memory.save(question, answer)
        expected_memory = [
            "<Previous Question>: Question 0 <Previous Answer>: Answer 0",
            "<Previous Question>: Question 1 <Previous Answer>: Answer 1",
            "<Previous Question>: Question 2 <Previous Answer>: Answer 2",
        ]
        self.assertEqual(list(self.memory.memory_deque), expected_memory)

    def test_memory_overflow(self):
        """Test that the memory deque drops the oldest entry when more than 5 entries are added."""
        for i in range(6):  # Add 6 entries, which exceeds the deque limit of 5
            question = f"Question {i}"
            answer = f"Answer {i}"
            self.memory.save(question, answer)
        
        # Oldest entry should be dropped, and deque should have entries from Question 1 to Question 5
        expected_memory = [
            "<Previous Question>: Question 1 <Previous Answer>: Answer 1",
            "<Previous Question>: Question 2 <Previous Answer>: Answer 2",
            "<Previous Question>: Question 3 <Previous Answer>: Answer 3",
            "<Previous Question>: Question 4 <Previous Answer>: Answer 4",
            "<Previous Question>: Question 5 <Previous Answer>: Answer 5",
        ]
        self.assertEqual(list(self.memory.memory_deque), expected_memory)

    def test_save_large_question(self):
        """Test that a large question triggers the memory to drop old entries."""
        # Fill deque
        for i in range(5):
            question = f"Question {i}"
            answer = f"Answer {i}"
            self.memory.save(question, answer)
        
        large_question = "Q" * 1000
        self.memory.save(large_question, "Answer large")

        # Ensure that the deque starts to drop old entries to maintain size constraint
        self.assertEqual(len(self.memory.memory_deque), 5)

    def test_get_last_answer(self):
        """Test retrieving the last answer."""
        self.memory.save("Question 1", "Answer 1")
        self.memory.save("Question 2", "Answer 2")

        last_answer = self.memory.get_last_answer()
        self.assertEqual(last_answer, "Answer 2")


    def test_get_last_answer_empty(self):
        """Test that get_last_answer returns an empty string if memory is empty."""
        last_answer = self.memory.get_last_answer()
        self.assertEqual(last_answer, "")

    def test_get_memory(self):
        """Test that get_memory returns the full chat history."""
        self.memory.save("What is your name?", "I am an assistant.")
        self.memory.save("How are you?", "I am doing well.")
        expected_memory = (
            "Chat history: <chat_history>"
            "<Previous Question>: What is your name? <Previous Answer>: I am an assistant."
            "<Previous Question>: How are you? <Previous Answer>: I am doing well."
            "</chat_history>"
        )
        self.assertEqual(self.memory.get_memory(), expected_memory)

    def test_clear_memory(self):
        """Test that the memory is cleared."""
        self.memory.save("What is your name?", "I am an assistant.")
        self.memory.clear()
        self.assertEqual(len(self.memory.memory_deque), 0)

if __name__ == '__main__':
    unittest.main()
