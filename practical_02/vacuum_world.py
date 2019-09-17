import argparse
import importlib
import logging
import sys
import random

NUM_TRIALS = 1000
LOGGER_NAME = "vacuum_world"
LOG_LEVEL = logging.INFO

MSG_AGENT_DECISION = "t={}\tAgent Decision: {}"
MSG_BAD_DIRT_STATUS_STR = "Invalid dirt status string: {}"
MSG_COMPLETE = "Simulation complete."
MSG_DESCRIPTION_AGENT = "Import path and class name for the agent"
MSG_DESCRIPTION_ENVIRONMENT = "Import path and class name for the environment"
MSG_DESCRIPTION_EVALUATOR = "Import path and class name for the evaluator"
MSG_DESCRIPTION_PROGRAM = "Agent evaluator and environment simulator for " \
                          "the vacuum world described in AIMA, page 38."
MSG_EXPERIMENT_ERROR = "Error in {}: {}"
MSG_ENVIRONMENT_INIT_ERROR = "Bad environment parameter: {}"
MSG_CLASS_NOT_FOUND = "Could not load {} \'{}\'"
MSG_HELLO = "Vacuum World Simulator v1.0"
MSG_MODULE_NOT_LOADED = "Could not load agent module \'{}\'"
MSG_SCORE = "Agent Score: {}"
MSG_UNRECOGNIZED_ARG = "Unrecognized argument: {}"

DIRTY_VALUES = ('y', 'yes', 't', 'true', 'dirty')
CLEAN_VALUES = ('n', 'no', 'f', 'false', 'clean')


class ExperimentError(Exception):
    def __init__(self, component, cause):
        self.component = component
        self.cause = cause


def run_experiment(environment, agent, evaluator):
    """
    Simulate an agent in the environment for 1000 steps.

    Decisions are logged to the 'vacuum_world' logger.

    :param environment: where the agent must perform
    :param agent: agent to evaluate
    :param evaluator: object that scores the agent against the
      performance measure
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(LOG_LEVEL)

    for t in range(1, 1001):
        try:
            decision = agent.decide(environment.observable_state)
        # We assume that ValueError means the environment's input failed the
        # agent's validation. We further assume that the agent's validation is
        # correct and the environment's input was truly illegal.
        except ValueError as e:
            raise ExperimentError('environment', e)
        except Exception as e:
            raise ExperimentError('agent', e)
        logger.info(MSG_AGENT_DECISION.format(t, repr(decision)))
        try:
            environment.update(decision)
        except ValueError as e:
            raise ExperimentError('agent', e)
        except Exception as e:
            raise ExperimentError('environment', e)
        evaluator.update(environment.state)


class BasicVacuumWorld(object):
    """
    Basic vacuum world specified on page 38 and depicted in Figure 2.2.

    There are two locations, A and B, and one agent. Either or both
    locations may contain dirt. The agent perceives its current location
    and whether there is dirt there.

    The agent may move left, move right, or suck up the dirt in its
    current location. Sucking cleans the current square and clean
    squares stay clean.
    """
    DIRTY_VALUES = ('y', 'yes', 't', 'true', 'dirty')
    CLEAN_VALUES = ('n', 'no', 'f', 'false', 'clean')
    locations = ['A', 'B']
    actions = ['LEFT', 'RIGHT', 'SUCK']

    def __init__(self, agent_location=('A',), dirt_status=('t', 't')):
        """
        Initialize a new environment.

        :param agent_location: One-element list of strings with the
          starting location of the agent as its element.
        :param dirt_status: A two-element list of strings
          denoting whether there is dirt at each location ['A', 'B'].
        """
        if len(agent_location) != 1:
            raise ValueError(agent_location)
        agent_location = agent_location[0]
        if agent_location not in BasicVacuumWorld.locations:
            raise ValueError(agent_location)
        if len(dirt_status) != len(BasicVacuumWorld.locations):
            raise ValueError(dirt_status)
        dirt_status_bools = map(BasicVacuumWorld._convert_to_dirt_status,
                                dirt_status)
        dirt_status_tuples = zip(BasicVacuumWorld.locations, dirt_status_bools)

        self._dirt_status = {location: status
                             for location, status in dirt_status_tuples}
        self._agent_location = agent_location

    @property
    def state(self):
        """
        All information, observable or not, about the state of the
        environment.

        A dictionary with two keys:
          - agent_location gives the agent's present location
          - dirt_status is a dictionary with a key for each location,
            and a boolean indicating whether there is dirt in that
            location.
        """
        return {
            "agent_location": self._agent_location,
            "dirt_status": self._dirt_status
        }

    @property
    def observable_state(self):
        """
        All information the agent's sensors can observe.

        A dictionary with two keys:
          - agent_location gives the agent's present location.
          - is_dirty is True if there is dirt in the agent's present
              location.
        """
        return {
            "agent_location": self._agent_location,
            "is_dirty": self._dirt_status[self._agent_location]
        }

    def update(self, action):
        """
        Update the environment with the results of an action taken by
        the agent's actuators.

        :param action: The action the agent takes. Allowed values are
          'LEFT', 'RIGHT', and 'SUCK'.
        """
        if action == 'SUCK':
            self._dirt_status[self._agent_location] = False
        elif action == 'RIGHT':
            self._agent_location = 'B'
        elif action == 'LEFT':
            self._agent_location = 'A'
        else:
            raise ValueError(action)

    @staticmethod
    def _convert_to_dirt_status(string):
        string = string.lower()
        if string in DIRTY_VALUES:
            dirt_status = True
        elif string in CLEAN_VALUES:
            dirt_status = False
        else:
            message = MSG_BAD_DIRT_STATUS_STR.format(string)
            raise ValueError(message)
        return dirt_status


class CleanFloorEvaluator(object):
    """
    Evaluator that scores Vacuum World environments highly for having
    clean floors.
    """
    def __init__(self):
        self._score = 0

    def update(self, state):
        """
        Award one point for each location that is clear of dirt.

        :param state: Environment state dictionary that has a
          "dirt_status" key, which maps to a dictionary of
          location -> has_dirt.
        """
        self._score += list(state["dirt_status"].values()).count(False)

    @property
    def score(self):
        """
        Sum of the total number of time steps each location has been
        clear of dirt.
        """
        return self._score


class SuckyAgent(object):
    """
    Vacuum World agent that only chooses the SUCK action.
    """
    def decide(self, _):
        """
        Suck up the dirt, if there is any.

        :param _: for compliance with the agent interface; not used.
        """
        return 'SUCK'

		
class RandomAgent(object):
    """
    Vacuum World agent that only chooses a random action.
    """

    def decide(self, _):
        """
        select a random action

        :param _: for compliance with the agent interface; not used.
		
        """


class RationalAgent(object):
    """
    Vacuum World agent that only chooses a random action.
    """

    def decide(self, _):
        """
        

        :param _: for compliance with the agent interface; not used.
		
        """

		
        
		

def main():
    # Set up logging
    logger = logging.getLogger()
    handler = logging.StreamHandler(stream=sys.stdout)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(handler)

    # Parse arguments
    args, environment_args = _parse_arguments()

    logger.info(MSG_HELLO)

    # Load classes for actors
    environment_class = _try_load_class(args.environment, 'environment')
    agent_class = _try_load_class(args.agent, 'agent')
    evaluator_class = _try_load_class(args.evaluator, 'evaluator')

    # Instantiate actors
    evaluator = evaluator_class()
    agent = agent_class()
    try:
        environment = environment_class(**environment_args)
    except ValueError as e:
        logger.error(MSG_ENVIRONMENT_INIT_ERROR.format(e.args[0]))
        return 1

    # Do the thing
    try:
        run_experiment(environment,
                       agent,
                       evaluator)

        logger.info(MSG_COMPLETE)
    except ExperimentError as e:
        logger.error(MSG_EXPERIMENT_ERROR.format(e.component, repr(e.cause)))

    # Report results
    score = evaluator.score
    logger.info(MSG_SCORE.format(score))


def _strtobool(string):
    string = string.lower()
    if string in DIRTY_VALUES:
        value = True
    elif string in CLEAN_VALUES:
        value = False
    else:
        message = MSG_BAD_DIRT_STATUS_STR.format(string)
        raise argparse.ArgumentTypeError(message)
    return value


def _try_load_class(import_path, role):
    logger = logging.getLogger()
    try:
        _class = _load_class(import_path)
    except ImportError as e:
        logger.error(MSG_MODULE_NOT_LOADED.format(e.name))
        sys.exit(1)
    except _ClassNotFoundError:
        logger.error(MSG_CLASS_NOT_FOUND.format(role, import_path))
        sys.exit(1)
    return _class


def _load_class(agent_path):
    agent_path_segments = agent_path.split('.')
    agent_module_name = '.'.join(agent_path_segments[:-1])
    agent_class_name = agent_path_segments[-1]
    if agent_module_name != '':
        agent_module = importlib.import_module(agent_module_name)
        try:
            agent_class = getattr(agent_module, agent_class_name)
        except AttributeError:
            raise _ClassNotFoundError
    else:
        try:
            agent_class = globals()[agent_class_name]
        except KeyError:
            raise _ClassNotFoundError
    return agent_class


def _extract_environment_args(args):
    environment_args = {}
    while len(args) > 0:
        if not args[0].startswith('--env-'):
            raise ValueError(args[0])
        param_name = args[0][6:].replace('-', '_')
        rest = args[1:]
        if len(rest) > 0:
            i = 0
            while i < len(rest):
                element = rest[i]
                if element.startswith('--env-'):
                    break
                i += 1
            environment_args[param_name] = rest[:i]
            args = rest[i:]
        else:
            environment_args[param_name] = []
            args = []

    return environment_args


def _parse_arguments():
    arg_parser = argparse.ArgumentParser(description=MSG_DESCRIPTION_PROGRAM)
    arg_parser.add_argument('--agent', type=str, required=False,
                            default='SuckyAgent', metavar='AGENT_CLASS',
                            help=MSG_DESCRIPTION_AGENT)
    arg_parser.add_argument('--environment', type=str, required=False,
                            default='BasicVacuumWorld',
                            metavar='ENVIRONMENT_CLASS',
                            help=MSG_DESCRIPTION_ENVIRONMENT)
    arg_parser.add_argument('--evaluator', type=str, required=False,
                            default='CleanFloorEvaluator',
                            metavar='EVALUATOR_CLASS',
                            help=MSG_DESCRIPTION_EVALUATOR)
    (args, custom_args) = arg_parser.parse_known_args()

    try:
        environment_args = _extract_environment_args(custom_args)
    except ValueError as e:
        message = MSG_UNRECOGNIZED_ARG.format(e.args[0])
        arg_parser.error(message)
        raise SystemError("I have reached unreachable code.")

    return args, environment_args


class _ClassNotFoundError(Exception):
    pass


if __name__ == '__main__':
    main()
