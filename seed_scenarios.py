import sqlite3
import json
import random
import time
import os
from dotenv import load_dotenv
load_dotenv()

# Set mock locally for speed if not strictly relying on bedrock
# os.environ["USE_MOCK_GENERATOR"] = "true" 

from services.scenario_generator import generate_specific_scenario, LANGUAGES, ISSUE_TYPES, DIFFICULTIES

def get_db_connection():
    return sqlite3.connect('scenarios.db')

def seed(count_per_topic=100):
    conn = get_db_connection()
    total_generated = 0
    total_topics = len(ISSUE_TYPES)
    
    print(f"🚀 Starting AI seed process: {total_topics} DevOps topics, {count_per_topic} scenarios each...")
    print("If Bedrock is active with AWS creds, this might take several minutes depending on the Bedrock API rate-limit.")
    print("--------------------------------------------------")
    
    # Create a mixed list of tasks so topics are generated randomly, not grouped sequentially
    tasks = []
    for issue in ISSUE_TYPES:
        for _ in range(count_per_topic):
            tasks.append(issue)
            
    random.shuffle(tasks)
    total_tasks = len(tasks)
    
    for i, issue in enumerate(tasks):
        lang = random.choice(LANGUAGES)
        diff = random.choice(DIFFICULTIES)
        
        # Generate the scenario via Bedrock (or mock fallback)
        data = generate_specific_scenario(lang, issue, diff)
        
        # Insert globally (user_id = NULL) so all users naturally see them
        conn.execute('''
            INSERT INTO scenarios (id, title, language, difficulty, issue_type, description, code_snippet, tags, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
        ''', (data['id'], data['title'], data['language'], data['difficulty'], data['issue_type'], data['description'], data['code_snippet'], json.dumps(data['tags'])))
        
        conn.commit()
        total_generated += 1
        print(f"  [{i+1}/{total_tasks}] Generated Topic: {issue} -> '{data['title']}' ({lang} / {diff})")
        
        # Briefly sleep to mitigate AWS rate limits (ThrottlingException) during bulk-generation
        time.sleep(0.3)

    conn.close()
    print(f"\n✅ Done! Successfully generated and inserted {total_generated} global scenarios.")

if __name__ == '__main__':
    seed(100)
