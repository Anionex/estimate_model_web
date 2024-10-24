import os
import time
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import subprocess
import json
import re
import dotenv
import psutil  
import signal
import platform
import traceback
from concurrent.futures import ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=10)
import asyncio

MODEL_MAX_PROCESS_TIME = 600

dotenv.load_dotenv()
env = os.environ.copy()
DEBUG = env.get('DEBUG') == 'True'
# 初始化Flask
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置数据库
if os.name == 'nt':
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:{env.get('DB_PASSWORD')}@localhost/modeltest"
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://modeltest:root@localhost/modeltest"
db = SQLAlchemy(app)


# 定义数据库模型
class ModelEstimate(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question = db.Column(db.String(2000))
    gpt_response = db.Column(db.String(4000))
    gpt_overall_rating = db.Column(db.Integer)
    gpt_route_rationality_rating = db.Column(db.Integer)
    gpt_representativeness_rating = db.Column(db.Integer)
    trip_response = db.Column(db.String(4000))
    trip_overall_rating = db.Column(db.Integer)
    trip_route_rationality_rating = db.Column(db.Integer)
    trip_representativeness_rating = db.Column(db.Integer)
    our_response = db.Column(db.String(4000))
    our_overall_rating = db.Column(db.Integer)
    our_route_rationality_rating = db.Column(db.Integer)
    our_representativeness_rating = db.Column(db.Integer)
    feedback = db.Column(db.String(2000))
    create_time = db.Column(db.DateTime)


@app.route('/start_session', methods=['POST'])
def start_session():
    # 创建一条新的记录
    new_conversation = ModelEstimate(question=request.json['query'])
    db.session.add(new_conversation)
    db.session.commit()

    # 返回新插入记录的 ID 作为 conversation_id
    return jsonify({"conversation_id": new_conversation.id})


@app.route('/ask_gpt', methods=['POST'])
def ask_gpt():
    data = request.json
    messages = data.get('query', [])
    conversation_id = data.get('conversation_id')

    conversation = ModelEstimate.query.filter_by(id=conversation_id).first()
    if conversation:
        conversation.question = messages[-1].get("content")
        db.session.commit()

        # 使用线程池异步执行
        future = executor.submit(ask_gptmodel, messages)
        gpt_response = future.result()['response']

        conversation.gpt_response = gpt_response

        accommodation_rating = re.search(r'Accommodation Rating: (\d)/5', gpt_response)
        attractions_rating = re.search(r'Attractions Average Rating: (\d)/5', gpt_response)
        restaurant_rating = re.search(r'Restaurant Average Rating: (\d)/5', gpt_response)
        overall_rating = re.search(r'Overall Rating: (\d)/5', gpt_response)

        accommodation_rate = accommodation_rating.group(1) if accommodation_rating else None
        attractions_avg_rate = attractions_rating.group(1) if attractions_rating else None
        restaurant_avg_rate = restaurant_rating.group(1) if restaurant_rating else None
        overall_avg_rate = overall_rating.group(1) if overall_rating else None

        db.session.commit()
        return {'gpt_response': gpt_response,
                'attractionsAvgRating': attractions_avg_rate,
                'restaurantAvgRating': restaurant_avg_rate,
                'accommodationRating': accommodation_rate,
                'overall_rating': overall_avg_rate,
                }
    else:
        return jsonify({'error': 'Invalid session ID!'})


@app.route('/ask_xxmodel', methods=['POST'])
def ask_trip():
    data = request.json
    print("ask_xxmodel received data: ",data)
    messages = next(item["content"] for item in data["query"] if item["role"] == "user")
    conversation_id = data.get('conversation_id')

    conversation = ModelEstimate.query.get(conversation_id)
    if conversation:

        # 使用线程池异步执行
        future = executor.submit(ask_tripadvisermodel, messages)
        trip_response = future.result()
        print("trip_response: ",trip_response)
        trip_response_content = trip_response.get("itinerary", "something went wrong")
        
        trip_response_rating=trip_response.get("average_rating", "something went wrong")

        attractions_avg_rate=trip_response_rating.get("Attractions")
        restaurant_avg_rate=trip_response_rating.get("Restaurants")
        accommodation_rate=trip_response_rating.get("Accommodations")
        overall_avg_rate=trip_response_rating.get("Overall")

        conversation.xxmodel_response = trip_response_content
        db.session.commit()

        return {'xxmodel_response': trip_response_content,
                'attractionsAvgRating': attractions_avg_rate,
                'restaurantAvgRating': restaurant_avg_rate,
                'accommodationRating': accommodation_rate,
                'overall_rating': overall_avg_rate,
                }
    else:
        return jsonify({'error': 'Invalid  ID!'})


@app.route('/ask_ourmodel', methods=['POST'])
def ask_our():
    data = request.json
    messages = data.get('query', "")
    conversation_id = data.get('conversation_id')

    conversation = ModelEstimate.query.get(conversation_id)

    if conversation:
        # 使用线程池异步执行
        future = executor.submit(ask_ourmodel, messages)
        our_response = future.result()
        print(our_response)
        
        
        our_response_content = our_response.get("itinerary")
        our_response_rating=our_response.get("average_rating")

        attractions_avg_rate=our_response_rating.get("Attractions")
        restaurant_avg_rate=our_response_rating.get("Restaurants")
        accommodation_rate=our_response_rating.get("Accommodations")
        overall_avg_rate=our_response_rating.get("Overall")

        conversation.our_response = our_response_content
        db.session.commit()
        our_response_content = our_response.get("itinerary")
        our_response_rating = our_response.get("rating info")

        return {'our_response': our_response_content,
                'attractionsAvgRating': attractions_avg_rate,
                'restaurantAvgRating': restaurant_avg_rate,
                'accommodationRating': accommodation_rate,
                'overall_rating': overall_avg_rate,
                }
        
    else:
        return jsonify({'error': 'Invalid session ID!'}), 404


@app.route('/rate', methods=['POST'])
def rate():
    data = request.json
    conversation_id = data.get('conversation_id')
    gpt_ratings = data.get('gpt', {})
    our_model_ratings = data.get('ourmodel', {})
    xx_model_ratings = data.get('xxmodel', {})
    feedback = data.get("feedback", "")

    gpt_overall_rating = gpt_ratings.get('overallRating')
    gpt_route_reasonability_rating = gpt_ratings.get('routeReasonabilityRating')
    gpt_representative_rating = gpt_ratings.get('representativeRating')

    our_overall_rating = our_model_ratings.get('overallRating')
    our_route_reasonability_rating = our_model_ratings.get('routeReasonabilityRating')
    our_representative_rating = our_model_ratings.get('representativeRating')

    xx_overall_rating = xx_model_ratings.get('overallRating')
    xx_route_reasonability_rating = xx_model_ratings.get('routeReasonabilityRating')
    xx_representative_rating = xx_model_ratings.get('representativeRating')

    conversation = ModelEstimate.query.get(conversation_id)
    if conversation:
        conversation.gpt_overall_rating = gpt_overall_rating
        conversation.gpt_route_rationality_rating = gpt_route_reasonability_rating
        conversation.gpt_representativeness_rating = gpt_representative_rating

        conversation.our_overall_rating = our_overall_rating
        conversation.our_route_rationality_rating = our_route_reasonability_rating
        conversation.our_representativeness_rating = our_representative_rating

        conversation.trip_overall_rating = xx_overall_rating
        conversation.trip_route_rationality_rating = xx_route_reasonability_rating
        conversation.trip_representativeness_rating = xx_representative_rating

        conversation.feedback = feedback
        db.session.commit()
        return jsonify({'message': 'Rating saved successfully!'})
    else:
        return jsonify({'error': 'Invalid conversation ID!'}), 404


def ask_gptmodel(messages):
    if DEBUG:
        return {"source": "gpt", "response": "test"}
    client = OpenAI(api_key=env.get('OPENAI_API_KEY'), base_url=env.get('OPENAI_API_BASE'))
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    gpt_response = completion.choices[0].message.content
    return {"source": "gpt", "response": gpt_response}


def ask_tripadvisermodel(messages) -> dict:
    if DEBUG:
        return {
        "itinerary": "Model failed to complete the task.",
        "average_rating": {
        "Attractions": None,
        "Restaurants": None,
        "Accommodations": None,
        "Overall": None
        }
    }
    try:
        # print("ask_tripadvisermodel received data: ",messages)
        # input_data = messages
        # query = next(item["content"] for item in input_data["query"] if item["role"] == "user")
        query = messages #todo need to fix the messages format problem
        python_script = "../TravelPlanner-master/agents/tool_agents.py"
        process = subprocess.Popen(
            f'conda run -n estimate_web python {python_script} "{query}"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        try:
            stdout, stderr = process.communicate(timeout=MODEL_MAX_PROCESS_TIME) 
            if process.returncode != 0:
                print("错误输出:", stderr)
                return {
                    "itinerary": "Model failed to complete the task.",
                    "average_rating": {
                        "Attractions": None,
                        "Restaurants": None,
                        "Accommodations": None,
                        "Overall": None
                    }
                }
            output = stdout
            
        except subprocess.TimeoutExpired:
            kill_proc_tree(process.pid)  # 确保杀死所有子进程
            process.kill()
            return {
                "itinerary": "Our model timed out.",
                "average_rating": {
                    "Attractions": None,
                    "Restaurants": None,
                    "Accommodations": None,
                    "Overall": None
                }
            }
        json_str = output.split("=====RETURN=====")[-1].strip()
        json_data = json.loads(json_str)
        return json_data

    except Exception as e:
        print("system stdout:", output)
        error_traceback = traceback.format_exc()  # 获取完整的堆栈跟踪
        print(f"Error in ask_tripadvisermodel:\n{error_traceback}")  # 打印详细错误信息
        return {
            "itinerary": f"Error occurred: {str(e)}\n",
            "average_rating": {
                "Attractions": None,
                "Restaurants": None,
                "Accommodations": None,
                "Overall": None
            }
        }

def ask_ourmodel(messages) -> dict:
    if DEBUG:
        return {
        "itinerary": "Model failed to complete the task.",
        "average_rating": {
        "Attractions": None,
        "Restaurants": None,
        "Accommodations": None,
        "Overall": None
        }
    }
    try:
        query = next(item["content"] for item in messages if item["role"] == "user")   
        print("input_data: ", query)
        
        python_script = "../ItineraryAgent-master/planner_checker_system.py"
        
        # 添加超时控制的装饰器
        process = subprocess.Popen(
            f'conda run -n estimate_web python {python_script} "{query}"' if platform.system() != "Windows" else
            f'conda run -n estimate_web python {python_script} "{query}"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        
        try:
            stdout, stderr = process.communicate(timeout=MODEL_MAX_PROCESS_TIME)
            if process.returncode != 0:
                kill_proc_tree(process.pid)
                return {
                    "itinerary": "Model failed to complete the task.",
                    "average_rating": {
                        "Attractions": None,
                        "Restaurants": None,
                        "Accommodations": None,
                        "Overall": None
                    }
                }
            output = stdout
            error = stderr
            
        except subprocess.TimeoutExpired:
            kill_proc_tree(process.pid)
            # 在 Linux/Mac 上额外杀死 python 进程
            if platform.system() != "Windows":
                subprocess.run("pkill -f 'python.*planner_checker_system.py'", shell=True)
            return {
                "itinerary": "Our model timed out.",
                "average_rating": {
                    "Attractions": None,
                    "Restaurants": None,
                    "Accommodations": None,
                    "Overall": None
                }
            }
        json_str = output.split("=====RETURN=====")[-1].strip()
        json_data = json.loads(json_str)
        return json_data

    except Exception as e:
        print("system stdout:", output)
        error_traceback = traceback.format_exc()  # 获取完整的堆栈跟踪
        print(f"Error in ask_ourmodel:\n{error_traceback}")  # 打印详细错误信息
        return {
            "itinerary": f"Error occurred: {str(e)}\n",
            "average_rating": {
                "Attractions": None,
                "Restaurants": None,
                "Accommodations": None,
                "Overall": None
            }
        }


def kill_proc_tree(pid):
    try:
        if platform.system() == "Windows":
            subprocess.run(f'taskkill /F /T /PID {pid}', shell=True)
        else:
            # Linux/Mac 系统
            subprocess.run(f'pkill -P {pid}', shell=True)
            os.kill(pid, signal.SIGKILL)
    except Exception as e:
        print(f"Kill process error: {e}")


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
