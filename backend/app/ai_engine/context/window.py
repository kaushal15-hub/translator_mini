from collections import deque
class ContextWindow:
    def __init__(self, max_messages=4): self.items = deque(maxlen=max_messages)
    def add(self, role, text): self.items.append({"role": role, "text": text[:2000]})
    def prompt_context(self): return list(self.items)
