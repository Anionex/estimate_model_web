import os
import time
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import subprocess
import json
import re

# 初始化Flask
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置数据库
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:root@localhost/model_conversation"
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

        gpt_response = ask_gptmodel(messages)['response']

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
                'ovrall_rating': overall_avg_rate,
                }
    else:
        return jsonify({'error': 'Invalid session ID!'})


@app.route('/ask_xxmodel', methods=['POST'])
def ask_trip():
    data = request.json

    messages = next(item["content"] for item in data["query"] if item["role"] == "user")
    conversation_id = data.get('conversation_id')

    conversation = ModelEstimate.query.get(conversation_id)
    if conversation:

        trip_response = ask_tripadvisermodel(messages)
        trip_response_content = trip_response.get("itinerary")
        trip_response_rating=trip_response.get("rating info")

        attractions_avg_rate=trip_response_rating.get("Attractions")
        restaurant_avg_rate=trip_response_rating.get("Restaurants")
        accommodation_rate=trip_response_rating.get("Accommodations")
        overall_avg_rate=trip_response_rating.get("overall")

        conversation.xxmodel_response = trip_response_content
        db.session.commit()

        return {'xxmodel_response': trip_response_content,
                'attractionsAvgRating': attractions_avg_rate,
                'restaurantAvgRating': restaurant_avg_rate,
                'accommodationRating': accommodation_rate,
                'ovrall_rating': overall_avg_rate,
                }
    else:
        return jsonify({'error': 'Invalid  ID!'})


@app.route('/ask_ourmodel', methods=['POST'])
def ask_our():
    data = request.json
    query = data.get('query', "")
    conversation_id = data.get('conversation_id')

    conversation = ModelEstimate.query.get(conversation_id)

    if conversation:
        our_response = ask_ourmodel(query)
        print(our_response)
        db.session.commit()

        return jsonify(our_response)
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
    api_key = "sk-Vq0Rr2GKwXozgLGB5f156a75944b43719e6bD5EeD66e7784"
    api_base = "https://chatapi.onechats.top/v1"
    client = OpenAI(api_key=api_key, base_url=api_base)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
    )
    gpt_response = completion.choices[0].message.content
    return {"source": "gpt", "response": gpt_response}


def ask_tripadvisermodel(messages):
    try:
        input_data = messages
        env = os.environ.copy()
        env['AMADEUS_API_KEY'] = 'i6eqZP984Xmcpj6Fu16MGAA31cnWOy8j'
        env['AMADEUS_API_SECRET'] = 'Jxb1Zvr8uyhTtySy'
        env['SERPER_API_KEY'] = '110b1bf3a1e22a4c9b5cecba17514abf4209085c'
        env['GOOGLE_MAPS_API_KEY'] = 'AIzaSyDfbM-JakXbHcJoPei5eYuW6jIgvb95wdQ'

        try:
            result = subprocess.run(
                ['D:/code_libary/web_work/estimate_model_web/venv/Scripts/python.exe',
                 '../TravelPlanner-master/agents/tool_agents.py', input_data],
                capture_output=True,
                text=True,
                env=env,
                timeout=600
            )

            if result.returncode != 0:
                print("Error output:", result.stderr)
                raise Exception(f"Subprocess failed with return code {result.returncode}")

            output_data = result.stdout.strip()

            return output_data

        except subprocess.TimeoutExpired:
            return {"source": "xxmodel", "response": "Our server timed out, and something went wrong with our model."}

    except Exception as e:
        return str(e)


def ask_ourmodel(messages):
    try:
        input_data = messages
        print(input_data)
        env = os.environ.copy()
        env['AMADEUS_API_KEY'] = 'i6eqZP984Xmcpj6Fu16MGAA31cnWOy8j'
        env['AMADEUS_API_SECRET'] = 'Jxb1Zvr8uyhTtySy'
        env['SERPER_API_KEY'] = '110b1bf3a1e22a4c9b5cecba17514abf4209085c'
        env['GOOGLE_MAPS_API_KEY'] = 'AIzaSyDfbM-JakXbHcJoPei5eYuW6jIgvb95wdQ'
        env['OPENAI_API_KEY'] = 'sk-Vq0Rr2GKwXozgLGB5f156a75944b43719e6bD5EeD66e7784'
        env['OPENAI_API_BASE']='https://chatapi.onechats.top/v1'
        result = subprocess.run(
            ['D:/code_libary/web_work/estimate_model_web/venv/Scripts/python.exe',
             '../ItineraryAgent-master/planner_checker_system.py', input_data],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            timeout=600
        )

        if result.returncode != 0:
            print("Error output:", result.stderr)
            raise Exception(f"Subprocess failed with return code {result.returncode}")

        output_data = result.stdout.strip()

        return output_data

    except subprocess.TimeoutExpired:
        return {"source": "ourmodel", "response": "Our server timed out, and something went wrong with our model."}

    except Exception as e:
        return str(e)


if __name__ == '__main__':
    app.run(debug=True)
