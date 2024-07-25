import json

class Agent:
    def __init__(self, name, schedule, when, system, prompt, tools):
        self.name = name
        self.schedule = schedule  # en minutes
        self.when = when
        self.system = system
        self.prompt = prompt
        self.tools = tools

    def to_dict(self):
        return {
            'name': self.name,
            'schedule': self.schedule,
            'when': self.when,
            'system': self.system,
            'prompt': self.prompt,
            'tools' : self.tools
        }

    @staticmethod
    def from_dict(data):
        return Agent(data['name'], data['schedule'],data['when'], data['system'],data['prompt'],data['tools'])

class AgentManager:
    def __init__(self):
        self.agents = []
        self.load_agents()

    def add_agent(self, agent_data):
        agent = Agent.from_dict(agent_data)
        # Check if the agent already exists
        existing_agent = self.find_agent_by_name(agent.name)
        if existing_agent:
            # Remove existing agent
            self.remove_agent(agent.name)
        # Add the new agent
        self.agents.append(agent)
        self.save_agents()

    def remove_agent(self, agent_name):
        self.agents = [agent for agent in self.agents if agent.name != agent_name]
        self.save_agents()

    def get_agents(self):
        return self.agents

    def load_agents(self):
        try:
            with open('agents.json', 'r') as file:
                agents_data = json.load(file)
                self.agents = [Agent.from_dict(data) for data in agents_data]
        except FileNotFoundError:
            print("No existing agents found.")

    def save_agents(self):
        with open('agents.json', 'w') as file:
            json.dump([agent.to_dict() for agent in self.agents], file)

    def find_agent_by_name(self, agent_name):
        for agent in self.agents:
            if agent.name == agent_name:
                return agent
        return None

