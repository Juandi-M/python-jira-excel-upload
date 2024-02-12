import pandas as pd
from jira import JIRA
import os
import sys

def load_env():
    env_vars = {}
    with open('env.txt', 'r') as file:
        for line in file:
            parts = line.strip().split('=', 1)
            if len(parts) == 2:
                key, value = parts
                if key in env_vars:
                    print(f"Warning: Duplicate environment variable '{key}' found. Using the latest value.")
                env_vars[key] = value
    return env_vars

env_vars = load_env()

JIRA_API_TOKEN = env_vars.get('JIRA_API_TOKEN')
JIRA_EMAIL = env_vars.get('JIRA_EMAIL')
JIRA_URL = env_vars.get('JIRA_URL')
CSV_FILE_PATH = env_vars.get('CSV_FILE_PATH')
JIRA_PROJECT_KEY = env_vars.get('JIRA_PROJECT_KEY')
JIRA_REPORTER_ACCOUNT_ID = env_vars.get('JIRA_REPORTER_ACCOUNT_ID')

try:
    jira = JIRA(basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN), options={'server': JIRA_URL})
except Exception as e:
    raise Exception(f"Failed to connect to JIRA due to: {e}")

def prompt_for_environment():
    env_options = {
        '1': 'DEV',
        '2': 'QA',
        '3': 'STAGING',
        '4': 'PROD'
    }
    for _ in range(3):
        for key, value in env_options.items():
            print(f"{key}. {value}")
        choice = input("Enter your choice (1-4): ")
        if choice.isdigit() and choice in env_options:
            return env_options[choice]
        print("Invalid input. Please enter a number between 1 and 4.")
    raise ValueError("Maximum attempts reached. Exiting.")

def load_csv_file(csv_file_path):
    try:
        df = pd.read_csv(csv_file_path)
        required_columns = ['APPLICATION NAME', 'Uploaded to Jira'] + [f'STORY {i}' for i in range(1, 6)]
        if not all(column in df.columns for column in required_columns):
            raise ValueError("CSV file is missing required columns.")
        return df
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found at {csv_file_path}")
    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty.")
    except pd.errors.ParserError:
        raise ValueError("CSV file is corrupt or improperly formatted.")
    except Exception as e:
        raise Exception(f"An unexpected error occurred while loading the CSV file: {e}")

def parse_story_details(story_text):
    details = {'title': '', 'epic': '', 'description': '', 'blockers': '', 'acceptance_criteria': ''}
    current_section = ''
    
    lines = story_text.split('\n')
    for line in lines:
        if line.startswith('TITLE:'):
            current_section = 'title'
        elif line.startswith('EPIC:'):
            current_section = 'epic'
        elif line.startswith('Description:'):
            current_section = 'description'
        elif line.startswith('Blockers:'):
            current_section = 'blockers'
        elif line.startswith('Acceptance Criteria:'):
            current_section = 'acceptance_criteria'
        else:
            if current_section:
                details[current_section] += line.strip()
                
        if current_section and line.startswith(current_section.split(':')[0] + ':'):
            details[current_section] = line.split(':', 1)[1].strip()
            
    return details

def get_parent_key(epic_name):
    epic_to_parent = {
        'Infrastructure for pipelines': 'AI-425',
        'AWS Native Secret Manager solution': 'AI-367',
        'CICD Pipelines': 'AI-331'
    }
    return epic_to_parent.get(epic_name)

def create_jira_ticket(application_name, story_details, env):
    parsed_details = parse_story_details(story_details)
    parent_key = get_parent_key(parsed_details['epic'])
    
    if parent_key is None:
        print(f"Warning: No parent key found for epic '{parsed_details['epic']}'")
        return False
    
    description = f"Epic: {parsed_details['epic']}\n\n" \
                  f"Description: {parsed_details['description']}\n\n" \
                  f"Blockers: {parsed_details['blockers']}\n\n" \
                  f"Acceptance Criteria: {parsed_details['acceptance_criteria']}"
    
    issue_dict = {
        'project': {'key': JIRA_PROJECT_KEY},
        'summary': f"[{env}] {parsed_details['title']}",
        'description': description,
        'issuetype': {'name': 'Task'},
        'reporter': {'accountId': JIRA_REPORTER_ACCOUNT_ID},
        'labels': ['TechTeam', 'DevOps'],
        'parent': {'key': parent_key},
    }
    
    try:
        new_issue = jira.create_issue(fields=issue_dict)
        print(f"Created issue {new_issue.key} for '{application_name}' in '{env}' environment, linked to parent '{parent_key}'.")
        return True
    except Exception as e:
        print(f"Failed to create issue for '{application_name}' in '{env}' due to: {e}")
        return False

def main():
    try:
        df = load_csv_file(CSV_FILE_PATH)
    except Exception as e:
        print(e)
        return

    try:
        selected_env = prompt_for_environment()
    except ValueError as e:
        print(e)
        return
    
    for index, row in df.iterrows():
        uploaded_to_jira = row.get('Uploaded to Jira')
        if pd.notnull(uploaded_to_jira) and f"Yes: {selected_env}" in uploaded_to_jira:
            print(f"Skipping row {index} as it has already been uploaded to JIRA for the '{selected_env}' environment.")
            continue

        application_name = row.get('APPLICATION NAME')
        if pd.isnull(application_name):
            print(f"Skipping row {index} due to missing 'APPLICATION NAME'.")
            continue

        for story_number in range(1, 6):
            story_column_name = f"STORY {story_number}"
            story_details = row.get(story_column_name)
            if pd.notnull(story_details) and selected_env in row.get(selected_env):
                create_jira_ticket(application_name, story_details, selected_env)

if __name__ == "__main__":
    main()