import math
import random
import numpy as np
from .llmsapis import llm2 
from . import config as cfg
import re

def get_context(messages):
    context=""
    for m in messages:
        context+=m['role'].capitalize()+" :\n\n"+m['content']+" \n\n"
    
    return context

def get_critique(context,draft_answer):
    prompt=(
        f"Context: \n{context}\n"
        f"Draft Answer : {draft_answer}\n"
        "Please critique the draft action, "
        "Do a careful assessement of whether the action is correct or not, and why"
        "Consider multiple ways of verifying the correctness of the action"
        "Do point out every flaw and hold the draft action to a high standard"
        "Do provide specific recommendations to improve the action"
        "Do think step by step"
        "Do not provide a revised action"
    )
    #print("prompt=",prompt)
    return llm2(prompt)


def improve_answer(question, draft_answer,critique):
    prompt=(
        f"Question: {question}\n"
        f"Draft Answer: {draft_answer}\n"
        f"Critique: {critique}\n\n"
        "Please improve the draft action based on the critique. Follow this format :\n"
        "Thought: <step-by-step reasoning process>\n"
        "Action: <the improved action from tools lost above>\n"
         "PAUSE\n"
    )

    # Create the request to the LLL
    improved_response = llm2(prompt)
    return improved_response

def rate_answer(question,answer):
    prompt=(
        f"Task: {question}\n"
        f"Action: {answer}\n\n"
        "Aa an expert on this topic, please provide a detailed critique of the action, pointing out every flaw. "
        "Provide only a critique, not a suggested action, "
        "Then, rate the action on a scale of 0 to 100. "
        "The response should be in the following format:\n"
        "Critique: <detailed critique>\n"
        "Rating: <rating>"
    )

    rating_response = llm2(prompt)
    #print(prompt)
    try:
        match=re.search(r'Rating:\s*(\d+)',rating_response)
        if match:
            rating=int(match.group(1))
            if rating > 95:
                rating=95
            rating= float(rating)/100
        else:
            raise ValueError("Rating not found in the response")
    except Exception as e:
        print(f"Error extracting rating {e}")
        print(f"Rating response was: {rating_response}")
        rating=0.0
    
    return rating

def get_answer_directly_from_llm(context):
    prompt=(
        f"Task: \n{context}\n"
        "Please provide the best next action with detailed reasoning. Follow this format :\n"
        "Thought: <step-by-step reasoning process>\n"
        "Action: <the improved action from tools list above>\n"
        "PAUSE\n"
    )
    llm_response=llm2(prompt)
    #Extract the final Answer
    try:
        
        match= re.findall(r"\*?\*?Action:?\*?\*?\s*?\s*([a-z_]+)\s*:\s*(.+)", llm_response, re.IGNORECASE)
        final_answer=match.group(1).strip() if match else None
    except Exception as e:
        final_answer = None
    return llm_response,final_answer

max_children=3

class Node:
    def __init__(self,context,action,parent=None):
        self.question=context
        self.answer=action
        self.parent=parent
        self.children=[]
        self.visits=0  # how many time we visit it ==> consider one of it's chilren
        self.value=0.0 # cumulated reward

    def is_fully_expanded(self):
        return len(self.children) >= max_children

    def best_child(self,exploration_weight=1.41):
        choices_weights = []
        for child in self.children:
            if child.visits == 0:
                weight = float('inf') # Prioritize unexplored nodes
            else:
                weight = (child.value / child.visits) + exploration_weight*math.sqrt((2*math.log(self.visits)/child.visits))
            choices_weights.append(weight)
        return self.children[np.argmax(choices_weights)]
                
    def most_visited_child(self):
        return max(self.children, key=lambda child: child.visits) #max des children selon le critère lambda (fonction anonyme / sans nom)
        
    def add_child(self,child_node):
        self.children.append(child_node)

class MCTS:
    def __init__(self,question, seed_answers,iterations=2):
        self.question=question
        self.seed_answers=seed_answers
        self.iterations=iterations
        self.root = Node(question, random.choice(seed_answers))

    def search(self):
        for i in range(self.iterations):
            #print(f"Iteration {i+1}/{self.iterations}")
            node=self.select(self.root)
            #print(f"Selected Node : {node.answer}")
            if not node.is_fully_expanded():
                node = self.expand(node)
                #print(f"Expanded node : {node.answer}")
            reward=self.simulate(node)
            #print(f"Simultaed Reward: {reward}")
            self.backpropagate(node,reward)
        #print(f"Visits to most visited child : {self.root.most_visited_child().visits}")
        return self.root.most_visited_child().answer
        
    def select(self,node):
        while node.is_fully_expanded() and node.children:
            node=node.best_child()
        return node
    
    def expand(self, node):
        for j in range(max_children-len(node.children)):
            child_node=Node(self.question,node.answer,parent=node) # 
            node.add_child(child_node)

            critique = get_critique(self.question,child_node.answer)
            #print(f"\nCritique {j} --\n{critique}")

            improved_answer = improve_answer(self.question, child_node.answer,critique)
            #print(f"\improved_answer {j} --\n{improved_answer}")

            child_node.answer = improved_answer
        return random.choice(node.children)

    def simulate(self,node):
        rating= rate_answer(self.question, node.answer)
        '''
        print("______ simulate ________________")
        print("rating ",rating)
        '''
        return rating

    def backpropagate(self,node,reward):
        while node is not None:
            node.visits += 1
            node.value += reward
            '''
            print("_________________________")
            print(node.visits,node.value,node.answer)
            print("_________________________")
            '''
            node=node.parent 

def mcts_action(messages):
    context=get_context(messages)
    print("")
    print("________________ context _____________________")
    print(context)
    print("________________ end context _____________________")
    '''
    seed_answers=[]
    for  i in range(3):
        #print(f"{i}")
        answer=llm2(context)
        seed_answers.append(answer)
    print(f"seed actions :\n {seed_answers} ")
    '''
    seed_answers = [
    "Thought : I don't know\nAction : None\nPause\n",
    "Thought : I'm not sure\nAction : Exit\nPause\n",
    "Thought : I can't say\nAction : Nothing\nPause\n"
]
    mcts = MCTS(context, seed_answers, iterations=2)
    best_action=mcts.search()
    print(f" _______________    mcts final best action : {best_action}")
    if best_action=='':
        print("")
        print("_________________ to do check _______________________")
        best_action=llm2(context)
    return best_action
