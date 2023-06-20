from random import shuffle

from golem.core.optimisers.genetic.operators.operator import PopulationT, Operator
from golem.core.utilities.data_structures import ComparableEnum as Enum


class ElitismTypesEnum(Enum):
    keep_n_best = 'keep_n_best'
    replace_worst = 'replace_worst'
    none = 'none'


class Elitism(Operator):
    def __call__(self, best_individuals: PopulationT, new_population: PopulationT) -> PopulationT:
        elitism_type = self.parameters.elitism_type
        if elitism_type is ElitismTypesEnum.none or not self._is_elitism_applicable():
            return new_population
        elif elitism_type is ElitismTypesEnum.keep_n_best:
            return self.keep_n_best_elitism(best_individuals, new_population)
        elif elitism_type is ElitismTypesEnum.replace_worst:
            return self.replace_worst_elitism(best_individuals, new_population)
        else:
            raise ValueError(f'Required elitism type not found: {elitism_type}')

    def _is_elitism_applicable(self) -> bool:
        if self.parameters.multi_objective:
            return False
        return self.parameters.pop_size >= self.parameters.min_pop_size_with_elitism

    @staticmethod
    def keep_n_best_elitism(best_individuals: PopulationT, new_population: PopulationT) -> PopulationT:
        shuffle(new_population)
        new_population[:len(best_individuals)] = best_individuals
        return new_population

    @staticmethod
    def replace_worst_elitism(best_individuals: PopulationT, new_population: PopulationT) -> PopulationT:
        population = best_individuals + new_population
        # sort in descending order (Fitness(10) > Fitness(11))
        sorted_ascending_population = sorted(population, key=lambda individual: individual.fitness, reverse=True)
        return sorted_ascending_population[:len(new_population)]
