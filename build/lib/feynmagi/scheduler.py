from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from .Job import Job
from datetime import datetime, timedelta


# Fonction pour afficher tous les jobs

        
class Scheduler:
    def __init__(self, agent_manager):
        self.scheduler = BackgroundScheduler()
        self.agent_manager = agent_manager
        
    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            print("Scheduler has been started.")

        
    def shutdown(self):
        self.scheduler.shutdown(wait=False)
        print("Scheduler has been shut down.")
    
    def remove_job(self, agent_name):
        # Check if the job exists before trying to remove it
        job = self.scheduler.get_job(job_id=agent_name)
        if job:
            try:
                self.scheduler.remove_job(agent_name)
                print(f"Job {agent_name} successfully removed.")
            except JobLookupError as e:
                print(f"Error removing job {agent_name}: {e}")
        else:
            print(f"No job found with ID {agent_name}.")

    def reschedule_job(self, agent):
        # First, attempt to remove the existing job if it exists
        self.remove_job(agent.name)
        # Then add the job back with possibly new scheduling parameters
        self.add_job(agent)

    def add_job(self, agent):
        job = Job(agent.name, datetime.now())  # Assuming a Job constructor that suits your needs
        # Example of handling different schedules; adapt trigger configuration accordingly
        print("agent.schedule=",agent.schedule)
        try:
            if agent.schedule[0].lower() == 'daily':
                hour, minute = map(int, agent.when.split(':'))
                self.scheduler.add_job(job.run, 'cron', day='*', hour=hour, minute=minute, id=agent.name)
            elif agent.schedule[0].lower() == 'weekly':
                hour, minute = map(int, agent.when.split(':'))
                self.scheduler.add_job(job.run, 'cron', week='*', day_of_week='*', hour='*', minute='*', id=agent.name)
            # Add other schedules as necessary
            print(f"Added/Rescheduled job for {agent.name}")
            self.display_jobs()
        except RuntimeError as e:
            print(f"Failed to add job: {e}")
        

    def display_jobs(self):
        jobs = self.scheduler.get_jobs()
        print("Currently scheduled jobs:")
        for job in jobs:
            print(f"Job ID: {job.id}")
            print(f"Next run time: {job.next_run_time}")

# This class definition assumes the existence of a Job class that correctly initializes with agent.name
