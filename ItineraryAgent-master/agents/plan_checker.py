from datetime import datetime
import json
import sys
import os
import re
from typing import Dict
import time
from tenacity import retry, stop_after_attempt, wait_fixed
print(os.getcwd())
sys.path.append(os.path.abspath(os.getcwd()))
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, '..'))
from chat_model import OpenAIChat
from prompts import *
from config import *

def calculate_budget(response):
    """
    Receives the output that has already been processed by COT
    """
    response = response.split("Summary")[-1].strip('=').strip().strip('`').strip()
    total_budget = 0
    categories = ['Unit', 'Transportation', 'Attractions', 'Accommodation', 'Dining']
    expense_info = {}
    
    lines = response.splitlines()
    if not len(lines) == len(categories):
        print(f"Unable to calculate budget: {response}")
        raise Exception(f"Unable to calculate budget: {response}")
    
    for i, category in enumerate(categories):
        if i < len(lines):
            if category == 'Unit':
                unit_value = lines[i].split(':', 1)[-1].strip()
                expense_info['Unit'] = unit_value
            else:
                expr = lines[i].split(':', 1)[-1].strip()
                try:
                    category_total = eval(expr)
                    expense_info[category] = round(category_total, 2)
                    total_budget += category_total
                except:
                    print(f"Unable to calculate expression: {expr}")
                    raise Exception(f"Unable to calculate expression: {expr}")

    expense_info['Total'] = round(total_budget, 2)
    print(str(expense_info))
    return expense_info


def calculate_rating(response):
    """
    Receives the output that has already been processed by COT
    """
    response = response.split("Summary")[-1].strip('=').strip().strip('`').strip()
    total_rating = 0
    categories = ['Total Restaurant Ratings', 'Total Attraction Ratings', 'Total Accommodation Ratings']
    rating_info = {}
    
    lines = response.splitlines()
    if not len(lines) == 3:
        raise Exception(f"Unable to calculate rating: {response}")
    for i, category in enumerate(categories):
        if i < len(lines):
            expr = lines[i].split(':', 1)[-1].strip()
            try:
                category_total = eval(expr)
            except:
                print(f"unable to calculate expression: {expr}")
                category_total = 0
                raise
            rating_info[category] = category_total
            total_rating += category_total
    
    rating_info['Total Restaurant Ratings'] = round(rating_info['Total Restaurant Ratings'], 2)
    rating_info['Total Attraction Ratings'] = round(rating_info['Total Attraction Ratings'], 2)
    rating_info['Total Accommodation Ratings'] = round(rating_info['Total Accommodation Ratings'], 2)
    rating_info['Total'] = round(total_rating, 2)
    print(str(rating_info))
    return rating_info
    
def count_poi(response):
    response = response.split("Summary")[-1].strip('=').strip().strip('`').strip()
    total_count = 0
    categories = ['Total Restaurants', 'Total Attractions', 'Total Accommodations']
    poi_info = {}
    
    lines = response.splitlines()
    if not len(lines) == 3:
        print(f"Unable to count POIs: len(lines) = {len(lines)}")
        raise Exception(f"Unable to count POIs: len(lines) = {len(lines)}")
    for i, category in enumerate(categories):
        if i < len(lines):
            expr = lines[i].split(':', 1)[-1].strip()
            try:
                category_total = eval(expr)
            except:
                print(f"Unable to calculate expressions: {expr}")
                category_total = 0
                raise
            poi_info[category] = category_total
            total_count += category_total
    
    poi_info['Total'] = total_count
    print(str(poi_info))
    return poi_info


class PlanChecker:
    def __init__(self, **kwargs) -> None: 
        kwargs['model'] = kwargs.get('model', 'gpt-4o')
        kwargs['temperature'] = kwargs.get('temperature', 0)
        kwargs['is_verbose'] = True
        self.kwargs = kwargs
        self.model = OpenAIChat(**kwargs)
        
        print("Initializing PlanChecker with model info:", kwargs)
        self.expense_info : Dict[str, float] = {}
        self.rating_info : Dict[str, str] = {}
        self.average_rating : Dict[str, float] = {}


    def build_system_input(self, query, extra_requirements, check_stage: str):
        if check_stage == 'budget':
            sys_prompt = PLAN_CHECKER_PROMPT_BUDGET.format(extra_requirements=extra_requirements, query=query)
        elif check_stage == 'reasonability':
            sys_prompt = PLAN_CHECKER_PROMPT.format(extra_requirements=extra_requirements, query=query, current_date=datetime.now().strftime("%Y-%m-%d"))
        return sys_prompt

        
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _budget_check(self, plan, query, extra_requirements):
        sys_prompt = self.build_system_input(query, extra_requirements, check_stage='budget')
        history = []
        response, history = self.model.chat(prompt=f"Here is the user's requirements:\n{query}\nHere is the itinerary:\n{plan}", history=history, meta_instruction=sys_prompt)
        
        self.expense_info = calculate_budget(response)
        self.model.kwargs['model'] = 'gpt-4o'
        response, history = self.model.chat(prompt=JUDGE_BUDGET_PROMPT.format(
            expense_info="\n"+str(self.expense_info),
            query=query),
                                   history=history,
                                   meta_instruction="You are a Budget Analyst.")
        try:
            print("budget check result:", response)
            response = response.strip().strip('```json').strip('```').strip()
            response = json.loads(response)
        
            if not ((response['if_the_user_provides_budget']['meets_criteria'] == False) or (response['total_expense_greater_than_eighty_percent_of_budget']['meets_criteria'] and 
                   response['expense_not_greater_than_required_budget']['meets_criteria'])):
                print("start budget advice")
                response, history = self.model.chat(prompt=BUDGET_ADVICE_PROMPT,
                                    history=history,
                                    meta_instruction=sys_prompt)
                return response+f"Current budget for each item is as follows：\n{str(self.expense_info)}\n"
        except Exception as e:
            print("Unable to parse budget check result:", e)
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _reasonability_check(self, plan, query, extra_requirements):
        history = []
        sys_prompt = self.build_system_input(query, extra_requirements, check_stage='reasonability')
        
        self.model.kwargs['model'] = 'gpt-4o'
        response, history = self.model.chat(
            prompt=ANALYZE_REASONABILITY_PROMPT.format(plan=plan), 
            history=history, 
            meta_instruction=sys_prompt)
        
        response = response.strip().strip('```json').strip('```').strip()
        response = json.loads(response)
        
        # 修改判断逻辑，检查 Itinerary_Review 中每个条目的 meets_criteria
        if not all(item["meets_criteria"] for item in response["Itinerary_Review"]): 
            # 输出不满足的标准
            failed_criteria = [
                item["criteria"] 
                for item in response["Itinerary_Review"] 
                if not item["meets_criteria"]
            ]
            for criterion in failed_criteria:
                print(f"The {criterion} criterion is not met.")
            
            response, history = self.model.chat(
                prompt=REASONABILITY_ADVICE_PROMPT,
                history=history,
                meta_instruction=sys_prompt
            )
            return response
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _rating_summary(self, plan):
        self.model.kwargs['model'] = 'gpt-4o'
        response, _ = self.model.chat(prompt=f"Here is the itinerary:\n{plan}",
                                            history=[],
                                            meta_instruction=RATING_SUMMARY_SYSTEM_PROMPT)
        self.rating_info = calculate_rating(response)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    def _count_poi(self, plan):
        response, _ = self.model.chat(prompt=f"Here is the itinerary:\n{plan}",
                                            history=[],
                                            meta_instruction=COUNT_POI_SYSTEM_PROMPT)
        self.poi_count = count_poi(response)

    def check_plan(self, plan, query, extra_requirements='') -> str:

        # 先检查基本面
        reasonability_result = self._reasonability_check(plan, query, extra_requirements)
        if reasonability_result:
            return reasonability_result

        # 行程通过，检查预算
        try:
            budget_result = self._budget_check(plan, query, extra_requirements)
        except Exception as e:
            print(f"Unable to calculate expenses. Please provide more detailed cost information in the itinerary.: {str(e)}")
            budget_result = "Unable to calculate expenses. Please provide more detailed cost information in the itinerary!"
        if budget_result:
            return budget_result
        
        # 行程通过，计算评分和POI数量
        self._rating_summary(plan)
        self._count_poi(plan)
        
        # 计算平均评分
        self.average_rating = {}
        categories = [
            ('Attractions', 'Total Attraction Ratings', 'Total Attractions'),
            ('Accommodations', 'Total Accommodation Ratings', 'Total Accommodations'),
            ('Restaurants', 'Total Restaurant Ratings', 'Total Restaurants'),
            ('Overall', 'Total', 'Total')
        ]
        
        for category, rating_key, count_key in categories:
            total_rating = self.rating_info[rating_key]
            total_count = self.poi_count[count_key]
            
            self.average_rating[category] = round(total_rating / total_count, 2) if total_count > 0 else 0.0
        
        print(f"Average rating: {self.average_rating}")
        
        
        return "No more suggestion"

def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

if __name__ == '__main__':
    plan_checker = PlanChecker()
    plan = read_file(os.path.join(current_dir, 'example_plan.txt'))
    query = read_file(os.path.join(current_dir, 'example_query.txt'))
    extra_requirements = ''
    response = plan_checker.check_plan(plan, query, extra_requirements)
    print(str(response))
