import logging 
import logging.config
from pathlib import Path

import yaml 
_CONFIG_LOADED = False


def _setup_logging() -> None:
    
    """ 
    ## Sets Up Logging Configuration
    - Sets up logging configuration from a YAML file. 
    - This function is called once to configure the logging settings for the application.
    - It reads the logging configuration from 'config/logging_config.yaml' and applies it using the logging.config.dictConfig method.
    """
    global _CONFIG_LOADED
    
    if _CONFIG_LOADED:
        return
    
    config_path  = Path("config/logging_config.yaml")
    
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
        
    logging.config.dictConfig(config)
    
    _CONFIG_LOADED = True
    

def get_logger(name: str) -> logging.Logger:
    """
    ### Gets a logger instance with the specified name.
    """
    _setup_logging()
    return logging.getLogger(name)