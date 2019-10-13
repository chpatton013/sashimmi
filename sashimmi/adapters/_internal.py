import abc


class Adapter(metaclass=abc.ABCMeta):
    def __init__(self):
        self.actions = []

    def adapt(self, action):
        self.actions.append(action)

    @abc.abstractmethod
    def command_line_arguments(self):
        pass

    @abc.abstractmethod
    def environment_variables(self):
        pass
