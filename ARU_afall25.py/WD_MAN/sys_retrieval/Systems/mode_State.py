
class modeState:
    def __init__(self):
        self.mode = False  # False = mode Manual, True = mode AI

    def set_mode(self, value: bool):
        self.mode = value

    def toggle(self):
        self.mode = not self.mode