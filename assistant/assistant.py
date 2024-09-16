import os
from groq import Groq
from lib.errors import Errors
from assistant.prompts import AIPrompts

import pandas as pd
from pandasai import SmartDataframe
from langchain_groq.chat_models import ChatGroq

# AI Assistant class ---------------------------------------------------------------------------------------------
class assistant():
    def __init__(self):
        return

    def __del__(self):
        return

    def findGDPRData(self,groq_api_key,model,temperature,sampledata):
        llm = ChatGroq(model = model,temperature = temperature, api_key = groq_api_key)
        sdf = SmartDataframe(sampledata,config = {'llm':llm})
        try:
            return sdf.chat(AIPrompts.findGDPRData)
        except Exception as e:
            return False


    def replaceDPRData(self,groq_api_key,model,temperature,sampledata):
        llm = ChatGroq(model = model,temperature = temperature, api_key = groq_api_key)       
        # Adding https://pypi.org/project/Faker/ to the whitelist of dependencies
        sdf = SmartDataframe(sampledata,config = {'llm':llm, "custom_whitelisted_dependencies": ["faker"]})       
        try:
            redux = sdf.chat(AIPrompts.replaceGDPRData)  
            if type(redux) is pd.core.frame.DataFrame:
                return redux
            else:
                print(f'Steps has been skipped because redux is type of {type(redux)}')
            
        except Exception as e:
            return False
