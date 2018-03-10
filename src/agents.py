'''
Created on 07/set/2016

@author: Lorenzo Selvatici
'''

import random
import util
from settings import Settings
from rules import Rules, Action
from inference import ExactInference

class AgentRole:
    """
    Enumeration representing the possible roles of an Agent.
    """
    Mr_X = "Mr_X"
    COP = "COP"


class AgentState:
    """
    Store the informations which characterize the state of a generic agent.
    Example: current position, moves history, number of ticket, ect.
    """
    
    def __init__(self, ticketDict, initialPosition, movesHistory=[]):
        """
        Initializes the agent state, the optional parameters movesHistory is by default an empty list.
        """
        self.position = initialPosition
        self.movesHistory = movesHistory # a list of Action
        self.ticketDict=ticketDict
    
    def getPosition(self):
        return self.position
    
    def addMoveToHistory(self, action):
        assert action.getStart()==self.position
        self.movesHistory.append(action)
        self.position = action.getEnd()
    
    def getMovesHistory(self):
        """
        Return a list of Action.
        """
        return self.movesHistory
    
    def getTicketsAsDict(self):
        return self.ticketDict
    
    def deepCopy(self):
        return AgentState(self.ticketDict.copy(), self.position, self.movesHistory[:])
    
    def __eq__(self, other):
        return self.getPosition() == other.getPosition() and \
            self.getMovesHistory() == other.getMovesHistory() and \
            self.getTicketsAsDict() == other.getTicketsAsDict()
    
    def __str__(self):
        return "pos : " + str(self.position) + "\ntickets : " + str(self.ticketDict) \
            + "\nmoves : " + str(self.movesHistory) + "\n"
        
    
class Agent:
    """
    Represents a generic ABSTRACT agent (the getAction and deepCopy methods are not implemented yet).    
    """
    
    def __init__(self, index, role, agentState):
        assert index>=0
        if index==0: assert role==AgentRole.Mr_X
        if index>0: assert role==AgentRole.COP
        self.index = index
        self.role = role
        self.agentState = agentState
    
    def getRole(self):
        """
        Returns an the role of the agent (AgentRole)
        """
        return self.role
    
    def getIndex(self):
        """
        Returns the index of the agent
        """
        return self.index
    
    def getAgentState(self):
        """
        Returns the state of the agent (AgentState)
        """
        return self.agentState
    
    def getAction(self, gameState, display):
        """
        Given a gameState (see game.py) return an instance of Action (see game.py).
        
        The display (Display see display.py) used by the agent controlled by the user, thus we can control how
        the user is asked for an action (console, GUI, etc..)
        
        Self-controlled Agents just ignore it. (es: randomAgent)
        """
        util.raiseNotDefined()
    
    def performAction(self, action):
        ticket = action.getTicketType()
        tickets = self.agentState.ticketDict
        assert ticket in tickets and tickets[ticket]>0
        tickets[ticket]-=1
        self.agentState.addMoveToHistory(action)
    
    def __repr__(self):
        return "{} ({}) -> {}\n".format(self.role, self.type, self.index) + self.agentState.__str__()

class MrX(Agent):
    """
    A generic Mr.X agent, still abstract.
    """
    
    def __init__(self, agentState=None):
        """
        An agent state (AgentState) can be optionally supplied, otherwise it would be loaded by the settings
        """
        if agentState is None:
            # create the agent state from the specified settings in Settings (see settings.py)
            ticketDict = Settings.getInitialMrXTickets()
            initialPosition = Settings.getInitialMrXPosition()
            agentState = AgentState(ticketDict, initialPosition)
        
        self.notHiddenMoves = {}
        moves = agentState.getMovesHistory()
        for i, action in enumerate(moves):
            if i+1 in Settings.getNotHiddenMovesNumbers():
                self.notHiddenMoves[i+1] = action.getEnd()
        
        Agent.__init__(self, 0, AgentRole.Mr_X, agentState)
    
    def __eq__(self, other):
        if not isinstance(other, MrX):
            return False
        return self.getAgentState() == other.getAgentState()
    
    def __repr__(self):
        if Settings.isDebug():
            return Agent.__repr__(self)
        else:
            not_hidden = {}
            for number in Settings.getNotHiddenMovesNumbers():
                not_hidden[number] = "-" if number not in self.notHiddenMoves \
                                         else self.notHiddenMoves[number]
                
            return "{} ({}) -> {}\n".format(self.role, self.type, self.index) + "tickets : " \
                 + str(self.agentState.ticketDict) + "\ntickets used: " \
                 + str([action.getTicketType() for action in self.agentState.movesHistory]) \
                 + "\n" + "\n".join("{} : {}".format(key, not_hidden[key]) for key in sorted(not_hidden))
    
    def performAction(self, action):
        Agent.performAction(self, action)
        current = len(self.agentState.movesHistory)
        if current in Settings.getNotHiddenMovesNumbers():
            self.notHiddenMoves[current] = self.agentState.getPosition()
        
class Cop(Agent):
    """
    A generic cop agent, still abstract.
    """
    
    def __init__(self, index, agentState=None):
        """
        An agent state (AgentState) can be optionally supplied, otherwise it would be loaded by the settings
        """
        if agentState is None:
            # create the agent state from the specified settings in Settings (see settings.py)
            ticketDict = Settings.getInitialCopsTickets()
            initialPosition = Settings.getInitialCopsPositions(index)
            agentState = AgentState(ticketDict, initialPosition)
        
        Agent.__init__(self, index, AgentRole.COP, agentState)
    
    def deepCopy(self):
        """
        Returns a deep copy of itself.
        """
        return Cop(self.index, self.agentState.deepCopy())
    
    def __eq__(self, other):
        if not isinstance(other, Cop):
            return False
        return self.index == other.index and self.getAgentState() == other.getAgentState()

class KeyboardAgent(Agent):
    """
    Defines a agent whose action are taken as input from the keyboard.
    """
   
    def getAction(self, gameState, display):
        """
        Given a certain gameState (GameState), returns an action (Action).
        """
        currPos = self.getAgentState().getPosition()
        assert gameState.data.getAgentState(self.getIndex()).getPosition() == currPos
        
        assert "askForAction" in dir(display)
        
        # ask for an action
        possActions = Rules.getLegalActions(self, gameState.data)
        
        # if possActions is empty then skip the turn
        if possActions == [] :
            display.showMessage("No possible actions for " + str(self.role) + " n." + str(self.index) + \
                                " from the current position " + str(currPos) + ".\nSkip the turn.\n")
            return None
        
        dest, ticket = display.askForAction(self.role, self.index, currPos, possActions)
        # check start != end otherwise Action.__init__ will crash the program
        while dest == currPos:
            display.showMessage("Illegal action!\ncurrent position == destination")
            display.wait(ms=2000)
            dest, ticket = display.askForAction(self.role, self.index, currPos, possActions)
            
        action = Action(currPos, dest, ticket)
        while action not in possActions:
            display.showMessage("Illegal action! " + action.__repr__())
            display.wait(ms=2000)
            dest, ticket = display.askForAction(self.role, self.index, currPos, possActions)
            action = Action(currPos, dest, ticket)
                    
        return action


class KeyboardMrX(KeyboardAgent, MrX):
    """
    A Mr.X agent whose action are taken as input from the keyboard.
    """
    def __init__(self, agentState = None):
        MrX.__init__(self, agentState)
        self.type = "KeyboardMrX"
    
    def deepCopy(self):
        """
        Returns a deep copy of itself.
        """
        return KeyboardMrX(self.agentState.deepCopy())
    
    def __repr__(self):
        return MrX.__repr__(self)
    
    def performAction(self, action):
        MrX.performAction(self, action)


class KeyboardCop(KeyboardAgent, Cop):
    """
    A Cop agent whose action are taken as input from the keyboard.
    """
    def __init__(self, index, agentState = None):
        Cop.__init__(self, index, agentState)
        self.type = "KeyboardCop"
        
    def deepCopy(self):
        """
        Returns a deep copy of itself.
        """
        return KeyboardCop(self.index, self.agentState.deepCopy())


class SmartKeyboardCop(Cop, KeyboardAgent):
    """
    A smart cop has a strong ability to guess Mr.X position.
    """
    def __init__(self, index, agentState=None, inference = None):
        Cop.__init__(self, index, agentState)
        self.type = "SmartCop"
        if inference is None:
            self.inference = ExactInference()
        else:
            self.inference = inference
    
    def deepCopy(self):
        return SmartKeyboardCop(self.index, self.agentState.deepCopy(), self.inference)
    
    def getAction(self, gameState, display):
        """
        Ask the user for an action after having displayed the beliefs distribution.
        """
        ticketList, notHiddenMoves = gameState.getMrXEvidences()
        self.inference.updateBeliefs(ticketList, notHiddenMoves, gameState.deepCopy())
        beliefsDistribution = self.inference.getBeliefsDistribution()  # util.Counter
        
        mostLikelyPositions = beliefsDistribution.argMax()  # the list of most likely positions
        
        ##### TO CHANGE (WHEN IMPLEMENTED THE GUI DISPLAYER OF BELIEFS DISTRIBUTION)
        print beliefsDistribution
        print mostLikelyPositions
        #####
        return KeyboardAgent.getAction(self, gameState, display)

class DistanceMinimizerCop(Agent, Cop):
    BELIEF_EPSILON = 0.000000001

    INFINITY = 999

    def __init__(self, index, agentState = None, inference = None):

        Cop.__init__(self, index, agentState)
        self.type = "DistanceMinimizerCop"

        if inference is None:
            self.inference = ExactInference()
        else:
            self.inference = inference

    def deepCopy(self):

        return DistanceMinimizerCop(self.index, self.agentState.deepCopy(), self.inference)

    def getMovesToState(self, finalState, gameState, visited, totalMoves):

        if self.getAgentState().getPosition() == finalState:
            return totalMoves
        else:

            currentPosition = self.getAgentState().getPosition()
            legalActions = Rules.getLegalActions(self, gameState.data)
            agentIndex = self.getIndex()

            # If not more legal actions possible from here, return INFINITY
            if legalActions is None or len(legalActions) == 0:

                return self.INFINITY
            else:

                moves = self.INFINITY
                for legalAction in legalActions:

                    if legalAction.getEnd() not in visited:

                        # Transition the agent, which creates a new copy of the game state.
                        gameStateCopy = gameState.generateSuccessor(agentIndex, legalAction, False)
                        agentCopy = gameStateCopy.data.getAgent(agentIndex)
                        visitedCopy = visited[:]

                        visitedCopy.append(agentCopy.getAgentState().getPosition())
                        new_moves = agentCopy.getMovesToState(finalState, gameStateCopy, visitedCopy, totalMoves + 1)

                        if new_moves < moves:

#                            print "Better move: [%u]->[%u] = %u" %(self.getAgentState().getPosition(),
#                                finalState,
#                                new_moves)
                            moves = new_moves

                return moves

    def getAction(self, gameState, display):

        ticketList, notHiddenMoves = gameState.getMrXEvidences()
        self.inference.updateBeliefs(ticketList, notHiddenMoves, gameState.deepCopy())
        beliefsDistribution = self.inference.getBeliefsDistribution()
        mostLikelyPositions = beliefsDistribution.argMax()  # the list of most likely positions
        agentIndex = self.getIndex()

        ##### TO CHANGE (WHEN IMPLEMENTED THE GUI DISPLAYER OF BELIEFS DISTRIBUTION)
        # print beliefsDistribution
        # print mostLikelyPositions
        #####

        currentPosition = self.getAgentState().getPosition()
        legalActions = Rules.getLegalActions(self, gameState.data)

        if legalActions is None or len(legalActions) == 0:

            display.showMessage("No possible actions for %s[%s] at %s.\n" % (str(self.role),
                 str(self.index),
                 str(currentPosition)))
            display.wait(ms=1000)
            return None
        else:

            actionCosts = {}

            for legalAction in legalActions:

                actionCosts[legalAction] = 0.0

                # Transition the agent, which creates a new copy of the game state.
                gameStateCopy = gameState.generateSuccessor(agentIndex, legalAction, False)
                agentCopy = gameStateCopy.data.getAgent(agentIndex)

                # for all the belief states, get the total number of moves.
                for state in beliefsDistribution:

                    visited = [ currentPosition, agentCopy.getAgentState().getPosition() ]
                    moves = agentCopy.getMovesToState(state, gameStateCopy, visited, 1)

                    actionCosts[legalAction] = actionCosts[legalAction] + moves * beliefsDistribution[state]

            bestAction = None
            maxCost = self.INFINITY * len(actionCosts)

            for action in actionCosts:

                if actionCosts[action] < maxCost:

                    bestAction = action
                    maxCost = actionCosts[action]

            display.wait(ms=200)
            return bestAction

class RandomAgent(Agent):

    """
        A rather dumb agent whose only purpose is to act randomly.

        However, random is still interesting, since a random walk on a graph is still complete.
    """

    # The 'simulated' thinking time in milliseconds.
    #
    # This helps control the frequency of the GUI update to make it easy on the human eyes.
    THINKING_TIME_IN_MS = 10

    def getAction(self, gameState, display):

        """ Returns a random action from the set of legal actions possible for the agent given the current state.
        
            Args:
                gameState:
                    The current game state.
                display:
                    The display manager.
            Returns:
                A legal action for the agent, None if no legal actions were possible.
            
        """

        # Get the agent's current position and make sure that the game state agrees with the same.
        currentPosition = self.getAgentState().getPosition()
        assert gameState.data.getAgentState(self.getIndex()).getPosition() == currentPosition

        # Make sure that the state is asking for an action.
        assert "askForAction" in dir(display)

        # Get the set of legal actions that are possible for this agent given the current game state.
        legalActions = Rules.getLegalActions(self, gameState.data)

        # If there are no legal actions, then skip the turn for the agent.
        # Else select a random action from the list of possible legal actions. All legal actions are guaranteed to move
        # the agent from their current location to a new location.
        if legalActions is None or len(legalActions) == 0:

            display.showMessage("No possible actions for %s[%s] at %s.\n" % (str(self.role),
                 str(self.index),
                 str(currentPosition)))
            display.wait(ms=self.THINKING_TIME_IN_MS)
            return None
        else:

            index = random.randint(0, len(legalActions) - 1)
            display.wait(ms=self.THINKING_TIME_IN_MS)
            return legalActions[index]

class RandomMrX(RandomAgent, MrX):

    def __init__(self, agentState = None):

        MrX.__init__(self, agentState)
        self.type = "RandomMrX"

    def deepCopy(self):

        return RandomMrX(self.agentState.deepCopy())

    def __repr__(self):

        return MrX.__repr__(self)

    def performAction(self, action):

        MrX.performAction(self, action)

class RandomCop(RandomAgent, Cop):

    def __init__(self, index, agentState = None):

        Cop.__init__(self, index, agentState)
        self.type = "RandomCop"

    def deepCopy(self):

        return RandomCop(self.index, self.agentState.deepCopy())

if __name__ == '__main__':
    # AgentState tests
#     import rules
#     as1 = AgentState({'k1': 1, 'k2': 3}, 1)
#     as1.getTicketsAsDict()['k2']-=1
#     assert as1.getTicketsAsDict()['k2']==2
#     as2 = as1.deepCopy()
#     as2.addMoveToHistory(rules.Action(1, 5, "TAXI"))
#     assert as1.getMovesHistory()==[]
#     as2.getTicketsAsDict()['k2']-=1
#     assert as1.getTicketsAsDict()['k2']==2
#     print "Passed!"
#     c = Cop(1)
#     print c
#     c2 = Cop(3)
#     print c2
#     assert c != c2
#     print "Passed!"
#     from rules import Action, TicketType
#     mrx1 = MrX()
#     mrx2 = mrx1.deepCopy()
#     mrx1.performAction(Action(mrx1.getAgentState().getPosition(), 2, TicketType.TAXI))
#     assert mrx1.getAgentState().getPosition() == 2
#     assert mrx2.getAgentState().getPosition() != 2
#     print "Passed!" 
    mrx = MrX()
    c1 = Cop(1)
    c2 = Cop(2)
    print mrx.getAgentState().getPosition()
    print c1.getAgentState().getPosition()
    print c2.getAgentState().getPosition()




