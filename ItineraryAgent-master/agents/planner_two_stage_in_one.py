import sys
import os
print(os.getcwd())
print(os.path.join(os.getcwd(), "tools"))
sys.path.append(os.path.abspath(os.getcwd()))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "tools")))
sys.path.append(os.path.join(os.getcwd(), "ItineraryAgent-master"))
print(os.path.join(os.getcwd(), "ItineraryAgent-master"))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from agents.react_agent import ReactAgent
from prompts import REACT_PLANNER_PROMPT_TWO_STAGE_IN_ONE
from tool_funcs import *
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, root_dir)
from utils.config import *
planner_two_stage_in_one = ReactAgent(model="gpt-4o", stop=['>']) # import this


# planner_two_stage_in_one.tools.add_tool(
#     name_for_human="calculator",
#     name_for_model="calculator",
#     func=calculator,
#     description="Used whenever you need to perform mathematical calculations.",
#     parameters=[
#         {
#             'name': 'expression',
#             'description': 'Arithmetic expression that may include parentheses',
#         }
#     ]
# )  
# planner_two_stage_in_one.tools.add_tool(
#     name_for_human="Get Recommend City",
#     name_for_model="get_recommend_city",
#     func=get_recommend_city,
#     description="Used whenever you need to retrieve information about recommended cities for a specified province/country/area.Must be used when the user does not specify the city.",
#     parameters=[
#         {
#             'name': 'area',
#             'description': 'Area name',
#         }
#     ]
# )

planner_two_stage_in_one.tools.add_tool(
    name_for_human="google search",
    name_for_model="google_search",
    func=google_search,
    description="A general search engine for accessing the internet. Commonly used when other tools cannot obtain information.Never use it unless absolutely necessary.",
    parameters=[
        {
            'name': 'search_query',
            'description': 'Search keywords or phrases',
        },
        {
            'name': 'gl',
            'description': 'Which country\'s internet content do you prefer to search, such as "China"',
        }
    ]
)   
planner_two_stage_in_one.tools.add_tool(
    name_for_human="Get Attraction Information",
    name_for_model="get_attractions",
    func=get_attractions,
    description="Used whenever you need to retrieve information about major attractions in a specified city.",
    parameters=[
        {
            'name': 'city',
            'description': 'City name',
        },
        {
            'name': 'query',
            'required': False,
            'description': 'Search keywords or phrases.Example: amusement parks',
            'default': 'must-visit attractions',
        }
    ]
)
planner_two_stage_in_one.tools.add_tool(
    name_for_human="Get Restaurant Information",
    name_for_model="get_restaurants",
    func=get_restaurants,
    description="Used whenever you need to retrieve restaurant recommendations for a specified city.",
    parameters=[
        {
            'name': 'city',
            'description': 'City name',
        },
        {
            'name': 'query',
            'required': False,
            'description': 'Search keywords or phrases.Example: chinese restuarants',
            'default': 'must-visit restaurants',
        }
    ]
)
planner_two_stage_in_one.tools.add_tool(
        name_for_human="获取住宿信息",
        name_for_model="get_accommodations",
        func=get_accommodations,
        description="Used whenever you need to retrieve accommodation options for a specified city, check-in date, check-out date, and number of adults.",
        parameters=[
            {
                'name': 'city',
                'description': '城市名称',
            },
            {
                'name': 'check_in_date',
                'description': '入住日期',
            },
            {
                'name': 'check_out_date',
                'description': '退房日期',
            },
            {
                'name': 'adults',
                'description': '成人数量',
                'schema': {'type': 'integer'},
            },
            {
                "name": "min_price",
                "description": "筛选的最低价格，不指定时默认为零",
                'schema': {'type': 'integer'},
            },
            {
                "name": "max_price",
                "description": "筛选的最高价格，不指定时默认为无上限",
                'schema': {'type': 'integer'},
            }
        
        ]
    )
planner_two_stage_in_one.tools.add_tool(
    name_for_human="Get Flight Information",
    name_for_model="get_flights",
    func=get_flights,
    description="Used whenever you need to retrieve flight information for specified origin, destination, and date.",
    parameters=[
        {
            'name': 'origin',
            'description': 'the *IATA code* of departure city',
        },
        {
            'name': 'destination',
            'description': 'the *IATA code* of destination city',
        },
        {
            'name': 'departure_date',
            'description': 'Departure date in YYYY-MM-DD format',
        }
    ]
)
planner_two_stage_in_one.tools.add_tool(
    name_for_human="Get Distance and Time Information",
    name_for_model="get_google_distance_matrix",
    func=get_google_distance_matrix,
    description="Used whenever you need to retrieve distance or travel time information between two locations.",
    parameters=[
        {
            'name': 'origin',
            'description': 'Starting point',
        },
        {
            'name': 'destination',
            'description': 'End point',
        },
        {
            'name': 'mode',
            'description': 'Mode of transportation, such as driving, walking, bicycling, or transit',
        }
    ]
) 

# init scratchpad content
planner_two_stage_in_one.scratchpad = PLANNER_BEGIN_WORDS
if __name__ == '__main__':

    # result = agent.run("马斯克发射了多少颗卫星？")
    #result = agent.run(input("请输入问题："), extra_requirements=input("请输入额外要求："))
    # result = planner_two_stage_in_one.run(
    #     "Please help me plan a trip from St. Petersburg to Rockford spanning 3 days from March 16th to March 18th, 2022. The travel should be planned for a single person with a budget of $1,700.", 
    #     # extra_requirements="请使用中文输出",
    #     system_prompt=REACT_PLANNER_PROMPT_TWO_STAGE_IN_ONE)
    planner_two_stage_in_one.tools.execute_tool(
        "get_accommodations", 
        city="Rockford", 
        check_in_date="2025-04-26",    # 需要提供具体日期
        check_out_date="2024-04-30",   # 需要提供具体日期
        adults=1,                       # 需要提供人数
        min_price=0, 
        max_price=200
    )
    # print(result)