import logging
import sys

# Configure logging
logger = logging.getLogger('HomutBot')
logger.setLevel(logging.INFO)

# Create console handler with a higher log level
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# Add console handler to the logger
logger.addHandler(console_handler)
