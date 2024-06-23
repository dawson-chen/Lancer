import yaml
import api


class Config:

    def __init__(self, context_dict={}) -> None:
        self.config_dict = {}
        with open('configs/config.yaml', encoding='utf-8') as f:
            self.config_dict = yaml.safe_load(f)
        
        api_config = self.config_dict.get('API', {})
        base_url = api_config.get('base_url', None)
        api_key = api_config.get('api_key', None)
        model_name = api_config.get('model_name', None)
        api.setup_client(base_url, api_key, model_name)
        
        self.context_info = context_dict.get('context_info', None)
        self.select_text = context_dict.get('select_text', None)

        self.always_on_top = self.config_dict['default'].get('always_on_top', True)
        self.close_when_focus_out = self.config_dict['default'].get('close_when_focus_out', False)

        self.system_prompt_wo_context = self.config_dict['default'].get('system_prompt_wo_context', '')
        self.system_prompt = self.config_dict['default'].get('system_prompt', '')
        self.user_prompt = self.config_dict['default'].get('user_prompt', '')
        self.user_prompt_custom = self.config_dict['default'].get('user_prompt_custom', '')
        self.load_custom_config()
        
    def load_custom_config(self,):
        self.custom_config_list = self.config_dict.get('custom', [])
        
        custom_task_prompt = '用户指定的需求：\n\n'
        matched_app = None
        for each in self.custom_config_list:
            custom_task_prompt += f'当前软件：{each["app"]}\n对应功能：\n'
            for task in each.get('tasks', []):
                custom_task_prompt += f'- {task}\n'
            custom_task_prompt += "\n\n"
        self.custom_task_prompt = custom_task_prompt
        
    def get_prompts(self,):
        matched_config = None
        for each in self.custom_config_list:
            if self.context_info and isinstance(self.context_info, dict) and \
                each["app"].lower() in self.context_info['application_name'].lower():
                matched_config = each

        system_prompt = self.system_prompt_wo_context
        user_prompt = None
        if self.select_text:
            system_prompt = self.system_prompt.replace(
                '{context_info}', f'{self.context_info}'
            ).replace(
                '{text}', f'{self.select_text}'
            )
            if self.custom_config_list:
                system_prompt = system_prompt.replace('{custom_tasks}', self.custom_task_prompt)
            else:
                system_prompt = system_prompt.replace('{custom_tasks}', '')
            user_prompt = self.user_prompt
            
            
            if matched_config and matched_config.get('tasks', []):
                tasks = matched_config.get('tasks', [])
                custom_task_prompt = f'功能：\n'
                for task in tasks:
                    custom_task_prompt += f'- {task} \n'
                custom_task_prompt += "\n\n"
                user_prompt = self.user_prompt_custom.replace('{custom_tasks}', custom_task_prompt)
                
        return system_prompt, user_prompt
        
                
        
if __name__ == '__main__':
    config = Config({
        'active_app':{'application_name': 'notion', 'subTitle': '晋升答辩'}, 
        'select_text': '个人优缺点如下：'
    })
    system_prompt, user_prompt = config.get_prompts()
    print(system_prompt)
    
    print(user_prompt)
    