from  datetime import datetime
import time
import os
class Job:
    def __init__(self, agent):
        self.agent = agent
        #self.next_run_time = next_run_time

    def run(self):
        # Logique d'exécution du prompt
        current_time = datetime.now()
        print(f"Executing job for agent {self.agent.name} at {current_time}\n{self.agent.prompt}")
        # Ajouter un enregistrement dans un fichier de log
        self.log_to_file(f"Executing job for agent {self.agent.name} at {current_time}")

    def log_to_file(self, message):
        # S'assurer que le dossier de logs existe
        if not os.path.exists('logs'):
            os.makedirs('logs')
        # Écrire le message dans un fichier log
        with open('logs/job_execution.log', 'a') as file:
            file.write(message + '\n')

    def to_json(self):
        return {
            'agent_name': self.agent.name,
            'next_run_time': self.next_run_time.isoformat()
        }

    @classmethod
    def from_json(cls, data):
        return cls(data['agent_name'], datetime.fromisoformat(data['next_run_time']))
