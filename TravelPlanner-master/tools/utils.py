import os
import sys
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
current_dir = os.path.dirname(__file__)
external_dir = os.path.abspath(os.path.join(current_dir, '..'))  
sys.path.append(external_dir)
from config import *
from langchain_community.utilities import GoogleSerperAPIWrapper
search = GoogleSerperAPIWrapper()
from agents.chat_model import OpenAIChat
from functools import lru_cache
search = GoogleSerperAPIWrapper()
llm = OpenAIChat(model="gpt-4o-2024-08-06")
# llm = OpenAIChat(model="gpt-4o-2024-08-06")
# llm.client = OpenAI(
#     api_key=os.getenv("GROQ_OPENAI_API_KEY"),
#     base_url=os.getenv("GROQ_OPENAI_API_BASE"),
# )
# llm.kwargs['model'] = "llama-3.2-90b-text-preview"



import requests
import json

@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def parse_itinerary(itinerary):
    parser = OpenAIChat(model='gpt-4o-2024-08-06', temperature=0)
    response, _ = parser.chat(prompt=itinerary, history=[], meta_instruction="Keep the Basic Information and itinerary sections as they are, remove other extraneous information, such as budget summaries. Do not output anything else!")
    return response

import concurrent.futures
@lru_cache()
@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def relavant_with_query(title,content, query):
    relavant_with_query_system_prompt = "You focus on determining whether information about the query is relavant to a given website. If possible, return 'yes', otherwise return 'no'. Do not output anything else!"
    # relavant_with_query_system_prompt = "You focus on determining whether a search result contains direct or indirect information about the query. If it does, return 'yes', otherwise return 'no'. Do not output anything else!"
    completion = llm.chat(f"query: {query}, website title: {title}", [], relavant_with_query_system_prompt)[0]
    # print("query:", query, "title:", title, "completion:", completion)
    return "yes" in completion.lower(), "query:"+query+"\ntitle:"+title+"\ncontent:"+content+"\ncompletion:"+completion+'\n'

@lru_cache()
@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def filter_search_results(search_results, query):
    extra_info = ""
    # only remain title and content 
    search_results = json.loads(search_results)['organic']
    # combine title and snippet
    short_search_results = []

    def process_result(result):
        result["snippet"] = result["snippet"].split("...")[0] + '...'
        judge, extra = relavant_with_query(result['title'], result['snippet'], query)
        if judge:
            return {
                "title": result['title'],
                "content": result['snippet']
            }, extra
        return None, None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_result, result) for result in search_results]
        for future in concurrent.futures.as_completed(futures):
            result, extra = future.result()
            if result:
                short_search_results.append(result)
                extra_info += extra

    return short_search_results, extra_info

@lru_cache()
@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def get_restaurant_average_cost(restaurant_name):
    extra_info = ""
    query = f"{restaurant_name} average cost 人均 价格"
    payload = json.dumps({
        "q": query,
        "num": SEARCH_NUM
    })
    response = requests.request("POST", "https://google.serper.dev/search", 
    headers={'X-API-KEY': os.getenv("SERPER_API_KEY"),'Content-Type': 'application/json'}, 
    data=payload)
    filtered_search_results, extra_info = filter_search_results(response.text, query) # filter title
    filtered_search_results = filtered_search_results[:SEARCH_REMAIN_NUM]
    # print("filtered_search_results:", str(filtered_search_results))
    extra_info += "\nfiltered search results: " + str(filtered_search_results)
    get_restaurant_average_cost_system_prompt = """You focus on extracting average cost information for a restaurant from web search results and returning the average cost data.
The final answer should be returned in JSON format, with the following schema:{"inference": "The inference process for determining the average cost in 20 words", "average_cost": "A number + currency unit expressing the average cost */person*.set it to $25 if no relevant information is found"}
If the currency type is not provided, please infer it from the search results context. Do not output anything other than the JSON format answer!return cost for a single person.if there is no such information, return '$25' rather than a uncertain range!
    """
    completion = llm.chat('average cost search results:\n' + str(filtered_search_results), [], get_restaurant_average_cost_system_prompt)[0]
    # print("completion:", completion)
    extra_info += "\ncompletion 2: " + completion + '\n'
    # 找 average_cost
    if not 'average_cost":' in completion:
        return "$25", extra_info
    return completion.split('average_cost":')[1].split('}')[0].strip().strip('"'), extra_info

@lru_cache()
@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
def get_entity_attribute(entity_name, attribute, default_value, extra_requirements="")->tuple[str, str]:
    """
    return the attribute value and extra information
    parameter:
        entity_name: the name of the entity
        attribute: the attribute to be extracted
        default_value: the default value if no relevant information is found
    """
    extra_info = ""
    query = f"{entity_name} {attribute} "
    payload = json.dumps({
        "q": query,
        "num": SEARCH_NUM
    })
    response = requests.request("POST", "https://google.serper.dev/search", 
    headers={'X-API-KEY': os.getenv("SERPER_API_KEY"),'Content-Type': 'application/json'}, 
    data=payload)
    filtered_search_results, extra_info = filter_search_results(response.text, query)
    # print("filtered_search_results:", str(filtered_search_results))
    filtered_search_results = filtered_search_results[:SEARCH_REMAIN_NUM]
    extra_info += f"\nFiltered search results: {str(filtered_search_results)}"
    
    get_attribute_system_prompt = f"""Your task is to extract information about the {attribute} of {entity_name} from web search results.
Please return the final answer in JSON format as follows: {{"inference": "Brief description of the inference process for determining the {attribute}", "{attribute}": "Extracted {attribute} information.Should be within 20 words"}}
If no relevant information is found, set it to "{default_value}". Do not output anything other than the JSON format answer!
{extra_requirements}   """
    completion = llm.chat(f'{attribute} search results:\n{str(filtered_search_results)}', [], get_attribute_system_prompt)[0]
    extra_info += f"\nCompletion result: {completion}\n"
    
    if not attribute in completion:
        return default_value, extra_info
    return completion.split(attribute+'":')[1].split('}')[0].strip().strip('"'), extra_info
from agents.prompts import *
from agents.chat_model import OpenAIChat
from agents.plan_checker import calculate_budget, calculate_rating, count_poi

check_llm = OpenAIChat(model="gpt-4o-2024-08-06", temperature=0, is_verbose=True)

def calculate_average_rating_for_raw(itinerary, query):
    """
    提取行程中的平均评分信息
    """
    rating_response, _ = check_llm.chat(prompt=f"Here is the itinerary:\n{itinerary}",
                                  history=[],
                                  meta_instruction=RATING_SUMMARY_SYSTEM_PROMPT)
    rating_info = calculate_rating(rating_response)
    
    poi_response, _ = check_llm.chat(prompt=f"Here is the itinerary:\n{itinerary}",
                               history=[],
                               meta_instruction=COUNT_POI_SYSTEM_PROMPT)
    poi_info = count_poi(poi_response)
    
    average_rating = {}
    categories = [
        ('Attractions', 'Total Attraction Ratings', 'Total Attractions'),
        ('Accommodations', 'Total Accommodation Ratings', 'Total Accommodations'),
        ('Restaurants', 'Total Restaurant Ratings', 'Total Restaurants'),
        ('Overall', 'Total', 'Total')
    ]
    
    for category, rating_key, count_key in categories:
        total_rating = rating_info[rating_key]
        total_count = poi_info[count_key]
        
        average_rating[category] = round(total_rating / total_count, 2) if total_count > 0 else 0.0
    
    return average_rating

def calculate_budget_for_raw(itinerary, query, extra_requirements=''):
    """
    提取行程中的预算信息
    """
    sys_prompt = PLAN_CHECKER_PROMPT_BUDGET.format(extra_requirements=extra_requirements, query=query)
    history = []
    response, history = check_llm.chat(prompt=itinerary, history=history, meta_instruction=sys_prompt)
    
    expense_info = calculate_budget(response)
    return expense_info

def count_poi_for_raw(itinerary, query):
    """
    计算行程中的兴趣点数量
    """
    response, _ = check_llm.chat(prompt=f"Here is the itinerary:\n{itinerary}",
                           history=[],
                           meta_instruction=COUNT_POI_SYSTEM_PROMPT)
    poi_info = count_poi(response)
    return poi_info

# Usage examples
if __name__ == "__main__":
    # print(get_restaurant_average_cost("丰源轩"))
    # print(get_entity_attribute("Fengyuanxuan", "average cost", "$25")[0])
    # print(str(get_entity_attribute("Great Wall", "location description", "No relevant information found")[1]))
    response, extra_info = get_entity_attribute("飞牌", "起源", "no information")
    print(response)
    print(extra_info)
    # print(get_entity_attribute("Beijing Hilton Hotel", "accommodation requirements", "No relevant information found")[0])
