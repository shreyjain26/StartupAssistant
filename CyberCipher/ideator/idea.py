import os
import re
import autogen
import json
import time
from flask import Flask, render_template, request, jsonify, Response, Blueprint
from flask_sqlalchemy import SQLAlchemy
from autogen.agentchat import AssistantAgent, UserProxyAgent
import random


app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chats.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model for chat history
class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), nullable=False)
    agent = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Database model for chat sessions
class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(50), nullable=False, unique=True)
    session_name = db.Column(db.String(100), nullable=False, default="Untitled Chat")

# Create the database and tables
with app.app_context():
    db.create_all()

# Global list to store messages for SSE
app.sse_messages = []
app.active_sessions = {}  # Store active chat sessions and their agents

# Extract role messages from the assistant's response
def extract_role_messages(input_string):
    entries = input_string['content'].split('\n')
    role_message_dict = {}
    for entry in entries:
        pattern = r'^(\d+\.\s*\w+\s*\w*\s*\w*)\:\s*(.+)$'
        match = re.match(pattern, entry, re.DOTALL)
        if match:
            role, message = match.groups()
            role = re.sub(r'^\d+\.\s*', '', role)
            role = re.sub(r'\s', '_', role)
            role_message_dict[role] = message.strip()
    return role_message_dict

# Custom Trackable Assistant Agent
class TrackableAssistantAgent(AssistantAgent):
    def _process_message_before_send(self, message, recipient, silent):
        print(f"{self.name} processing message")
        
        message_content = message if isinstance(message, str) else message['content']
        app.sse_messages.append({"agent": self.name, "message": message_content, "session_id": app.current_session_id})
        
        chat_entry = ChatHistory(session_id=app.current_session_id, agent=self.name, message=message_content)
        db.session.add(chat_entry)
        db.session.commit()
        
        hook_list = self.hook_lists["process_message_before_send"]
        for hook in hook_list:
            message = hook(sender=self, message=message, recipient=recipient, silent=silent)
        
        return message

# Custom Trackable User Proxy Agent
class TrackableUserProxyAgent(UserProxyAgent):
    def _process_message_before_send(self, message, recipient, silent):
        print(f"{self.name} processing message")
        
        message_content = message if isinstance(message, str) else message['content']
        app.sse_messages.append({"agent": self.name, "message": message_content, "session_id": app.current_session_id})
        
        chat_entry = ChatHistory(session_id=app.current_session_id, agent=self.name, message=message_content)
        db.session.add(chat_entry)
        db.session.commit()
        
        hook_list = self.hook_lists["process_message_before_send"]
        for hook in hook_list:
            message = hook(sender=self, message=message, recipient=recipient, silent=silent)
        
        return message

config_list = autogen.config_list_from_json("model_config.json")

# Chat Session Manager
class ChatSessionManager:
    def __init__(self, session_id):
        self.session_id = session_id
        self.assistant = TrackableAssistantAgent(
            name="Assistant",
            llm_config={"config_list": config_list},
            system_message=(
                "You are a general manager who assigns tasks and your job is to identify which possible agents would be required for a prompt given by the user, try to add as many agents as you can since the tasks require insights from all angles. Assign additional agents only if explicitly asked by the user. Keep in mind that the format strictly is this, no other sentence should be present=> 1.assistant name: system message. The system message must describe what the agent is supposed to do, must be an instruction, and 1 can be replaced by the respective number and make sure there is no gap between assistant name and number."
            ),
        )
        self.user_proxy = TrackableUserProxyAgent(
            name="User",
            system_message="A human admin.",
            human_input_mode="NEVER",
            code_execution_config={"work_dir": "coding", "use_docker": False},
            max_consecutive_auto_reply=2,
        )
        self.manager = None
        self.assistants = []
        self.initialized = False
        self.groupchat = None

    def initialize_chat(self, user_input):
        if not self.initialized:
            result = self.assistant.generate_reply(messages=[{"content": user_input, "role": "user"}])
            roles = extract_role_messages(result)
            self.assistants = [self.user_proxy, self.assistant]
            
            for role, message in roles.items():
                new_assistant = TrackableAssistantAgent(
                    name=role,
                    llm_config={"config_list": config_list},
                    system_message=message,
                )
                self.assistants.append(new_assistant)

            self.assistant.update_system_message(
                "Act as a general manager that orchestrates the conversation and understand the user/user proxy, also provide a final summary of the chat."
            )

            self.groupchat = autogen.GroupChat(
                agents=self.assistants,
                messages=[],
                max_round=10,
                speaker_selection_method='round_robin'
            )
            self.manager = autogen.GroupChatManager(groupchat=self.groupchat, llm_config={"config_list": config_list})
            self.initialized = True

        return self.manager, self.assistants

    def continue_chat(self, user_input):
        if not self.initialized:
            return self.initialize_chat(user_input)
        
        # Add the user's message to the groupchat
        self.groupchat.messages.append({
            "role": "user",
            "content": user_input
        })
        
        return self.manager, self.assistants

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    session_id = request.json.get('session_id', 'default_session')
    app.current_session_id = session_id
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400
    
    # Get or create session
    if session_id not in app.active_sessions:
        app.active_sessions[session_id] = ChatSessionManager(session_id)
    
    session = app.active_sessions[session_id]
    
    # Initialize or continue chat based on session state
    if not session.initialized:
        manager, assistants = session.initialize_chat(user_input)
    else:
        manager, assistants = session.continue_chat(user_input)
    
    # Initiate chat without clearing history
    session.user_proxy.initiate_chat(
        manager,
        message=user_input,
        summary_method="reflection_with_llm",
        clear_history=False
    )
    
    # Return the list of agents for the active session
    agent_names = [agent.name for agent in assistants]
    return jsonify({"status": "Chat initiated", "agents": agent_names})

@app.route('/chat_stream')
def chat_stream():
    def generate():
        while True:
            if app.sse_messages:
                message_data = app.sse_messages.pop(0)
                if message_data["session_id"] == app.current_session_id:
                    # Skip displaying the user's input again
                    if message_data["agent"] != "User":
                        yield f"data: {json.dumps(message_data)}\n\n"
            else:
                time.sleep(0.1)
    
    return Response(generate(), content_type='text/event-stream')

@app.route('/new_chat', methods=['POST'])
def new_chat():
    session_id = request.json.get('session_id', f"session_{int(time.time())}")
    session_name = request.json.get('session_name', "Untitled Chat")
    app.current_session_id = session_id

    # Create a new chat session in the database
    new_session = ChatSession(session_id=session_id, session_name=session_name)
    db.session.add(new_session)
    db.session.commit()

    return jsonify({"status": "New chat session created", "session_id": session_id, "session_name": session_name})

@app.route('/load_chat', methods=['POST'])
def load_chat():
    session_id = request.json.get('session_id', 'default_session')
    chat_history = ChatHistory.query.filter_by(session_id=session_id).order_by(ChatHistory.timestamp).all()
    messages = [{"agent": entry.agent, "message": entry.message} for entry in chat_history]
    return jsonify({"status": "Chat history loaded", "messages": messages})

@app.route('/delete_chat', methods=['POST'])
def delete_chat():
    session_id = request.json.get('session_id')
    if not session_id:
        return jsonify({"error": "No session ID provided"}), 400

    # Delete chat history and session
    ChatHistory.query.filter_by(session_id=session_id).delete()
    ChatSession.query.filter_by(session_id=session_id).delete()
    db.session.commit()

    # Remove from active sessions if present
    if session_id in app.active_sessions:
        del app.active_sessions[session_id]

    return jsonify({"status": "Chat session deleted", "session_id": session_id})

@app.route('/rename_chat', methods=['POST'])
def rename_chat():
    session_id = request.json.get('session_id')
    new_name = request.json.get('new_name')
    if not session_id or not new_name:
        return jsonify({"error": "Session ID or new name not provided"}), 400

    # Rename the chat session
    session = ChatSession.query.filter_by(session_id=session_id).first()
    if session:
        session.session_name = new_name
        db.session.commit()
        return jsonify({"status": "Chat session renamed", "session_id": session_id, "new_name": new_name})
    else:
        return jsonify({"error": "Session not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)