import os
import asyncio
import logging
from claude_repo_creator import ClaudeRepoCreator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    async def main():
        async with ClaudeRepoCreator(debug_mode=debug_mode) as creator:
            await creator.run()

    asyncio.run(main())
