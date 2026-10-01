from abc import ABC, abstractmethod
import pandas as pd

class DataSource(ABC):
    @abstractmethod
    def fetch(self, spec: dict) -> pd.DataFrame:
        """Return columns observation_date, value."""
        raise NotImplementedError
