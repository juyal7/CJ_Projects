import os
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

# Initialize LangChain Ollama LLM (replace with your desired model)
# By default, this connects to the locally running Ollama server
llm = Ollama(model="gemma3:1b", temperature=0)

# Define the prompt template for translation
template = """
Translate the following English sentence to French:

'{sentence}'
"""
prompt = PromptTemplate(template=template, input_variables=["sentence"])

def translate_with_langchain(sentence):
    """Translate English text to French using LangChain and Ollama."""
    # Create an LLM chain with our prompt and model
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # Run the chain with the input sentence
    result = chain.run(sentence)
    
    # Return the translated text
    return result.strip()

# Test the LangChain-based translation
if __name__ == "__main__":
    test_sentence = "Hello, world!"
    response = translate_with_langchain(test_sentence)
    print(f"Original: {test_sentence}")
    print(f"Translated: {response}")