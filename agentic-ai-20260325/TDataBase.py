from abc import ABC, abstractmethod


class TDataBase(ABC):
    """
    Base Class
    """

    def __init__(self, agent_id: str) -> None:
        """
        Constructor
        """
        self.agent_id = agent_id

    @abstractmethod
    def _execute_method(self):
        """
        The only method that should be overridden
        1. TAKE input
        2. PERFORM work
        3. RETURN output
        """
        pass

    def run(self):
        """
        Public API
        4. CALLS the business logic
        5.
        6. Returns the output as JSON

        """
        result = {}
        return result
