from datetime import timedelta
from functools import partial

from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

from examples.synthetic_graph_evolution.generators import generate_labeled_graph
from examples.synthetic_graph_evolution.utils import draw_graphs_subplots
from golem.core.adapter.nx_adapter import BaseNetworkxAdapter
from golem.core.dag.verification_rules import DEFAULT_DAG_RULES
from golem.core.optimisers.adaptive.rl.hyperparameter_env import HyperparameterEnv
from golem.core.optimisers.adaptive.rl.learn_agent import learn_agent
from golem.core.optimisers.genetic.gp_optimizer import EvoGraphOptimizer
from golem.core.optimisers.genetic.gp_params import GPAlgorithmParameters
from golem.core.optimisers.genetic.operators.base_mutations import MutationTypesEnum
from golem.core.optimisers.genetic.operators.crossover import CrossoverTypesEnum
from golem.core.optimisers.genetic.operators.inheritance import GeneticSchemeTypesEnum
from golem.core.optimisers.objective import Objective
from golem.core.optimisers.optimization_parameters import GraphRequirements
from golem.core.optimisers.optimizer import GraphGenerationParams
from golem.metrics.edit_distance import tree_edit_dist


def run_graph_search(size=16, timeout=0.5, visualize=True):
    # Generate target graph that will be sought by optimizer
    node_types = ('a', 'b')
    target_graph = generate_labeled_graph('tree', size, node_labels=node_types)

    # Generate initial population with small tree graphs
    initial_graphs = [generate_labeled_graph('tree', 5, node_types) for _ in range(10)]
    # Setup objective: edit distance to target graph
    objective = Objective(partial(tree_edit_dist, target_graph))

    # Setup optimization parameters
    requirements = GraphRequirements(
        early_stopping_iterations=100,
        timeout=timedelta(minutes=timeout),
        n_jobs=-1,
    )
    gp_params = GPAlgorithmParameters(
        genetic_scheme_type=GeneticSchemeTypesEnum.parameter_free,
        max_pop_size=50,
        mutation_types=[MutationTypesEnum.single_add,
                        MutationTypesEnum.single_drop,
                        MutationTypesEnum.single_change],
        crossover_types=[CrossoverTypesEnum.subtree]
    )
    adapter = BaseNetworkxAdapter()  # Example works with NetworkX graphs
    graph_gen_params = GraphGenerationParams(
        adapter=adapter,
        rules_for_constraint=DEFAULT_DAG_RULES,  # We don't want cycles in the graph
        available_node_types=node_types  # Node types that can appear in graphs
    )
    all_parameters = (requirements, graph_gen_params, gp_params)

    # Build and run the optimizer
    def optimiser_producer(pop_size_adaptor):
        return EvoGraphOptimizer(objective, initial_graphs, pop_size_adaptor=pop_size_adaptor, *all_parameters)

    hp_env = HyperparameterEnv(optimiser_producer, objective)
    env = DummyVecEnv([lambda: Monitor(hp_env)])

    # learn_agent(env)
    play_env(env)


def play_env(env):
    env.reset()
    while True:
        action = env.action_space.sample()
        print(f"Env action: {action}")
        s, r, done, _ = env.step(action)
        print(f"Env state: {s}")
        print(f"Env reward: {r}")

        if done:
            break

    # return hp_env.optimizer.best_individuals


if __name__ == '__main__':
    """
    In this example Optimizer is expected to find the target graph
    using Tree Edit Distance metric and a random tree (nx.random_tree) as target.
    The convergence can be seen from achieved metrics and visually from graph plots.
    """
    run_graph_search(visualize=True)
