###########################################################################################
#
# FeynmAGI V0.1
# Imed MAGROUNE
# 2024-06
#
#########################################################################################
import os
import json
import glob
from datetime import datetime
import pkg_resources


class SessionHistory:
    def __init__(self):
        self.history_dir =pkg_resources.resource_filename('feynmagi', 'data/sessions_history')
        if not os.path.exists(self.history_dir):
            os.makedirs(self.history_dir)

    def load_session(self, session_id):
        """Load a specific session from a file."""
        session_file = os.path.join(self.history_dir, f'{session_id}.json')
        print(f"Loading session from file: {session_file}")
        if os.path.exists(session_file):
            with open(session_file, 'r',encoding='utf-8') as file:
                print(f"File {session_file} found, loading content")
                return json.load(file)
        print(f"File {session_file} does not exist")
        return None

    def save_session(self, session, session_id):
        """Save a session to a file."""
        # session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        session_file = os.path.join(self.history_dir, f'{session_id}.json')
        print(f"Saving session to file: {session_file}")
        with open(session_file, 'w',encoding='utf-8') as file:
            json.dump(session, file)
        return session_id

    def delete_session(self, session_id):
        """Delete a specific session."""
        session_file = os.path.join(self.history_dir, f'{session_id}.json')
        if os.path.exists(session_file):
            print(f"Deleting session file: {session_file}")
            os.remove(session_file)
            return True
        return False

    def list_sessions(self):
        """List all sessions."""
        session_files = glob.glob(os.path.join(self.history_dir, '*.json'))
        sessions = []
        for session_file in session_files:
            with open(session_file, 'r',encoding='utf-8') as file:
                session_data = json.load(file)
                if session_data != [] and session_data is not None:
                    sessions.append({'session_id': os.path.basename(session_file).replace('.json', ''), 'data': session_data})
        sessions.sort(key=lambda x: x['session_id'], reverse=True)
        return sessions

