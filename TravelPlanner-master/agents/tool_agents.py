import re, string, os, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../agents")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "tools/planner")))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "../tools/planner")))


os.environ['OUTPUT_DIR'] = './outputs'
os.environ['MODEL_NAME'] = 'gpt-4o-2024-08-06-mini'
os.environ['OPENAI_API_KEY'] = 'sk-Opz25zl4iSRoXnwF87350eC7E5B9494bA3BfFfF4243c4331'
os.environ['OPENAI_API_BASE'] = 'https://chatapi.onechats.top/v1'
os.environ['GOOGLE_API_KEY'] = '1'
os.environ['SET_TYPE'] = 'validation'
import importlib
from typing import List, Dict, Any
import tiktoken
from pandas import DataFrame
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback
from langchain.llms.base import BaseLLM
from langchain.prompts import PromptTemplate
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
from agents.prompts import zeroshot_react_agent_prompt
from utils.func import load_line_json_data, save_file
import sys
import json
import openai
import time
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from langchain_google_genai import ChatGoogleGenerativeAI
import argparse
from datasets import load_dataset
import os

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']


pd.options.display.max_info_columns = 200

os.environ['TIKTOKEN_CACHE_DIR'] = './tmp'

actionMapping = {"FlightSearch":"flights","AttractionSearch":"attractions","GoogleDistanceMatrix":"googleDistanceMatrix","AccommodationSearch":"accommodation","RestaurantSearch":"restaurants","Planner":"planner","NotebookWrite":"notebook","CitySearch":"cities"}

class CityError(Exception):
    pass

class DateError(Exception):
    pass


from openai import APIError, RateLimitError, APIConnectionError, AuthenticationError
def catch_openai_api_error(): 
    error = sys.exc_info()[0]
    if error == APIConnectionError:
        print("APIConnectionError")
    elif error == RateLimitError:
        print("RateLimitError")
        time.sleep(60)
    elif error == APIError:
        print("APIError")
    elif error == AuthenticationError:
        print("AuthenticationError")
    else:
        print("API error:", error)

class ReactAgent:
    def __init__(self,
                 args,
                 mode: str = 'zero_shot',
                 tools: List[str] = None,
                 max_steps: int = 300,
                 max_retries: int = 5,
                 illegal_early_stop_patience: int = 30,
                 react_llm_name = 'gpt-4o-2024-08-06',
                 planner_llm_name = 'gpt-4o-2024-08-06',
                #  logs_path = '../logs/',
                 city_file_path = '../database/background/citySet.txt'
                 ) -> None: 

        self.answer = ''
        self.max_steps = max_steps
        self.mode = mode

        self.react_name = react_llm_name
        self.planner_name = planner_llm_name

        if self.mode == 'zero_shot':
            # langchain的带输入变量的prompt
            # 此处需要两个变量，query（查询计划）和scratchpad（上下文）            
            self.agent_prompt = zeroshot_react_agent_prompt

        self.json_log = []

        self.current_observation = ''
        self.current_data = None

        if 'gpt-3.5' in react_llm_name:
            # 设置停止词，遇到停止词就停止生成，因此每次生成一行
            stop_list = ['\n']
            self.max_token_length = 15000
            self.llm = ChatOpenAI(temperature=0, # 改为0，最大程度防止不一样
                     model_name=react_llm_name,
                     openai_api_key=OPENAI_API_KEY,
                     model_kwargs={"stop": stop_list})
            
        elif 'gpt-4' in react_llm_name:
            stop_list = ['\n']
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     model_name=react_llm_name,
                     openai_api_key=OPENAI_API_KEY,
                     model_kwargs={"stop": stop_list})
            
        elif react_llm_name in ['mistral-7B-32K']:
            stop_list = ['\n']
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=256,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo",
                     model_kwargs={"stop": stop_list})
            
        elif react_llm_name in ['mixtral']:
            stop_list = ['\n']
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=256,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo",
                     model_kwargs={"stop": stop_list})
            
        elif react_llm_name in ['ChatGLM3-6B-32K']:
            stop_list = ['\n']
            self.max_token_length = 30000
            self.llm = ChatOpenAI(
                     temperature=0,
                     max_tokens=256,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo",
                     model_kwargs={"stop": stop_list})
        
        elif react_llm_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-pro",google_api_key=GOOGLE_API_KEY)
            self.max_token_length = 30000


        self.illegal_early_stop_patience = illegal_early_stop_patience

        self.tools = self.load_tools(tools, planner_model_name=planner_llm_name)
        
        # 应用monkey patch
        self.apply_monkey_patches()
        
        self.max_retries = max_retries
        self.retry_record = {key: 0 for key in self.tools}
        self.retry_record['invalidAction'] = 0

        # print(self.retry_record)

        self.last_actions = []

        # self.log_path = logs_path + datetime.now().strftime('%Y%m%d%H%M%S') + '.out'
        # self.log_file = open(self.log_path, 'a+')

        # print("logs will be stored in " + self.log_path)

        self.city_set = self.load_city(city_set_path=city_file_path)

        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        self.__reset_agent()

    def run(self, query, reset=True) -> None:

        self.query = query
        
        if reset:
            self.__reset_agent()

        while not self.is_halted() and not self.is_finished():
            self.step()

        return self.answer, self.scratchpad, self.json_log

    def step(self) -> None:

        self.json_log.append({"step": self.step_n, "thought":"",
                              "action": "", "observation": "", "state":""})
        # Thought
        # 获取模型生成的下一个Thought
        self.scratchpad += f'\nThought {self.step_n}:'
        self.scratchpad += ' ' + self.prompt_agent()

        print(self.scratchpad.split('\n')[-1])
        self.json_log[-1]['thought'] = self.scratchpad.split('\n')[-1].replace(f'\nThought {self.step_n}:',"")
        # self.log_file.write(self.scratchpad.split('\n')[-1] + '\n')


        # Act
        self.scratchpad += f'\nAction {self.step_n}:'
        # 获取模型生成的下一个action，如"Action x: FlightSearch[Los Angeles, San Francisco, 2022-12-12]"
        action = self.prompt_agent()

        import re

        # 使用正则表达式移除可能的前缀
        def remove_prefixes(text):
            # 这个模式匹配 "Action", "Thought", 或 "Observation"，
            # 后面可能跟着任意数字，然后是冒号和可能的空白
            pattern = r'^(Action|Thought|Observation)(\s*\d*\s*:)?\s*'
            return re.sub(pattern, '', text, flags=re.IGNORECASE)

        action = remove_prefixes(action)
                
        if action == None or action == '' or action == '\n':
            self.scratchpad += " Your action is filtered due to content. Please make sure your action does not start with ['\\n', 'Thought', 'Action', 'Observation'] and assume all the actions are permitted in this environment and take the action again."
        else:
            self.scratchpad += ' ' + action


        if len(self.last_actions) > 0 and self.last_actions[-1] != action:
            self.last_actions.clear()

        # refresh last_action list
        self.last_actions.append(action)

        self.json_log[-1]['action'] = self.scratchpad.split('\n')[-1].replace(f'\nAction {self.step_n}:',"")


        # examine if the same action has been repeated 3 times consecutively
        # if len(self.last_actions) == 3:
        #     print("The same action has been repeated 3 times consecutively. So we stop here.")
        #     # self.log_file.write("The same action has been repeated 3 times consecutively. So we stop here.")
        #     self.json_log[-1]['state'] = 'same action 3 times repeated'
        #     self.finished = True
        #     return


        # action_type, action_arg = parse_action(action)
        print(self.scratchpad.split('\n')[-1])
        # self.log_file.write(self.scratchpad.split('\n')[-1]+'\n')

        # Observe
        self.scratchpad += f'\nObservation {self.step_n}: '

        if action == None or action == '' or action == '\n':
            action_type = None 
            action_arg = None
            self.scratchpad += "No feedback from the environment due to the null action. Please make sure your action does not start with [Thought, Action, Observation]."
        
        else:
             # 解析模型采取的Action，并尝试获得反馈
            action_type, action_arg = parse_action(action)
            
            if action_type != "Planner":
                if action_type in actionMapping:
                    pending_action = actionMapping[action_type]
                elif action_type not in actionMapping:
                    pending_action = 'invalidAction'
                
                if pending_action in self.retry_record:
                    if self.retry_record[pending_action] + 1 > self.max_retries:
                        action_type = 'Planner'
                        print(f"{pending_action} early stop due to {self.max_retries} max retries.")
                        # self.log_file.write(f"{pending_action} early stop due to {self.max_retries} max retries.")
                        self.json_log[-1]['state'] = f"{pending_action} early stop due to {self.max_retries} max retries."
                        self.finished = True
                        return
                    
                elif pending_action not in self.retry_record:
                    if self.retry_record['invalidAction'] + 1 > self.max_retries:
                        action_type = 'Planner'
                        print(f"invalidAction Early stop due to {self.max_retries} max retries.")
                        # self.log_file.write(f"invalidAction early stop due to {self.max_retries} max retries.")
                        self.json_log[-1]['state'] = f"invalidAction early stop due to {self.max_retries} max retries."
                        self.finished = True
                        return

            if action_type == 'FlightSearch': 
                try:
                    if validate_date_format(action_arg.split(', ')[2]) and validate_city_format(action_arg.split(', ')[0],self.city_set ) and validate_city_format(action_arg.split(', ')[1],self.city_set):
                        self.scratchpad = self.scratchpad.replace(to_string(self.current_data).strip(),'Masked due to limited length. Make sure the data has been written in Notebook.')
                        self.current_data = self.tools['flights'].run(action_arg.split(', ')[0], action_arg.split(', ')[1], action_arg.split(', ')[2])
                        self.current_observation = str(to_string(self.current_data))
                        self.scratchpad += self.current_observation 
                        self.__reset_record()
                        self.json_log[-1]['state'] = f'Successful'
                # 错误处理，告诉模型错在哪儿
                except DateError:
                    self.retry_record['flights'] += 1
                    self.current_observation = f"'{action_arg.split(', ')[2]}' is not in the format YYYY-MM-DD"
                    self.scratchpad += f"'{action_arg.split(', ')[2]}' is not in the format YYYY-MM-DD"
                    self.json_log[-1]['state'] = f'Illegal args. DateError'

                except ValueError as e:
                    self.retry_record['flights'] += 1
                    self.current_observation = str(e)
                    self.scratchpad += str(e)
                    self.json_log[-1]['state'] = f'Illegal args. City Error'

                except Exception as e:
                    print(e)
                    self.retry_record['flights'] += 1
                    self.current_observation = f'Illegal Flight Search. Please try again.'
                    self.scratchpad += f'Illegal Flight Search. Please try again.'
                    self.json_log[-1]['state'] = f'Illegal args. Other Error'

            elif action_type == 'AttractionSearch': # add field query for run

                try:
                    if validate_city_format(action_arg, self.city_set):
                        self.scratchpad = self.scratchpad.replace(to_string(self.current_data).strip().strip(),'Masked due to limited length. Make sure the data has been written in Notebook.')
                        self.current_data = self.tools['attractions'].run(action_arg.split(', ')[0], action_arg.split(', ')[1])
                        self.current_observation = to_string(self.current_data).strip('\n').strip()
                        self.scratchpad += self.current_observation
                        self.__reset_record()
                        self.json_log[-1]['state'] = f'Successful'
                except ValueError as e:
                    self.retry_record['attractions'] += 1
                    self.current_observation = str(e)
                    self.scratchpad += str(e)
                    self.json_log[-1]['state'] = f'Illegal args. City Error'
                except Exception as e:
                    print(e)
                    self.retry_record['attractions'] += 1
                    self.current_observation = f'Illegal Attraction Search. Please try again.'
                    self.scratchpad += f'Illegal Attraction Search. Please try again.'
                    self.json_log[-1]['state'] = f'Illegal args. Other Error'

            elif action_type == 'AccommodationSearch': # add field checkin date checkout date adults for run

                try:
                    if validate_city_format(action_arg, self.city_set):
                        self.scratchpad = self.scratchpad.replace(to_string(self.current_data).strip().strip(),'Masked due to limited length. Make sure the data has been written in Notebook.')
                        self.current_data = self.tools['accommodations'].run(action_arg.split(', ')[0], action_arg.split(', ')[1], action_arg.split(', ')[2], action_arg.split(', ')[3])
                        self.current_observation = to_string(self.current_data).strip('\n').strip()
                        self.scratchpad += self.current_observation
                        self.__reset_record()
                        self.json_log[-1]['state'] = f'Successful'
                except ValueError as e :
                    self.retry_record['accommodations'] += 1
                    self.current_observation = str(e)
                    self.scratchpad += str(e)
                    self.json_log[-1]['state'] = f'Illegal args. City Error'
                except Exception as e:
                    print(e)
                    self.retry_record['accommodations'] += 1
                    self.current_observation = f'Illegal Accommodation Search. Please try again.'
                    self.scratchpad += f'Illegal Accommodation Search. Please try again.'
                    self.json_log[-1]['state'] = f'Illegal args. Other Error'

            elif action_type == 'RestaurantSearch': # add field query for run

                try:
                    if validate_city_format(action_arg, self.city_set):
                        self.scratchpad = self.scratchpad.replace(to_string(self.current_data).strip().strip(),'Masked due to limited length. Make sure the data has been written in Notebook.')
                        self.current_data = self.tools['restaurants'].run(action_arg.split(', ')[0], action_arg.split(', ')[1])
                        self.current_observation = to_string(self.current_data).strip()
                        self.scratchpad += self.current_observation
                        self.__reset_record()
                        self.json_log[-1]['state'] = f'Successful'

                except ValueError as e:
                    self.retry_record['restaurants'] += 1
                    self.current_observation = str(e)
                    self.scratchpad += str(e)
                    self.json_log[-1]['state'] = f'Illegal args. City Error'

                except Exception as e:
                    print(e)
                    self.retry_record['restaurants'] += 1
                    self.current_observation = f'Illegal Restaurant Search. Please try again.'
                    self.scratchpad += f'Illegal Restaurant Search. Please try again.'
                    self.json_log = f'Illegal args. Other Error'
                    
            elif action_type == "CitySearch":
                try:
                    self.scratchpad = self.scratchpad.replace(to_string(self.current_data).strip(),'Masked due to limited length. Make sure the data has been written in Notebook.')
                    # self.current_data = self.tools['cities'].run(action_arg)
                    self.current_observation = to_string(self.tools['cities'].run(action_arg)).strip()
                    self.scratchpad += self.current_observation
                    self.__reset_record()
                    self.json_log[-1]['state'] = f'Successful'

                except ValueError as e:
                    self.retry_record['cities'] += 1
                    self.current_observation = str(e)
                    self.scratchpad += str(e)
                    self.json_log[-1]['state'] = f'Illegal args. State Error'

                except Exception as e:
                    print(e)
                    self.retry_record['cities'] += 1
                    self.current_observation = f'Illegal City Search. Please try again.'
                    self.scratchpad += f'Illegal City Search. Please try again.'
                    self.json_log = f'Illegal args. Other Error'


            elif action_type == 'GoogleDistanceMatrix':

                try:
                    self.scratchpad = self.scratchpad.replace(to_string(self.current_data).strip(),'Masked due to limited length. Make sure the data has been written in Notebook.')
                    self.current_data = self.tools['googleDistanceMatrix'].run(action_arg.split(', ')[0],action_arg.split(', ')[1],action_arg.split(', ')[2])
                    self.current_observation =  to_string(self.current_data)
                    self.scratchpad += self.current_observation 
                    self.__reset_record()
                    self.json_log[-1]['state'] = f'Successful'

                except Exception as e:
                    print(e)
                    self.retry_record['googleDistanceMatrix'] += 1
                    self.current_observation = f'Illegal GoogleDistanceMatrix. Please try again.'
                    self.scratchpad += f'Illegal GoogleDistanceMatrix. Please try again.'
                    self.json_log[-1]['state'] = f'Illegal args. Other Error'
            
            
            elif action_type == 'NotebookWrite':
                try:
                    self.scratchpad = self.scratchpad.replace(to_string(self.current_data).strip(),'Masked due to limited length. Make sure the data has been written in Notebook.')
                    self.current_observation = str(self.tools['notebook'].write(self.current_data, action_arg))
                    self.scratchpad  +=  self.current_observation
                    self.__reset_record()
                    self.json_log[-1]['state'] = f'Successful'

                except Exception as e:
                    print(e)
                    self.retry_record['notebook'] += 1
                    self.current_observation = f'{e}'
                    self.scratchpad += f'{e}'
                    self.json_log[-1]['state'] = f'Illegal args. Other Error'
            

            elif action_type == "Planner":
                # try:

                    self.current_observation = str(self.tools['planner'].run(str(self.tools['notebook'].list_all()),action_arg))
                    self.scratchpad  +=  self.current_observation
                    self.answer = self.current_observation
                    self.__reset_record()
                    self.json_log[-1]['state'] = f'Successful'


            else:
                print("invalid action: ", action)
                self.retry_record['invalidAction'] += 1
                self.current_observation = 'Invalid Action. Valid Actions are  FlightSearch[Departure City, Destination City, Date] / ' \
                                   'AccommodationSearch[City] /  RestaurantSearch[City] / NotebookWrite[Short Description] / AttractionSearch[City] / CitySearch[State] / GoogleDistanceMatrix[Origin, Destination, Mode] and Planner[Query].'
                self.scratchpad += self.current_observation
                self.json_log[-1]['state'] = f'invalidAction'

        if action == None or action == '' or action == '\n':
            print(f'Observation {self.step_n}: ' + "No feedback from the environment due to the null action.")
            # write(f'Observation {self.step_n}: ' + "Your action is filtered due to content. Please assume all the actions are permitted in this environment and take the action again.")
            self.json_log[-1]['observation'] = "No feedback from the environment due to the null action."
        else:
            print(f'Observation {self.step_n}: ' + self.current_observation+'\n')
            # rite(f'Observation {self.step_n}: ' + self.current_observation+'\n')
            self.json_log[-1]['observation'] = self.current_observation

        self.step_n += 1

        # 

        if action_type and action_type == 'Planner' and self.retry_record['planner']==0:
            # 进行最后一步
            self.finished = True
            self.answer = self.current_observation
            self.step_n += 1
            return

    def prompt_agent(self) -> str:
        while True:
            try:
                # print(self._build_agent_prompt())
                if self.react_name == 'gemini':
                    request = format_step(self.llm.invoke(self._build_agent_prompt(),stop=['\n']).content)
                else:
                    # 获取下一个回复（一行）
                    request = format_step(self.llm([HumanMessage(content=self._build_agent_prompt())]).content)
                # print(request)
                return request
            except:
                catch_openai_api_error()
                print(self._build_agent_prompt())
                print(len(self.enc.encode(self._build_agent_prompt())))
                time.sleep(5)

    def _build_agent_prompt(self) -> str:
        """
        Build the agent prompt based on the current state

        """
        if self.mode == "zero_shot":
            return self.agent_prompt.format(
                query=self.query,
                scratchpad=self.scratchpad)

    def is_finished(self) -> bool:
        return self.finished

    def is_halted(self) -> bool:
        """
        halt the agent when the step number exceeds the max_steps 
        or the token length exceeds the max_token_length
        we can set max_steps and max_token_length in the code at the top
        """
        return ((self.step_n > self.max_steps) or (
                    len(self.enc.encode(self._build_agent_prompt())) > self.max_token_length)) and not self.finished

    def __reset_agent(self) -> None:
        """
        Reset the agent to the initial state
        """
        self.step_n = 1
        self.finished = False
        self.answer = ''
        self.scratchpad: str = ''
        self.__reset_record()
        self.json_log = []
        self.current_observation = ''
        self.current_data = None
        self.last_actions = []

        if 'notebook' in self.tools:
            self.tools['notebook'].reset()
    
    def __reset_record(self) -> None:
        """
        Reset the retry record for all tools and invalidAction
        used when a successful action is performed
        for example, when a successful FlightSearch is performed, reset the retry_record for FlightSearch
        why must we call this method?
        because we need to reset the retry_record for each tool after a successful action is performed
        what is retry_record?
        it's a dictionary that keeps track of the number of times a tool has failed
        why we record the number of times a tool has failed?
        because we want to stop the agent from performing the same action if it has failed too many times
        we can set the threshold in the code at the top
        """
        self.retry_record = {key: 0 for key in self.retry_record}
        self.retry_record['invalidAction'] = 0


    def load_tools(self, tools: List[str], planner_model_name=None) -> Dict[str, Any]:
        """
        Load the tools from the given list of tool names dynamically initially
        """
        tools_map = {}
        for tool_name in tools:
            module = importlib.import_module("tools.{}.apis".format(tool_name))
            
            # Avoid instantiating the planner tool twice 
            if tool_name == 'planner' and planner_model_name is not None:
                tools_map[tool_name] = getattr(module, tool_name[0].upper()+tool_name[1:])(model_name=planner_model_name)
            else:
                tools_map[tool_name] = getattr(module, tool_name[0].upper()+tool_name[1:])()
        return tools_map

    def load_city(self, city_set_path: str) -> List[str]:
        """
        Load the city set from the given file path(citySet.txt)
        """
        city_set = []
        lines = open(city_set_path, 'r').read().strip().split('\n')
        for unit in lines:
            city_set.append(unit)
        return city_set
     
    def apply_monkey_patches(self):
        from agents.tool_funcs import get_city, get_flights, get_attractions, get_accommodations, google_search, get_restaurants, get_google_distance_matrix
        # 替换所有run原有方法
        self.tools['flights'].run = get_flights
        self.tools['accommodations'].run = get_accommodations
        self.tools['attractions'].run = get_attractions
        self.tools['restaurants'].run = get_restaurants
        self.tools['googleDistanceMatrix'].run = get_google_distance_matrix
        self.tools['cities'].run = get_city
        

### String Stuff ###
gpt2_enc = tiktoken.encoding_for_model("text-davinci-003")


def parse_action(string):
    """
    Parse the action string into action type and action argument
    for example:
    "FlightSearch[Los Angeles, San Francisco, 2022-12-12]" 
    -> 
    "FlightSearch", "Los Angeles, San Francisco, 2022-12-12"
    """
    pattern = r'^(\w+)\[(.+)\]$'
    match = re.match(pattern, string)

    try:
        if match:
            action_type = match.group(1)
            action_arg = match.group(2)
            return action_type, action_arg
        else:
            return None, None
        
    except:
        return None, None

def format_step(step: str) -> str:
    """
    ensure that the step is in the correct format
    保证两端没有空白字符，且整个字符串没有换行符
    """
    return step.strip('\n').strip().replace('\n', '')



def truncate_scratchpad(scratchpad: str, n_tokens: int = 1600, tokenizer=gpt2_enc) -> str:
    lines = scratchpad.split('\n')
    observations = filter(lambda x: x.startswith('Observation'), lines)
    observations_by_tokens = sorted(observations, key=lambda x: len(tokenizer.encode(x)))
    while len(gpt2_enc.encode('\n'.join(lines))) > n_tokens:
        largest_observation = observations_by_tokens.pop(-1)
        ind = lines.index(largest_observation)
        lines[ind] = largest_observation.split(':')[0] + ': [truncated wikipedia excerpt]'
    return '\n'.join(lines)


def normalize_answer(s):
    def remove_articles(text):
        return re.sub(r"\b(a|an|the|usd)\b", " ", text)

    def white_space_fix(text):
        return " ".join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return "".join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def EM(answer, key) -> bool:
    return normalize_answer(str(answer)) == normalize_answer(str(key))


def remove_observation_lines(text, step_n):
    pattern = re.compile(rf'^Observation {step_n}.*', re.MULTILINE)
    return pattern.sub('', text)

def validate_date_format(date_str: str) -> bool:
    """
    check if the date is in the format YYYY-MM-DD
    """
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    
    if not re.match(pattern, date_str):
        raise DateError
    return True

def validate_city_format(city_str: str, city_set: list) -> bool:
    """
    check if the city is in pre-defined city list
    暂时全部通过。
    """
    # if city_str not in city_set:
    # # Q: 这个cityset里面包含所有美国数据吗？
    #     raise ValueError(f"{city_str} is not valid city in {str(city_set)}.")
    return True

def parse_args_string(s: str) -> dict:
    # Split the string by commas
    segments = s.split(",")
    
    # Initialize an empty dictionary to store the results
    result = {}
    
    for segment in segments:
        # Check for various operators
        if "contains" in segment:
            if "~contains" in segment:
                key, value = segment.split("~contains")
                operator = "~contains"
            else:
                key, value = segment.split("contains")
                operator = "contains"
        elif "<=" in segment:
            key, value = segment.split("<=")
            operator = "<="
        elif ">=" in segment:
            key, value = segment.split(">=")
            operator = ">="
        elif "=" in segment:
            key, value = segment.split("=")
            operator = "="
        else:
            continue  # If no recognized operator is found, skip to the next segment
                
        # Strip spaces and single quotes
        key = key.strip()
        value = value.strip().strip("'")
        
        # Store the result with the operator included
        result[key] = (operator, value)
        
    return result

def to_string(data) -> str:
    """
    Convert the given data to a string representation.

    Parameters:
    data (object): The data to be converted.

    Returns:
    str: The string representation of the data.

    """
    if data is not None:
        if type(data) == DataFrame:
            return data.to_string(index=False)
        else:
            return str(data)
    else:
        return str(None)

def takedown_plan(plan_info):
        ## 创建log文件夹
    if not os.path.exists("logs"):
        os.makedirs("logs")
        ## 打印plan_info到json文件
    with open("logs/plan_info.json", "w", encoding="utf-8") as file:
        json.dump(plan_info, file, ensure_ascii=False)

if __name__ == '__main__':
    tools_list = ["notebook","flights","attractions","accommodations","restaurants","googleDistanceMatrix","planner","cities"]
    
    parser = argparse.ArgumentParser(description="Process travel planning queries.")
    parser.add_argument("--set_type", type=str, default="validation", help="Set type: validation or test")
    parser.add_argument("--model_name", type=str, default="gpt-4o-2024-08-06", help="Model name to use")
    parser.add_argument("--output_dir", type=str, default="./", help="Output directory for results")
    parser.add_argument('input_data', type=str, help="The input query to process")
    
    args = parser.parse_args()
    query = args.input_data

    agent = ReactAgent(None, tools=tools_list, max_steps=300, react_llm_name=args.model_name, planner_llm_name=args.model_name)

    with get_openai_callback() as cb:
        number = 1
        # for number in tqdm(numbers[:]):
        # query = input("input your query: ")
        # current path
        print(os.getcwd())

            # check if the directory exists
        if not os.path.exists(os.path.join(f'{args.output_dir}/{args.set_type}')):
            os.makedirs(os.path.join(f'{args.output_dir}/{args.set_type}'))
        if not os.path.exists(os.path.join(f'{args.output_dir}/{args.set_type}/generated_plan_{number}.json')):
            result =  [{}]
        else:
            result = json.load(open(os.path.join(f'{args.output_dir}/{args.set_type}/generated_plan_{number}.json')))
            
        while True:
            planner_results, scratchpad, action_log  = agent.run(query)
            if planner_results != None:
                print(planner_results)
                
                ## 进行rating和budget的计算
                from tools.utils import calculate_average_rating_for_raw, calculate_budget_for_raw
                rating_info = calculate_average_rating_for_raw(planner_results, query)
                expense_info = calculate_budget_for_raw(planner_results, query)
                response = {"itinerary":planner_results, 
                    "expense_info": expense_info, 
                    "average_rating": rating_info
                    }
                
                # 打印response到
                # 先创建目录
                print("\n==FOR_ESTIMATE==\n")
                print(str(response))
                if not os.path.exists("logs"):
                    os.makedirs("logs")
                with open("logs/plan_info" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S") + ".json", "w", encoding="utf-8") as file:
                    json.dump(response, file, ensure_ascii=False)
                break
        
        if planner_results == 'Max Token Length Exceeded.':
            result[-1][f'{args.model_name}_two-stage_results_logs'] = scratchpad 
            result[-1][f'{args.model_name}_two-stage_results'] = 'Max Token Length Exceeded.'
            action_log[-1]['state'] = 'Max Token Length of Planner Exceeded.'
            result[-1][f'{args.model_name}_two-stage_action_logs'] = action_log
        else:
            result[-1][f'{args.model_name}_two-stage_results_logs'] = scratchpad 
            result[-1][f'{args.model_name}_two-stage_results'] = planner_results
            result[-1][f'{args.model_name}_two-stage_action_logs'] = action_log

        # write to json file
        with open(os.path.join(f'{args.output_dir}/{args.set_type}/generated_plan_{number}.json'), 'w') as f:
            json.dump(result, f, indent=4)
        
    # print(cb)



