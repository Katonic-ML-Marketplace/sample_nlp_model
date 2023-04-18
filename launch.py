
import pandas as pd
from typing import Any, Union,Dict
from transformers import PegasusTokenizer, PegasusForConditionalGeneration, TFPegasusForConditionalGeneration
import requests
import json
import os

def loadmodel(logger):
    """Get model from cloud object storage."""
    model_name = f"human-centered-summarization/financial-summarization-pegasus"
    logger.info(f"model file path {model_name}")
    model = PegasusForConditionalGeneration.from_pretrained(model_name)
    logger.info("returning model object")
    return model  

def preprocessing(text_to_summarize:str,logger):
    """ Applies preprocessing techniques to the raw data"""
    logger.info("loading tokniser model")
    model_name = f"human-centered-summarization/financial-summarization-pegasus"
    tokenizer = PegasusTokenizer.from_pretrained(model_name)
    ## in template keep this False by default, if its there then the return result will be other than False
    logger.info("creating tokens")
    input_ids = tokenizer(text_to_summarize, return_tensors="pt").input_ids
    return input_ids
    
def predict(features,model,logger):
    """Predicts the results for the given inputs"""
    logger.info(f"input:{features[:10]}")
    logger.info("model prediction")
    model_name = f"human-centered-summarization/financial-summarization-pegasus"
    try:
        output = model.generate(
        features, 
        max_length=32, 
        num_beams=5, 
        early_stopping=True
        )
    except Exception as e:
        logger.info(e)
    logger.info("prediction decoding")
    tokenizer = PegasusTokenizer.from_pretrained(model_name)
    predicted_result = tokenizer.decode(output[0], skip_special_tokens=True)
#     pred_results = json.dumps(predicted_result)
    return predicted_result
