from flask import Flask, request, jsonify
from threading import Thread
import json

app = Flask(__name__)
received_data = []

def your_meeting_assistant(data): 
    from app1 import graph
    output_data = graph.invoke({
        "user_request": data
    })
    return output_data['final_output']

@app.route('/receive', methods=['POST'])
def receive():
    data = request.get_json()
    print(f"\n Received: {json.dumps(data, indent=2)}")
    new_data = your_meeting_assistant(data)  # Your AI Meeting Assistant Function Call
    received_data.append(data)
    # print(f"\n\n\n Sending:\n {json.dumps(new_data, indent=2)}")
    return jsonify(new_data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)