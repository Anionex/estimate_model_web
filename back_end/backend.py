from datetime import datetime
import os
import textwrap
import time
from flask import Flask, request, jsonify, Response
from tenacity import retry, stop_after_attempt, wait_exponential, wait_fixed
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
from flask_migrate import Migrate
import hashlib  # 添加到文件顶部的导入部分
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, ".."))
from utils.jsonify_chat_model import get_json_response

MODEL_MAX_PROCESS_TIME = 1800
MODEL_FAIL_TO_COMPLETE_RESPONSE = {
    "itinerary": "Model failed to complete the task.",
    "average_rating": {
        "Attractions": None,
        "Restaurants": None,
        "Accommodations": None,
        "Overall": None
    },
    "expense_info": {
        "Unit": None,
        "Transportation": None,
        "Attractions": None,
        "Accommodation": None,
        "Dining": None,
        "Total": None
    }
}

MODEL_TIME_OUT_RESPONSE = {
    "itinerary": "Our model timed out.",
    "average_rating": {
        "Attractions": None,
        "Restaurants": None,
        "Accommodations": None,
        "Overall": None
    }
}
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
migrate = Migrate(app, db)

# 定义数据库模型
from sqlalchemy.sql import func

class ModelEstimate(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    question = db.Column(db.String(2000))
    
    # GPT相关字段
    gpt_response = db.Column(db.Text)
    gpt_overall_rating = db.Column(db.Integer)
    gpt_route_rationality_rating = db.Column(db.Integer)
    gpt_representativeness_rating = db.Column(db.Integer)
    
    # trip相关字段
    trip_response = db.Column(db.Text)
    trip_overall_rating = db.Column(db.Integer)
    trip_route_rationality_rating = db.Column(db.Integer)
    trip_representativeness_rating = db.Column(db.Integer)
    
    # xx model的费用字段
    trip_currency_unit = db.Column(db.String(10))
    trip_transportation_cost = db.Column(db.Float)
    trip_attractions_cost = db.Column(db.Float)
    trip_accommodation_cost = db.Column(db.Float)
    trip_dining_cost = db.Column(db.Float)
    trip_total_cost = db.Column(db.Float)
    
    # our model相关字段
    our_response = db.Column(db.Text)
    our_overall_rating = db.Column(db.Integer)
    our_route_rationality_rating = db.Column(db.Integer)
    our_representativeness_rating = db.Column(db.Integer)
    
    # our model的费用字段
    our_currency_unit = db.Column(db.String(10))
    our_transportation_cost = db.Column(db.Float)
    our_attractions_cost = db.Column(db.Float)
    our_accommodation_cost = db.Column(db.Float)
    our_dining_cost = db.Column(db.Float)
    our_total_cost = db.Column(db.Float)
    
    feedback = db.Column(db.String(2000))
    create_time = db.Column(db.DateTime, nullable=True, server_default=func.now())
    
    # Add new fields for level of details
    gpt_level_of_details = db.Column(db.Integer)
    our_level_of_details = db.Column(db.Integer)
    trip_level_of_details = db.Column(db.Integer)


@app.route('/start_session', methods=['POST'])
def start_session():
    # 创建一条新的记录
    new_conversation = ModelEstimate(
        question=request.json['query'],
        create_time=func.now()  
    )
    db.session.add(new_conversation)
    db.session.commit()

    # 返回新插入记录的 ID 作为 conversation_id
    return jsonify({"conversation_id": new_conversation.id})

from datetime import datetime, timedelta

@app.route('/is_query_available', methods=['POST'])
def is_query_available():
    """
    Check if the query can be processed by our model.
    The query is available only when:
    1. requested itinerary's time interval is between current date and 2 months later
    2. requested itinerary's duration is within 20 days
    """
    if DEBUG:
        return {}, 200
        
    data = request.json
    query = data.get('query')
    print("query: ", query)
    
    try:
        parsed_query = parse_query(query)
        if not parsed_query.get('is_a_itinerary_planning_request'):
            return jsonify({'error': 'Not an itinerary planning request'}), 400
            
        # Get dates from parsed query
        departure_str = parsed_query.get('departure_date')
        return_str = parsed_query.get('return_date')
        duration = parsed_query.get('duration')
        
        # Check duration constraint
        if duration and duration > 20:
            return jsonify({'error': 'Trip duration cannot exceed 20 days'}), 400
            
        # Check date constraints if dates are specified
        if departure_str != "Not specified" and return_str != "Not specified":
            departure_date = datetime.strptime(departure_str, "%Y-%m-%d").date()
            return_date = datetime.strptime(return_str, "%Y-%m-%d").date()
            
            current_date = datetime.now().date()
            two_months_later = current_date + timedelta(days=60)
            
            # check if the duration is consistent with the interval between departure and return dates
            if (return_date - departure_date + timedelta(days=1)).days != duration:
                return jsonify({'error': 'Duration does not match the interval between departure and return dates'}), 400
            
            if departure_date < current_date:
                return jsonify({'error': 'Departure date cannot be in the past'}), 400
                
            if departure_date > two_months_later:
                return jsonify({'error': 'Departure date cannot be more than 2 months in the future'}), 400
                
            if return_date < departure_date:
                return jsonify({'error': 'Return date must be after departure date'}), 400
                
    except Exception as e:
        return jsonify({'error': f"Error parsing query: {str(e)}"}), 500
        
    return jsonify({'message': 'Query is available!'}), 200

    

def parse_query(query) -> dict:
    output_format = textwrap.dedent("""
    {
        "is_a_itinerary_planning_request": bool,
        "departure_date": string,  // date in "YYYY-MM-DD" or "Not specified"
        "return_date": string,  // date in "YYYY-MM-DD" or "Not specified"
        "duration": number  // number of days
    }    
    """)
    return get_json_response(system_prompt=f"Your task is to parse the given itinerary planning request.current year: {datetime.now().year}.",
                             user_prompt=query,
                             output_format=output_format)



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

        conversation.trip_response = trip_response_content  # 使用正确的字段名
        db.session.commit()

        # 添加费用信息的保存
        expense_info = trip_response.get("expense_info", {})
        conversation.trip_currency_unit = expense_info.get("Unit")
        conversation.trip_transportation_cost = expense_info.get("Transportation")
        conversation.trip_attractions_cost = expense_info.get("Attractions")
        conversation.trip_accommodation_cost = expense_info.get("Accommodation")
        conversation.trip_dining_cost = expense_info.get("Dining")
        conversation.trip_total_cost = expense_info.get("Total")
        
        db.session.commit()
        
        return {
            'xxmodel_response': trip_response_content,
            'attractionsAvgRating': attractions_avg_rate,
            'restaurantAvgRating': restaurant_avg_rate,
            'accommodationRating': accommodation_rate,
            'overall_rating': overall_avg_rate,
            'expense_info': expense_info  # 添加费用信息到返回数据
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

        # 添加费用信息的保存
        expense_info = our_response.get("expense_info", {})
        conversation.our_currency_unit = expense_info.get("Unit")
        conversation.our_transportation_cost = expense_info.get("Transportation")
        conversation.our_attractions_cost = expense_info.get("Attractions")
        conversation.our_accommodation_cost = expense_info.get("Accommodation")
        conversation.our_dining_cost = expense_info.get("Dining")
        conversation.our_total_cost = expense_info.get("Total")
        
        db.session.commit()
        
        return {
            'our_response': our_response_content,
            'attractionsAvgRating': attractions_avg_rate,
            'restaurantAvgRating': restaurant_avg_rate,
            'accommodationRating': accommodation_rate,
            'overall_rating': overall_avg_rate,
            'expense_info': expense_info  # 添加费用信息到返回数据
        }
        
    else:
        return jsonify({'error': 'Invalid session ID!'}), 404


def safe_int(value):
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None

@app.route('/rate', methods=['POST'])
def rate():
    data = request.json
    if DEBUG:
        print("rate received data: ",data)
    conversation_id = data.get('conversation_id')
    gpt_ratings = data.get('gpt', {})
    our_model_ratings = data.get('ourmodel', {})
    xx_model_ratings = data.get('xxmodel', {})
    feedback = data.get("feedback", "")

    gpt_overall_rating = safe_int(gpt_ratings.get('overall_rating'))
    gpt_route_reasonability_rating = safe_int(gpt_ratings.get('route_reasonability_rating'))
    gpt_representative_rating = safe_int(gpt_ratings.get('representative_rating'))

    our_overall_rating = safe_int(our_model_ratings.get('overall_rating'))
    our_route_reasonability_rating = safe_int(our_model_ratings.get('route_reasonability_rating'))
    our_representative_rating = safe_int(our_model_ratings.get('representative_rating'))

    xx_overall_rating = safe_int(xx_model_ratings.get('overall_rating'))
    xx_route_reasonability_rating = safe_int(xx_model_ratings.get('route_reasonability_rating'))
    xx_representative_rating = safe_int(xx_model_ratings.get('representative_rating'))

    gpt_level_of_details = safe_int(gpt_ratings.get('level_of_details'))
    our_level_of_details = safe_int(our_model_ratings.get('level_of_details'))
    xx_level_of_details = safe_int(xx_model_ratings.get('level_of_details'))
    
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

        # Add new level of details assignments
        conversation.gpt_level_of_details = gpt_level_of_details
        conversation.our_level_of_details = our_level_of_details
        conversation.trip_level_of_details = xx_level_of_details

        conversation.feedback = feedback
        db.session.commit()
        return jsonify({'message': 'Rating saved successfully!'})
    else:
        return jsonify({'error': 'Invalid conversation ID!'}), 404



@retry(stop=stop_after_attempt(10), wait=wait_exponential(multiplier=1.5, min=3, max=120))
def ask_gptmodel(messages):
    if DEBUG:
        response = "test"
        return {"source": "gpt", "response": response}
    client = OpenAI(api_key=env.get('OPENAI_API_KEY'), base_url=env.get('OPENAI_API_BASE'))
    completion = client.chat.completions.create(
        model="gpt-4o-plus",
        messages=messages,
    )
    gpt_response = completion.choices[0].message.content
    return {"source": "gpt", "response": gpt_response}


def ask_tripadvisermodel(messages) -> dict:
    output = ""
    stdout, stderr = "", ""
    if DEBUG:
        return MODEL_FAIL_TO_COMPLETE_RESPONSE
    try:
        query = messages
        python_script = "../TravelPlanner-master/agents/tool_agents.py"
        process = subprocess.Popen(
            ['conda', 'run', '-n', 'estimate_web', 'python', python_script, query],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            shell=False  # 设置为False以避免shell解释
        )
        
        try:
            stdout, stderr = process.communicate(timeout=MODEL_MAX_PROCESS_TIME)
            save_model_output(query, stdout, stderr, "tripadviser")
            if process.returncode != 0:
                print("错误输出:", stderr)
                return MODEL_FAIL_TO_COMPLETE_RESPONSE
            output = stdout
            
        except subprocess.TimeoutExpired:
            kill_proc_tree(process.pid)  
            save_model_output(query, stdout, stderr, "tripadviser")
            return MODEL_TIME_OUT_RESPONSE
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
    output = ""
    stdout, stderr = "", ""
    # if DEBUG:
    #     time.sleep(3)
    #     return MODEL_FAIL_TO_COMPLETE_RESPONSE #tmp
    try:
        query = next(item["content"] for item in messages if item["role"] == "user")   
        print("input_data: ", query)
        
        python_script = "../ItineraryAgent-master/planner_checker_system.py"
        
        # 使用列表形式传递命令
        process = subprocess.Popen(
            ['conda', 'run', '-n', 'estimate_web', 'python', python_script, query],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            shell=False  # 设置为False以避免shell解释
        )
        
        try:
            stdout, stderr = process.communicate(timeout=MODEL_MAX_PROCESS_TIME)
            save_model_output(query, stdout, stderr, "ourmodel")
            if process.returncode != 0:
                kill_proc_tree(process.pid)
                print("Our model failed, traceback: \n", stderr)
                return MODEL_FAIL_TO_COMPLETE_RESPONSE
            output = stdout
            
        except subprocess.TimeoutExpired:
            kill_proc_tree(process.pid)  
            save_model_output(query, stdout, stderr, "ourmodel")
            return MODEL_TIME_OUT_RESPONSE
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

def save_model_output(query: str, stdout: str, stderr: str, model_name: str) -> None:
    """保存模型输出到文件"""
    # 生成query的MD5哈希值
    query_hash = hashlib.md5(query.encode()).hexdigest()
    
    # 创建logs目录（如果不存在）
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存stdout
    stdout_filename = f"{log_dir}/{model_name}_{query_hash}_{timestamp}_stdout.log"
    with open(stdout_filename, "w", encoding="utf-8") as f:
        f.write(f"Query: {query}\n\n")
        f.write(stdout)
    
    # 保存stderr（如果有）
    if stderr:
        stderr_filename = f"{log_dir}/{model_name}_{query_hash}_{timestamp}_stderr.log"
        with open(stderr_filename, "w", encoding="utf-8") as f:
            f.write(f"Query: {query}\n\n")
            f.write(stderr)

if __name__ == '__main__':
    app.run(debug=DEBUG, threaded=True)




