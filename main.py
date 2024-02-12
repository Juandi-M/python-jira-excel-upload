# Import necessary libraries
import pandas as pd
# It seems that you've provided an empty code snippet. 
# Please provide the actual Python code that you would like to refactor.
from jira import JIRA
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_URL = os.getenv('JIRA_URL')
CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')

# Initialize OpenAI with the API key
openai.api_key = OPENAI_API_KEY

def generate_ticket_content(row):
    """Generates ticket content using the OpenAI API with a structured prompt."""
    prompt = f"""Given the data below, generate a concise Jira ticket that includes a Title, a Description, a Blocker, and Acceptance Criteria. Format your response with headings for each section.

Data:
- Feature: {row['Feature']}
- Detail: {row['Detail']}
- Urgency: {row['Urgency']}
- Additional Info: {row.get('Additional Info', 'N/A')}

Please format your response as follows:
Title: [Generated Title]
Description: [Generated Description]
Blocker: [Generated Blocker]
Acceptance Criteria: [Generated Acceptance Criteria]
"""
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.5,  # Adjusted for more predictable output
        max_tokens=256,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    return response.choices[0].text.strip()

def create_jira_ticket(description, title, blocker, acceptance_criteria):
    """Creates a ticket in Jira."""
    jira = JIRA(basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN), options={'server': JIRA_URL})
    issue_dict = {
        'project': {'key': JIRA_PROJECT_KEY},
        'summary': title,
        'description': description,
        'issuetype': {'name': 'Task'},
        # Add custom fields for blocker and acceptance criteria if needed
    }
    new_issue = jira.create_issue(fields=issue_dict)
    print(f"Created issue {new_issue.key}")

# Read the CSV file into a DataFrame
df = pd.read_csv(CSV_FILE_PATH)

# Iterate over each row in the DataFrame to process ticket creation
for index, row in df.iterrows():
    generated_content = generate_ticket_content(row)
    # Parsing the generated content to extract structured data
    # Assuming generated_content follows the requested format exactly
    sections = generated_content.split('\n')
    title = sections[1].split(': ')[1]
    description = sections[3].split(': ')[1]
    blocker = sections[5].split(': ')[1]
    acceptance_criteria = sections[7].split(': ')[1]
    
    # Create Jira ticket with the extracted information
    create_jira_ticket(description, title, blocker, acceptance_criteria)

