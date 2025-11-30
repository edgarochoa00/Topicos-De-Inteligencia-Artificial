import random
import numpy as np
from typing import List


class LocalSearchOperators:
    """Operadores de búsqueda local"""

    @staticmethod
    def two_opt(inner_route: List[int]) -> List[int]:
        if len(inner_route) < 2:
            return inner_route[:]
        i, j = sorted(np.random.choice(len(inner_route), 2, replace=False))
        return inner_route[:i] + list(reversed(inner_route[i:j + 1])) + inner_route[j + 1:]

    @staticmethod
    def swap_two(inner_route: List[int]) -> List[int]:
        if len(inner_route) < 2:
            return inner_route[:]
        new_route = inner_route[:]
        i, j = np.random.choice(len(inner_route), 2, replace=False)
        new_route[i], new_route[j] = new_route[j], new_route[i]
        return new_route

    @staticmethod
    def relocate_one(inner_route: List[int]) -> List[int]:
        if len(inner_route) < 2:
            return inner_route[:]
        new_route = inner_route[:]
        i, j = np.random.choice(len(inner_route), 2, replace=False)
        node = new_route.pop(i)
        new_route.insert(j, node)
        return new_route

    @staticmethod
    def get_random_operator():
        operators = [
            LocalSearchOperators.two_opt,
            LocalSearchOperators.swap_two,
            LocalSearchOperators.relocate_one
        ]
        return random.choice(operators)
