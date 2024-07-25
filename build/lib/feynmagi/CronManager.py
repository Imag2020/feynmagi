import threading
from datetime import datetime, timedelta
import time

class CronManager:
    def __init__(self):
        self.jobs = []
        self.lock = threading.Lock()  # Pour garantir que les modifications de la liste des jobs sont thread-safe

    def add_job(self, job, run_time):
        with self.lock:
            self.jobs.append((job, run_time))

    def remove_job(self, job_name):
        with self.lock:
            self.jobs = [(job, time) for job, time in self.jobs if job.agent.name != job_name]

    def reschedule_job(self, job_name, new_time):
        with self.lock:
            for i, (job, _) in enumerate(self.jobs):
                if job.agent.name == job_name:
                    self.jobs[i] = (job, new_time)
                    break

    def run(self):
        while True:
            now = datetime.now()
            with self.lock:
                for job, next_run in list(self.jobs):  # Utiliser list pour copier et éviter des modifications pendant l'itération
                    if now >= next_run:
                        threading.Thread(target=job.run).start()  # Exécuter le job dans un thread séparé
                        # Recalculer le prochain temps d'exécution
                        if job.agent.schedule[0].lower() == 'daily':
                            next_run += timedelta(days=1)
                        elif job.agent.schedule[0].lower() == 'weekly':
                            next_run += timedelta(weeks=1)
                        # Mettre à jour le prochain temps d'exécution
                        self.jobs = [(j, n) if j != job else (j, next_run) for j, n in self.jobs]
            time.sleep(60)  # Vérifier toutes les minutes
