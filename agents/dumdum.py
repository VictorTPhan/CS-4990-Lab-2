from hanabi import *
import util
import agent
import random

def format_hint(h):
    if h == HINT_COLOR:
        return "color"
    return "rank"
        
class DumDum(agent.Agent):
    def __init__(self, name, pnr):
        self.name = name
        self.hints = {}
        self.pnr = pnr
        self.explanation = []
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints, hits, cards_left):        
        ### FROM OSAWA OUTER
        for player,hand in enumerate(hands):
            for card_index,_ in enumerate(hand):
                if (player,card_index) not in self.hints:
                    self.hints[(player,card_index)] = set()
        known = [""]*5
        for h in self.hints:
            pnr, card_index = h 
            if pnr != nr:
                known[card_index] = str(list(map(format_hint, self.hints[h])))
        self.explanation = [["hints received:"] + known]
        ### FROM OSAWA OUTER

        my_knowledge = knowledge[nr]
        #before we move on, let's look through all of our card knowledge and 
        #modify it based on what we know has been trashed, played, and what's in the other guy's hands
        
        '''
        for every card in any other player's hand,
        update your knowledge of every one of your cards
        to not include their specific card

        ex: if someome as a green 1, go through all your
        knowledges and decrement green 1 by 1
        '''

        '''
        TODO - based on what has been played and trashed, 
        and what's in the other player's hand,
        figure out how many cards are left in the pool

        - for example, since a game can only have 2 yellow 4's, then if you trashed
            a yellow 4, and your opponent has a yellow 4, hint them that they have one.
            in your opponent's perspective, they should be able to deduce that 
            they do in fact have the only yellow 4 left and mark it as important

        - for another example, if you have a 5 card, mark it as important and never
            trash it ever
        '''
        cards_i_know = [None, None, None, None, None]
        #3D dictionary, access amount of card by key tuple (COLOR, RANK)
        remaining_card_pool = {}
        for color in range(5):
            for rank in range(1,6):
                amount = 2
                if rank == 1:
                    amount = 3
                elif rank == 5:
                    amount = 1
                remaining_card_pool[(color, rank)] = amount

        # we'll store the other player's hands, the played, and the trashed in here
        knowledge_modifiers = trash + played
        for i in range(len(hands)):
            if i == nr:
                continue
            else:
                for card in hands[i]:
                    knowledge_modifiers.append(card)

        #for each other card, adjust knowledge accordingly
        for card in knowledge_modifiers:
            #card is a tuple, (COLOR, RANK)
            color = card[0]
            rank = card[1]
            for my_card in my_knowledge:
                if my_card[color][rank-1] > 1:
                    my_card[color][rank-1] -= 1
            remaining_card_pool[(color, rank)]-=1
                
        potential_plays = []
        potential_discards = []
        for i,k in enumerate(my_knowledge): #for every card in your knowledge bank
            chance_its_playable = util.probability(util.playable(board), k)
            chance_its_5 = util.probability(util.has_rank(5), k)
            
            if chance_its_playable > 0.75: 
                potential_plays.append(i) #consider moderately playable cards
            else:
                possibly_useless = util.maybe_useless(k, board) 
                not_a_5 = chance_its_5 < 0.2 #never ever discard a 5
                if possibly_useless and not_a_5:
                    potential_discards.append(i) #consider possibly useful non-5 cards

        # play the most useful card (minimum is 75% usefulness)
        if potential_plays:
            bestProbability = 0
            bestCard = 0
            for index in potential_plays:
                if util.probability(util.playable(board), my_knowledge[index]) > bestProbability:
                    bestCard = index
                    bestProbability = util.probability(util.playable(board), my_knowledge[index])
            return Action(PLAY, card_index=bestCard)
        
        # trash the least useful card (doesn't include 5's)
        if potential_discards:
            worstProability = 1
            worstCard = 0
            for index in potential_discards:
                if util.probability(util.playable(board), my_knowledge[index]) < worstProability:
                    worstCard = index
                    worstProability = util.probability(util.playable(board), my_knowledge[index])
            
            #print("My worst card is",worstCard,worstProability)
            if worstProability < 0.1 :
                return Action(DISCARD, card_index=worstCard)

        ### FROM OSAWA OUTER
        playables = []        
        for player,hand in enumerate(hands):
            if player != nr:
                for card_index,card in enumerate(hand):
                    if card.is_playable(board):                              
                        playables.append((player,card_index))
        
        playables.sort(key=lambda which: -hands[which[0]][which[1]].rank)
        while playables and hints > 0:
            player,card_index = playables[0]
            knows_rank = True
            real_color = hands[player][card_index].color
            real_rank = hands[player][card_index].rank
            k = knowledge[player][card_index]
            
            '''
            TODO - check if the other player knows what their card is with some certainty
            the player that knows least about their cards should be hinted
            '''

            hinttype = [HINT_COLOR, HINT_RANK]
            
            for h in self.hints[(player,card_index)]:
                hinttype.remove(h)
            
            t = None
            if hinttype:
                t = random.choice(hinttype)

            if t == HINT_RANK:
                for i,card in enumerate(hands[player]):
                    if card.rank == hands[player][card_index].rank:
                        self.hints[(player,i)].add(HINT_RANK)
                return Action(HINT_RANK, player=player, rank=hands[player][card_index].rank)
            if t == HINT_COLOR:
                for i,card in enumerate(hands[player]):
                    if card.color == hands[player][card_index].color:
                        self.hints[(player,i)].add(HINT_COLOR)
                return Action(HINT_COLOR, player=player, color=hands[player][card_index].color)
            playables = playables[1:]
 
        if hints > 0:
            hints = util.filter_actions(HINT_COLOR, valid_actions) + util.filter_actions(HINT_RANK, valid_actions)
            hintgiven = hints[2]

            number = []
            for _ in hands[player]:
                number.append(hands[player][card_index].rank)

            for j in range(5):
                count = 0
                for k in number:
                    if j+1 == k:
                        count += 1
                if count >= 3:
                    for i, card in enumerate(hands[hintgiven.player]):
                        if card.rank == hintgiven.rank:
                            self.hints[(hintgiven.player, i)].add(HINT_RANK)
            else:
                for i, card in enumerate(hands[hintgiven.player]):
                    if card.color == hintgiven.color:
                        self.hints[(hintgiven.player, i)].add(HINT_COLOR)
            
            return hintgiven

        ### FROM OSAWA OUTER
        
        '''
        Worst case, just discard your least playable card (and also no 5's)
        '''
        least_playable = 1
        worst_card = 0
        for i,k in enumerate(my_knowledge):
            playable_chance = util.probability(util.playable(board), k)
            chance_its_5 = util.probability(util.has_rank(5), k)
            
            if chance_its_5 > 0.9:
                continue
            elif playable_chance < least_playable:
                least_playable = playable_chance
                worst_card = i
        return Action(DISCARD, card_index=worst_card)

    def inform(self, action, player):
        if action.type in [PLAY, DISCARD]:
            if (player,action.card_index) in self.hints:
                self.hints[(player,action.card_index)] = set()
            for i in range(5):
                if (player,action.card_index+i+1) in self.hints:
                    self.hints[(player,action.card_index+i)] = self.hints[(player,action.card_index+i+1)]
                    self.hints[(player,action.card_index+i+1)] = set()


agent.register("dumdum", "Dum Dum Player", DumDum)