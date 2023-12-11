""" Module with genetic optimization settings
    that reproduces behavior of default GOLEM
    genetic optimization """
from collections import defaultdict
from itertools import chain

from golem.core.optimisers.common_optimizer.nodes.evaluator import Evaluator
from golem.core.optimisers.common_optimizer.nodes.old_crossover import Crossover, CrossoverTask
from golem.core.optimisers.common_optimizer.nodes.old_elitism import Elitism, ElitismTask
from golem.core.optimisers.common_optimizer.nodes.old_inheritance import Inheritance, InheritanceTask
from golem.core.optimisers.common_optimizer.nodes.old_mutation import Mutation, MutationTask
from golem.core.optimisers.common_optimizer.nodes.old_regularization import Regularization, RegularizationTask
from golem.core.optimisers.common_optimizer.nodes.old_selection import Selection, SelectionTask
from golem.core.optimisers.common_optimizer.runner import ParallelRunner, OneThreadRunner
from golem.core.optimisers.common_optimizer.scheme import Scheme, SequentialScheme
from golem.core.optimisers.common_optimizer.stage import Stage
from golem.core.optimisers.common_optimizer.task import Task, TaskStatusEnum
from golem.core.optimisers.common_optimizer.temp.adaptive import AdaptivePopulationSize, AdaptiveParametersTask

default_stages = list()


# adaptive parameters
nodes = [AdaptivePopulationSize()]
scheme = SequentialScheme(nodes=nodes)
def adaptive_parameter_updater(finished_tasks, parameters):
    parameters = finished_tasks[0].update_parameters(parameters)
    return parameters

default_stages.append(Stage(runner=OneThreadRunner(), nodes=nodes, task_builder=AdaptiveParametersTask,
                            scheme=scheme, stop_fun=lambda f, a: bool(f),
                            parameter_updater=adaptive_parameter_updater))

# main evolution process
class EvolvePopulationTask(ElitismTask, MutationTask,
                           CrossoverTask, RegularizationTask,
                           SelectionTask, InheritanceTask, Task):
    def update_parameters(self, parameters: 'CommonOptimizerParameters'):
        parameters = super().update_parameters(parameters)
        return parameters

scheme_map = dict()
scheme_map[None] = defaultdict(lambda: 'regularization')
scheme_map['regularization'] = defaultdict(lambda: 'selection')
scheme_map['selection'] = defaultdict(lambda: 'crossover')
scheme_map['crossover'] = defaultdict(lambda: 'mutation')
scheme_map['mutation'] = {TaskStatusEnum.SUCCESS: 'evaluator', TaskStatusEnum.FAIL: None}
scheme_map['evaluator'] = defaultdict(lambda: None)
scheme = Scheme(scheme_map=scheme_map)

nodes = [Elitism(), Mutation(), Crossover(), Regularization(),
         Selection(), Inheritance(), Evaluator()]

def stop_fun(finished_tasks, all_tasks):
    if all_tasks:
        pop_size = all_tasks[0].graph_generation_params.pop_size
        if len(finished_tasks) >= pop_size:
            return True
    return False



def parameter_updater(finished_tasks, parameters):
    parameters.new_population = list(chain(*[task.generation for task in finished_tasks]))
    return parameters

runner = OneThreadRunner()
runner = ParallelRunner()
default_stages.append(Stage(runner=runner, nodes=nodes, task_builder=EvolvePopulationTask,
                            scheme=scheme, stop_fun=stop_fun, parameter_updater=parameter_updater))
