import abc

ACTION_REGISTRY = {}


def register_action_class(action_class):
    ACTION_REGISTRY[action_class.name()] = action_class


def get_action_class(name):
    return ACTION_REGISTRY[name]


class Action(metaclass=abc.ABCMeta):
    @staticmethod
    @abc.abstractmethod
    def name():
        pass

    @staticmethod
    @abc.abstractmethod
    def make_from_yaml_node(yaml_node, target_reference):
        pass

    @abc.abstractmethod
    def adapter(self):
        pass

    @abc.abstractmethod
    def command_line_arguments(self):
        pass

    @abc.abstractmethod
    def environment_variables(self):
        pass

    @abc.abstractmethod
    def substitutions(self, existing_substitutions):
        pass
