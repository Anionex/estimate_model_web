import sys
import os
import logging



logger = logging.getLogger(__name__)
print(os.getcwd())
print(os.path.join(os.getcwd(), "tools"))
sys.path.append(os.path.abspath(os.getcwd()))
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "tools")))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, root_dir)
from datetime import datetime
import json5
from utils.chat_model import OpenAIChat
from tool_registry import Tools
from prompts import REACT_PROMPT, TOOL_DESC
import os, sys
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, root_dir)
from utils.config import *

from tool_funcs import calculator, google_search

THOUGHT_HEADER = "<Analysis:"
ACTION_HEADER = "<Tool Invocation:"
ACTION_INPUT_HEADER = "<Tool Input:"
ACTION_OUTPUT_HEADER = "Tool Output:"
ANSWER_HEADER = "<Itinerary:"


class ReactAgent:
    def __init__(self, **kwargs) -> None: 
        self.tools = Tools()
        kwargs['model'] = kwargs.get('model', 'gpt-4o')
        kwargs['stop'] = kwargs.get('stop', ['\n'])
        kwargs['temperature'] = kwargs.get('temperature', 0)
        self.kwargs = kwargs
        self.model = OpenAIChat(**kwargs)
        print("Initializing ReactAgent with model info:", kwargs)
        self.scratchpad = ""
        self.hit_final_answer = False


    def build_system_input(self, query, extra_requirements, system_prompt):
        tool_descs, tool_names = [], []
        for tool in self.tools.toolConfig:
            tool_descs.append(TOOL_DESC.format(**tool))
            tool_names.append(tool['name_for_model'])
        tool_descs = '\n\n'.join(tool_descs)
        tool_names = ','.join(tool_names)
        sys_prompt = system_prompt.format(tool_descs=tool_descs, 
                                         tool_names=tool_names, 
                                         current_date=datetime.now().strftime("%Y-%m-%d"), 
                                         query=query,
                                         extra_requirements=extra_requirements)
        if GLOBAL_LANGUAGE != "en":
            sys_prompt += f"\n请你使用{GLOBAL_LANGUAGE}作为输出语言"
        return sys_prompt
    
    def parse_latest_plugin_call(self, text):
        # 查找最后一个 Tool Invocation 和 Tool Input
        tool_invocation = text.split(ACTION_HEADER)[-1].split(STOP_WORD)[0].strip().strip('"') # 去掉一个加上的STOP_WORD
        tool_input = text.split(ACTION_INPUT_HEADER)[-1].strip().strip('"')
        print("tool_invocation:", tool_invocation)
        print("tool_input:", tool_input)
        return tool_invocation, tool_input
    def call_plugin(self, plugin_name, plugin_args):

        try:
            plugin_args = json5.loads(plugin_args)
        except Exception as e:
            return f'\n{ACTION_OUTPUT_HEADER}' + f"Input parsing error: {str(e)} Please check if the input parameters are correct"
        # print(f"success! then we will call the tool {plugin_name} with args {plugin_args}")
        try:
            return f'\n{ACTION_OUTPUT_HEADER}\n' + str(self.tools.execute_tool(plugin_name, **plugin_args))
        except Exception as e:
            return f'\n{ACTION_OUTPUT_HEADER}' + f"Tool execution error: {str(e)} Please check if the input parameters are correct"

    
    def step(self, scratchpad):
        # return self.model.create_assistant_completion(scratchpad, meta_instruction=self.system_prompt)
        return self.model.chat(scratchpad, [], self.system_prompt)[0]

      
    def run(self, query, extra_requirements="", system_prompt=REACT_PROMPT):
        # 构建系统提示词
        self.system_prompt = self.build_system_input(query, extra_requirements, system_prompt)
        # print(self.system_prompt)
        # 
        # print("system_prompt: ", self.system_prompt)
        self.model.kwargs = self.kwargs
        while True:
            response = self.step(self.scratchpad)
            is_tool_input = response.startswith(ACTION_INPUT_HEADER)
            if response.startswith(ANSWER_HEADER):
                print("=====\nGET AN ITINERARY\n=====")
                self.hit_final_answer = True
            elif response.startswith(THOUGHT_HEADER) or response.startswith("<Draft:"):
                pass
            elif is_tool_input:
                plugin_name, plugin_args = self.parse_latest_plugin_call(self.scratchpad+'\n'+ response)
                delta = self.call_plugin(plugin_name, plugin_args)
                response += STOP_WORD + delta
            elif response.startswith(ACTION_HEADER):
                pass
            elif response.startswith(ACTION_OUTPUT_HEADER):
                response = "Please remember that you shouldn't generate Tool Output by yourself"
            else:
                print("the ai gave an unexpected response:", response)
                if response != "error: list index out of range":
                    logger.info(f"the model give response: {response}\n")
                    response = f"Please remember that only the following tags are allowed: {THOUGHT_HEADER + STOP_WORD}, {ACTION_HEADER + STOP_WORD}, {ACTION_INPUT_HEADER + STOP_WORD}, {ANSWER_HEADER}"
            if not is_tool_input:
                response += STOP_WORD
            print("[1]" + response)
            
            # 修改日志文件路径处理
            try:
                # 获取项目根目录（使用绝对路径）
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                log_path = os.path.join(project_root, "my_react_agent_response1.txt")
                
                # 确保父目录存在
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                
                # 写入日志
                with open(log_path, "a", encoding='utf-8') as f:
                    f.write(response + "\n")  
            except Exception as e:
                print(f"Log writing error: {str(e)}")
                
                
            self.scratchpad += '\n' + response
            
            # 限制 scratchpad 只保留最新的30次回复
            responses = self.scratchpad.split(STOP_WORD)
            if len(responses) > MAX_SCRATCHPAD_ITEMS:
                self.scratchpad = STOP_WORD.join(responses[-MAX_SCRATCHPAD_ITEMS:])
                
            if self.hit_final_answer:
                return response
    
    
            

